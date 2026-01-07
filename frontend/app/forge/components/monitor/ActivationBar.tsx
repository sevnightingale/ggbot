'use client'

import React, { useState } from 'react'
import { Clock, Play, PauseCircle, Zap, Crown } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { RiskAcknowledgmentModal } from '@/components/RiskAcknowledgmentModal'
import { BotImageUpload } from '@/components/BotImageUpload'

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
  const { canAccess } = usePermissions()
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const [riskModalOpen, setRiskModalOpen] = useState(false)

  const isLiveTrading = selectedBot.trading_mode === 'symphony' || selectedBot.trading_mode === 'aster'

  const handleActivate = () => {
    if (!canAccess('bot_activation')) {
      setUpgradeModalOpen(true)
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

  const handleManualTrigger = () => {
    if (!canAccess('bot_activation')) {
      setUpgradeModalOpen(true)
      return
    }
    onManualTrigger()
  }

  return (
    <>
      <div className="sticky top-[64px] z-30 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        {/* Row 1: Bot Name + Status + Controls */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 mb-4">
          {/* Left: Profile Image + Bot Name + Status */}
          <div className="flex flex-col items-center lg:items-start gap-2">
            <div className="flex items-center gap-3">
              <BotImageUpload
                configId={selectedBot.config_id}
                currentImageUrl={selectedBot.profile_image_url || null}
                onUploadComplete={(url) => {
                  // Update parent state if needed - currently handled by SSE refresh
                  console.log('Image uploaded:', url)
                }}
              />
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                {selectedBot.config_name || 'Untitled Bot'}
              </h2>
            </div>
            {/* Status Message - Dynamic when active, static "last activity" when inactive */}
            {latestActivity && (
              <StatusMessage latestActivity={latestActivity} isActive={isActive} />
            )}
          </div>

          {/* Right: Controls */}
          <div className="flex items-center justify-center lg:justify-end gap-3 flex-wrap">
            {/* Countdown */}
            {countdown && !isSignalDriven && (
              <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                <Clock className="h-4 w-4" />
                <span>{countdown}</span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleManualTrigger}
                disabled={isManualTriggering || isStarting || isStopping}
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!canAccess('bot_activation') ? (
                  <Crown className="h-4 w-4" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                {isManualTriggering ? 'Triggering...' : 'Run once'}
              </button>

              <button
                onClick={isActive ? onStop : handleActivate}
                disabled={isStarting || isStopping}
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

        {/* Row 2: KPI Metrics - Only show for Paper Trading */}
        {metrics && selectedBot.trading_mode === 'paper' && (
          <>
            {/* Row 1: Financial Health */}
            <div className="grid grid-cols-3 gap-3 mb-2">
              <KPICard label="Total Equity" value={`$${Math.round(metrics.totalEquity).toLocaleString()}`} />
              <KPICard label="Available" value={`$${Math.round(metrics.availableBalance).toLocaleString()}`} />
              <KPICard
                label="Unrealized"
                value={`${metrics.pnl >= 0 ? '+' : ''}$${Math.round(metrics.pnl).toLocaleString()}`}
                positive={metrics.pnl >= 0}
              />
            </div>

            {/* Row 2: Trading Performance */}
            <div className="grid grid-cols-3 gap-3">
              <KPICard label="Trades" value={String(metrics.trades)} />
              <KPICard label="Win Rate" value={`${Math.round(metrics.winRate)}%`} />
              <KPICard
                label="Perf"
                value={`${metrics.performance.toFixed(2)}%`}
                positive={metrics.performance >= 0}
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

      {/* Risk Acknowledgment Modal */}
      <RiskAcknowledgmentModal
        isOpen={riskModalOpen}
        onClose={() => setRiskModalOpen(false)}
        onAccept={handleRiskAccepted}
        tradingMode={selectedBot.trading_mode || 'paper'}
        botName={selectedBot.config_name || 'Untitled Bot'}
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
    <div className="border rounded-lg px-3 py-2 border-[var(--border)]">
      <div className="text-[10px] uppercase tracking-[0.18em] text-[var(--text-muted)]">
        {label}
      </div>
      <div className={`text-lg sm:text-xl leading-snug ${
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
  latestActivity: Activity
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
        <span className="font-mono text-[var(--agent-extraction)]">
          {spinnerChars[spinnerIndex]}
        </span>
      ) : (
        <span className="text-[var(--text-muted)]">○</span>
      )}
      <span>{displayMessage}</span>
    </div>
  )
}