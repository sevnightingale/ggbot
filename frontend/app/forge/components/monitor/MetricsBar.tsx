'use client'

import React, { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface Account {
  config_id: string
  account_id: string
  current_balance: number
  total_pnl: number
  total_trades: number
  win_trades: number
  loss_trades: number
  open_positions: number
  updated_at: string
  // Enhanced portfolio analytics from SSE
  unrealized_pnl?: number
  current_pnl?: number  // Aggregate unrealized P&L of open positions
  portfolio_return_pct?: number  // Total P&L as % of initial balance
  total_balance?: number
  win_rate?: number
  avg_win?: number
  avg_loss?: number
  largest_win?: number
  largest_loss?: number
  sharpe_ratio?: number
}

interface MetricsBarProps {
  account?: Account | null
  positions?: Array<{ trade_id: string; symbol: string; side: string }> // For open positions count
  className?: string
  onTotalTradesClick?: () => void
}

export function MetricsBar({ account, className = '', onTotalTradesClick }: MetricsBarProps) {
  // Track SSE updates for slide animations
  const [isAnimating, setIsAnimating] = useState(false)
  const [displayValues, setDisplayValues] = useState<{
    portfolioReturn: string
    currentPnl: string
    winRate: string
    totalTrades: string
  } | null>(null)

  // Trigger slide animation on every SSE update (account prop change)
  useEffect(() => {
    if (!account) return

    // Calculate new values
    const portfolioReturnPct = account.portfolio_return_pct || 0
    const currentPnl = account.current_pnl || 0
    const winRate = account.win_rate || 0
    const totalTrades = account.total_trades || 0

    const newValues = {
      portfolioReturn: `${portfolioReturnPct >= 0 ? '+' : ''}${portfolioReturnPct.toFixed(2)}%`,
      currentPnl: `${currentPnl >= 0 ? '+' : ''}$${Math.abs(currentPnl).toFixed(2)}`,
      winRate: `${winRate.toFixed(0)}%`,
      totalTrades: `${totalTrades} ${totalTrades === 1 ? 'trade' : 'trades'}`
    }

    // Start slide-out animation
    setIsAnimating(true)

    // After slide-out completes, update values and slide-in
    setTimeout(() => {
      setDisplayValues(newValues)
      setIsAnimating(false)
    }, 250)
  }, [account])

  if (!account) {
    return (
      <div className={`grid grid-cols-2 gap-3 ${className}`}>
        {/* Loading skeleton */}
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
            <div className="h-4 bg-[var(--bg-tertiary)] rounded animate-pulse mb-2" />
            <div className="h-6 bg-[var(--bg-tertiary)] rounded animate-pulse mb-1" />
            <div className="h-3 bg-[var(--bg-tertiary)] rounded animate-pulse w-16" />
          </div>
        ))}
      </div>
    )
  }

  // Use current values or fallback to calculated values
  const portfolioReturnPct = account.portfolio_return_pct || 0
  const currentPnl = account.current_pnl || 0
  const winRate = account.win_rate || 0
  const totalTrades = account.total_trades || 0

  const currentValues = displayValues || {
    portfolioReturn: `${portfolioReturnPct >= 0 ? '+' : ''}${portfolioReturnPct.toFixed(2)}%`,
    currentPnl: `${currentPnl >= 0 ? '+' : ''}$${Math.abs(currentPnl).toFixed(2)}`,
    winRate: `${winRate.toFixed(0)}%`,
    totalTrades: `${totalTrades} ${totalTrades === 1 ? 'trade' : 'trades'}`
  }

  return (
    <div className={`grid grid-cols-2 gap-3 ${className}`}>
      {/* KPI 1: Portfolio Return */}
      <KPICard
        label="Portfolio Return"
        value={currentValues.portfolioReturn}
        delta={portfolioReturnPct}
        isPercentage={true}
        isAnimating={isAnimating}
      />

      {/* KPI 2: Current P&L */}
      <KPICard
        label="Current P&L"
        value={currentValues.currentPnl}
        delta={currentPnl}
        isPercentage={false}
        isAnimating={isAnimating}
      />

      {/* KPI 3: Win Rate */}
      <KPICard
        label="Win Rate"
        value={currentValues.winRate}
        delta={null} // No trend indicator for win rate
        isPercentage={false}
        isAnimating={isAnimating}
      />

      {/* KPI 4: Total Trades - Clickable */}
      <KPICard
        label="Total Trades"
        value={currentValues.totalTrades}
        delta={null} // No trend indicator for trade count
        isPercentage={false}
        isAnimating={isAnimating}
        onClick={onTotalTradesClick}
        isClickable={!!onTotalTradesClick}
      />
    </div>
  )
}

interface KPICardProps {
  label: string
  value: string
  delta?: number | null
  isPercentage: boolean
  isAnimating: boolean
  onClick?: () => void
  isClickable?: boolean
}

function KPICard({ label, value, delta, isPercentage, isAnimating, onClick, isClickable = false }: KPICardProps) {
  const hasPositiveDelta = (delta ?? 0) >= 0
  const showTrend = delta !== null && delta !== undefined

  // Determine if this metric should be colored based on value
  const shouldColorValue = label === 'Portfolio Return' || label === 'Daily P&L'
  const isPositive = shouldColorValue && (delta ?? 0) > 0
  const isNegative = shouldColorValue && (delta ?? 0) < 0

  // Color for the main value
  const valueColorClass = shouldColorValue
    ? isPositive
      ? 'text-[var(--profit-color)]'
      : isNegative
        ? 'text-[var(--loss-color)]'
        : 'text-[var(--neutral-color)]'
    : 'text-[var(--text-primary)]'

  return (
    <div
      className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 ${
        isClickable ? 'cursor-pointer hover:bg-[var(--bg-tertiary)] transition-colors' : ''
      }`}
      onClick={onClick}
    >
      <div className="text-xs text-[var(--text-muted)]">{label}</div>
      <div className="relative overflow-hidden h-7 mt-1">
        <div
          className={`text-xl font-semibold tracking-tight transition-all duration-250 ease-in-out ${valueColorClass} ${
            isAnimating
              ? 'transform translate-y-8 opacity-0'
              : 'transform translate-y-0 opacity-100'
          }`}
        >
          {value}
        </div>
      </div>
      {showTrend && (
        <div className={`mt-1 flex items-center text-xs ${
          hasPositiveDelta ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
        }`}>
          {hasPositiveDelta ? (
            <TrendingUp className="mr-1 h-3 w-3" />
          ) : (
            <TrendingDown className="mr-1 h-3 w-3" />
          )}
          {isPercentage
            ? `${Math.abs(delta || 0).toFixed(2)}%`
            : `$${Math.abs(delta || 0).toFixed(2)}`
          }
        </div>
      )}
    </div>
  )
}