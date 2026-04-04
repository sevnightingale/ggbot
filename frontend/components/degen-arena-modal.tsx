'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalTitle,
  ModalDescription,
} from '@/components/ui/modal'
import {
  Loader2, Copy, Check, RefreshCw, Trophy,
  TrendingUp, TrendingDown, ExternalLink, AlertCircle,
  ArrowRight, Play,
} from 'lucide-react'
import { createClient } from '@/lib/supabase'

const API_BASE = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
const LEADERBOARD_URL = 'https://degen.virtuals.io/#leaderboard'
const POLL_INTERVAL = 10_000 // 10s auto-refresh when modal is open

interface DegenArenaModalProps {
  isOpen: boolean
  onClose: () => void
  configId: string
  configName: string
  isBotActive: boolean
  onActivateBot: () => void
  isActivating?: boolean
}

interface ArenaStatus {
  status: 'not_joined' | 'joined'
  agent_name?: string
  token_symbol?: string
  wallet_address?: string
  user_wallet_address?: string
  wallet_balance_usdc?: number
  dgclaw_balance?: number
  is_registered?: boolean
  positions?: Position[]
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

export function DegenArenaModal({
  isOpen,
  onClose,
  configId,
  configName,
  isBotActive,
  onActivateBot,
  isActivating = false,
}: DegenArenaModalProps) {
  const supabase = createClient()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // State
  const [loading, setLoading] = useState(true)
  const [arenaStatus, setArenaStatus] = useState<ArenaStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Join flow
  const [walletInput, setWalletInput] = useState('')
  const [joining, setJoining] = useState(false)

  // Deposit flow
  const [checking, setChecking] = useState(false)
  const [depositStatus, setDepositStatus] = useState<string | null>(null)

  // Withdraw flow
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawing, setWithdrawing] = useState(false)

  // UI
  const [copied, setCopied] = useState(false)

  // ── Auth helper ──
  const getHeaders = useCallback(async (): Promise<HeadersInit> => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) throw new Error('Not authenticated')
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    }
  }, [supabase])

  // ── Fetch status ──
  const fetchStatus = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true)
      const headers = await getHeaders()
      const res = await fetch(
        `${API_BASE}/api/v2/virtuals-arena/status?config_id=${configId}`,
        { headers }
      )
      const data = await res.json()
      setArenaStatus(data)
      // Clear errors on successful fetch
      if (!showLoading) setError(null)
    } catch (e: unknown) {
      if (showLoading) setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [configId, getHeaders])

  // Auto-refresh when modal is open
  useEffect(() => {
    if (isOpen) {
      fetchStatus(true)
      pollRef.current = setInterval(() => fetchStatus(false), POLL_INTERVAL)
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [isOpen, fetchStatus])

  // ── Join ──
  const handleJoin = async () => {
    if (!walletInput || !walletInput.startsWith('0x') || walletInput.length < 42) {
      setError('Enter a valid wallet address (0x...)')
      return
    }
    try {
      setJoining(true)
      setError(null)
      const headers = await getHeaders()
      const res = await fetch(`${API_BASE}/api/v2/virtuals-arena/join`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ config_id: configId, wallet_address: walletInput }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to join')
      await fetchStatus(true)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to join')
    } finally {
      setJoining(false)
    }
  }

  // ── Check deposit ──
  const handleCheckDeposit = async () => {
    try {
      setChecking(true)
      setDepositStatus('Checking wallet balance...')
      setError(null)
      const headers = await getHeaders()
      const res = await fetch(`${API_BASE}/api/v2/virtuals-arena/check-deposit`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ config_id: configId }),
      })
      const data = await res.json()

      if (data.status === 'deposited') {
        setDepositStatus(data.message || 'Funds deposited successfully!')
        await fetchStatus(false)
        setTimeout(() => setDepositStatus(null), 8000)
      } else if (data.status === 'registering') {
        setDepositStatus(data.message || 'Registering on Degen Claw (~30s)...')
        // Registration is async — poll will pick up completion
        setTimeout(() => setDepositStatus(null), 10000)
      } else if (data.status === 'no_funds') {
        setDepositStatus(null)
        setError('No USDC detected yet. Transfers can take a few minutes — try again shortly.')
      } else if (data.status === 'insufficient') {
        setDepositStatus(null)
        setError(data.message)
      } else if (data.status === 'error') {
        setDepositStatus(null)
        setError(data.reason || 'Deposit failed')
      } else {
        setDepositStatus(data.message || null)
      }
    } catch (e: unknown) {
      setDepositStatus(null)
      setError(e instanceof Error ? e.message : 'Check failed')
    } finally {
      setChecking(false)
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
      const headers = await getHeaders()
      const res = await fetch(`${API_BASE}/api/v2/virtuals-arena/withdraw`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ config_id: configId, amount }),
      })
      const data = await res.json()
      if (data.status === 'success') {
        setWithdrawAmount('')
        await fetchStatus(false)
      } else {
        setError(data.reason || 'Withdrawal failed')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Withdrawal failed')
    } finally {
      setWithdrawing(false)
    }
  }

  // ── Copy ──
  const copyAddress = (addr: string) => {
    navigator.clipboard.writeText(addr)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Bot not active ──
  if (isOpen && !isBotActive && (!arenaStatus || arenaStatus.status === 'not_joined')) {
    return (
      <Modal open={isOpen} onOpenChange={onClose} size="sm">
        <ModalHeader onClose={onClose}>
          <ModalTitle className="flex items-center gap-2">
            <Play className="h-5 w-5 text-[var(--accent)]" />
            Activate Your Bot First
          </ModalTitle>
          <ModalDescription>
            Your bot must be running for arena trades to be mirrored
          </ModalDescription>
        </ModalHeader>
        <ModalBody>
          <div className="rounded-lg bg-[var(--bg-tertiary)] p-4">
            <p className="text-sm text-[var(--text-secondary)]">
              <strong className="text-[var(--text-primary)]">&quot;{configName}&quot;</strong> is
              currently inactive. Activate it first, then enter the Degen Arena.
            </p>
          </div>
        </ModalBody>
        <ModalFooter>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => { onActivateBot(); onClose() }}
            disabled={isActivating}
            className="px-4 py-2 rounded-lg bg-[var(--accent)] text-[var(--bg-primary)] font-medium hover:bg-[var(--accent-hover)] disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            <Play className="h-4 w-4" />
            {isActivating ? 'Activating...' : 'Activate Bot'}
          </button>
        </ModalFooter>
      </Modal>
    )
  }

  // ── Loading ──
  if (loading) {
    return (
      <Modal open={isOpen} onOpenChange={onClose} size="sm">
        <ModalBody>
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
          </div>
        </ModalBody>
      </Modal>
    )
  }

  // ── STATE 1: Not Joined ──
  if (!arenaStatus || arenaStatus.status === 'not_joined') {
    return (
      <Modal open={isOpen} onOpenChange={onClose} size="sm">
        <ModalHeader onClose={onClose}>
          <ModalTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-[var(--accent)]" />
            Degen Arena
          </ModalTitle>
          <ModalDescription>
            Enter &quot;{configName}&quot; into the arena
          </ModalDescription>
        </ModalHeader>

        <ModalBody>
          <div className="space-y-4">
            {/* Explanation */}
            <div className="rounded-lg bg-[var(--bg-tertiary)] p-3 space-y-2">
              <p className="text-sm text-[var(--text-secondary)]">
                Your arena agent will <strong className="text-[var(--text-primary)]">mirror
                this bot&apos;s trades</strong> on Degen Claw. Your bot runs
                normally — paper or live trading is unaffected.
              </p>
            </div>

            {/* Steps */}
            <div className="space-y-2.5">
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">How it works</p>
              <div className="space-y-2">
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center">1</span>
                  <p className="text-sm text-[var(--text-secondary)]">Fund your arena agent with USDC on Base ($10+ recommended, $6 minimum)</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center">2</span>
                  <p className="text-sm text-[var(--text-secondary)]">Your bot automatically mirrors each trade decision to Degen Claw</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center">3</span>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Compete on the{' '}
                    <a href={LEADERBOARD_URL} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline">
                      global leaderboard
                    </a>
                  </p>
                </div>
              </div>
            </div>

            {/* Fees */}
            <div className="flex items-start gap-2 text-xs text-[var(--text-muted)]">
              <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
              <span>~$1 bridge fee per deposit. $0.01 per trade. For a $10 deposit, ~$9 becomes your trading balance.</span>
            </div>

            {/* Wallet input */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                Your wallet address (Base chain)
              </label>
              <input
                type="text"
                value={walletInput}
                onChange={(e) => setWalletInput(e.target.value)}
                placeholder="0x..."
                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-colors"
              />
              <p className="text-xs text-[var(--text-muted)] mt-1">Withdrawals will be sent to this address.</p>
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-lg bg-[var(--ember)]/10 border border-[var(--ember)]/30 p-3">
                <p className="text-sm text-[var(--ember)]">{error}</p>
              </div>
            )}
          </div>
        </ModalBody>

        <ModalFooter>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleJoin}
            disabled={joining || !walletInput}
            className="px-4 py-2 rounded-lg bg-[var(--accent)] text-[var(--bg-primary)] font-medium hover:bg-[var(--accent-hover)] disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {joining ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
            {joining ? 'Joining...' : 'Enter Arena'}
          </button>
        </ModalFooter>
      </Modal>
    )
  }

  // ── STATE 2 & 3: Joined ──
  const balance = arenaStatus.dgclaw_balance || 0
  const walletBalance = arenaStatus.wallet_balance_usdc || 0
  const positions = arenaStatus.positions || []
  const isRegistered = arenaStatus.is_registered !== false
  const hasFundsInWallet = walletBalance >= 0.1
  const needsFunding = balance === 0 && !hasFundsInWallet

  // Determine the primary action button label and behavior
  const getDepositButtonLabel = () => {
    if (checking) return depositStatus || 'Processing...'
    if (!isRegistered && hasFundsInWallet) return 'Register & Deposit'
    if (hasFundsInWallet && balance === 0) return 'Deposit to Arena'
    if (hasFundsInWallet) return 'Deposit More'
    return "I've Sent USDC — Check Balance"
  }

  return (
    <Modal open={isOpen} onOpenChange={onClose} size="sm">
      <ModalHeader onClose={onClose}>
        <ModalTitle className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-[var(--accent)]" />
          Degen Arena
        </ModalTitle>
        <ModalDescription>
          {arenaStatus.agent_name}
          {arenaStatus.token_symbol ? ` · $${arenaStatus.token_symbol}` : ''}
        </ModalDescription>
      </ModalHeader>

      <ModalBody>
        <div className="space-y-4">
          {/* Arena Balance — the main number */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Arena Balance</p>
              {hasFundsInWallet && (
                <span className="text-xs text-[var(--accent)]">
                  +${walletBalance.toFixed(2)} in wallet
                </span>
              )}
            </div>
            <p className="text-3xl font-semibold text-[var(--text-primary)] mt-1 font-mono">
              ${balance.toFixed(2)}
            </p>
            {balance > 0 && (
              <p className="text-xs text-[var(--text-muted)] mt-1">
                This is what your bot trades with on Degen Claw
              </p>
            )}
          </div>

          {/* Registration in progress */}
          {!isRegistered && hasFundsInWallet && (
            <div className="rounded-lg bg-[var(--accent)]/5 border border-[var(--accent)]/20 p-3 flex items-center gap-3">
              <Loader2 className="h-4 w-4 animate-spin text-[var(--accent)] flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">Registering on Degen Claw...</p>
                <p className="text-xs text-[var(--text-muted)]">This takes about 30 seconds. We&apos;ll deposit your funds automatically once complete.</p>
              </div>
            </div>
          )}

          {/* Needs funding prompt */}
          {needsFunding && (
            <div className="rounded-lg bg-[var(--accent)]/5 border border-[var(--accent)]/20 p-3 space-y-2">
              <p className="text-sm font-medium text-[var(--text-primary)]">Fund your arena agent</p>
              <p className="text-sm text-[var(--text-secondary)]">
                Send <strong>USDC</strong> on Base chain to:
              </p>
              <div className="flex items-center gap-2 bg-[var(--bg-primary)] rounded-lg px-3 py-2">
                <span className="text-xs font-mono text-[var(--text-muted)] truncate flex-1">
                  {arenaStatus.wallet_address}
                </span>
                <button
                  onClick={() => copyAddress(arenaStatus.wallet_address || '')}
                  className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-[var(--profit-color)]" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                $10+ recommended (minimum $6). ~$1 bridge fee deducted on deposit.
              </p>
            </div>
          )}

          {/* Deposit address (when already funded — collapsed) */}
          {!needsFunding && (
            <div className="flex items-center gap-2 bg-[var(--bg-secondary)] rounded-lg px-3 py-2">
              <span className="text-xs text-[var(--text-muted)]">Deposit:</span>
              <span className="text-xs font-mono text-[var(--text-muted)] truncate flex-1">
                {arenaStatus.wallet_address}
              </span>
              <button
                onClick={() => copyAddress(arenaStatus.wallet_address || '')}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-[var(--profit-color)]" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          )}

          {/* Action button */}
          <button
            onClick={handleCheckDeposit}
            disabled={checking}
            className="w-full py-2 rounded-lg text-sm font-medium border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:bg-[var(--bg-secondary)] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {checking ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {depositStatus || 'Processing...'}
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                {getDepositButtonLabel()}
              </>
            )}
          </button>

          {/* Deposit status message */}
          {depositStatus && !checking && (
            <p className="text-xs text-[var(--profit-color)]">{depositStatus}</p>
          )}

          {/* Positions */}
          {positions.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Open Positions</p>
              <div className="space-y-1.5">
                {positions.map((pos, i) => {
                  const pnl = Number(pos.unrealizedPnl || 0)
                  return (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] px-3 py-2 text-sm">
                      <div className="flex items-center gap-2">
                        {pos.side === 'long' ? (
                          <TrendingUp className="h-3.5 w-3.5 text-[var(--profit-color)]" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5 text-[var(--loss-color)]" />
                        )}
                        <span className="text-[var(--text-primary)] font-medium">
                          {pos.pair || pos.coin}
                        </span>
                        <span className="text-[var(--text-muted)] text-xs">{pos.leverage}x</span>
                      </div>
                      <span className={`font-mono ${pnl >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
                        {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* No positions note */}
          {positions.length === 0 && balance > 0 && (
            <div className="rounded-lg bg-[var(--bg-tertiary)] p-3 flex items-start gap-2">
              <AlertCircle className="h-3.5 w-3.5 text-[var(--text-muted)] flex-shrink-0 mt-0.5" />
              <p className="text-xs text-[var(--text-muted)]">
                No open positions. Your bot will appear on the leaderboard after its first arena trade.
              </p>
            </div>
          )}

          {/* Withdraw */}
          {balance > 2 && (
            <div className="pt-3 border-t border-[var(--border)]">
              <p className="text-xs font-medium text-[var(--text-muted)] mb-2">Withdraw</p>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  placeholder="Amount (min $2)"
                  min="2"
                  className="flex-1 px-3 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-colors"
                />
                <button
                  onClick={handleWithdraw}
                  disabled={withdrawing || !withdrawAmount}
                  className="px-3 py-1.5 rounded-lg text-sm border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:bg-[var(--bg-secondary)] disabled:opacity-50 transition-colors flex items-center gap-1.5"
                >
                  {withdrawing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                  Withdraw
                </button>
              </div>
              {arenaStatus.user_wallet_address && (
                <p className="text-xs text-[var(--text-muted)] mt-1.5">
                  Sent to <span className="font-mono">{arenaStatus.user_wallet_address.slice(0, 6)}...{arenaStatus.user_wallet_address.slice(-4)}</span>
                </p>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="rounded-lg bg-[var(--ember)]/10 border border-[var(--ember)]/30 p-3">
              <p className="text-sm text-[var(--ember)]">{error}</p>
            </div>
          )}
        </div>
      </ModalBody>

      <ModalFooter>
        <a
          href={LEADERBOARD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] inline-flex items-center gap-1 transition-colors"
        >
          View Leaderboard
          <ExternalLink className="h-3 w-3" />
        </a>
      </ModalFooter>
    </Modal>
  )
}
