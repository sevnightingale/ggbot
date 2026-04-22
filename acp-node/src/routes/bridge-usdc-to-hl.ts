// Bridge USDC from the agent's Arbitrum wallet balance into Hyperliquid.
//
// The agent's Privy smart wallet lives at the same address on Base and Arbitrum.
// For MVP the user deposits USDC directly to the agent wallet on Arbitrum; this
// route then signs an ERC-20 transfer of that USDC to the Hyperliquid bridge
// contract (0x2df1c51e09aecf9cacb7bc98cb1742757f163df7), which credits the
// agent's HL unified account.
//
// Native USDC on Arbitrum: 0xaf88d065e77c8cC2239327C5EDb3A432268e5831 (6 decimals).
// HL bridge minimum: 5 USDC.

import type { FastifyInstance } from 'fastify'
import { encodeFunctionData, erc20Abi, parseUnits } from 'viem'
import { arbitrum, base } from 'viem/chains'
import { getEvmAdapter } from '../lib/privy-sign.js'

const USDC_ARBITRUM = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' as const
const HL_BRIDGE = '0x2df1c51e09aecf9cacb7bc98cb1742757f163df7' as const
const ARBITRUM_CHAIN_ID = arbitrum.id
const HL_BRIDGE_MIN_USDC = 5

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
  amountUsdc: string          // human-readable, e.g., "25" or "10.5"
}

export function registerBridgeUsdcToHl(app: FastifyInstance) {
  app.post<{ Body: Body }>('/bridge-usdc-to-hl', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey, amountUsdc } = req.body

    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey || !amountUsdc) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    const amountNumber = Number(amountUsdc)
    if (!Number.isFinite(amountNumber) || amountNumber < HL_BRIDGE_MIN_USDC) {
      reply.code(400).send({
        error: `amountUsdc must be a finite number >= ${HL_BRIDGE_MIN_USDC} (HL bridge minimum)`,
      })
      return
    }

    let adapter
    try {
      // Pass both chains so future operations (signing ACP jobs on Base, etc.)
      // still work with the same adapter instance.
      adapter = await getEvmAdapter({
        agentWalletAddress,
        agentWalletId,
        signerPrivateKey,
        chains: [base, arbitrum],
      })
    } catch (err) {
      req.log.error({ err }, 'bridge-usdc-to-hl: adapter init failed')
      reply.code(502).send({ error: 'privy adapter init failed', detail: String(err) })
      return
    }

    // parseUnits handles fractional strings correctly; "10.5" → 10_500_000n
    const amountRaw = parseUnits(amountUsdc, 6)

    const calldata = encodeFunctionData({
      abi: erc20Abi,
      functionName: 'transfer',
      args: [HL_BRIDGE, amountRaw],
    })

    req.log.info(
      { agentWalletAddress, amountUsdc, amountRaw: amountRaw.toString() },
      'bridge-usdc-to-hl: sending',
    )

    let txHash: `0x${string}` | `0x${string}`[]
    try {
      txHash = await adapter.sendCalls(ARBITRUM_CHAIN_ID, [
        { to: USDC_ARBITRUM, data: calldata, value: 0n },
      ])
    } catch (err) {
      req.log.error({ err }, 'bridge-usdc-to-hl: sendCalls failed')
      reply.code(502).send({ error: 'sendCalls failed', detail: String(err) })
      return
    }

    req.log.info({ agentWalletAddress, txHash }, 'bridge-usdc-to-hl: ok')
    reply.send({ success: true, txHash, amountUsdc })
  })
}
