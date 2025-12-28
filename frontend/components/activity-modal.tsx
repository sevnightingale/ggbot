'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useCallback, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'

// Activity interface matching tv-timeline.tsx
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
    take_profit_price?: number
  }
}

interface ActivityModalProps {
  isOpen: boolean
  activities: Activity[]
  currentIndex: number
  onClose: () => void
  onNavigate: (index: number) => void
}

// Theme colors (matching tv-timeline)
const VIBE = {
  obsidian: '#0B0B0C',
  carbon: '#141416',
  ivory: '#EDEBE7',
  hair: 'rgba(237,235,231,0.16)',
  brass: '#C1A87D',
  signal: '#3CA6E0',
  ember: '#D74A1F',
}

// Formatting helpers
const formatPrice = (price: number | null | undefined): string => {
  if (price == null) return '—'
  return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatPercent = (value: number | null | undefined): string => {
  if (value == null) return 'N/A'
  return `${(value * 100).toFixed(1)}%`
}

const formatPnL = (value: number | null | undefined): string => {
  if (value == null) return '—'
  const sign = value >= 0 ? '+' : ''
  return `${sign}$${value.toFixed(2)}`
}

// Get activity type info
function getActivityTypeInfo(activity: Activity): { label: string; icon: string; color: string } {
  const isLong = activity.data?.details?.side === 'long'

  switch (activity.type) {
    case 'trade_entry':
      return isLong
        ? { label: 'Long Entry', icon: '↑', color: '#16a34a' }
        : { label: 'Short Entry', icon: '↓', color: '#dc2626' }
    case 'trade_exit':
      const pnl = Number(activity.data?.details?.pnl || 0)
      return pnl >= 0
        ? { label: 'Position Closed', icon: '✓', color: '#16a34a' }
        : { label: 'Position Closed', icon: '✗', color: '#dc2626' }
    case 'market_query':
      return { label: 'Market Query', icon: '📊', color: VIBE.signal }
    case 'llm_thought':
      return { label: 'Decision Analysis', icon: '🧠', color: VIBE.brass }
    case 'agent_wait':
      return { label: 'Agent Waiting', icon: '⏸', color: VIBE.ivory }
    case 'price_check':
      return { label: 'Price Check', icon: '💱', color: VIBE.signal }
    case 'observation_recorded':
      return { label: 'Observation', icon: '📝', color: VIBE.brass }
    case 'strategy_updated':
      return { label: 'Strategy Update', icon: '⚙️', color: VIBE.signal }
    case 'signal_received':
      return { label: 'Signal Received', icon: '📡', color: VIBE.signal }
    case 'bot_created':
      return { label: 'Bot Created', icon: '🤖', color: '#16a34a' }
    default:
      return { label: activity.type, icon: '●', color: VIBE.brass }
  }
}

// Individual activity type formatters
function TradeEntryContent({ activity }: { activity: Activity }) {
  const details = activity.data.details || {}
  const isLong = details.side === 'long'
  const symbol = details.symbol || activity.data.symbol || 'N/A'

  return (
    <div className="space-y-4">
      {/* Symbol and Side hero */}
      <div className="text-center p-3 rounded-lg" style={{ backgroundColor: isLong ? 'rgba(22, 163, 74, 0.15)' : 'rgba(220, 38, 38, 0.15)' }}>
        <div className="text-2xl font-bold" style={{ color: isLong ? '#16a34a' : '#dc2626' }}>
          {isLong ? '↑ LONG' : '↓ SHORT'}
        </div>
        <div className="text-sm mt-1" style={{ color: VIBE.signal }}>{String(symbol)}</div>
      </div>

      {/* Main trade info card */}
      <div className="grid grid-cols-2 gap-3">
        <InfoCard label="Entry Price" value={formatPrice(Number(details.entry_price))} />
        <InfoCard label="Position Size" value={formatPrice(Number(details.size_usd))} />
        <InfoCard label="Leverage" value={`${details.leverage || 1}x`} />
        {details.margin_used != null && (
          <InfoCard label="Margin" value={formatPrice(Number(details.margin_used))} />
        )}
      </div>

      {/* Confidence bar */}
      {details.confidence != null && (
        <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(237,235,231,0.05)' }}>
          <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
            Confidence
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-black bg-opacity-30 rounded-full h-2 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${(Number(details.confidence) || 0) * 100}%`,
                  backgroundColor: VIBE.signal
                }}
              />
            </div>
            <span className="text-sm font-semibold" style={{ color: VIBE.signal }}>
              {formatPercent(Number(details.confidence))}
            </span>
          </div>
        </div>
      )}

      {/* Risk levels - check both naming conventions */}
      <div className="grid grid-cols-2 gap-3">
        {(details.stop_loss != null || details.stop_loss_price != null) && (
          <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(220, 38, 38, 0.1)' }}>
            <div className="text-xs uppercase tracking-wider mb-1" style={{ color: VIBE.ember }}>
              Stop Loss
            </div>
            <div className="font-mono" style={{ color: VIBE.ember }}>
              {formatPrice(Number(details.stop_loss || details.stop_loss_price))}
            </div>
          </div>
        )}
        {(details.take_profit != null || details.take_profit_price != null) && (
          <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(60, 166, 224, 0.1)' }}>
            <div className="text-xs uppercase tracking-wider mb-1" style={{ color: VIBE.signal }}>
              Take Profit
            </div>
            <div className="font-mono" style={{ color: VIBE.signal }}>
              {formatPrice(Number(details.take_profit || details.take_profit_price))}
            </div>
          </div>
        )}
      </div>

      {/* Liquidation price if available */}
      {details.liquidation_price != null && (
        <div className="text-sm text-center" style={{ color: VIBE.ember }}>
          Liquidation: {formatPrice(Number(details.liquidation_price))}
        </div>
      )}
    </div>
  )
}

function TradeExitContent({ activity }: { activity: Activity }) {
  const details = activity.data.details || {}
  const pnl = Number(details.pnl || 0)
  const isProfit = pnl >= 0
  const isLong = details.side === 'long'
  const symbol = details.symbol || activity.data.symbol || 'N/A'

  // Format duration nicely
  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours}h ${mins}m`
    return `${mins}m`
  }

  return (
    <div className="space-y-4">
      {/* Symbol and result header */}
      <div className="text-center">
        <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
          {isLong ? 'LONG' : 'SHORT'} {String(symbol)}
        </div>
      </div>

      {/* P&L Hero */}
      <div className="p-4 rounded-lg text-center" style={{ backgroundColor: isProfit ? 'rgba(22, 163, 74, 0.15)' : 'rgba(220, 38, 38, 0.15)' }}>
        <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
          Realized P&L
        </div>
        <div className="text-3xl font-bold" style={{ color: isProfit ? '#16a34a' : '#dc2626' }}>
          {formatPnL(pnl)}
        </div>
        {details.pnl_pct != null && (
          <div className="text-sm mt-1" style={{ color: isProfit ? '#16a34a' : '#dc2626' }}>
            ({Number(details.pnl_pct).toFixed(2)}%)
          </div>
        )}
      </div>

      {/* Trade details */}
      <div className="grid grid-cols-2 gap-3">
        <InfoCard label="Entry" value={formatPrice(Number(details.entry_price))} />
        <InfoCard label="Exit" value={formatPrice(Number(details.exit_price))} />
        {details.size_usd != null && (
          <InfoCard label="Size" value={formatPrice(Number(details.size_usd))} />
        )}
        {details.leverage != null && (
          <InfoCard label="Leverage" value={`${details.leverage}x`} />
        )}
      </div>

      {/* Duration and close reason */}
      <div className="grid grid-cols-2 gap-3">
        {details.duration_seconds != null && (
          <InfoCard
            label="Duration"
            value={formatDuration(Number(details.duration_seconds))}
          />
        )}
        {details.close_reason != null && (
          <InfoCard label="Close Reason" value={String(details.close_reason).replace(/_/g, ' ')} />
        )}
      </div>

      {/* Fees */}
      {details.total_fees != null && (
        <div className="text-sm text-center" style={{ color: 'rgba(237,235,231,0.5)' }}>
          Fees: -${Number(details.total_fees).toFixed(2)}
        </div>
      )}
    </div>
  )
}

function LLMThoughtContent({ activity }: { activity: Activity }) {
  const details = activity.data.details || {}
  const thought = String(details.thought || details.reasoning || '')
  const action = String(details.action || 'wait').toUpperCase()
  const confidence = Number(details.confidence || 0)

  // Try to parse structured sections from thought (using [\s\S] instead of . for cross-browser compat)
  const keySignal = thought.match(/KEY[_\s]?SIGNAL:?\s*([\s\S]+?)(?=SUPPORTING|RISK|SUMMARY|$)/i)?.[1]?.trim()
  const supporting = thought.match(/SUPPORTING:?\s*([\s\S]+?)(?=RISK|SUMMARY|$)/i)?.[1]?.trim()
  const risk = thought.match(/RISK:?\s*([\s\S]+?)(?=SUMMARY|$)/i)?.[1]?.trim()
  const summary = thought.match(/SUMMARY:?\s*([\s\S]+?)$/i)?.[1]?.trim()

  const isStructured = keySignal || supporting || risk || summary

  return (
    <div className="space-y-4">
      {/* Action and Confidence */}
      <div className="flex items-center gap-4">
        <div className="px-4 py-2 rounded-lg font-bold" style={{
          backgroundColor: action === 'LONG' ? 'rgba(22, 163, 74, 0.2)' :
                          action === 'SHORT' ? 'rgba(220, 38, 38, 0.2)' :
                          'rgba(237,235,231,0.1)',
          color: action === 'LONG' ? '#16a34a' :
                 action === 'SHORT' ? '#dc2626' :
                 VIBE.ivory
        }}>
          {action}
        </div>
        <div className="flex-1">
          <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
            Confidence
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-black bg-opacity-30 rounded-full h-2 overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${confidence * 100}%`, backgroundColor: VIBE.brass }}
              />
            </div>
            <span className="text-sm font-semibold">{formatPercent(confidence)}</span>
          </div>
        </div>
      </div>

      {/* Structured or raw reasoning */}
      {isStructured ? (
        <div className="space-y-3">
          {keySignal != null && (
            <ReasoningSection title="Key Signal" content={keySignal} color={VIBE.signal} />
          )}
          {supporting != null && (
            <ReasoningSection title="Supporting" content={supporting} color={VIBE.brass} />
          )}
          {risk != null && (
            <ReasoningSection title="Risk" content={risk} color={VIBE.ember} />
          )}
          {summary != null && (
            <ReasoningSection title="Summary" content={summary} color={VIBE.ivory} />
          )}
        </div>
      ) : (
        <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(237,235,231,0.05)' }}>
          <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
            Reasoning
          </div>
          <div className="prose prose-invert prose-sm max-w-none text-sm" style={{ color: VIBE.ivory }}>
            <ReactMarkdown>{thought.slice(0, 800) + (thought.length > 800 ? '...' : '')}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Symbol if present */}
      {details.symbol != null && (
        <div className="text-center text-sm" style={{ color: VIBE.signal }}>
          {String(details.symbol)}
        </div>
      )}
    </div>
  )
}

function MarketQueryContent({ activity }: { activity: Activity }) {
  const details = activity.data.details || {}
  const metadata = (details.metadata || {}) as Record<string, unknown>
  const formattedData = (details.formatted_data || {}) as Record<string, string>

  return (
    <div className="space-y-4">
      {/* Query summary */}
      <div className="grid grid-cols-2 gap-3">
        {details.current_price != null && (
          <InfoCard label="Price at Query" value={formatPrice(Number(details.current_price))} color={VIBE.signal} />
        )}
        {details.query_mode != null && (
          <InfoCard label="Mode" value={String(details.query_mode).replace(/_/g, ' ')} />
        )}
        {metadata.timeframes_analyzed != null && (
          <InfoCard label="Timeframes" value={String((metadata.timeframes_analyzed as string[]).length)} />
        )}
        {metadata.indicators_count != null && (
          <InfoCard label="Indicators" value={String(metadata.indicators_count)} />
        )}
      </div>

      {/* Data age */}
      {details.data_age_seconds != null && (
        <div className="text-sm text-center" style={{ color: 'rgba(237,235,231,0.5)' }}>
          Data age: {Number(details.data_age_seconds).toFixed(1)}s
        </div>
      )}

      {/* Collapsible data sections */}
      {Object.keys(formattedData).length > 0 && (
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-wider" style={{ color: 'rgba(237,235,231,0.6)' }}>
            Data Sent to LLM
          </div>
          {Object.entries(formattedData).map(([key, value]) => (
            <details key={key} className="rounded-lg border" style={{ borderColor: VIBE.hair }}>
              <summary className="cursor-pointer px-3 py-2 text-sm font-medium" style={{ color: VIBE.brass }}>
                {key.replace(/_/g, ' ').toUpperCase()}
              </summary>
              <div className="px-3 pb-3 max-h-48 overflow-y-auto">
                <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: 'rgba(237,235,231,0.8)' }}>
                  {String(value).slice(0, 2000)}
                </pre>
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  )
}

function GenericActivityContent({ activity }: { activity: Activity }) {
  const details = activity.data.details || {}

  return (
    <div className="space-y-4">
      {/* Summary */}
      {activity.data.summary != null && (
        <div className="prose prose-invert prose-sm max-w-none" style={{ color: VIBE.ivory }}>
          <ReactMarkdown>{String(activity.data.summary)}</ReactMarkdown>
        </div>
      )}

      {/* Raw details if any */}
      {Object.keys(details).length > 0 && (
        <details className="rounded-lg border" style={{ borderColor: VIBE.hair }}>
          <summary className="cursor-pointer px-3 py-2 text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
            View Details
          </summary>
          <div className="px-3 pb-3">
            <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: 'rgba(237,235,231,0.6)' }}>
              {JSON.stringify(details, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </div>
  )
}

// Helper components
function InfoCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(237,235,231,0.05)' }}>
      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
        {label}
      </div>
      <div className="font-semibold" style={{ color: color || VIBE.ivory }}>
        {value}
      </div>
    </div>
  )
}

function ReasoningSection({ title, content, color }: { title: string; content: string; color: string }) {
  return (
    <div className="p-3 rounded-lg" style={{ backgroundColor: `${color}15` }}>
      <div className="text-xs uppercase tracking-wider mb-1 font-semibold" style={{ color }}>
        {title}
      </div>
      <div className="text-sm" style={{ color: VIBE.ivory }}>
        {content}
      </div>
    </div>
  )
}

export default function ActivityModal({
  isOpen,
  activities,
  currentIndex,
  onClose,
  onNavigate
}: ActivityModalProps) {
  const activity = activities[currentIndex]
  const canGoPrev = currentIndex > 0
  const canGoNext = currentIndex < activities.length - 1

  // Touch swipe state
  const touchStartX = useRef<number | null>(null)
  const touchEndX = useRef<number | null>(null)
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null)

  // Minimum swipe distance to trigger navigation
  const minSwipeDistance = 50

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchEndX.current = null
    touchStartX.current = e.targetTouches[0].clientX
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    touchEndX.current = e.targetTouches[0].clientX

    // Preview swipe direction for visual feedback
    if (touchStartX.current !== null && touchEndX.current !== null) {
      const diff = touchStartX.current - touchEndX.current
      if (Math.abs(diff) > 20) {
        setSwipeDirection(diff > 0 ? 'left' : 'right')
      }
    }
  }, [])

  const handleTouchEnd = useCallback(() => {
    setSwipeDirection(null)

    if (touchStartX.current === null || touchEndX.current === null) return

    const distance = touchStartX.current - touchEndX.current
    const isLeftSwipe = distance > minSwipeDistance
    const isRightSwipe = distance < -minSwipeDistance

    if (isLeftSwipe && canGoNext) {
      onNavigate(currentIndex + 1)
    } else if (isRightSwipe && canGoPrev) {
      onNavigate(currentIndex - 1)
    }

    touchStartX.current = null
    touchEndX.current = null
  }, [canGoPrev, canGoNext, currentIndex, onNavigate])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case 'Escape':
        onClose()
        break
      case 'ArrowLeft':
        if (canGoPrev) onNavigate(currentIndex - 1)
        break
      case 'ArrowRight':
        if (canGoNext) onNavigate(currentIndex + 1)
        break
    }
  }, [isOpen, canGoPrev, canGoNext, currentIndex, onClose, onNavigate])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!activity) return null

  const typeInfo = getActivityTypeInfo(activity)

  // Render content based on activity type
  const renderContent = () => {
    switch (activity.type) {
      case 'trade_entry':
        return <TradeEntryContent activity={activity} />
      case 'trade_exit':
        return <TradeExitContent activity={activity} />
      case 'llm_thought':
        return <LLMThoughtContent activity={activity} />
      case 'market_query':
        return <MarketQueryContent activity={activity} />
      default:
        return <GenericActivityContent activity={activity} />
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal - Fixed position, centered, with proper height constraints */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1, x: swipeDirection === 'left' ? -10 : swipeDirection === 'right' ? 10 : 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed z-50 flex flex-col rounded-xl border-2 overflow-hidden"
            style={{
              backgroundColor: VIBE.carbon,
              borderColor: VIBE.brass,
              // Mobile: full width with margins
              // Desktop: centered fixed size
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 'min(calc(100vw - 32px), 500px)',
              maxHeight: 'min(calc(100vh - 64px), 700px)',
            }}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
          >
            {/* Header with navigation */}
            <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: VIBE.hair }}>
              {/* Prev button */}
              <button
                onClick={() => canGoPrev && onNavigate(currentIndex - 1)}
                disabled={!canGoPrev}
                className="p-2 rounded-lg transition-colors"
                style={{
                  opacity: canGoPrev ? 1 : 0.3,
                  cursor: canGoPrev ? 'pointer' : 'not-allowed'
                }}
              >
                <ChevronLeft size={20} style={{ color: VIBE.brass }} />
              </button>

              {/* Timestamp and counter */}
              <div className="text-center flex-1">
                <div className="text-sm font-medium" style={{ color: VIBE.ivory }}>
                  {new Date(activity.timestamp).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                </div>
                <div className="text-xs" style={{ color: 'rgba(237,235,231,0.5)' }}>
                  {currentIndex + 1} of {activities.length}
                </div>
              </div>

              {/* Next button */}
              <button
                onClick={() => canGoNext && onNavigate(currentIndex + 1)}
                disabled={!canGoNext}
                className="p-2 rounded-lg transition-colors"
                style={{
                  opacity: canGoNext ? 1 : 0.3,
                  cursor: canGoNext ? 'pointer' : 'not-allowed'
                }}
              >
                <ChevronRight size={20} style={{ color: VIBE.brass }} />
              </button>

              {/* Close button */}
              <button
                onClick={onClose}
                className="p-2 rounded-lg transition-colors hover:bg-white/10 ml-2"
              >
                <X size={20} style={{ color: VIBE.ivory }} />
              </button>
            </div>

            {/* Activity type badge */}
            <div className="px-4 pt-4">
              <div
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold"
                style={{ backgroundColor: `${typeInfo.color}20`, color: typeInfo.color }}
              >
                <span>{typeInfo.icon}</span>
                <span>{typeInfo.label}</span>
              </div>
              {activity.data.symbol && (
                <span className="ml-3 text-sm font-mono" style={{ color: VIBE.signal }}>
                  {activity.data.symbol}
                </span>
              )}
            </div>

            {/* Content - scrollable */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
              {renderContent()}
            </div>

            {/* Footer hint */}
            <div className="px-4 py-2 text-center text-xs border-t" style={{ borderColor: VIBE.hair, color: 'rgba(237,235,231,0.4)' }}>
              <span className="hidden md:inline">Use ← → arrows to navigate • Esc to close</span>
              <span className="md:hidden">Swipe left/right to navigate • Tap outside to close</span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
