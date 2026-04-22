// Port of dgclaw-skill/scripts/activate-unified.ts — without the execSync to acp-cli.
// Signs the userSetAbstraction EIP-712 action via Privy, POSTs to HL.

import type { FastifyInstance } from 'fastify'
import {
  HL_DOMAIN,
  UserSetAbstractionTypes,
  CHAIN_ID,
  parseSignature,
  broadcastToHL,
} from '../lib/hl.js'
import { signTypedDataWithPrivy } from '../lib/privy-sign.js'

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
}

export function registerSetupHlUnified(app: FastifyInstance) {
  app.post<{ Body: Body }>('/setup-hl-unified-account', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey } = req.body
    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    const nonce = Date.now()
    const action = {
      type: 'userSetAbstraction' as const,
      signatureChainId: `0x${CHAIN_ID.toString(16)}`,
      hyperliquidChain: 'Mainnet',
      user: agentWalletAddress,
      abstraction: 'unifiedAccount',
      nonce,
    }

    const typedData = {
      domain: HL_DOMAIN,
      types: UserSetAbstractionTypes,
      primaryType: Object.keys(UserSetAbstractionTypes)[0]!,
      message: {
        hyperliquidChain: 'Mainnet',
        user: agentWalletAddress,
        abstraction: 'unifiedAccount',
        nonce,
      },
    }

    req.log.info({ agentWalletAddress, agentWalletId, nonce }, 'setup-hl-unified: signing')

    let signatureHex: string
    try {
      signatureHex = await signTypedDataWithPrivy({
        agentWalletAddress,
        agentWalletId,
        signerPrivateKey,
        typedData,
      })
    } catch (err) {
      req.log.error({ err }, 'setup-hl-unified: sign failed')
      reply.code(502).send({ error: 'privy sign failed', detail: String(err) })
      return
    }

    const signature = parseSignature(signatureHex)
    const { httpStatus, body } = await broadcastToHL(action, signature, nonce)

    if (body?.status !== 'ok') {
      req.log.warn({ httpStatus, body }, 'setup-hl-unified: HL rejected')
      reply.code(502).send({ error: 'HL rejected action', hlResponse: body })
      return
    }

    req.log.info({ agentWalletAddress }, 'setup-hl-unified: ok')
    reply.send({ success: true, hlResponse: body })
  })
}
