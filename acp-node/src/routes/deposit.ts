// Deposit USDC into the agent's Hyperliquid account via ACP `perp_deposit`.
//
// DGClaw is an ACP v1 provider, so we use the official v2-to-v1 compat layer
// (LegacyBuyerAdapter) — same pattern @Virtual-Protocol/acp-cli uses when
// invoked with `--legacy`. Our v2 Privy provider adapter is reused for signing;
// the legacy bridge routes the signed calls to the v1 contract that DGClaw
// watches.
//
// Flow:
//   1. LegacyBuyerAdapter.getAgent(DGCLAW) → resolve v1 offering metadata
//   2. adapter.createJob(perp_deposit, {amount}) → on-chain v1 job, phase=REQUEST
//   3. Poll until phase=NEGOTIATION (DGClaw set the budget)
//   4. adapter.fundJob(jobId) → transfers USDC escrow to v1 contract
//   5. Poll until phase=EVALUATION (DGClaw submitted deliverable)
//   6. adapter.completeJob(jobId) → release escrow, return deliverable
//
// DGClaw's SLA is 30 min end-to-end; typical is 2-5 min.

import type { FastifyInstance } from 'fastify'
import { base } from 'viem/chains'
import { AcpJobPhases } from '@virtuals-protocol/acp-node'
import { getEvmAdapter } from '../lib/privy-sign.js'
import { LegacyBuyerAdapter } from '../lib/compat/legacyBuyerAdapter.js'

const DGCLAW_PROVIDER_ADDRESS = '0xd478a8B40372db16cA8045F28C6FE07228F3781A'
const CHAIN_ID = base.id
const POLL_INTERVAL_MS = 5_000
const OVERALL_TIMEOUT_MS = 30 * 60 * 1000   // 30 min matching DGClaw SLA

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
  amountUsdc: string
}

type Phase =
  | 'REQUEST'
  | 'NEGOTIATION'
  | 'TRANSACTION'
  | 'EVALUATION'
  | 'COMPLETED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'unknown'

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

export function registerDeposit(app: FastifyInstance) {
  app.post<{ Body: Body }>('/deposit', async (req, reply) => {
    const { agentWalletAddress, agentWalletId, signerPrivateKey, amountUsdc } = req.body
    if (!agentWalletAddress || !agentWalletId || !signerPrivateKey || !amountUsdc) {
      reply.code(400).send({ error: 'missing required fields' })
      return
    }

    let provider
    try {
      provider = await getEvmAdapter({ agentWalletAddress, agentWalletId, signerPrivateKey })
    } catch (err) {
      req.log.error({ err }, 'deposit: adapter init failed')
      reply.code(502).send({ error: 'privy adapter init failed', detail: String(err) })
      return
    }

    let adapter: LegacyBuyerAdapter
    try {
      adapter = await LegacyBuyerAdapter.create(provider, CHAIN_ID)
    } catch (err) {
      req.log.error({ err }, 'deposit: legacy adapter init failed')
      reply.code(502).send({ error: 'legacy adapter init failed', detail: String(err) })
      return
    }

    // 1. Resolve v1 offering metadata from DGClaw
    let legacyAgent
    try {
      legacyAgent = await adapter.getAgent(DGCLAW_PROVIDER_ADDRESS)
    } catch (err) {
      req.log.error({ err }, 'deposit: getAgent failed')
      reply.code(502).send({ error: 'failed to resolve DGClaw agent', detail: String(err) })
      return
    }
    if (!legacyAgent) {
      reply.code(502).send({ error: 'DGClaw agent not found in v1 registry' })
      return
    }

    const offering = legacyAgent.jobOfferings.find((o: any) => o.name === 'perp_deposit')
    if (!offering) {
      const available = legacyAgent.jobOfferings.map((o: any) => o.name).join(', ')
      reply.code(502).send({
        error: 'perp_deposit offering not found on DGClaw',
        available,
      })
      return
    }

    // 2. Create the v1 job (phase=REQUEST)
    let jobId: number
    try {
      jobId = await adapter.createJob({
        providerAddress: DGCLAW_PROVIDER_ADDRESS,
        requirement: { amount: amountUsdc },
        priceType: offering.priceType,
        priceValue: Number(offering.price),
        expiredAt: new Date(Date.now() + (offering.slaMinutes || 30) * 60 * 1000),
        offeringName: 'perp_deposit',
      })
    } catch (err) {
      req.log.error({ err }, 'deposit: createJob failed')
      reply.code(502).send({ error: 'createJob failed', detail: String(err) })
      return
    }

    req.log.info(
      { jobId, agentWalletAddress, amountUsdc, priceType: offering.priceType, price: offering.price },
      'deposit: v1 job created',
    )

    // 3/4/5/6. Poll phase transitions, fund on NEGOTIATION, complete on EVALUATION
    const started = Date.now()
    let lastPhase: Phase | null = null
    let funded = false
    let completed = false
    let deliverable: any = null

    while (Date.now() - started < OVERALL_TIMEOUT_MS) {
      let job
      try {
        job = await adapter.getJob(jobId)
      } catch (err) {
        req.log.warn({ err, jobId }, 'deposit: getJob poll failed, retrying')
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
        continue
      }

      if (!job) {
        req.log.warn({ jobId }, 'deposit: job not found on poll, retrying')
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
        continue
      }

      const phase = phaseName(job.phase as AcpJobPhases)
      if (phase !== lastPhase) {
        req.log.info({ jobId, phase }, 'deposit: phase transition')
        lastPhase = phase
      }

      if (phase === 'NEGOTIATION' && !funded) {
        try {
          req.log.info({ jobId }, 'deposit: funding job')
          await adapter.fundJob(jobId, 'ggbots deposit')
          funded = true
          req.log.info({ jobId }, 'deposit: fund call submitted')
        } catch (err) {
          req.log.error({ err, jobId }, 'deposit: fundJob failed')
          reply.code(502).send({ error: 'fundJob failed', detail: String(err), jobId })
          return
        }
      } else if (phase === 'EVALUATION' && !completed) {
        // v1 SDK: getDeliverable() returns DeliverablePayload | null (string | object)
        try { deliverable = (job as any).getDeliverable?.() ?? null } catch { deliverable = null }
        try {
          req.log.info({ jobId }, 'deposit: completing job')
          await adapter.completeJob(jobId, 'ggbots approved')
          completed = true
          req.log.info({ jobId }, 'deposit: complete call submitted')
        } catch (err) {
          req.log.error({ err, jobId }, 'deposit: completeJob failed')
          reply.code(502).send({ error: 'completeJob failed', detail: String(err), jobId })
          return
        }
      } else if (phase === 'COMPLETED') {
        try { deliverable = (job as any).getDeliverable?.() ?? deliverable } catch { /* keep existing */ }
        req.log.info(
          { jobId, agentWalletAddress, deliverable },
          'deposit: COMPLETED — logging deliverable for schema discovery',
        )

        // Parse deliverable if it's a JSON string
        let parsed: Record<string, unknown> | null = null
        let parseError: string | null = null
        if (typeof deliverable === 'string') {
          try { parsed = JSON.parse(deliverable) }
          catch (err) { parseError = String(err) }
        } else if (deliverable && typeof deliverable === 'object') {
          parsed = deliverable
        }

        reply.send({
          success: true,
          jobId: String(jobId),
          phase: 'COMPLETED',
          deliverable: parsed,
          deliverableRaw: deliverable,
          parseError,
        })
        return
      } else if (phase === 'REJECTED' || phase === 'EXPIRED') {
        req.log.warn({ jobId, phase }, 'deposit: terminal failure')
        reply.code(502).send({
          error: `job terminated with phase=${phase}`,
          jobId,
        })
        return
      }

      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
    }

    req.log.error({ jobId, lastPhase }, 'deposit: overall timeout')
    reply.code(504).send({
      error: `timeout after ${OVERALL_TIMEOUT_MS / 60_000}min`,
      jobId,
      lastPhase,
    })
  })
}
