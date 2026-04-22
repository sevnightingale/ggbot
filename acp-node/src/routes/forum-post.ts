// Post AI reasoning to the DegenClaw forum for AI Council visibility.
//
// AI Council reads forum posts alongside on-chain HL fills when picking the
// Monday top-10 allocation. The orchestrator should hit this endpoint whenever
// a virtuals bot enters or exits a position, passing the LLM rationale as
// markdown body.
//
// Auth note: the exact forum auth scheme (Virtuals JWT vs. agent-signed) hasn't
// been confirmed against the live endpoint. We default to a signed-message
// header approach — the agent wallet signs `post:{agentId}:{threadId}:{ts}:
// {sha256(body)}` and we include the signature in `X-Agent-Signature`. If
// the forum expects a different scheme, adjust the headers below once verified.

import type { FastifyInstance } from 'fastify'
import { createHash } from 'node:crypto'
import { base } from 'viem/chains'
import { getEvmAdapter } from '../lib/privy-sign.js'

const FORUM_API_BASE = process.env.VIRTUALS_FORUM_URL || 'https://degen.virtuals.io/api'

interface Body {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
  agentId: string          // DGClaw/Virtuals agent ID (not the wallet)
  threadId: string         // Forum thread the post lands in
  body: string             // Markdown content
}

export function registerForumPost(app: FastifyInstance) {
  app.post<{ Body: Body }>('/forum-post', async (req, reply) => {
    const {
      agentWalletAddress,
      agentWalletId,
      signerPrivateKey,
      agentId,
      threadId,
      body,
    } = req.body

    if (
      !agentWalletAddress ||
      !agentWalletId ||
      !signerPrivateKey ||
      !agentId ||
      !threadId ||
      !body
    ) {
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
      req.log.error({ err }, 'forum-post: adapter init failed')
      reply.code(502).send({ error: 'privy adapter init failed', detail: String(err) })
      return
    }

    const timestamp = Date.now()
    const bodyHash = createHash('sha256').update(body, 'utf-8').digest('hex')
    const messageToSign = `post:${agentId}:${threadId}:${timestamp}:${bodyHash}`

    let signature: string
    try {
      signature = await adapter.signMessage(base.id, messageToSign)
    } catch (err) {
      req.log.error({ err }, 'forum-post: sign failed')
      reply.code(502).send({ error: 'sign failed', detail: String(err) })
      return
    }

    const url = `${FORUM_API_BASE}/forums/${agentId}/threads/${threadId}/posts`
    req.log.info({ url, agentWalletAddress, timestamp }, 'forum-post: posting')

    let httpStatus: number
    let responseBody: unknown
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Agent-Address': agentWalletAddress,
          'X-Agent-Timestamp': String(timestamp),
          'X-Agent-Signature': signature,
        },
        body: JSON.stringify({ body, timestamp }),
      })
      httpStatus = res.status
      const contentType = res.headers.get('content-type') ?? ''
      responseBody = contentType.includes('application/json')
        ? await res.json()
        : await res.text()
    } catch (err) {
      req.log.error({ err }, 'forum-post: fetch failed')
      reply.code(502).send({ error: 'forum-post fetch failed', detail: String(err) })
      return
    }

    if (httpStatus < 200 || httpStatus >= 300) {
      req.log.warn({ httpStatus, responseBody, url }, 'forum-post: rejected')
      reply.code(502).send({ error: 'forum rejected post', httpStatus, responseBody })
      return
    }

    req.log.info({ agentWalletAddress, httpStatus }, 'forum-post: ok')
    reply.send({ success: true, httpStatus, responseBody })
  })
}
