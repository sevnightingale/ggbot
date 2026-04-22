'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { createClient } from '@/lib/supabase'
import { Loader2, Check, X, ExternalLink, RefreshCw, Copy } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'

type AuthStatus = 'idle' | 'awaiting_popup' | 'polling' | 'completed' | 'failed'
type SignerStatus = 'idle' | 'awaiting_popup' | 'polling' | 'completed' | 'failed'

interface AgentInfo {
  id: string
  walletAddress: string
  name: string
  description?: string
}

interface VerifyTradeResult {
  status: string
  entry_price?: number
  close_status?: string
  stage?: string
  detail?: unknown
}

interface VerifySnapshotResult {
  status: string
  wallet: string
  processed: Record<string, unknown>
  raw_user_state: unknown
  raw_fills_sample: unknown[]
  fills_total: number
}

export default function AcpV2TestPage() {
  const supabase = createClient()

  // Session state
  const [connected, setConnected] = useState(false)
  const [jwtPreview, setJwtPreview] = useState<string | null>(null)
  const [virtualsWallet, setVirtualsWallet] = useState<string | null>(null)
  const [authStatus, setAuthStatus] = useState<AuthStatus>('idle')
  const [authError, setAuthError] = useState<string | null>(null)

  // Agent state
  const [agentName, setAgentName] = useState(() => {
    const now = new Date()
    const stamp = `${now.toISOString().slice(0, 10)}-${now.toISOString().slice(11, 16).replace(':', '')}`
    return `ggbot-test-${stamp}`
  })
  const [agent, setAgent] = useState<AgentInfo | null>(null)
  const [signerStatus, setSignerStatus] = useState<SignerStatus>('idle')
  const [signerError, setSignerError] = useState<string | null>(null)

  // Verify state
  const [hlApiKey, setHlApiKey] = useState('')
  const [tradeResult, setTradeResult] = useState<VerifyTradeResult | null>(null)
  const [snapshotResult, setSnapshotResult] = useState<VerifySnapshotResult | null>(null)
  const [verifyBusy, setVerifyBusy] = useState<'trade' | 'snapshot' | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const authHeaders = useCallback(async (): Promise<HeadersInit> => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) throw new Error('Not authenticated')
    return {
      Authorization: `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    }
  }, [supabase])

  const refreshSessionStatus = useCallback(async () => {
    try {
      const headers = await authHeaders()
      const res = await fetch(`${API_BASE}/api/v2/acp-test/session-status`, { headers })
      if (!res.ok) return
      const data = await res.json()
      setConnected(!!data.connected)
      setJwtPreview(data.jwt_preview || null)
    } catch {
      // ignore
    }
  }, [authHeaders])

  useEffect(() => {
    refreshSessionStatus()
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [refreshSessionStatus])

  // ── Step 1: Connect Virtuals (popup 1) ────────────────────────────────────
  const handleConnect = useCallback(async () => {
    setAuthError(null)
    setAuthStatus('awaiting_popup')
    try {
      const headers = await authHeaders()
      const startRes = await fetch(`${API_BASE}/api/v2/acp-test/auth-start`, {
        method: 'POST',
        headers,
      })
      if (!startRes.ok) throw new Error(`auth-start failed: ${startRes.status}`)
      const { authUrl, requestId } = await startRes.json()
      window.open(authUrl, '_blank', 'width=600,height=760')
      setAuthStatus('polling')

      const startedAt = Date.now()
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        if (Date.now() - startedAt > 5 * 60 * 1000) {
          if (pollRef.current) clearInterval(pollRef.current)
          setAuthStatus('failed')
          setAuthError('Timed out after 5 minutes')
          return
        }
        try {
          const pollHeaders = await authHeaders()
          const pollRes = await fetch(
            `${API_BASE}/api/v2/acp-test/auth-poll?requestId=${encodeURIComponent(requestId)}`,
            { headers: pollHeaders },
          )
          if (!pollRes.ok) return
          const data = await pollRes.json()
          if (data.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current)
            setAuthStatus('completed')
            setConnected(true)
            setJwtPreview(data.jwt_preview)
            setVirtualsWallet(data.walletAddress || null)
          }
        } catch {
          // keep polling
        }
      }, 3000)
    } catch (e) {
      setAuthStatus('failed')
      setAuthError(e instanceof Error ? e.message : String(e))
    }
  }, [authHeaders])

  const handleResetSession = useCallback(async () => {
    try {
      const headers = await authHeaders()
      await fetch(`${API_BASE}/api/v2/acp-test/session-reset`, { method: 'POST', headers })
      setConnected(false)
      setJwtPreview(null)
      setVirtualsWallet(null)
      setAuthStatus('idle')
      setAgent(null)
      setSignerStatus('idle')
    } catch {
      // ignore
    }
  }, [authHeaders])

  // ── Step 2: Create Agent + Signer (popup 2) ───────────────────────────────
  const handleCreateAgent = useCallback(async () => {
    setSignerError(null)
    setSignerStatus('awaiting_popup')
    setAgent(null)
    try {
      const headers = await authHeaders()
      const res = await fetch(`${API_BASE}/api/v2/acp-test/agent-create`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name: agentName }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`agent-create failed: ${res.status} ${text.slice(0, 200)}`)
      }
      const { agent: created, signerUrl, signerRequestId } = await res.json()
      setAgent({
        id: String(created.id),
        walletAddress: created.walletAddress,
        name: created.name || agentName,
        description: created.description,
      })
      window.open(signerUrl, '_blank', 'width=600,height=760')
      setSignerStatus('polling')

      const startedAt = Date.now()
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        if (Date.now() - startedAt > 5 * 60 * 1000) {
          if (pollRef.current) clearInterval(pollRef.current)
          setSignerStatus('failed')
          setSignerError('Timed out after 5 minutes')
          return
        }
        try {
          const pollHeaders = await authHeaders()
          const pollRes = await fetch(
            `${API_BASE}/api/v2/acp-test/signer-poll?agentId=${encodeURIComponent(created.id)}&requestId=${encodeURIComponent(signerRequestId)}`,
            { headers: pollHeaders },
          )
          if (!pollRes.ok) return
          const data = await pollRes.json()
          if (data.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current)
            setSignerStatus('completed')
          }
        } catch {
          // keep polling
        }
      }, 5000)
    } catch (e) {
      setSignerStatus('failed')
      setSignerError(e instanceof Error ? e.message : String(e))
    }
  }, [authHeaders, agentName])

  // ── Step 3: Verify Monitoring ────────────────────────────────────────────
  const runVerifyTrade = useCallback(async () => {
    if (!agent?.walletAddress || !hlApiKey) return
    setVerifyBusy('trade')
    setVerifyError(null)
    try {
      const headers = await authHeaders()
      const res = await fetch(`${API_BASE}/api/v2/acp-test/verify-trade`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agentWalletAddress: agent.walletAddress,
          hlApiWalletKey: hlApiKey,
        }),
      })
      const data = await res.json()
      setTradeResult(data)
    } catch (e) {
      setVerifyError(e instanceof Error ? e.message : String(e))
    } finally {
      setVerifyBusy(null)
    }
  }, [authHeaders, agent, hlApiKey])

  const runVerifySnapshot = useCallback(async () => {
    if (!agent?.walletAddress) return
    setVerifyBusy('snapshot')
    setVerifyError(null)
    try {
      const headers = await authHeaders()
      const res = await fetch(
        `${API_BASE}/api/v2/acp-test/verify-snapshot?wallet=${encodeURIComponent(agent.walletAddress)}`,
        { headers },
      )
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      setSnapshotResult(data)
    } catch (e) {
      setVerifyError(e instanceof Error ? e.message : String(e))
    } finally {
      setVerifyBusy(null)
    }
  }, [authHeaders, agent])

  const copy = (text: string) => navigator.clipboard.writeText(text)

  return (
    <div className="mx-auto max-w-4xl p-6 font-mono text-sm text-zinc-100">
      <h1 className="mb-1 text-xl font-semibold">ACP v2 Migration — Phase 0 Gate</h1>
      <p className="mb-6 text-zinc-400">
        Admin-only test harness. Verifies Virtuals v2 auth, signer registration, Privy-provisioned
        wallet compatibility with HyperliquidAccountAdapter. No production data is touched.
      </p>

      {/* ── Session ──────────────────────────────── */}
      <Section title="Session">
        <div className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-3">
            {connected ? <Check className="h-4 w-4 text-green-500" /> : <X className="h-4 w-4 text-zinc-500" />}
            <div>
              <div className="text-zinc-100">{connected ? 'Connected to Virtuals' : 'Not connected'}</div>
              {connected && jwtPreview && (
                <div className="text-xs text-zinc-500">jwt: {jwtPreview}</div>
              )}
              {virtualsWallet && (
                <div className="text-xs text-zinc-500">wallet: {virtualsWallet}</div>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {!connected && (
              <button
                onClick={handleConnect}
                disabled={authStatus === 'polling' || authStatus === 'awaiting_popup'}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {authStatus === 'polling' || authStatus === 'awaiting_popup' ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <ExternalLink className="h-3.5 w-3.5" />
                )}
                Connect Virtuals
              </button>
            )}
            <button
              onClick={handleResetSession}
              className="inline-flex items-center gap-1.5 rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
            >
              <RefreshCw className="h-3 w-3" /> reset
            </button>
          </div>
        </div>
        {authError && <p className="mt-2 text-xs text-red-400">{authError}</p>}
        {authStatus === 'polling' && (
          <p className="mt-2 text-xs text-zinc-500">
            Waiting for browser auth — approve in the popup. Polling every 3s, 5min timeout.
          </p>
        )}
      </Section>

      {/* ── Agent + Signer ──────────────────────── */}
      <Section title="Create Agent + Register Signer" disabled={!connected}>
        <div className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <label className="block">
            <span className="text-xs text-zinc-400">Agent name</span>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              disabled={!connected || !!agent}
              className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100 disabled:opacity-60"
            />
          </label>
          <button
            onClick={handleCreateAgent}
            disabled={!connected || !agentName || signerStatus === 'polling' || signerStatus === 'awaiting_popup' || signerStatus === 'completed'}
            className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {signerStatus === 'polling' || signerStatus === 'awaiting_popup' ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <ExternalLink className="h-3.5 w-3.5" />
            )}
            Create Agent + Sign
          </button>
          {signerError && <p className="text-xs text-red-400">{signerError}</p>}
          {signerStatus === 'polling' && (
            <p className="text-xs text-zinc-500">Approve the signer in the popup. Polling every 5s, 5min timeout.</p>
          )}
          {agent && (
            <div className="rounded-md border border-zinc-800 bg-zinc-950 p-3 text-xs">
              <Row label="id" value={agent.id} onCopy={() => copy(agent.id)} />
              <Row label="name" value={agent.name} />
              <Row label="walletAddress" value={agent.walletAddress} onCopy={() => copy(agent.walletAddress)} />
              <Row
                label="signer"
                value={
                  signerStatus === 'completed'
                    ? 'approved ✓'
                    : signerStatus === 'polling'
                    ? 'awaiting approval…'
                    : signerStatus
                }
              />
            </div>
          )}
        </div>
      </Section>

      {/* ── Monitoring Verification ─────────────── */}
      <Section title="Verify Monitoring" disabled={signerStatus !== 'completed'}>
        <div className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="rounded-md border border-amber-900/40 bg-amber-950/40 p-3 text-xs text-amber-200">
            <p className="mb-1 font-semibold">Prep steps (manual — copy values from dashboard/CLI):</p>
            <ol className="list-decimal space-y-0.5 pl-5">
              <li>Send $5–$10 USDC on Base to the agent wallet above.</li>
              <li>
                Use <code>dgclaw-skill</code> scripts (<code>activate-unified.ts</code>,{' '}
                <code>add-api-wallet.ts</code>) against that agent to bridge USDC into HL and
                generate the HL API wallet private key.
              </li>
              <li>Paste the HL API wallet private key below.</li>
            </ol>
          </div>
          <label className="block">
            <span className="text-xs text-zinc-400">HL API wallet private key (0x…)</span>
            <input
              type="password"
              value={hlApiKey}
              onChange={(e) => setHlApiKey(e.target.value)}
              placeholder="0x…"
              className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100"
            />
          </label>
          <div className="flex gap-2">
            <button
              onClick={runVerifyTrade}
              disabled={!agent || !hlApiKey || verifyBusy !== null}
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {verifyBusy === 'trade' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Run $5 ETH test trade (open + close)
            </button>
            <button
              onClick={runVerifySnapshot}
              disabled={!agent || verifyBusy !== null}
              className="inline-flex items-center gap-1.5 rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-100 hover:bg-zinc-800 disabled:opacity-50"
            >
              {verifyBusy === 'snapshot' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Dump HL snapshot
            </button>
          </div>
          {verifyError && <p className="text-xs text-red-400">{verifyError}</p>}
          {tradeResult && (
            <div className="rounded-md border border-zinc-800 bg-zinc-950 p-3 text-xs">
              <div className="mb-2 text-zinc-400">verify-trade</div>
              <pre className="whitespace-pre-wrap break-all text-zinc-200">{JSON.stringify(tradeResult, null, 2)}</pre>
            </div>
          )}
          {snapshotResult && (
            <div className="space-y-2 rounded-md border border-zinc-800 bg-zinc-950 p-3 text-xs">
              <div className="text-zinc-400">verify-snapshot · processed (adapter shape)</div>
              <pre className="whitespace-pre-wrap break-all text-zinc-200">
                {JSON.stringify(snapshotResult.processed, null, 2)}
              </pre>
              <div className="text-zinc-400">raw user_state (truncated)</div>
              <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all text-zinc-500">
                {JSON.stringify(snapshotResult.raw_user_state, null, 2)}
              </pre>
              <div className="text-zinc-400">
                fills total: {snapshotResult.fills_total} (sample shown)
              </div>
              <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-all text-zinc-500">
                {JSON.stringify(snapshotResult.raw_fills_sample, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Section>

      {/* ── Gate decision crib ───────────────────── */}
      <Section title="Gate criteria">
        <ul className="list-disc space-y-1 pl-5 text-xs text-zinc-400">
          <li>Both popups auto-close (or have clear manual-close UX) — under 30s total</li>
          <li>Agent + signer visible on app.virtuals.io after flow</li>
          <li>Test trade fills + closes with a concrete entry_price</li>
          <li>verify-snapshot returns non-zero account_value + withdrawable + closedPnl after close</li>
          <li>Snapshot JSON matches reference v1 HL bot shape (no missing fields)</li>
        </ul>
      </Section>
    </div>
  )
}

function Section({
  title,
  children,
  disabled,
}: {
  title: string
  children: React.ReactNode
  disabled?: boolean
}) {
  return (
    <section className={`mb-6 ${disabled ? 'opacity-50' : ''}`}>
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">{title}</h2>
      {children}
    </section>
  )
}

function Row({
  label,
  value,
  onCopy,
}: {
  label: string
  value: string
  onCopy?: () => void
}) {
  return (
    <div className="flex items-center justify-between gap-2 py-0.5">
      <span className="text-zinc-500">{label}</span>
      <span className="flex items-center gap-1 font-mono text-zinc-100 break-all">
        {value}
        {onCopy && (
          <button onClick={onCopy} className="text-zinc-500 hover:text-zinc-300" title="Copy">
            <Copy className="h-3 w-3" />
          </button>
        )}
      </span>
    </div>
  )
}
