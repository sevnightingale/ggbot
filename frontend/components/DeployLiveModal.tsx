'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { Modal, ModalHeader, ModalBody, ModalTitle } from '@/components/ui/modal'
import {
  Loader2, Copy, CheckCircle2, Wallet, TrendingUp, ArrowDownToLine,
  ArrowRight, AlertCircle,
} from 'lucide-react'
import { apiClient } from '@/lib/api'
import { VirtualsConnectButton } from '@/components/VirtualsConnectButton'

interface DeployLiveModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceConfigId?: string
  virtualsConfigId?: string
  sourceConfigName?: string
  onDeployComplete?: (newConfigId: string) => void
}

type Stage = 'connect' | 'setup' | 'deploying' | 'funding' | 'processing' | 'manage'

const POLL_MS = 3000
const MIN_DEPOSIT = 10
const DEFAULT_DEPOSIT = '25'

// Backend deposit-progress stage names (must match api/arena_v2.py)
const BACKEND_STAGES = [
  { id: 'starting',    label: 'Starting',        order: 0 },
  { id: 'depositing',  label: 'Depositing',      order: 1 },
  { id: 'hl_setup',    label: 'Hyperliquid',     order: 2 },
  { id: 'leaderboard', label: 'Leaderboard',     order: 3 },
  { id: 'complete',    label: 'Live',            order: 4 },
] as const

export function DeployLiveModal({
  open,
  onOpenChange,
  sourceConfigId,
  virtualsConfigId,
  sourceConfigName,
  onDeployComplete,
}: DeployLiveModalProps) {
  const [stage, setStage] = useState<Stage>('connect')
  const [checkingConnection, setCheckingConnection] = useState(true)
  const [agentName, setAgentName] = useState(sourceConfigName || '')
  const [deployProgress, setDeployProgress] = useState<string>('Waiting for signer approval…')
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [activeConfigId, setActiveConfigId] = useState<string | undefined>(virtualsConfigId)
  const [status, setStatus] = useState<
    Awaited<ReturnType<typeof apiClient.arenaV2Status>> | null
  >(null)
  const [depositBusy, setDepositBusy] = useState(false)
  const [depositAmount, setDepositAmount] = useState(DEFAULT_DEPOSIT)
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawDest, setWithdrawDest] = useState('')
  const [withdrawBusy, setWithdrawBusy] = useState(false)

  const pollDeployRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollStatusRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const popupRef = useRef<Window | null>(null)

  const clearDeployPoll = () => {
    if (pollDeployRef.current) { clearInterval(pollDeployRef.current); pollDeployRef.current = null }
  }
  const clearStatusPoll = () => {
    if (pollStatusRef.current) { clearInterval(pollStatusRef.current); pollStatusRef.current = null }
  }

  // ---------------------------------------------------------------------
  // Initial state when modal opens
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!open) {
      clearDeployPoll()
      clearStatusPoll()
      return
    }

    setError(null)
    setCheckingConnection(true)
    apiClient
      .arenaV2ConnectionStatus()
      .then((r) => {
        if (virtualsConfigId) {
          setActiveConfigId(virtualsConfigId)
          setStage('funding')
        } else {
          setStage(r.connected ? 'setup' : 'connect')
        }
      })
      .catch(() => setStage(virtualsConfigId ? 'funding' : 'connect'))
      .finally(() => setCheckingConnection(false))
  }, [open, virtualsConfigId])

  // ---------------------------------------------------------------------
  // Status poll — drives funding → processing → manage transitions.
  // Runs in all post-deploy stages since the backend can finish the flow
  // even if the user closed the modal, and we want to pick up on reopen.
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!open || !activeConfigId) return
    if (stage === 'connect' || stage === 'setup' || stage === 'deploying') return

    const tick = async () => {
      try {
        const s = await apiClient.arenaV2Status(activeConfigId)
        setStatus(s)

        const progress = s.deposit_progress
        const backendStage = progress?.stage

        // Drive UI stage based on backend state
        if (s.status === 'active' && backendStage === 'complete') {
          // Fully done — transition to management UI
          setStage('manage')
        } else if (backendStage && backendStage !== 'complete' && backendStage !== 'failed') {
          // Flow in progress (starting / depositing / hl_setup / leaderboard)
          setStage('processing')
        } else if (backendStage === 'failed') {
          // Leave user on processing stage to show retry; frontend renders failed state
          setStage('processing')
        } else if (s.status === 'active') {
          // Active but no progress row (e.g. retry on already-done) — go to manage
          setStage('manage')
        } else {
          // No flow running — show funding stage (user can trigger deposit)
          setStage((cur) => (cur === 'manage' ? 'manage' : 'funding'))
        }
      } catch {
        // transient errors are fine
      }
    }

    tick()
    clearStatusPoll()
    pollStatusRef.current = setInterval(tick, POLL_MS)
    return () => clearStatusPoll()
  }, [open, activeConfigId, stage])

  // ---------------------------------------------------------------------
  // Popup 2 — signer approval flow (unchanged)
  // ---------------------------------------------------------------------
  const startDeploy = useCallback(async () => {
    if (!sourceConfigId) return
    setError(null)
    setStage('deploying')
    try {
      const res = await apiClient.arenaV2DeployLive(sourceConfigId, agentName || undefined)
      setActiveConfigId(res.new_config_id)
      setDeployProgress('Waiting for signer approval in popup…')

      const w = 480, h = 720
      const left = Math.max(0, (window.screen.width - w) / 2)
      const top = Math.max(0, (window.screen.height - h) / 2)
      popupRef.current = window.open(
        res.signerUrl, 'virtuals-signer',
        `width=${w},height=${h},left=${left},top=${top}`,
      )

      clearDeployPoll()
      pollDeployRef.current = setInterval(async () => {
        try {
          const poll = await apiClient.arenaV2DeployPoll(res.signerRequestId)
          if (poll.status === 'pending') {
            if (poll.stage === 'signer') setDeployProgress('Waiting for signer approval…')
            return
          }
          if (poll.status === 'error') {
            clearDeployPoll()
            setError(
              `${poll.stage ?? 'deploy'}: ${
                poll.reason ?? (typeof poll.detail === 'string' ? poll.detail : JSON.stringify(poll.detail ?? {}))
              }`,
            )
            setStage('setup')
            return
          }
          if (poll.status === 'completed') {
            clearDeployPoll()
            if (popupRef.current && !popupRef.current.closed) popupRef.current.close()
            setStage('funding')
            onDeployComplete?.(res.new_config_id)
          }
        } catch {
          // keep polling
        }
      }, POLL_MS)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Deploy failed')
      setStage('setup')
    }
  }, [sourceConfigId, agentName, onDeployComplete])

  // ---------------------------------------------------------------------
  // Funding — kick off async deposit flow (returns immediately)
  // ---------------------------------------------------------------------
  const copyWallet = () => {
    if (!status?.agent_wallet_address) return
    navigator.clipboard.writeText(status.agent_wallet_address)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  const startDeposit = async () => {
    if (!activeConfigId) return
    const amt = parseFloat(depositAmount)
    if (!isFinite(amt) || amt < MIN_DEPOSIT) {
      setError(`Enter a deposit amount of at least $${MIN_DEPOSIT}.`)
      return
    }
    setDepositBusy(true)
    setError(null)
    try {
      const result = await apiClient.arenaV2CheckDeposit(activeConfigId, amt)
      if (result.status === 'in_progress' || result.status === 'already_in_progress') {
        // Backend kicked off (or already running) — transition immediately to processing UI.
        setStage('processing')
      } else if (result.status === 'already_complete') {
        setStage('manage')
      } else if (result.status === 'amount_too_low') {
        setError(result.message ?? `Minimum deposit is $${MIN_DEPOSIT}`)
      } else if (result.status === 'insufficient') {
        setError(result.message ?? 'Not enough USDC on Base. Send more to the agent wallet.')
      } else if (result.status === 'rpc_error') {
        setError(result.message ?? 'Could not read Base USDC balance — try again shortly.')
      } else {
        setError(`Unknown status: ${result.status}`)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'check-deposit failed')
    } finally {
      setDepositBusy(false)
    }
  }

  const doWithdraw = async () => {
    if (!activeConfigId) return
    const amt = parseFloat(withdrawAmount)
    if (!isFinite(amt) || amt < 2) { setError('Minimum withdrawal is $2'); return }
    setWithdrawBusy(true)
    setError(null)
    try {
      const result = await apiClient.arenaV2Withdraw(activeConfigId, amt, withdrawDest || undefined)
      if (result.status !== 'success') {
        setError(`Withdraw failed: ${JSON.stringify(result.detail ?? {})}`)
      } else {
        setWithdrawAmount('')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Withdraw failed')
    } finally {
      setWithdrawBusy(false)
    }
  }

  // ---------------------------------------------------------------------
  // Stage renderers
  // ---------------------------------------------------------------------

  const renderConnectStage = () => (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-muted)]">
        First, connect your Virtuals Protocol account. This one-time step lets ggbots
        spin up agent wallets on your behalf.
      </p>
      <VirtualsConnectButton
        onConnected={() => setStage(virtualsConfigId ? 'funding' : 'setup')}
        label="Connect Virtuals"
        pollingLabel="Waiting for Virtuals approval…"
      />
    </div>
  )

  const renderSetupStage = () => (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-muted)]">
        Deploying creates a dedicated Virtuals agent with its own Hyperliquid wallet.
        You&apos;ll get one approval popup; after that ggbots handles the rest.
      </p>
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
          Agent Name (public on Virtuals)
        </label>
        <input
          value={agentName}
          onChange={(e) => setAgentName(e.target.value)}
          className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-sm"
          placeholder="e.g. trend-hunter"
        />
      </div>
      <button
        onClick={startDeploy}
        disabled={!agentName.trim()}
        className="px-4 py-2 rounded bg-[var(--accent)] text-white font-medium disabled:opacity-50"
      >
        Deploy Live Version
      </button>
    </div>
  )

  const renderDeployingStage = () => (
    <div className="flex flex-col items-center justify-center py-10 gap-3">
      <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
      <p className="text-sm text-[var(--text-primary)]">{deployProgress}</p>
      <p className="text-xs text-[var(--text-muted)]">
        Do not close this window — the flow resumes automatically when the popup is approved.
      </p>
    </div>
  )

  // Step 1 of 2: show wallet address, wait for USDC deposit, collect amount.
  const renderFundingStage = () => {
    const wallet = status?.agent_wallet_address
    const baseBal = status?.base_usdc_balance ?? null
    const parsedAmount = parseFloat(depositAmount)
    const amountValid = isFinite(parsedAmount) && parsedAmount >= MIN_DEPOSIT
    const maxDepositable = baseBal === null ? null : Math.max(0, baseBal - 1)
    const amountFitsBalance =
      amountValid && maxDepositable !== null && parsedAmount <= maxDepositable
    const hasEnoughBalance = baseBal !== null && baseBal >= MIN_DEPOSIT + 1
    // Tokenization is required for DegenClaw leaderboard delivery. Undefined =
    // probe hasn't landed yet → treat as unknown (soft); false = hard block.
    const tokenizationKnown = status?.is_tokenized !== undefined
    const isTokenized = status?.is_tokenized === true
    const tokenizeBlocked = tokenizationKnown && !isTokenized
    const tokenizeUrl = status?.tokenize_url || 'https://app.virtuals.io'
    const canDeposit =
      !depositBusy && hasEnoughBalance && amountFitsBalance && !tokenizeBlocked

    return (
      <div className="space-y-4">
        {/* Stepper header */}
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
          <span className="text-[var(--accent)]">Step 1 of 2</span>
          <span>·</span>
          <span>Fund your agent wallet</span>
        </div>

        <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="h-4 w-4 text-[var(--accent)]" />
            <span className="text-sm font-medium">Agent Wallet (Base)</span>
          </div>
          <div className="flex items-center gap-2">
            <code className="text-xs break-all px-2 py-1 rounded bg-[var(--bg-primary)] flex-1">
              {wallet || '—'}
            </code>
            <button onClick={copyWallet} className="p-1 hover:bg-[var(--bg-hover)] rounded">
              {copied ? <CheckCircle2 className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            Send <strong>USDC on Base</strong> (native Base USDC). Minimum ${MIN_DEPOSIT}
            — we keep $1 in the wallet for ACP fees.{' '}
            <strong>Do NOT send from Arbitrum or Ethereum mainnet — funds will be lost.</strong>
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="p-2 rounded bg-[var(--bg-primary)]">
              <div className="text-[10px] uppercase text-[var(--text-muted)]">Base balance</div>
              <div className="text-sm font-mono">
                {baseBal === null ? '—' : `$${baseBal.toFixed(2)}`}
              </div>
            </div>
            <div className="p-2 rounded bg-[var(--bg-primary)]">
              <div className="text-[10px] uppercase text-[var(--text-muted)]">Max depositable</div>
              <div className="text-sm font-mono">
                {maxDepositable === null ? '—' : `$${maxDepositable.toFixed(2)}`}
              </div>
            </div>
          </div>
        </div>

        {/* Tokenization gate — DegenClaw silently expires leaderboard jobs
            when the agent hasn't launched a token yet. Warn early. */}
        {tokenizeBlocked && (
          <div className="p-3 rounded border border-amber-500/40 bg-amber-500/5">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-700 dark:text-amber-500">
                  Tokenize your agent first
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  DegenClaw only accepts deposits for tokenized agents. Launch a
                  token on the Virtuals dashboard, then come back to deposit.
                </p>
                <a
                  href={tokenizeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-[var(--accent)] hover:underline"
                >
                  Open Virtuals dashboard <ArrowRight className="h-3 w-3" />
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Amount input only appears when balance is sufficient */}
        {hasEnoughBalance ? (
          <>
            <div className="flex items-center gap-2 pt-2 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
              <span className="text-[var(--accent)]">Step 2 of 2</span>
              <span>·</span>
              <span>Choose amount to deposit</span>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
                Deposit Amount (USDC)
              </label>
              <input
                type="number"
                min={MIN_DEPOSIT}
                step={1}
                placeholder={`Min $${MIN_DEPOSIT}`}
                value={depositAmount}
                onChange={(e) => setDepositAmount(e.target.value)}
                className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-sm"
              />
            </div>
            <button
              onClick={startDeposit}
              disabled={!canDeposit}
              className="w-full px-4 py-2 rounded bg-[var(--accent)] text-white font-medium disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {depositBusy ? (
                <><Loader2 className="h-4 w-4 animate-spin" />Starting…</>
              ) : tokenizeBlocked ? (
                'Tokenize your agent first'
              ) : !amountValid ? (
                `Enter at least $${MIN_DEPOSIT}`
              ) : !amountFitsBalance ? (
                'Amount exceeds available balance'
              ) : (
                <>Deposit ${parsedAmount.toFixed(0)} to Hyperliquid <ArrowRight className="h-4 w-4" /></>
              )}
            </button>
          </>
        ) : (
          <div className="p-4 rounded border border-dashed border-[var(--border)] bg-[var(--bg-secondary)] text-center">
            <Loader2 className="h-5 w-5 animate-spin mx-auto text-[var(--accent)] mb-2" />
            <p className="text-sm font-medium">Waiting for USDC deposit…</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              This page auto-refreshes every few seconds. You can close and come back.
            </p>
          </div>
        )}
      </div>
    )
  }

  // In-flight deposit — show backend stage + animated progress bar.
  const renderProcessingStage = () => {
    const progress = status?.deposit_progress
    const currentStage = progress?.stage || 'starting'
    const currentMessage = progress?.message || 'Starting…'
    const failed = currentStage === 'failed'

    const currentOrder = BACKEND_STAGES.find((s) => s.id === currentStage)?.order ?? 0
    const completed = currentStage === 'complete'

    return (
      <div className="space-y-5 py-4">
        {/* Stage pill */}
        <div className="flex items-center justify-center">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
            failed
              ? 'bg-red-500/10 text-red-600 border border-red-500/30'
              : completed
              ? 'bg-green-500/10 text-green-600 border border-green-500/30'
              : 'bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/30'
          }`}>
            {failed ? <AlertCircle className="h-3 w-3" /> :
             completed ? <CheckCircle2 className="h-3 w-3" /> :
             <Loader2 className="h-3 w-3 animate-spin" />}
            <span className="uppercase tracking-wider">{currentStage.replace('_', ' ')}</span>
          </div>
        </div>

        {/* Status message */}
        <p className="text-sm text-center text-[var(--text-primary)] px-4">{currentMessage}</p>

        {/* Animated progress bar with stepper */}
        <div className="space-y-2">
          <div className="h-2 rounded-full bg-[var(--bg-secondary)] overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${failed ? 'bg-red-500' : 'bg-[var(--accent)]'}`}
              style={{ width: `${Math.min(100, ((currentOrder + (completed ? 1 : 0.5)) / BACKEND_STAGES.length) * 100)}%` }}
            />
          </div>
          <div className="grid grid-cols-4 gap-1 text-[10px] text-center text-[var(--text-muted)]">
            {BACKEND_STAGES.filter((s) => s.id !== 'starting').map((s) => (
              <div key={s.id} className={`${currentOrder >= s.order ? 'text-[var(--text-primary)] font-medium' : ''}`}>
                {s.label}
              </div>
            ))}
          </div>
        </div>

        {/* Info / action rows */}
        {failed ? (
          <div className="space-y-3">
            <div className="p-3 rounded border border-red-500/30 bg-red-500/10 text-xs text-red-600">
              <div className="font-medium mb-1">Setup stopped at a step it can safely retry from.</div>
              <div className="text-red-600/80">{currentMessage}</div>
            </div>
            <button
              onClick={() => { setStage('funding'); setError(null) }}
              className="w-full px-4 py-2 rounded bg-[var(--accent)] text-white font-medium"
            >
              Retry from where it left off
            </button>
          </div>
        ) : completed ? (
          <div className="p-3 rounded border border-green-500/30 bg-green-500/10 text-xs text-green-600 text-center">
            🎉 Your bot is live and trading on Hyperliquid.
          </div>
        ) : (
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-xs text-[var(--text-muted)] text-center">
            This takes up to 5 minutes. <strong className="text-[var(--text-primary)]">You can close this modal</strong>{' '}
            — the deposit keeps running in the background. Come back to watch progress.
          </div>
        )}
      </div>
    )
  }

  const renderManageStage = () => {
    const hlVal = status?.hl_account_value ?? 0
    const dgclawBal = status?.dgclaw_balance ?? null
    const positions = status?.hl_positions ?? []
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="text-xs text-[var(--text-muted)]">DGClaw Balance</div>
            <div className="text-lg font-mono mt-1">
              {dgclawBal === null ? '—' : `$${dgclawBal.toFixed(2)}`}
            </div>
          </div>
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="text-xs text-[var(--text-muted)]">Open Margin (HL)</div>
            <div className="text-lg font-mono mt-1">${hlVal.toFixed(2)}</div>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4" />
            <span className="text-sm font-medium">Open Positions</span>
          </div>
          {positions.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)]">No open positions.</p>
          ) : (
            <div className="space-y-1">
              {positions.map((p) => (
                <div
                  key={p.coin}
                  className="p-2 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-xs font-mono flex justify-between"
                >
                  <span>
                    {p.coin} {p.size > 0 ? 'long' : 'short'} × ${Math.abs(p.entry_price).toFixed(2)}
                  </span>
                  <span className={p.unrealized_pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                    {p.unrealized_pnl >= 0 ? '+' : ''}${p.unrealized_pnl.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ArrowDownToLine className="h-4 w-4" />
            <span className="text-sm font-medium">Withdraw from HL</span>
          </div>
          <div className="flex gap-2">
            <input
              type="number" min="2" step="0.01"
              placeholder="Amount (USDC)"
              value={withdrawAmount}
              onChange={(e) => setWithdrawAmount(e.target.value)}
              className="flex-1 px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-sm"
            />
            <button
              onClick={doWithdraw}
              disabled={withdrawBusy || !withdrawAmount}
              className="px-4 py-2 rounded bg-[var(--accent)] text-white font-medium disabled:opacity-50"
            >
              {withdrawBusy ? 'Withdrawing…' : 'Withdraw'}
            </button>
          </div>
          <input
            placeholder="Destination (blank = agent wallet)"
            value={withdrawDest}
            onChange={(e) => setWithdrawDest(e.target.value)}
            className="w-full px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-xs"
          />
          <p className="text-xs text-[var(--text-muted)]">
            HL charges ~$1 flat fee. Funds arrive on Arbitrum.
          </p>
        </div>

        <div className="space-y-2">
          {status?.leaderboard_joined ? (
            <a
              href="https://degen.virtuals.io/#leaderboard"
              target="_blank" rel="noopener noreferrer"
              className="block text-center px-4 py-2 rounded border border-[var(--border)] text-sm hover:bg-[var(--bg-hover)]"
            >
              View on DegenClaw leaderboard ↗
            </a>
          ) : (
            <p className="text-xs text-center text-[var(--text-muted)]">
              Leaderboard registration pending — this happens automatically.
            </p>
          )}
        </div>
      </div>
    )
  }

  const title = (() => {
    if (stage === 'manage') return 'Manage Live Bot'
    if (stage === 'processing') return 'Setting Up Your Live Bot'
    if (stage === 'funding') return 'Fund Your Live Bot'
    if (stage === 'deploying') return 'Deploying Live Bot'
    return 'Deploy Live Version'
  })()

  return (
    <Modal open={open} onOpenChange={onOpenChange} size="md">
      <ModalHeader onClose={() => onOpenChange(false)}>
        <ModalTitle>{title}</ModalTitle>
      </ModalHeader>
      <ModalBody>
        {checkingConnection ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            {error && (
              <div className="p-2 rounded border border-red-500/30 bg-red-500/10 text-xs text-red-600">
                {error}
              </div>
            )}
            {stage === 'connect' && renderConnectStage()}
            {stage === 'setup' && renderSetupStage()}
            {stage === 'deploying' && renderDeployingStage()}
            {stage === 'funding' && renderFundingStage()}
            {stage === 'processing' && renderProcessingStage()}
            {stage === 'manage' && renderManageStage()}
          </div>
        )}
      </ModalBody>
    </Modal>
  )
}
