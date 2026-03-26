'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { ApiClient } from '@/lib/api'
import {
  ArrowLeft, Loader2, Copy, Check, RefreshCw, ChevronDown,
  TrendingUp, TrendingDown, Wallet, Bot, ExternalLink,
} from 'lucide-react'

const api = new ApiClient()

// ─── Types ───────────────────────────────────────────────────────────────────

interface ArenaStatus {
  status: 'not_joined' | 'joined' | 'already_joined'
  agent_name?: string
  token_symbol?: string
  wallet_address?: string
  user_wallet_address?: string
  wallet_balance_usdc?: number
  dgclaw_balance?: number
  positions?: Position[]
  active_bot?: ActiveBot | null
}

interface Position {
  pair?: string
  coin?: string
  side: string
  size?: number
  entryPrice?: number
  unrealizedPnl?: number
  leverage?: number
  margin?: number
}

interface ActiveBot {
  config_id: string
  config_name: string
  symbol: string
}

interface BotConfig {
  config_id: string
  config_name: string
  selected_pair: string
  state: string
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function VirtualsArenaPage() {
  const router = useRouter()
  const supabase = createClient()

  const [loading, setLoading] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)
  const [status, setStatus] = useState<ArenaStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Action states
  const [joining, setJoining] = useState(false)
  const [checking, setChecking] = useState(false)
  const [withdrawing, setWithdrawing] = useState(false)
  const [settingBot, setSettingBot] = useState(false)
  const [copied, setCopied] = useState(false)

  // Forms
  const [walletInput, setWalletInput] = useState('')
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [bots, setBots] = useState<BotConfig[]>([])
  const [showBotSelector, setShowBotSelector] = useState(false)

  // Check messages
  const [depositMessage, setDepositMessage] = useState<string | null>(null)

  // ── Auth check ──
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        router.push('/login')
        return
      }
      setAuthenticated(true)
      await fetchStatus()
    }
    checkAuth()
  }, [])

  // ── Fetch arena status ──
  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.authenticatedFetch(
        `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/virtuals-arena/status`
      )
      const data = await res.json()
      setStatus(data)

      // If joined, also fetch user's bots for the selector
      if (data.status === 'joined') {
        const botsRes = await api.authenticatedFetch(
          `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/config`
        )
        if (botsRes.ok) {
          const botsData = await botsRes.json()
          const configs = (botsData.configs || botsData || [])
            .filter((b: BotConfig) => b.state === 'active')
          setBots(configs)
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load arena status'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Join arena ──
  const handleJoin = async () => {
    if (!walletInput || !walletInput.startsWith('0x')) {
      setError('Please enter a valid wallet address (0x...)')
      return
    }
    try {
      setJoining(true)
      setError(null)
      const res = await api.authenticatedFetch(
        `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/virtuals-arena/join`,
        { method: 'POST', body: JSON.stringify({ wallet_address: walletInput }) }
      )
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to join')
      await fetchStatus()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to join arena'
      setError(msg)
    } finally {
      setJoining(false)
    }
  }

  // ── Check deposit ──
  const handleCheckDeposit = async () => {
    try {
      setChecking(true)
      setDepositMessage(null)
      setError(null)
      const res = await api.authenticatedFetch(
        `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/virtuals-arena/check-deposit`,
        { method: 'POST' }
      )
      const data = await res.json()
      setDepositMessage(data.message || `Status: ${data.status}`)
      if (data.status === 'deposited') {
        await fetchStatus()
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Deposit check failed'
      setError(msg)
    } finally {
      setChecking(false)
    }
  }

  // ── Set bot ──
  const handleSetBot = async (configId: string) => {
    try {
      setSettingBot(true)
      setError(null)
      const res = await api.authenticatedFetch(
        `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/virtuals-arena/set-bot`,
        { method: 'POST', body: JSON.stringify({ config_id: configId }) }
      )
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to set bot')
      }
      setShowBotSelector(false)
      await fetchStatus()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to set bot'
      setError(msg)
    } finally {
      setSettingBot(false)
    }
  }

  // ── Withdraw ──
  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount)
    if (!amount || amount < 2) {
      setError('Minimum withdrawal is $2')
      return
    }
    try {
      setWithdrawing(true)
      setError(null)
      const res = await api.authenticatedFetch(
        `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/virtuals-arena/withdraw`,
        { method: 'POST', body: JSON.stringify({ amount }) }
      )
      const data = await res.json()
      if (data.status === 'success') {
        setWithdrawAmount('')
        await fetchStatus()
      } else {
        setError(data.reason || 'Withdrawal failed')
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Withdrawal failed'
      setError(msg)
    } finally {
      setWithdrawing(false)
    }
  }

  // ── Copy address ──
  const copyAddress = (addr: string) => {
    navigator.clipboard.writeText(addr)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Loading state ──
  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Header onBack={() => router.push('/forge')} />
        <div className="max-w-2xl mx-auto px-4 py-20 flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
          <span className="text-[var(--text-muted)]">Loading arena...</span>
        </div>
      </div>
    )
  }

  if (!authenticated) return null

  // ── Not joined ──
  if (!status || status.status === 'not_joined') {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Header onBack={() => router.push('/forge')} />
        <div className="max-w-2xl mx-auto px-4 py-8">
          <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
            Virtuals DGClaw Arena
          </h1>
          <p className="text-[var(--text-muted)] mb-8">
            Trade on DGClaw via Virtuals Protocol. Every trade is an on-chain ACP transaction.
            Your bot makes the decisions, DGClaw executes the trades.
          </p>

          <div className="border border-[var(--border)] rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Join the Arena
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-[var(--text-muted)] mb-2">
                  Your wallet address (Base chain, for withdrawals)
                </label>
                <input
                  type="text"
                  value={walletInput}
                  onChange={(e) => setWalletInput(e.target.value)}
                  placeholder="0x..."
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] text-sm font-mono"
                />
              </div>

              <div className="bg-[var(--bg-secondary)] rounded-lg p-4 text-sm text-[var(--text-muted)] space-y-1">
                <p>1. You&apos;ll be assigned a trading agent with its own wallet</p>
                <p>2. Send USDC (Base chain) to the agent wallet</p>
                <p>3. Select which bot drives your arena trades</p>
                <p className="text-[var(--text-secondary)] mt-2">
                  Bridge fee: ~$1 flat. Minimum deposit: $5 USDC.
                </p>
              </div>

              {error && (
                <p className="text-red-400 text-sm">{error}</p>
              )}

              <button
                onClick={handleJoin}
                disabled={joining || !walletInput}
                className="w-full py-3 rounded-xl font-medium text-white bg-[var(--accent)] hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
              >
                {joining ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {joining ? 'Joining...' : 'Join Arena'}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Joined ──
  const walletBalance = status.wallet_balance_usdc || 0
  const dgclawBalance = status.dgclaw_balance || 0
  const positions = status.positions || []
  const activeBot = status.active_bot
  const needsDeposit = dgclawBalance === 0 && walletBalance === 0

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Header onBack={() => router.push('/forge')} onRefresh={fetchStatus} />

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Agent Info */}
        <div className="border border-[var(--border)] rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                {status.agent_name}
              </h2>
              {status.token_symbol && (
                <span className="text-xs text-[var(--text-muted)]">
                  ${status.token_symbol}
                </span>
              )}
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                ${dgclawBalance.toFixed(2)}
              </p>
              <p className="text-xs text-[var(--text-muted)]">DGClaw Balance</p>
            </div>
          </div>

          {/* Wallet address */}
          <div className="flex items-center gap-2 bg-[var(--bg-secondary)] rounded-lg px-3 py-2">
            <Wallet className="h-4 w-4 text-[var(--text-muted)] flex-shrink-0" />
            <span className="text-xs font-mono text-[var(--text-muted)] truncate flex-1">
              {status.wallet_address}
            </span>
            <button
              onClick={() => copyAddress(status.wallet_address || '')}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            >
              {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>

          {walletBalance > 0 && (
            <p className="text-xs text-[var(--text-muted)] mt-2">
              Wallet: ${walletBalance.toFixed(2)} USDC (not yet deposited to DGClaw)
            </p>
          )}
        </div>

        {/* Deposit Section */}
        {needsDeposit && (
          <div className="border border-yellow-500/30 bg-yellow-500/5 rounded-xl p-4">
            <h3 className="text-sm font-medium text-yellow-400 mb-2">Deposit Required</h3>
            <p className="text-sm text-[var(--text-muted)] mb-3">
              Send USDC on Base chain to your agent wallet above.
              Minimum $5. Bridge fee ~$1.
            </p>
            <button
              onClick={handleCheckDeposit}
              disabled={checking}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              {checking ? 'Checking...' : "I've sent it"}
            </button>
            {depositMessage && (
              <p className="text-xs text-[var(--text-muted)] mt-2">{depositMessage}</p>
            )}
          </div>
        )}

        {/* Top up + check deposit (when already funded) */}
        {!needsDeposit && (
          <div className="flex gap-3">
            <button
              onClick={handleCheckDeposit}
              disabled={checking}
              className="flex-1 px-4 py-2 rounded-lg text-sm font-medium border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Check / Deposit More
            </button>
            {depositMessage && (
              <p className="text-xs text-[var(--text-muted)] self-center">{depositMessage}</p>
            )}
          </div>
        )}

        {/* Active Bot */}
        <div className="border border-[var(--border)] rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-[var(--accent)]" />
              <span className="text-sm font-medium text-[var(--text-primary)]">Arena Bot</span>
            </div>
            <button
              onClick={() => setShowBotSelector(!showBotSelector)}
              className="text-sm text-[var(--accent)] hover:underline flex items-center gap-1"
            >
              {activeBot ? 'Change' : 'Select Bot'}
              <ChevronDown className="h-3 w-3" />
            </button>
          </div>

          {activeBot ? (
            <div className="mt-2 bg-[var(--bg-secondary)] rounded-lg px-3 py-2">
              <p className="text-sm font-medium text-[var(--text-primary)]">{activeBot.config_name}</p>
              <p className="text-xs text-[var(--text-muted)]">{activeBot.symbol}</p>
            </div>
          ) : (
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              No bot selected. Pick a bot to drive your arena trades.
            </p>
          )}

          {showBotSelector && (
            <div className="mt-3 border border-[var(--border)] rounded-lg overflow-hidden">
              {bots.length === 0 ? (
                <p className="px-3 py-2 text-sm text-[var(--text-muted)]">
                  No active bots found. Create and activate a bot first.
                </p>
              ) : (
                bots.map((bot) => (
                  <button
                    key={bot.config_id}
                    onClick={() => handleSetBot(bot.config_id)}
                    disabled={settingBot}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-[var(--bg-secondary)] transition-colors border-b border-[var(--border)] last:border-b-0 ${
                      activeBot?.config_id === bot.config_id ? 'bg-[var(--accent)]/10' : ''
                    }`}
                  >
                    <p className="font-medium text-[var(--text-primary)]">{bot.config_name}</p>
                    <p className="text-xs text-[var(--text-muted)]">{bot.selected_pair}</p>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Positions */}
        {positions.length > 0 && (
          <div className="border border-[var(--border)] rounded-xl p-4">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">Open Positions</h3>
            <div className="space-y-2">
              {positions.map((pos, i) => {
                const pnl = Number(pos.unrealizedPnl || 0)
                const isPositive = pnl >= 0
                return (
                  <div key={i} className="flex items-center justify-between bg-[var(--bg-secondary)] rounded-lg px-3 py-2">
                    <div className="flex items-center gap-2">
                      {pos.side === 'long' ? (
                        <TrendingUp className="h-4 w-4 text-green-400" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-400" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-[var(--text-primary)]">
                          {pos.pair || pos.coin} {pos.side?.toUpperCase()}
                        </p>
                        <p className="text-xs text-[var(--text-muted)]">
                          {pos.leverage}x | Entry: ${Number(pos.entryPrice || 0).toFixed(2)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        {isPositive ? '+' : ''}${pnl.toFixed(2)}
                      </p>
                      <p className="text-xs text-[var(--text-muted)]">
                        ${Number(pos.size || pos.margin || 0).toFixed(0)} size
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Withdraw */}
        {dgclawBalance > 0 && (
          <div className="border border-[var(--border)] rounded-xl p-4">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">Withdraw</h3>
            <p className="text-xs text-[var(--text-muted)] mb-3">
              Withdraw USDC to {status.user_wallet_address ? (
                <span className="font-mono">{status.user_wallet_address.slice(0, 6)}...{status.user_wallet_address.slice(-4)}</span>
              ) : 'your wallet'}. Minimum $2.
            </p>
            <div className="flex gap-2">
              <input
                type="number"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                placeholder="Amount (USD)"
                min="2"
                step="1"
                className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] text-sm"
              />
              <button
                onClick={handleWithdraw}
                disabled={withdrawing || !withdrawAmount}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--accent)] text-white hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center gap-2"
              >
                {withdrawing ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Withdraw
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Info footer */}
        <div className="text-center pb-8">
          <a
            href="https://degen.virtuals.io"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] inline-flex items-center gap-1"
          >
            Powered by Virtuals Protocol + DGClaw
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  )
}

// ─── Header ──────────────────────────────────────────────────────────────────

function Header({ onBack, onRefresh }: { onBack: () => void; onRefresh?: () => void }) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]">
      <div className="flex items-center justify-between px-4 py-3 max-w-2xl mx-auto">
        <button
          onClick={onBack}
          className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-[var(--text-muted)]" />
        </button>
        <span className="text-sm font-medium text-[var(--text-primary)]">Virtuals Arena</span>
        {onRefresh ? (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] transition-colors"
          >
            <RefreshCw className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        ) : (
          <div className="w-8" />
        )}
      </div>
    </header>
  )
}
