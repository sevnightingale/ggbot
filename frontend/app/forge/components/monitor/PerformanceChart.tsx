'use client'

import React, { useState, useEffect } from 'react'
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter, ReferenceLine } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface Trade {
  trade_id: string
  symbol: string
  side: string
  entry_price: number
  size_usd: number
  leverage: number
  realized_pnl: number
  close_reason: string
  opened_at: string | null
  closed_at: string | null
  confidence_score: number | null
  decision_id: string | null
  action: string | null
  decision_confidence: number | null
  reasoning: string | null
}

interface Account {
  config_id: string
  account_id: string
  current_balance: number | null
  total_pnl: number
  total_trades: number
  win_trades: number
  loss_trades: number
  open_positions: number
  updated_at: string
  unrealized_pnl?: number
  current_pnl?: number
  portfolio_return_pct?: number | null
  total_balance?: number
  win_rate?: number
  avg_win?: number
  avg_loss?: number
  largest_win?: number
  largest_loss?: number
  sharpe_ratio?: number
  source?: 'paper' | 'live'
}

interface EquityPoint {
  timestamp: number
  date: string
  balance: number
}

interface TradeMarker extends Trade {
  timestamp: number
  balance: number
}

interface PerformanceChartProps {
  account?: Account | null
  configId: string
  className?: string
}

export function PerformanceChart({ account, configId, className = '' }: PerformanceChartProps) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([])
  const [tradeMarkers, setTradeMarkers] = useState<TradeMarker[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTrade, setSelectedTrade] = useState<TradeMarker | null>(null)

  useEffect(() => {
    if (!configId) return

    const loadData = async () => {
      setLoading(true)
      try {
        const isLive = account?.source === 'live'

        // Load trade history from appropriate endpoint
        let trades: Trade[]
        if (isLive) {
          // Live trading: Get trades from Symphony via /api/v2/trades/live/{config_id}
          const liveData = await apiClient.getLiveTradeHistory(configId, 50)
          // Map live trades to Trade interface (no decision data from Symphony)
          trades = liveData.trades.map(t => ({
            ...t,
            confidence_score: null,
            decision_id: null,
            action: null,
            decision_confidence: null,
            reasoning: null
          }))
        } else {
          // Paper trading: Get trades with decisions from paper endpoint
          const historyData = await apiClient.getTradeHistoryWithDecisions(configId, 50)
          trades = historyData.trades
        }

        setTrades(trades)

        // Calculate equity curve
        // For live trading: Build cumulative P&L from $0 (no balance tracking)
        // For paper trading: Calculate from current balance
        const balance = isLive ? null : (account?.current_balance ?? 10000)
        const { curve, markers } = calculateEquityCurve(trades, balance, isLive)
        setEquityCurve(curve)
        setTradeMarkers(markers)
      } catch (error) {
        console.error('Failed to load trade history:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configId])  // Only reload when config changes, not on every SSE account update (prevents jitter)

  // Calculate equity curve from trades
  const calculateEquityCurve = (trades: Trade[], currentBalance: number | null, isLive: boolean = false) => {
    if (trades.length === 0) {
      return { curve: [], markers: [] }
    }

    // Sort trades by close time (oldest first)
    const sortedTrades = [...trades].sort((a, b) => {
      const timeA = a.closed_at ? new Date(a.closed_at).getTime() : 0
      const timeB = b.closed_at ? new Date(b.closed_at).getTime() : 0
      return timeA - timeB
    })

    // Calculate starting balance
    let startingBalance: number
    if (isLive || currentBalance === null) {
      // Live trading: Start from $0 and show cumulative P&L
      startingBalance = 0
    } else {
      // Paper trading: Work backwards from current balance
      const totalPnL = sortedTrades.reduce((sum, trade) => sum + trade.realized_pnl, 0)
      startingBalance = currentBalance - totalPnL
    }

    const curve: EquityPoint[] = []
    const markers: TradeMarker[] = []
    let runningBalance = startingBalance

    // Add starting point
    const firstTrade = sortedTrades[0]
    if (firstTrade.closed_at) {
      const firstTime = new Date(firstTrade.closed_at).getTime()
      curve.push({
        timestamp: firstTime - 3600000, // 1 hour before first trade
        date: new Date(firstTime - 3600000).toLocaleDateString(),
        balance: startingBalance
      })
    }

    // Add points for each trade
    sortedTrades.forEach((trade) => {
      if (!trade.closed_at) return

      runningBalance += trade.realized_pnl
      const timestamp = new Date(trade.closed_at).getTime()

      curve.push({
        timestamp,
        date: new Date(timestamp).toLocaleDateString(),
        balance: runningBalance
      })

      markers.push({
        ...trade,
        timestamp,
        balance: runningBalance
      })
    })

    return { curve, markers }
  }

  const formatPrice = (value: number) => {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
  }

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Empty state
  if (!loading && trades.length === 0) {
    const isLive = account?.source === 'live'
    return (
      <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Performance Chart</h3>
        <div className="relative" style={{ height: 300 }}>
          <div className="text-center py-16">
            <div className="text-[var(--text-muted)] mb-2">📊 No trading history yet</div>
            <div className="text-sm text-[var(--text-muted)]">
              Your {isLive ? 'cumulative P&L' : 'equity curve'} will appear here after your first trade
            </div>
          </div>
        </div>
        <MetricsStrip
          currentBalance={isLive ? null : (account?.current_balance ?? 10000)}
          portfolioReturnPct={isLive ? null : (account?.portfolio_return_pct ?? 0)}
          totalTrades={0}
          winRate={0}
          isLive={isLive}
        />
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Performance Chart</h3>
        <div className="text-center py-16">
          <div className="text-[var(--text-muted)]">Loading performance data...</div>
        </div>
      </div>
    )
  }

  const isLive = account?.source === 'live'
  const currentBalance = isLive ? null : (account?.current_balance ?? 10000)
  const portfolioReturnPct = isLive ? null : (account?.portfolio_return_pct ?? 0)
  const totalTrades = account?.total_trades ?? 0
  const winRate = account?.win_rate ?? 0
  const startingBalance = equityCurve[0]?.balance ?? (isLive ? 0 : 10000)

  return (
    <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 relative ${className}`}>
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
        {isLive ? 'Cumulative P&L' : 'Performance Chart'}
        <span className="text-xs text-[var(--text-muted)] ml-2 font-normal">(Last {trades.length} Trades)</span>
      </h3>

      {/* Chart */}
      <div className="relative" style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
            <XAxis
              dataKey="timestamp"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={formatDate}
              tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
              stroke="var(--border)"
            />
            <YAxis
              tickFormatter={formatPrice}
              tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
              stroke="var(--border)"
              domain={['auto', 'auto']}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: 'var(--border)', strokeWidth: 1 }}
            />
            <ReferenceLine
              y={startingBalance}
              stroke="var(--text-muted)"
              strokeDasharray="5 5"
              opacity={0.5}
            />
            <Line
              data={equityCurve}
              type="monotone"
              dataKey="balance"
              stroke={(portfolioReturnPct ?? 0) >= 0 ? 'var(--profit-color)' : 'var(--loss-color)'}
              strokeWidth={2}
              dot={false}
              isAnimationActive={true}
            />
            <Scatter
              data={tradeMarkers}
              dataKey="balance"
              fill="var(--profit-color)"
              shape={(props: unknown) => {
                const { cx, cy, payload } = props as { cx?: number; cy?: number; payload?: TradeMarker }
                if (!cx || !cy || !payload) return <></>

                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={6}
                    fill={payload.realized_pnl >= 0 ? 'var(--profit-color)' : 'var(--loss-color)'}
                    className="cursor-pointer hover:opacity-80 transition-opacity"
                    onClick={() => setSelectedTrade(payload)}
                    style={{ cursor: 'pointer' }}
                  />
                )
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Strip Below Chart */}
      <MetricsStrip
        currentBalance={currentBalance}
        portfolioReturnPct={portfolioReturnPct}
        totalTrades={totalTrades}
        winRate={winRate}
        isLive={isLive}
      />

      {/* Trade Detail Popover */}
      {selectedTrade && (
        <TradeDetailPopover trade={selectedTrade} onClose={() => setSelectedTrade(null)} />
      )}
    </div>
  )
}

// Metrics Strip Component
interface MetricsStripProps {
  currentBalance: number | null
  portfolioReturnPct: number | null
  totalTrades: number
  winRate: number
  isLive?: boolean
}

function MetricsStrip({ currentBalance, portfolioReturnPct, totalTrades, winRate, isLive = false }: MetricsStripProps) {
  return (
    <div className="mt-4 flex items-center justify-around border-t border-[var(--border)] pt-4">
      {/* Balance or P&L */}
      <div className="text-center">
        <div className="text-xs text-[var(--text-muted)] mb-1">
          {isLive ? 'Balance' : 'Balance'}
        </div>
        <div className="text-sm font-semibold text-[var(--text-primary)]">
          {currentBalance === null ? (
            <span className="text-[var(--text-muted)]">Track on Symphony</span>
          ) : (
            `$${currentBalance.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="h-8 w-px bg-[var(--border)]" />

      {/* Return */}
      <div className="text-center">
        <div className="text-xs text-[var(--text-muted)] mb-1">Return</div>
        <div className={`text-sm font-semibold flex items-center gap-1 justify-center ${
          portfolioReturnPct === null ? 'text-[var(--text-muted)]' :
          portfolioReturnPct >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
        }`}>
          {portfolioReturnPct === null ? (
            'N/A'
          ) : (
            <>
              {portfolioReturnPct >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {portfolioReturnPct >= 0 ? '+' : ''}{portfolioReturnPct.toFixed(2)}%
            </>
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="h-8 w-px bg-[var(--border)]" />

      {/* Trades */}
      <div className="text-center">
        <div className="text-xs text-[var(--text-muted)] mb-1">Trades</div>
        <div className="text-sm font-semibold text-[var(--text-primary)]">{totalTrades}</div>
      </div>

      {/* Divider */}
      <div className="h-8 w-px bg-[var(--border)]" />

      {/* Win Rate */}
      <div className="text-center">
        <div className="text-xs text-[var(--text-muted)] mb-1">Win Rate</div>
        <div className="text-sm font-semibold text-[var(--text-primary)]">{winRate.toFixed(0)}%</div>
      </div>
    </div>
  )
}

// Custom Tooltip Component
interface TooltipProps {
  active?: boolean
  payload?: Array<{
    payload: EquityPoint
  }>
}

function CustomTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload || !payload[0]) return null

  const data = payload[0].payload
  return (
    <div className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 shadow-lg">
      <div className="text-xs text-[var(--text-muted)]">{data.date}</div>
      <div className="text-sm font-semibold text-[var(--text-primary)]">
        ${data.balance.toLocaleString(undefined, { maximumFractionDigits: 2 })}
      </div>
    </div>
  )
}

// Trade Detail Popover Component
interface TradeDetailPopoverProps {
  trade: TradeMarker
  onClose: () => void
}

function TradeDetailPopover({ trade, onClose }: TradeDetailPopoverProps) {
  const formatPrice = (price: number) => {
    if (price >= 1000) return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
    if (price >= 1) return `$${price.toFixed(4)}`
    return `$${price.toFixed(6)}`
  }

  const formatPnL = (pnl: number) => {
    const sign = pnl >= 0 ? '+' : ''
    return `${sign}$${pnl.toFixed(2)}`
  }

  const formatPercentage = (pnl: number, size: number) => {
    const pct = (pnl / size) * 100
    const sign = pct >= 0 ? '+' : ''
    return `${sign}${pct.toFixed(2)}%`
  }

  const getSideColor = (side: string) => {
    return side.toLowerCase() === 'long' ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Popover */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl shadow-2xl p-4 w-80">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-[var(--text-primary)]">{trade.symbol}</span>
            <span className={`text-sm font-medium ${getSideColor(trade.side)}`}>
              {trade.side.toUpperCase()}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Entry:</span>
            <span className="text-[var(--text-secondary)]">{formatPrice(trade.entry_price)}</span>
          </div>

          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Size:</span>
            <span className="text-[var(--text-secondary)]">${trade.size_usd.toLocaleString()}</span>
          </div>

          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Leverage:</span>
            <span className="text-[var(--text-secondary)]">{trade.leverage}x</span>
          </div>

          <div className="flex justify-between pt-2 border-t border-[var(--border)]">
            <span className="text-[var(--text-muted)]">P&L:</span>
            <div className={`font-semibold ${trade.realized_pnl >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
              {formatPnL(trade.realized_pnl)} ({formatPercentage(trade.realized_pnl, trade.size_usd)})
            </div>
          </div>

          {trade.confidence_score && (
            <div className="flex justify-between">
              <span className="text-[var(--text-muted)]">Confidence:</span>
              <span className="text-[var(--text-secondary)]">{(trade.confidence_score * 100).toFixed(0)}%</span>
            </div>
          )}

          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Reason:</span>
            <span className="text-[var(--text-secondary)] capitalize text-xs">
              {trade.close_reason?.replace(/_/g, ' ') || '—'}
            </span>
          </div>

          <div className="flex justify-between text-xs pt-2 border-t border-[var(--border)]">
            <span className="text-[var(--text-muted)]">Closed:</span>
            <span className="text-[var(--text-muted)]">
              {trade.closed_at ? new Date(trade.closed_at).toLocaleString() : '—'}
            </span>
          </div>
        </div>
      </div>
    </>
  )
}
