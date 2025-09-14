'use client'

import React from 'react'
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
  daily_pnl?: number
  portfolio_return_pct?: number
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
}

export function MetricsBar({ account, positions = [], className = '' }: MetricsBarProps) {

  if (!account) {
    return (
      <div className={`grid grid-cols-2 gap-3 md:grid-cols-4 ${className}`}>
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

  // Calculate metrics
  const portfolioReturnPct = account.portfolio_return_pct || 0
  const dailyPnl = account.daily_pnl || 0
  const winRate = account.win_rate || 0
  const openPositions = positions.length || account.open_positions || 0

  // Note: totalPnl calculation available if needed for future metrics
  // const totalPnl = (account.total_pnl || 0) + (account.unrealized_pnl || 0)

  return (
    <div className={`grid grid-cols-2 gap-3 md:grid-cols-4 ${className}`}>
      {/* KPI 1: Portfolio Return */}
      <KPICard
        label="Portfolio Return"
        value={`${portfolioReturnPct >= 0 ? '+' : ''}${(portfolioReturnPct * 100).toFixed(2)}%`}
        delta={portfolioReturnPct}
        isPercentage={true}
      />

      {/* KPI 2: Daily P&L */}
      <KPICard
        label="Daily P&L"
        value={`${dailyPnl >= 0 ? '+' : ''}$${Math.abs(dailyPnl).toFixed(2)}`}
        delta={dailyPnl}
        isPercentage={false}
      />

      {/* KPI 3: Win Rate */}
      <KPICard
        label="Win Rate"
        value={`${winRate.toFixed(0)}%`}
        delta={null} // No trend indicator for win rate
        isPercentage={false}
      />

      {/* KPI 4: Open Positions */}
      <KPICard
        label="Open Positions"
        value={`${openPositions} ${openPositions === 1 ? 'open' : 'open'}`}
        delta={null} // No trend indicator for position count
        isPercentage={false}
      />
    </div>
  )
}

interface KPICardProps {
  label: string
  value: string
  delta?: number | null
  isPercentage: boolean
}

function KPICard({ label, value, delta, isPercentage }: KPICardProps) {
  const hasPositiveDelta = (delta ?? 0) >= 0
  const showTrend = delta !== null && delta !== undefined

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
      <div className="text-xs text-[var(--text-muted)]">{label}</div>
      <div className="mt-1 text-xl font-semibold tracking-tight text-[var(--text-primary)]">
        {value}
      </div>
      {showTrend && (
        <div className={`mt-1 flex items-center text-xs ${
          hasPositiveDelta ? 'text-[var(--success)]' : 'text-[var(--danger)]'
        }`}>
          {hasPositiveDelta ? (
            <TrendingUp className="mr-1 h-3 w-3" />
          ) : (
            <TrendingDown className="mr-1 h-3 w-3" />
          )}
          {isPercentage
            ? `${Math.abs((delta || 0) * 100).toFixed(2)}%`
            : `$${Math.abs(delta || 0).toFixed(2)}`
          }
        </div>
      )}
    </div>
  )
}