// Deposit USDC into the agent's Hyperliquid account via ACP `perp_deposit`
// buyer job against DGClaw's v1 provider agent.
//
// Flow:
//   1. User has already sent USDC (Base chain) to their agent wallet.
//   2. AcpAgent.createJobByOfferingName → on-chain job against DGClaw provider.
//   3. Provider sets budget ($0.01 fee) → we auto-fund.
//   4. Provider performs the Base→Arbitrum→HL bridge internally.
//   5. Provider submits deliverable (JSON with bridge tx hash, possibly forumThreadId).
//   6. We call session.complete() so provider gets paid.
//
// DGClaw provider agent: 0xd478a8B40372db16cA8045F28C6FE07228F3781A (ACP v1)
// Offering: "perp_deposit" — $0.01 USDC fee, 30-min SLA, requiredFunds=true
// Minimum deposit: $6 per DGClaw docs (enforced by caller at $10 for headroom).

import type { FastifyInstance } from 'fastify'
import {
  AcpAgent,
  AcpApiClient,
  SseTransport,
} from '@virtuals-protocol/acp-node-v2'
import { base } from 'viem/chains'
import { getEvmAdapter } from '../lib/privy-sign.js'

const DGCLAW_PROVIDER_ADDRESS = '0xd478a8B40372db16cA8045F28C6FE07228F3781A' as const
const CHAIN_ID = base.id
// DGClaw publishes a 30-min SLA on perp_deposit; give a buffer for block finality.
const DELIVERABLE_TIMEOUT_MS = 30 * 60 * 1000

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
  amountUsdc: string    // stringified decimal, e.g. "10.00"
}

export function registerDeposit(app: FastifyInstance) {
  app.post<{ Body: Body }>('/deposit', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey, amountUsdc } = req.body
    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey || !amountUsdc) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    let adapter
    try {
      adapter = await getEvmAdapter({
        agentWalletAddress,
        agentWalletId,
        signerPrivateKey,
      })
    } catch (err) {
      req.log.error({ err }, 'deposit: adapter init failed')
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
        req.log.info({ jobId: jobId.toString(), eventType }, 'deposit: session event')

        if (eventType === 'budget.set') {
          // Client role per ACP v2 tool matrix: once provider sets the budget, we fund.
          try {
            const job = await session.fetchJob()
            await session.fund(job.budget)
            req.log.info({ jobId: jobId.toString() }, 'deposit: funded')
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
        'perp_deposit',
        DGCLAW_PROVIDER_ADDRESS,
        {
          amount: amountUsdc,
        },
      )

      req.log.info(
        { jobId: jobId.toString(), agentWalletAddress, amountUsdc },
        'deposit: job created',
      )

      deliverable = await deliverablePromise

      const session = agent.getSession(CHAIN_ID, jobId.toString())
      if (session) {
        try {
          await session.complete('deposit confirmed')
          req.log.info({ jobId: jobId.toString() }, 'deposit: completed')
        } catch (completeErr) {
          req.log.warn({ completeErr }, 'deposit: complete failed (non-fatal)')
        }
      }
    } catch (err) {
      req.log.error({ err }, 'deposit: flow failed')
      await agent.stop().catch(() => {})
      reply.code(502).send({ error: 'deposit failed', detail: String(err) })
      return
    }

    await agent.stop().catch(() => {})

    // Parse the deliverable (schema undocumented — log raw once for discovery).
    let parsed: Record<string, unknown> | null = null
    let parseError: string | null = null
    try {
      parsed = JSON.parse(deliverable)
    } catch (err) {
      parseError = String(err)
      req.log.warn({ err, deliverable }, 'deposit: deliverable not JSON')
    }

    req.log.info(
      {
        agentWalletAddress,
        jobId: jobId.toString(),
        deliverableRaw: deliverable,
        deliverableParsed: parsed,
      },
      'deposit: complete — logging deliverable shape for schema discovery',
    )

    reply.send({
      success: true,
      jobId: jobId.toString(),
      deliverable: parsed,
      deliverableRaw: deliverable,
      parseError,
    })
  })
}
