'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { Modal, ModalHeader, ModalBody, ModalTitle } from '@/components/ui/modal'
import { Loader2, Copy, CheckCircle2, Wallet, TrendingUp, ArrowDownToLine } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { VirtualsConnectButton } from '@/components/VirtualsConnectButton'

interface DeployLiveModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /**
   * When opening for deployment of a paper bot, pass its config_id. Once the
   * deploy flow finishes, the modal swaps to `virtualsConfigId` (the newly
   * created virtuals config) so subsequent state views manage the live bot.
   *
   * If opened directly for an existing virtuals bot (e.g. "Manage Live Bot"),
   * pass that config_id as `virtualsConfigId` and leave `sourceConfigId`
   * undefined — the modal skips the deploy stage.
   */
  sourceConfigId?: string
  virtualsConfigId?: string
  sourceConfigName?: string
  onDeployComplete?: (newConfigId: string) => void
}

type Stage = 'connect' | 'setup' | 'deploying' | 'funding' | 'manage'

const POLL_MS = 3000
const MIN_HL_BRIDGE = 5

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
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawDest, setWithdrawDest] = useState('')
  const [withdrawBusy, setWithdrawBusy] = useState(false)

  const pollDeployRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollStatusRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const popupRef = useRef<Window | null>(null)

  const clearDeployPoll = () => {
    if (pollDeployRef.current) {
      clearInterval(pollDeployRef.current)
      pollDeployRef.current = null
    }
  }
  const clearStatusPoll = () => {
    if (pollStatusRef.current) {
      clearInterval(pollStatusRef.current)
      pollStatusRef.current = null
    }
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
          // Management flow — we already have a virtuals bot. For management
          // the JWT isn't needed; skip straight to funding/manage.
          setActiveConfigId(virtualsConfigId)
          setStage('funding')
        } else {
          setStage(r.connected ? 'setup' : 'connect')
        }
      })
      .catch(() => {
        setStage(virtualsConfigId ? 'funding' : 'connect')
      })
      .finally(() => setCheckingConnection(false))
  }, [open, virtualsConfigId])

  // ---------------------------------------------------------------------
  // Poll arena_v2 status whenever we're past deploy stage
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!open || !activeConfigId) return
    if (stage !== 'funding' && stage !== 'manage') return

    const tick = async () => {
      try {
        const s = await apiClient.arenaV2Status(activeConfigId)
        setStatus(s)
        if (s.status === 'active' && s.hl_account_value && s.hl_account_value > 0) {
          setStage('manage')
        }
      } catch {
        // Transient errors are fine — keep polling.
      }
    }

    tick()
    clearStatusPoll()
    pollStatusRef.current = setInterval(tick, 10000)
    return () => clearStatusPoll()
  }, [open, activeConfigId, stage])

  // ---------------------------------------------------------------------
  // Popup 2 — signer approval flow
  // ---------------------------------------------------------------------
  const startDeploy = useCallback(async () => {
    if (!sourceConfigId) return
    setError(null)
    setStage('deploying')
    try {
      const res = await apiClient.arenaV2DeployLive(sourceConfigId, agentName || undefined)
      setActiveConfigId(res.new_config_id)
      setDeployProgress('Waiting for signer approval in popup…')

      // Open popup 2
      const w = 480
      const h = 720
      const left = Math.max(0, (window.screen.width - w) / 2)
      const top = Math.max(0, (window.screen.height - h) / 2)
      popupRef.current = window.open(
        res.signerUrl,
        'virtuals-signer',
        `width=${w},height=${h},left=${left},top=${top}`,
      )

      // Start polling /deploy-poll
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

      // After signer approved, we also drive a progress message based on stage
      const progressMessages = [
        { after: 4000, msg: 'Activating Hyperliquid unified account…' },
        { after: 12000, msg: 'Authorizing Hyperliquid API wallet…' },
      ]
      progressMessages.forEach(({ after, msg }) => setTimeout(() => setDeployProgress((cur) => (pollDeployRef.current ? msg : cur)), after))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Deploy failed')
      setStage('setup')
    }
  }, [sourceConfigId, agentName, onDeployComplete])

  // ---------------------------------------------------------------------
  // Funding actions
  // ---------------------------------------------------------------------
  const copyWallet = () => {
    if (!status?.agent_wallet_address) return
    navigator.clipboard.writeText(status.agent_wallet_address)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  const checkDeposit = async () => {
    if (!activeConfigId) return
    setDepositBusy(true)
    setError(null)
    try {
      const result = await apiClient.arenaV2CheckDeposit(activeConfigId)
      if (result.status === 'bridged') {
        // Force an immediate status refresh
        const s = await apiClient.arenaV2Status(activeConfigId)
        setStatus(s)
      } else if (result.status === 'insufficient') {
        setError(result.message ?? `Need at least $${MIN_HL_BRIDGE} USDC on Arbitrum`)
      } else if (result.status === 'bridge_failed') {
        setError(`Bridge failed: ${JSON.stringify(result.detail)}`)
      } else {
        setError('Could not read Arbitrum balance — try again shortly.')
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
    if (!isFinite(amt) || amt < 2) {
      setError('Minimum withdrawal is $2')
      return
    }
    setWithdrawBusy(true)
    setError(null)
    try {
      const result = await apiClient.arenaV2Withdraw(
        activeConfigId,
        amt,
        withdrawDest || undefined,
      )
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
  // Render
  // ---------------------------------------------------------------------

  const renderConnectStage = () => (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-muted)]">
        First, connect your Virtuals Protocol account. This one-time step lets ggbots
        spin up agent wallets on your behalf. You'll get a second approval popup
        per bot for signer registration.
      </p>
      <VirtualsConnectButton
        onConnected={() => {
          setStage(virtualsConfigId ? 'funding' : 'setup')
        }}
        label="Connect Virtuals"
        pollingLabel="Waiting for Virtuals approval…"
      />
    </div>
  )

  const renderSetupStage = () => (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-muted)]">
        Deploying this paper bot creates a dedicated Virtuals agent with its own
        Hyperliquid wallet. You'll get one approval popup; after that ggbots handles
        the rest — account activation, API wallet authorization, and leaderboard
        registration once funded.
      </p>
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
          Agent Name (public on Virtuals)
        </label>
        <input
          value={agentName}
          onChange={(e) => setAgentName(e.target.value)}
          className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-secondary)] text-sm"
          placeholder="e.g. trend-hunter-9000"
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
        Do not close this window — the flow resumes automatically when the popup
        is approved.
      </p>
    </div>
  )

  const renderFundingStage = () => {
    const wallet = status?.agent_wallet_address
    const arbBal = status?.arbitrum_usdc_balance ?? null
    const hlBal = status?.hl_account_value ?? null
    return (
      <div className="space-y-4">
        <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="h-4 w-4 text-[var(--accent)]" />
            <span className="text-sm font-medium">Agent Wallet (Arbitrum)</span>
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
            Send <strong>USDC on Arbitrum</strong> (native USDC, not USDC.e). Minimum
            ${MIN_HL_BRIDGE} — we keep $1 in the wallet for ACP fees.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="text-xs text-[var(--text-muted)]">Arbitrum USDC</div>
            <div className="text-lg font-mono mt-1">
              {arbBal === null ? '—' : `$${arbBal.toFixed(2)}`}
            </div>
          </div>
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="text-xs text-[var(--text-muted)]">HL Account</div>
            <div className="text-lg font-mono mt-1">
              {hlBal === null ? '—' : `$${hlBal.toFixed(2)}`}
            </div>
          </div>
        </div>

        <button
          onClick={checkDeposit}
          disabled={depositBusy || !arbBal || arbBal < MIN_HL_BRIDGE}
          className="w-full px-4 py-2 rounded bg-[var(--accent)] text-white font-medium disabled:opacity-50"
        >
          {depositBusy ? 'Bridging…' : arbBal && arbBal >= MIN_HL_BRIDGE ? 'Bridge to Hyperliquid' : 'Awaiting deposit…'}
        </button>

        {status?.leaderboard_joined && (
          <div className="flex items-center gap-2 text-xs text-green-600">
            <CheckCircle2 className="h-3 w-3" />
            <span>Registered on DegenClaw leaderboard</span>
          </div>
        )}
      </div>
    )
  }

  const renderManageStage = () => {
    const hlVal = status?.hl_account_value ?? 0
    const withdrawable = status?.hl_withdrawable ?? 0
    const positions = status?.hl_positions ?? []
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="text-xs text-[var(--text-muted)]">HL Account</div>
            <div className="text-lg font-mono mt-1">${hlVal.toFixed(2)}</div>
          </div>
          <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)]">
            <div className="text-xs text-[var(--text-muted)]">Withdrawable</div>
            <div className="text-lg font-mono mt-1">${withdrawable.toFixed(2)}</div>
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
              type="number"
              min="2"
              step="0.01"
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

        {status?.leaderboard_joined && (
          <a
            href="https://degen.virtuals.io/#leaderboard"
            target="_blank"
            rel="noopener noreferrer"
            className="block text-center px-4 py-2 rounded border border-[var(--border)] text-sm hover:bg-[var(--bg-hover)]"
          >
            View on DegenClaw leaderboard ↗
          </a>
        )}
      </div>
    )
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} size="md">
      <ModalHeader onClose={() => onOpenChange(false)}>
        <ModalTitle>
          {stage === 'manage'
            ? 'Manage Live Bot'
            : stage === 'funding'
            ? 'Fund Your Live Bot'
            : stage === 'deploying'
            ? 'Deploying Live Bot'
            : 'Deploy Live Version'}
        </ModalTitle>
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
            {stage === 'manage' && renderManageStage()}
          </div>
        )}
      </ModalBody>
    </Modal>
  )
}
