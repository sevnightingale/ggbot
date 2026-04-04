'use client'

import React, { useState, useEffect } from 'react'
import { Clock, Play, PauseCircle, Zap, Crown, Trophy, CheckCircle, Coins, AlertTriangle } from 'lucide-react'
import { BotConfiguration, apiClient } from '@/lib/api'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { AddCreditsModal } from '@/components/AddCreditsModal'
import { RiskAcknowledgmentModal } from '@/components/RiskAcknowledgmentModal'
import { BotImageUpload } from '@/components/BotImageUpload'
import { ArenaRegistrationModal } from '@/components/arena-registration-modal'
import { DegenArenaModal } from '@/components/degen-arena-modal'
import { estimateDailyCost } from '@/lib/cost-estimation'
import { EloTierBadge } from '../shared/EloTierBadge'

interface AccountMetrics {
  totalEquity: number
  availableBalance: number
  pnl: number
  trades: number
  winRate: number
  performance: number
}

interface Activity {
  id: string
  timestamp: string
  type: string
  priority: number
  data: {
    summary?: string
    details?: Record<string, unknown>
    symbol?: string
    importance?: number
    trade_id?: string
    trade_type?: string
    confidence?: number
    leverage?: number
    entry_price?: number
    stop_loss_price?: number
    platform_cost_usd?: number
  }
}

interface ActivationBarProps {
  selectedBot: BotConfiguration
  countdown: string | null
  isStarting: boolean
  isStopping: boolean
  isManualTriggering: boolean
  onStart: () => void
  onStop: () => void
  onManualTrigger: () => void
  metrics?: AccountMetrics | null  // KPI metrics from SSE
  latestActivity?: Activity | null  // Latest activity for status display
}

export function ActivationBar({
  selectedBot,
  countdown,
  isStarting,
  isStopping,
  isManualTriggering,
  onStart,
  onStop,
  onManualTrigger,
  metrics,
  latestActivity
}: ActivationBarProps) {
  const isActive = selectedBot.state === 'active'
  const isSignalDriven = selectedBot.config_data.decision?.analysis_frequency === 'signal_driven'
  const dojoLocked = selectedBot.dojo_locked ?? false
  const { canAccess, userProfile } = usePermissions()
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const [addCreditsOpen, setAddCreditsOpen] = useState(false)
  const [riskModalOpen, setRiskModalOpen] = useState(false)
  const [arenaModalOpen, setArenaModalOpen] = useState(false)
  const [degenArenaOpen, setDegenArenaOpen] = useState(false)

  // Check if user is prepaid tier with no credits
  const isPrepaidNoCredits = userProfile?.subscription_tier === 'prepaid' &&
                             userProfile?.can_activate_bots &&
                             !userProfile?.has_available_credits

  const isLiveTrading = selectedBot.trading_mode === 'symphony' || selectedBot.trading_mode === 'aster' || selectedBot.trading_mode === 'hyperliquid'
  // Hyperliquid single-bot model uses real account equity (like paper), not cumulative P&L
  const usePnlOnlyKPIs = selectedBot.trading_mode === 'symphony' || selectedBot.trading_mode === 'aster'
  const isRegisteredForArena = selectedBot.is_public_performance === true
  const isPaperTrading = selectedBot.trading_mode === 'paper' || !selectedBot.trading_mode

  // Check if bot was paused due to credit exhaustion (set by UsageMonitor)
  const isPausedForCredits = selectedBot.state === 'inactive' &&
                             selectedBot.pause_reason === 'prepaid_credits_exhausted'

  // Fetch config usage for cost display
  const [configUsage, setConfigUsage] = useState<{
    period_usage_usd: number
    today_usage_usd: number
    total_usage_usd: number
  } | null>(null)

  useEffect(() => {
    // Skip optimistic placeholder bots (temp IDs from duplication)
    if (selectedBot.config_id.startsWith('temp-')) return

    const fetchConfigUsage = async () => {
      try {
        const usage = await apiClient.getConfigUsage(selectedBot.config_id)
        setConfigUsage({
          period_usage_usd: usage.period_usage_usd,
          today_usage_usd: usage.today_usage_usd,
          total_usage_usd: usage.total_usage_usd
        })
      } catch (err) {
        // Non-critical - just don't show usage if it fails
        console.debug('Could not fetch config usage:', err)
      }
    }

    fetchConfigUsage()
    // Refresh every 5 minutes while component is mounted
    const interval = setInterval(fetchConfigUsage, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [selectedBot.config_id])

  // Calculate daily cost display: actual avg when usage exists, estimate when not
  const getDailyCostDisplay = (): { text: string; title: string } | null => {
    // Try actual usage first
    if (configUsage && configUsage.period_usage_usd > 0) {
      const dayOfMonth = new Date().getDate()

      if (dayOfMonth === 1) {
        return configUsage.today_usage_usd > 0
          ? { text: `$${configUsage.today_usage_usd.toFixed(2)} today`, title: 'LLM cost today' }
          : null
      } else {
        const avgDaily = configUsage.period_usage_usd / dayOfMonth
        return avgDaily > 0.001
          ? { text: `~$${avgDaily.toFixed(2)}/day`, title: 'Average daily LLM cost this month' }
          : null
      }
    }

    // No real usage — show estimate from config
    const estimated = estimateDailyCost(selectedBot.config_data)
    if (estimated && estimated > 0.001) {
      return { text: `~$${estimated.toFixed(2)}/day est.`, title: 'Estimated daily LLM cost based on model, tier, and frequency' }
    }

    return null
  }

  const handleActivate = () => {
    if (!hasStrategy) {
      alert('Configure a trading pair and strategy before activating this bot.')
      return
    }
    if (!canAccess('bot_activation')) {
      // Prepaid users with no credits → show Add Credits modal
      // Free users → show Subscribe/Upgrade modal
      if (isPrepaidNoCredits) {
        setAddCreditsOpen(true)
      } else {
        setUpgradeModalOpen(true)
      }
      return
    }

    // Show risk modal for live/aster bots
    if (isLiveTrading) {
      setRiskModalOpen(true)
      return
    }

    // For paper trading, activate immediately
    onStart()
  }

  const handleRiskAccepted = () => {
    setRiskModalOpen(false)
    onStart()
  }

  // Check if user can run: either has premium access OR has free runs remaining
  const freeRunsRemaining = selectedBot.free_runs_remaining ?? 0
  const canRunOnce = canAccess('bot_activation') || freeRunsRemaining > 0

  const hasStrategy = Boolean(selectedBot.config_data?.selected_pair)

  const handleManualTrigger = () => {
    if (!hasStrategy) {
      alert('Configure a trading pair and strategy before running this bot.')
      return
    }
    if (!canRunOnce) {
      // Prepaid users with no credits → show Add Credits modal
      // Free users → show Subscribe/Upgrade modal
      if (isPrepaidNoCredits) {
        setAddCreditsOpen(true)
      } else {
        setUpgradeModalOpen(true)
      }
      return
    }
    onManualTrigger()
  }

  return (
    <>
      <div className="sticky top-[64px] z-30 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        {/* Credit Exhaustion Warning Banner */}
        {isPausedForCredits && (
          <div className="mb-3 flex items-center justify-between gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-500">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <span>
                AI credits depleted — bot paused
                {isLiveTrading && '. Your Hyperliquid trading funds are safe.'}
              </span>
            </div>
            <button
              onClick={() => setAddCreditsOpen(true)}
              className="rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-medium text-black hover:bg-amber-400 whitespace-nowrap"
            >
              Add AI Credits
            </button>
          </div>
        )}

        {/* Row 1: Bot Name + Status + Controls */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 mb-4">
          {/* Left: Profile Image + Bot Name + Status */}
          <div className="flex flex-col items-center lg:items-start gap-1">
            <div className="flex items-center gap-3">
              <BotImageUpload
                configId={selectedBot.config_id}
                currentImageUrl={selectedBot.profile_image_url || null}
                onUploadComplete={(url) => {
                  console.log('Image uploaded:', url)
                }}
              />
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                {selectedBot.config_name || 'Untitled Bot'}
              </h2>
              {isPaperTrading && selectedBot.elo_rating != null && (
                <EloTierBadge elo={selectedBot.elo_rating} size="sm" />
              )}
            </div>
            {/* Status — always rendered so it never adds/removes height */}
            <StatusMessage latestActivity={latestActivity ?? null} isActive={isActive} />
          </div>

          {/* Right: Controls */}
          <div className="flex items-center justify-center lg:justify-end gap-3">
            {/* Countdown & Cost */}
            <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
              {countdown && !isSignalDriven && (
                <div className="flex items-center gap-1 whitespace-nowrap">
                  <Clock className="h-4 w-4 flex-shrink-0" />
                  <span>{countdown}</span>
                </div>
              )}
              {configUsage?.total_usage_usd != null && configUsage.total_usage_usd > 0 && (
                <div className="flex items-center gap-1 whitespace-nowrap" title="Total LLM cost for this bot (all-time)">
                  <Coins className="h-3.5 w-3.5 flex-shrink-0" />
                  <span>${configUsage.total_usage_usd.toFixed(2)} total</span>
                </div>
              )}
              {getDailyCostDisplay() && (
                <div className="flex items-center gap-1 whitespace-nowrap" title={getDailyCostDisplay()!.title}>
                  <Coins className="h-3.5 w-3.5 flex-shrink-0" />
                  <span>{getDailyCostDisplay()!.text}</span>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              {/* Degen Arena (DGClaw) */}
              <button
                onClick={() => setDegenArenaOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-[var(--accent)]/50 px-3 py-1.5 text-sm hover:bg-[var(--accent)]/10 text-[var(--accent)] transition-colors"
              >
                <Trophy className="h-4 w-4" />
                <span>Degen Arena</span>
              </button>

              {/* Enter Arena Button — disabled during training, re-enable when S2 registration API is ready (Phase B) */}
              {false && isPaperTrading && (
                isRegisteredForArena ? (
                  <div className="inline-flex items-center gap-1.5 rounded-xl border border-green-500/30 bg-green-500/10 px-3 py-1.5 text-sm text-green-500">
                    <CheckCircle className="h-4 w-4" />
                    <span>In Arena</span>
                  </div>
                ) : (
                  <button
                    onClick={() => setArenaModalOpen(true)}
                    disabled={!isActive}
                    className="inline-flex items-center gap-2 rounded-xl border border-[var(--accent)]/50 px-3 py-1.5 text-sm hover:bg-[var(--accent)]/10 text-[var(--accent)] disabled:opacity-50 disabled:cursor-not-allowed"
                    title={!isActive ? 'Activate your bot first to enter the Arena' : 'Register for ggArena Season 2'}
                  >
                    <Trophy className="h-4 w-4" />
                    <span>Enter Arena</span>
                  </button>
                )
              )}

              <button
                onClick={handleManualTrigger}
                disabled={isManualTriggering || isStarting || isStopping || !canRunOnce || dojoLocked}
                className={`inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-primary)] disabled:cursor-not-allowed ${
                  !canRunOnce || dojoLocked
                    ? 'opacity-50'
                    : 'hover:bg-[var(--bg-tertiary)] disabled:opacity-50'
                }`}
                title={dojoLocked ? 'Locked for Dojo match' : !canRunOnce ? 'No free test runs remaining. Subscribe to run your bot.' : undefined}
              >
                {!canAccess('bot_activation') && freeRunsRemaining === 0 ? (
                  <Crown className="h-4 w-4" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                {isManualTriggering ? 'Triggering...' : (
                  <>
                    Run once
                    {!canAccess('bot_activation') && freeRunsRemaining > 0 && (
                      <span className="text-xs text-[var(--text-muted)]">({freeRunsRemaining} free)</span>
                    )}
                  </>
                )}
              </button>

              <button
                onClick={isActive ? onStop : handleActivate}
                disabled={isStarting || isStopping || (isActive && dojoLocked)}
                title={isActive && dojoLocked ? 'Locked for Dojo match — forfeit to unlock' : undefined}
                className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-sm font-medium shadow-sm ring-1 ring-inset transition ${
                  isActive
                    ? 'bg-rose-600/90 hover:bg-rose-700 ring-rose-500 text-white'
                    : 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] ring-[var(--accent)] text-[#edebe7] dark:text-[#1a1816]'
                } disabled:opacity-50`}
              >
                {isActive ? (
                  <>
                    <PauseCircle className="h-4 w-4" />
                    {isStopping ? 'Deactivating...' : 'Deactivate'}
                  </>
                ) : (
                  <>
                    {!canAccess('bot_activation') ? (
                      <Crown className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    {isStarting ? 'Activating...' : 'Activate'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Row 2: KPI Metrics — always render grid, show placeholder dashes pre-SSE */}
        {usePnlOnlyKPIs ? (
          <>
            <div className="grid grid-cols-3 gap-3 mb-2">
              <KPICard
                label="Cumulative P&L"
                value={metrics ? `${metrics.totalEquity >= 0 ? '+' : ''}$${Math.round(metrics.totalEquity).toLocaleString()}` : '—'}
                positive={metrics ? metrics.totalEquity >= 0 : undefined}
              />
              <KPICard
                label="Unrealized"
                value={metrics ? `${metrics.pnl >= 0 ? '+' : ''}$${Math.round(metrics.pnl).toLocaleString()}` : '—'}
                positive={metrics ? metrics.pnl >= 0 : undefined}
              />
              <KPICard label="Trades" value={metrics ? String(metrics.trades) : '—'} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <KPICard label="Win Rate" value={metrics ? `${Math.round(metrics.winRate)}%` : '—'} />
              <KPICard
                label="Perf"
                value={metrics ? `${metrics.performance.toFixed(2)}%` : '—'}
                positive={metrics ? metrics.performance >= 0 : undefined}
              />
            </div>
          </>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-3 mb-2">
              <KPICard label="Total Equity" value={metrics ? `$${Math.round(metrics.totalEquity).toLocaleString()}` : '—'} />
              <KPICard label="Available" value={metrics ? `$${Math.round(metrics.availableBalance).toLocaleString()}` : '—'} />
              <KPICard
                label="Unrealized"
                value={metrics ? `${metrics.pnl >= 0 ? '+' : ''}$${Math.round(metrics.pnl).toLocaleString()}` : '—'}
                positive={metrics ? metrics.pnl >= 0 : undefined}
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <KPICard label="Trades" value={metrics ? String(metrics.trades) : '—'} />
              <KPICard label="Win Rate" value={metrics ? `${Math.round(metrics.winRate)}%` : '—'} />
              <KPICard
                label="Perf"
                value={metrics ? `${metrics.performance.toFixed(2)}%` : '—'}
                positive={metrics ? metrics.performance >= 0 : undefined}
              />
            </div>
          </>
        )}
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
        botConfig={selectedBot}
      />

      {/* Add Credits Modal - for prepaid users with no credits */}
      <AddCreditsModal
        open={addCreditsOpen}
        onOpenChange={setAddCreditsOpen}
        currentBalance={userProfile?.credit_balance_usd ?? undefined}
      />

      {/* Risk Acknowledgment Modal */}
      <RiskAcknowledgmentModal
        isOpen={riskModalOpen}
        onClose={() => setRiskModalOpen(false)}
        onAccept={handleRiskAccepted}
        tradingMode={selectedBot.trading_mode || 'paper'}
        botName={selectedBot.config_name || 'Untitled Bot'}
      />

      {/* Arena Registration Modal */}
      <ArenaRegistrationModal
        isOpen={arenaModalOpen}
        onClose={() => setArenaModalOpen(false)}
        configId={selectedBot.config_id}
        configName={selectedBot.config_name || 'Untitled Bot'}
        onSuccess={() => {
          // Trigger a refresh - the SSE will pick up the change
          window.location.reload()
        }}
        isBotActive={isActive}
        onActivateBot={onStart}
        isActivating={isStarting}
      />

      {/* Degen Arena (DGClaw) Modal */}
      <DegenArenaModal
        isOpen={degenArenaOpen}
        onClose={() => setDegenArenaOpen(false)}
        configId={selectedBot.config_id}
        configName={selectedBot.config_name || 'Untitled Bot'}
        isBotActive={isActive}
        onActivateBot={onStart}
        isActivating={isStarting}
      />
    </>
  )
}

interface KPICardProps {
  label: string
  value: string
  positive?: boolean
}

function KPICard({ label, value, positive }: KPICardProps) {
  return (
    <div className="border rounded-lg px-3 py-2 border-[var(--border)] overflow-hidden">
      <div className="text-[10px] uppercase tracking-[0.18em] text-[var(--text-muted)] truncate">
        {label}
      </div>
      <div className={`text-lg sm:text-xl leading-snug font-mono tabular-nums truncate ${
        positive !== undefined
          ? positive
            ? 'text-green-500'
            : 'text-red-500'
          : 'text-[var(--text-primary)]'
      }`}>
        {value}
      </div>
    </div>
  )
}


interface StatusMessageProps {
  latestActivity: Activity | null
  isActive: boolean
}

// Format time ago with appropriate units (seconds, minutes, hours, days)
function formatTimeAgo(diffMs: number): string {
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffDays > 0) {
    return `${diffDays}d ago`
  } else if (diffHours > 0) {
    return `${diffHours}h ago`
  } else if (diffMins > 0) {
    return `${diffMins}m ago`
  } else {
    return `${diffSecs}s ago`
  }
}

function StatusMessage({ latestActivity, isActive }: StatusMessageProps) {
  const spinnerChars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
  const [spinnerIndex, setSpinnerIndex] = React.useState(0)
  const [variantIndex, setVariantIndex] = React.useState(0)
  const [displayMessage, setDisplayMessage] = React.useState('')

  // Generate activity-based status messages with variants
  React.useEffect(() => {
    if (!latestActivity) {
      setDisplayMessage(isActive ? 'Waiting for first activity...' : 'No activity yet')
      return
    }

    const generateMessage = () => {
      const activity = latestActivity
      const details = activity.data?.details || {}
      const activityTime = new Date(activity.timestamp)
      const now = new Date()
      const diffMs = now.getTime() - activityTime.getTime()
      const timeAgo = formatTimeAgo(diffMs)

      // If bot is inactive, show static "last activity" message
      if (!isActive) {
        setDisplayMessage(`Last activity ${timeAgo}`)
        return
      }

      let variants: string[] = []

      switch (activity.type) {
        case 'trade_entry':
          const side = (details.side as string | undefined)?.toUpperCase() || 'POSITION'
          const symbol = (details.symbol as string | undefined) || (activity.data?.symbol as string | undefined) || 'Unknown'
          const entryPrice = details.entry_price ? `@ $${Math.round(details.entry_price as number).toLocaleString()}` : ''
          const leverage = details.leverage ? `${details.leverage}x` : ''
          const confidence = details.confidence ? `${Math.round((details.confidence as number) * 100)}%` : ''
          variants = [
            `${side === 'LONG' ? '↑' : '↓'} ${side} ${symbol} ${entryPrice} • ${timeAgo}`,
            `${side === 'LONG' ? '↑' : '↓'} Position opened ${leverage ? `• ${leverage} leverage` : ''} • ${timeAgo}`,
            `${side === 'LONG' ? '↑' : '↓'} Entry: ${entryPrice} ${confidence ? `(${confidence} confidence)` : ''} • ${timeAgo}`
          ]
          break

        case 'trade_exit':
          const exitSymbol = (details.symbol as string | undefined) || (activity.data?.symbol as string | undefined) || 'Position'
          const pnl = (details.pnl as number | undefined) || (details.realized_pnl as number | undefined)
          const pnlStr = pnl ? `${pnl >= 0 ? '+' : ''}$${Math.round(pnl).toLocaleString()}` : ''
          const reason = (details.close_reason as string | undefined) || (details.reason as string | undefined) || ''
          variants = [
            `⨯ CLOSED ${exitSymbol} ${pnlStr ? `• ${pnlStr}` : ''} • ${timeAgo}`,
            `⨯ Position closed${reason ? ` (${reason})` : ''} • ${timeAgo}`,
            `⨯ Exit ${pnlStr ? `• ${pnlStr}` : ''} • ${timeAgo}`
          ]
          break

        case 'market_query':
          const querySymbol = (details.symbol as string | undefined) || (activity.data?.symbol as string | undefined) || 'Market'
          const categories = (details.categories as unknown[] | undefined)?.length || 0
          const timeframe = (details.timeframe as string | undefined) || ''
          variants = [
            `📊 QUERIED ${querySymbol} • ${categories} indicators • ${timeAgo}`,
            `📊 Market data fetched${timeframe ? ` (${timeframe})` : ''} • ${timeAgo}`,
            `📊 Analyzed ${querySymbol} • ${timeAgo}`
          ]
          break

        case 'llm_thought':
          const action = (details.action as string | undefined) || (details.decision as string | undefined) || 'Wait'
          const thoughtConf = details.confidence ? `${Math.round((details.confidence as number) * 100)}%` : ''
          const reasoning = (details.reasoning as string | undefined) || (details.thought as string | undefined) || ''
          const reasoningSnippet = reasoning.length > 30 ? reasoning.substring(0, 30) + '...' : reasoning
          variants = [
            `💭 ANALYZED • ${action}${thoughtConf ? ` (${thoughtConf})` : ''} • ${timeAgo}`,
            `💭 AI decision complete • ${timeAgo}`,
            `💭 Reasoning: ${reasoningSnippet} • ${timeAgo}`
          ]
          break

        case 'agent_wait':
          if (details.next_check_at) {
            const nextCheck = new Date(String(details.next_check_at))
            const remainingMs = nextCheck.getTime() - now.getTime()
            if (remainingMs > 0) {
              const mins = Math.floor(remainingMs / 60000)
              const secs = Math.floor((remainingMs % 60000) / 1000)
              const countdown = `${mins}m ${secs}s`
              variants = [
                `⏸ WAITING • Next check in ${countdown}`,
                `⏸ Agent paused • Resume in ${countdown}`,
                `⏸ Monitoring... Next check in ${countdown}`
              ]
            } else {
              variants = [`⏸ WAITING • Resuming soon...`]
            }
          } else {
            const duration = (details.wait_duration_minutes as string | number | undefined) || ''
            variants = [
              `⏸ WAITING${duration ? ` (${duration}m)` : ''} • ${timeAgo}`,
              `⏸ Agent paused • ${timeAgo}`,
              `⏸ Monitoring... • ${timeAgo}`
            ]
          }
          break

        case 'price_check':
          const priceSymbol = (details.symbol as string | undefined) || (activity.data?.symbol as string | undefined) || 'Asset'
          const price = details.price ? `$${Math.round(details.price as number).toLocaleString()}` : ''
          variants = [
            `💱 PRICE CHECK • ${priceSymbol}: ${price} • ${timeAgo}`,
            `💱 Current price fetched • ${timeAgo}`,
            `💱 ${priceSymbol} @ ${price} • ${timeAgo}`
          ]
          break

        case 'observation_recorded':
          const observation = (details.observation as string | undefined) || (details.text as string | undefined) || ''
          const obsSnippet = observation.length > 35 ? observation.substring(0, 35) + '...' : observation
          variants = [
            `📝 REFLECTION RECORDED • Post-trade • ${timeAgo}`,
            `📝 Agent learning logged • ${timeAgo}`,
            `📝 Observation: ${obsSnippet} • ${timeAgo}`
          ]
          break

        case 'strategy_updated':
          const changes = (details.changes as string | undefined) || (details.updates as string | undefined) || 'Config modified'
          const changesSnippet = typeof changes === 'string' && changes.length > 25 ? changes.substring(0, 25) + '...' : changes
          variants = [
            `⚙️ STRATEGY UPDATED • ${changesSnippet} • ${timeAgo}`,
            `⚙️ Config modified by agent • ${timeAgo}`,
            `⚙️ Changes: ${changesSnippet} • ${timeAgo}`
          ]
          break

        case 'signal_received':
          const source = (details.source as string | undefined) || 'External'
          const signalSymbol = (details.symbol as string | undefined) || (activity.data?.symbol as string | undefined) || ''
          const signalType = (details.signal_type as string | undefined) || (details.side as string | undefined) || ''
          variants = [
            `📡 SIGNAL • ${source}: ${signalSymbol} ${signalType} • ${timeAgo}`,
            `📡 External signal received • ${timeAgo}`,
            `📡 ${source} → ${signalType} ${signalSymbol} • ${timeAgo}`
          ]
          break

        case 'bot_created':
          const botName = (details.config_name as string | undefined) || 'Bot'
          const tradingMode = (details.trading_mode as string | undefined)?.toUpperCase() || 'PAPER'
          const pair = (details.selected_pair as string | undefined) || ''
          variants = [
            `🤖 BOT CREATED • ${tradingMode} mode • ${timeAgo}`,
            `🤖 ${botName} initialized • ${timeAgo}`,
            `🤖 Ready to trade${pair ? ` ${pair}` : ''} • ${timeAgo}`
          ]
          break

        default:
          variants = [activity.data?.summary || `Activity • ${timeAgo}`]
      }

      setDisplayMessage(variants[variantIndex % variants.length])
    }

    generateMessage()
    // Update time every second
    const interval = setInterval(generateMessage, 1000)
    return () => clearInterval(interval)
  }, [latestActivity, variantIndex, isActive])

  // Cycle through variants every 4 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      setVariantIndex(prev => prev + 1)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  // Braille spinner animation - always active
  React.useEffect(() => {
    const interval = setInterval(() => {
      setSpinnerIndex((prev) => (prev + 1) % spinnerChars.length)
    }, 80)
    return () => clearInterval(interval)
  }, [spinnerChars.length])

  return (
    <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
      {isActive ? (
        <span className="font-mono text-[var(--agent-extraction)] flex-shrink-0">
          {spinnerChars[spinnerIndex]}
        </span>
      ) : (
        <span className="text-[var(--text-muted)] flex-shrink-0">○</span>
      )}
      <span className="line-clamp-1">{displayMessage}</span>
    </div>
  )
}