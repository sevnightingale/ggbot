// Register the agent on DegenClaw's leaderboard via an ACP v2 buyer-side job.
//
// Flow:
//   1. Generate RSA keypair locally (provider encrypts the returned DGClaw API key)
//   2. AcpAgent.createJobByOfferingName → on-chain job against DGClaw provider
//   3. Provider sets budget ($0.01) → we auto-fund
//   4. Provider submits deliverable with encryptedApiKey → we decrypt
//   5. We call session.complete() so provider gets paid
//
// DGClaw provider agent: 0xd478a8B40372db16cA8045F28C6FE07228F3781A
// Offering: "join_leaderboard" — $0.01 USDC, SLA 5min, requiredFunds=false

import type { FastifyInstance } from 'fastify'
import {
  generateKeyPairSync,
  privateDecrypt,
  constants as cryptoConstants,
} from 'node:crypto'
import {
  AcpAgent,
  AcpApiClient,
  SseTransport,
} from '@virtuals-protocol/acp-node-v2'
import { base } from 'viem/chains'
import { getEvmAdapter } from '../lib/privy-sign.js'

const DGCLAW_PROVIDER_ADDRESS = '0xd478a8B40372db16cA8045F28C6FE07228F3781A' as const
const CHAIN_ID = base.id
const DELIVERABLE_TIMEOUT_MS = 180_000

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
}

export function registerJoinLeaderboard(app: FastifyInstance) {
  app.post<{ Body: Body }>('/join-leaderboard', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey } = req.body
    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    const { publicKey, privateKey } = generateKeyPairSync('rsa', {
      modulusLength: 2048,
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
    })

    let adapter
    try {
      adapter = await getEvmAdapter({
        agentWalletAddress,
        agentWalletId,
        signerPrivateKey,
      })
    } catch (err) {
      req.log.error({ err }, 'join-leaderboard: adapter init failed')
      reply.code(502).send({ error: 'privy adapter init failed', detail: String(err) })
      return
    }

    const transport = new SseTransport()
    const api = new AcpApiClient()
    const agent = await AcpAgent.create({ provider: adapter, transport, api })

    let jobId: bigint | null = null

    const deliverablePromise = new Promise<string>((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error(`timeout waiting for deliverable after ${DELIVERABLE_TIMEOUT_MS / 1000}s`)),
        DELIVERABLE_TIMEOUT_MS,
      )

      agent.on('entry', async (session, entry) => {
        if (jobId === null || session.jobId !== jobId.toString()) return
        if (entry.kind !== 'system') return

        const eventType = entry.event.type
        req.log.info({ jobId: jobId.toString(), eventType }, 'join-leaderboard: session event')

        if (eventType === 'budget.set') {
          // Client role per ACP v2 tool matrix: once budget is set, we fund.
          try {
            const job = await session.fetchJob()
            await session.fund(job.budget)
            req.log.info({ jobId: jobId.toString() }, 'join-leaderboard: funded')
          } catch (err) {
            clearTimeout(timer)
            reject(err instanceof Error ? err : new Error(String(err)))
          }
        } else if (eventType === 'job.submitted') {
          clearTimeout(timer)
          resolve(entry.event.deliverable)
        } else if (eventType === 'job.rejected' || eventType === 'job.expired') {
          clearTimeout(timer)
          const reason = 'reason' in entry.event ? entry.event.reason : 'no reason'
          reject(new Error(`job ${eventType}: ${reason}`))
        }
      })
    })

    let deliverable: string
    try {
      await agent.start()

      jobId = await agent.createJobByOfferingName(
        CHAIN_ID,
        'join_leaderboard',
        DGCLAW_PROVIDER_ADDRESS,
        {
          agentAddress: agentWalletAddress,
          publicKey,
        },
      )

      req.log.info(
        { jobId: jobId.toString(), agentWalletAddress },
        'join-leaderboard: job created',
      )

      deliverable = await deliverablePromise

      const session = agent.getSession(CHAIN_ID, jobId.toString())
      if (session) {
        try {
          await session.complete('registered')
          req.log.info({ jobId: jobId.toString() }, 'join-leaderboard: completed')
        } catch (completeErr) {
          req.log.warn({ completeErr }, 'join-leaderboard: complete failed (non-fatal)')
        }
      }
    } catch (err) {
      req.log.error({ err }, 'join-leaderboard: flow failed')
      await agent.stop().catch(() => {})
      reply.code(502).send({ error: 'leaderboard join failed', detail: String(err) })
      return
    }

    await agent.stop().catch(() => {})

    // Decrypt the DGClaw API key from the deliverable.
    let dgclawApiKey: string | null = null
    let decryptError: string | null = null
    try {
      const parsed: Record<string, unknown> = JSON.parse(deliverable)
      const encrypted =
        (parsed.encryptedApiKey as string | undefined) ??
        (parsed.encrypted_api_key as string | undefined)
      if (!encrypted) {
        throw new Error('no encryptedApiKey field in deliverable')
      }
      const decrypted = privateDecrypt(
        {
          key: privateKey,
          padding: cryptoConstants.RSA_PKCS1_OAEP_PADDING,
          oaepHash: 'sha256',
        },
        Buffer.from(encrypted, 'base64'),
      )
      dgclawApiKey = decrypted.toString('utf-8')
    } catch (err) {
      decryptError = String(err)
      req.log.warn({ err, deliverable }, 'join-leaderboard: deliverable decode failed')
    }

    req.log.info(
      { agentWalletAddress, hasApiKey: Boolean(dgclawApiKey) },
      'join-leaderboard: complete',
    )

    reply.send({
      success: true,
      jobId: jobId.toString(),
      dgclawApiKey,
      decryptError,
    })
  })
}
