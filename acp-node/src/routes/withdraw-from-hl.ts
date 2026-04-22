// HL withdraw3 — transfers USDC from Hyperliquid back to the destination EVM
// address on Arbitrum. Protocol charges a small flat fee (currently $1). The
// destination can be the agent's own wallet (which then shows up on Arbitrum
// as a regular USDC balance) or any address the user specifies.

import type { FastifyInstance } from 'fastify'
import {
  HL_DOMAIN,
  WithdrawTypes,
  CHAIN_ID,
  parseSignature,
  broadcastToHL,
} from '../lib/hl.js'
import { signTypedDataWithPrivy } from '../lib/privy-sign.js'

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
  amountUsdc: string          // human-readable USDC amount, e.g., "100" or "5.25"
  destination?: `0x${string}` // defaults to agentWalletAddress
}

export function registerWithdrawFromHl(app: FastifyInstance) {
  app.post<{ Body: Body }>('/withdraw-from-hl', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey, amountUsdc } = req.body
    const destination = req.body.destination ?? agentWalletAddress

    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey || !amountUsdc) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    const time = Date.now()
    const action = {
      type: 'withdraw3' as const,
      signatureChainId: `0x${CHAIN_ID.toString(16)}`,
      hyperliquidChain: 'Mainnet',
      destination,
      amount: amountUsdc,
      time,
    }

    const typedData = {
      domain: HL_DOMAIN,
      types: WithdrawTypes,
      primaryType: Object.keys(WithdrawTypes)[0]!,
      message: {
        hyperliquidChain: 'Mainnet',
        destination,
        amount: amountUsdc,
        time,
      },
    }

    req.log.info({ agentWalletAddress, destination, amountUsdc, time }, 'withdraw-from-hl: signing')

    let signatureHex: string
    try {
      signatureHex = await signTypedDataWithPrivy({
        agentWalletAddress,
        agentWalletId,
        signerPrivateKey,
        chainId: CHAIN_ID,
        typedData,
      })
    } catch (err) {
      req.log.error({ err }, 'withdraw-from-hl: sign failed')
      reply.code(502).send({ error: 'privy sign failed', detail: String(err) })
      return
    }

    const signature = parseSignature(signatureHex)
    const { httpStatus, body } = await broadcastToHL(action, signature, time)

    if (body?.status !== 'ok') {
      req.log.warn({ httpStatus, body }, 'withdraw-from-hl: HL rejected')
      reply.code(502).send({ error: 'HL rejected action', hlResponse: body })
      return
    }

    req.log.info({ agentWalletAddress, destination, amountUsdc }, 'withdraw-from-hl: ok')
    reply.send({ success: true, hlResponse: body })
  })
}
