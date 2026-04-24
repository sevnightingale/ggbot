// Register the agent on DegenClaw's leaderboard via ACP `join_leaderboard`.
//
// DGClaw is an ACP v1 provider → we route through LegacyBuyerAdapter just like
// /deposit does. RSA keypair stays — DGClaw encrypts the returned API key with
// our public key, we decrypt with the private key locally.
//
// Offering: "join_leaderboard" — $0.01 USDC fee, ~5min SLA, requiredFunds=false

import type { FastifyInstance } from 'fastify'
import {
  generateKeyPairSync,
  privateDecrypt,
  constants as cryptoConstants,
} from 'node:crypto'
import { base } from 'viem/chains'
import { AcpJobPhases } from '@virtuals-protocol/acp-node'
import { getEvmAdapter } from '../lib/privy-sign.js'
import { LegacyBuyerAdapter } from '../lib/compat/legacyBuyerAdapter.js'

const DGCLAW_PROVIDER_ADDRESS = '0xd478a8B40372db16cA8045F28C6FE07228F3781A'
const CHAIN_ID = base.id
const POLL_INTERVAL_MS = 5_000
const OVERALL_TIMEOUT_MS = 10 * 60 * 1000  // 10 min (SLA is 5, buffer)

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
}

type Phase =
  | 'REQUEST' | 'NEGOTIATION' | 'TRANSACTION' | 'EVALUATION'
  | 'COMPLETED' | 'REJECTED' | 'EXPIRED' | 'unknown'

function phaseName(phase: AcpJobPhases): Phase {
  switch (phase) {
    case AcpJobPhases.REQUEST: return 'REQUEST'
    case AcpJobPhases.NEGOTIATION: return 'NEGOTIATION'
    case AcpJobPhases.TRANSACTION: return 'TRANSACTION'
    case AcpJobPhases.EVALUATION: return 'EVALUATION'
    case AcpJobPhases.COMPLETED: return 'COMPLETED'
    case AcpJobPhases.REJECTED: return 'REJECTED'
    case AcpJobPhases.EXPIRED: return 'EXPIRED'
    default: return 'unknown'
  }
}

export function registerJoinLeaderboard(app: FastifyInstance) {
  app.post<{ Body: Body }>('/join-leaderboard', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey } = req.body
    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    // Client-generated RSA keypair — DGClaw encrypts the API key with pub.
    const { publicKey, privateKey } = generateKeyPairSync('rsa', {
      modulusLength: 2048,
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
    })

    let provider
    try {
      provider = await getEvmAdapter({ agentWalletAddress, agentWalletId, signerPrivateKey })
    } catch (err) {
      req.log.error({ err }, 'join-leaderboard: adapter init failed')
      reply.code(502).send({ error: 'privy adapter init failed', detail: String(err) })
      return
    }

    let adapter: LegacyBuyerAdapter
    try {
      adapter = await LegacyBuyerAdapter.create(provider, CHAIN_ID)
    } catch (err) {
      req.log.error({ err }, 'join-leaderboard: legacy adapter init failed')
      reply.code(502).send({ error: 'legacy adapter init failed', detail: String(err) })
      return
    }

    let legacyAgent
    try {
      legacyAgent = await adapter.getAgent(DGCLAW_PROVIDER_ADDRESS)
    } catch (err) {
      reply.code(502).send({ error: 'getAgent failed', detail: String(err) })
      return
    }
    if (!legacyAgent) {
      reply.code(502).send({ error: 'DGClaw agent not found in v1 registry' })
      return
    }

    const offering = legacyAgent.jobOfferings.find((o: any) => o.name === 'join_leaderboard')
    if (!offering) {
      const available = legacyAgent.jobOfferings.map((o: any) => o.name).join(', ')
      reply.code(502).send({ error: 'join_leaderboard offering not found', available })
      return
    }

    let jobId: number
    try {
      jobId = await adapter.createJob({
        providerAddress: DGCLAW_PROVIDER_ADDRESS,
        requirement: { agentAddress: agentWalletAddress, publicKey },
        priceType: offering.priceType,
        priceValue: Number(offering.price),
        // DGClaw's offering advertises 5min but actual delivery is slower.
        // Override to 30min to prevent on-chain job expiry before seller delivers.
        expiredAt: new Date(Date.now() + 30 * 60 * 1000),
        offeringName: 'join_leaderboard',
      })
    } catch (err) {
      req.log.error({ err }, 'join-leaderboard: createJob failed')
      reply.code(502).send({ error: 'createJob failed', detail: String(err) })
      return
    }

    req.log.info({ jobId, agentWalletAddress }, 'join-leaderboard: v1 job created')

    const started = Date.now()
    let lastPhase: Phase | null = null
    let funded = false
    let fundAttempts = 0
    let completed = false
    let deliverable: any = null

    while (Date.now() - started < OVERALL_TIMEOUT_MS) {
      let job
      try {
        job = await adapter.getJob(jobId)
      } catch (err) {
        req.log.warn({ err, jobId }, 'join-leaderboard: poll failed, retrying')
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
        continue
      }
      if (!job) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
        continue
      }

      const phase = phaseName(job.phase as AcpJobPhases)
      if (phase !== lastPhase) {
        req.log.info({ jobId, phase }, 'join-leaderboard: phase transition')
        lastPhase = phase
      }

      if (phase === 'NEGOTIATION' && !funded) {
        // DGClaw's requirement memo takes a few seconds to propagate after
        // the NEGOTIATION phase transition. payAndAcceptRequirement throws
        // "No notification memo found" if we call too early — retry with
        // increasing backoff up to 6 attempts (~60s).
        fundAttempts += 1
        try {
          await adapter.fundJob(jobId, 'ggbots leaderboard fee')
          funded = true
          req.log.info({ jobId, fundAttempts }, 'join-leaderboard: fund call submitted')
        } catch (err) {
          const msg = String(err)
          if (msg.includes('No notification memo') && fundAttempts < 6) {
            req.log.info({ jobId, fundAttempts }, 'join-leaderboard: memo not ready, will retry')
            await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS * 2))
            continue
          }
          reply.code(502).send({ error: 'fundJob failed', detail: msg, jobId, fundAttempts })
          return
        }
      } else if (phase === 'EVALUATION' && !completed) {
        try { deliverable = (job as any).getDeliverable?.() ?? null } catch { deliverable = null }
        try {
          await adapter.completeJob(jobId, 'ggbots approved leaderboard')
          completed = true
        } catch (err) {
          reply.code(502).send({ error: 'completeJob failed', detail: String(err), jobId })
          return
        }
      } else if (phase === 'COMPLETED') {
        try { deliverable = (job as any).getDeliverable?.() ?? deliverable } catch { /* keep existing */ }
        req.log.info({ jobId, deliverable }, 'join-leaderboard: COMPLETED — deliverable for schema discovery')

        // Decrypt the DGClaw API key from the deliverable (if present).
        let dgclawApiKey: string | null = null
        let forumThreadId: string | null = null
        let decryptError: string | null = null
        let parsed: Record<string, unknown> | null = null
        try {
          parsed = typeof deliverable === 'string' ? JSON.parse(deliverable) : deliverable
        } catch (err) {
          decryptError = `deliverable not JSON: ${String(err)}`
        }
        if (parsed && typeof parsed === 'object') {
          const encrypted =
            (parsed.encryptedApiKey as string | undefined) ??
            (parsed.encrypted_api_key as string | undefined)
          if (encrypted) {
            try {
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
              decryptError = `RSA decrypt failed: ${String(err)}`
            }
          }
          forumThreadId =
            (parsed.forumThreadId as string | undefined) ??
            (parsed.forum_thread_id as string | undefined) ??
            (parsed.threadId as string | undefined) ??
            (parsed.thread_id as string | undefined) ??
            null
        }

        reply.send({
          success: true,
          jobId: String(jobId),
          dgclawApiKey,
          forumThreadId,
          decryptError,
          deliverable: parsed,
          deliverableRaw: deliverable,
        })
        return
      } else if (phase === 'REJECTED' || phase === 'EXPIRED') {
        reply.code(502).send({ error: `job terminated with phase=${phase}`, jobId })
        return
      }

      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
    }

    reply.code(504).send({
      error: `timeout after ${OVERALL_TIMEOUT_MS / 60_000}min`,
      jobId,
      lastPhase,
    })
  })
}
