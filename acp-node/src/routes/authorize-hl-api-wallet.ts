// Port of dgclaw-skill/scripts/add-api-wallet.ts — without the execSync to acp-cli
// and without the .env file-write (we return the privkey so Python can stash it in Vault).

import type { FastifyInstance } from 'fastify'
import { generatePrivateKey, privateKeyToAccount } from 'viem/accounts'
import {
  HL_DOMAIN,
  ApproveAgentTypes,
  CHAIN_ID,
  parseSignature,
  broadcastToHL,
} from '../lib/hl.js'
import { signTypedDataWithPrivy } from '../lib/privy-sign.js'

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
  agentName?: string | null
}

export function registerAuthorizeHlApiWallet(app: FastifyInstance) {
  app.post<{ Body: Body }>('/authorize-hl-api-wallet', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey, agentName } = req.body
    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    const apiPriv = generatePrivateKey()
    const apiAccount = privateKeyToAccount(apiPriv)

    const nonce = Date.now()
    const action = {
      type: 'approveAgent' as const,
      signatureChainId: `0x${CHAIN_ID.toString(16)}`,
      hyperliquidChain: 'Mainnet',
      agentAddress: apiAccount.address,
      agentName: agentName ?? null,
      nonce,
    }

    const typedData = {
      domain: HL_DOMAIN,
      types: ApproveAgentTypes,
      primaryType: Object.keys(ApproveAgentTypes)[0]!,
      message: {
        hyperliquidChain: 'Mainnet',
        agentAddress: apiAccount.address,
        agentName: agentName ?? '',
        nonce,
      },
    }

    req.log.info(
      { agentWalletAddress, apiWalletAddress: apiAccount.address, nonce },
      'authorize-hl-api-wallet: signing',
    )

    let signatureHex: string
    try {
      signatureHex = await signTypedDataWithPrivy({
        agentWalletAddress,
        agentWalletId,
        signerPrivateKey,
        typedData,
      })
    } catch (err) {
      req.log.error({ err }, 'authorize-hl-api-wallet: sign failed')
      reply.code(502).send({ error: 'privy sign failed', detail: String(err) })
      return
    }

    const signature = parseSignature(signatureHex)
    const { httpStatus, body } = await broadcastToHL(action, signature, nonce)

    if (body?.status !== 'ok') {
      req.log.warn({ httpStatus, body }, 'authorize-hl-api-wallet: HL rejected')
      reply.code(502).send({ error: 'HL rejected action', hlResponse: body })
      return
    }

    req.log.info(
      { agentWalletAddress, apiWalletAddress: apiAccount.address },
      'authorize-hl-api-wallet: ok',
    )
    reply.send({
      success: true,
      apiWalletAddress: apiAccount.address,
      apiWalletPrivateKey: apiPriv,
      hlResponse: body,
    })
  })
}
