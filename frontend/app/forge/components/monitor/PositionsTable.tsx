'use client'

import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface Position {
  trade_id: string
  symbol: string
  side: string
  size_usd: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  status: string
  opened_at: string
  stop_loss?: number
  take_profit?: number
}

interface PositionsTableProps {
  positions?: Position[]
  className?: string
}

export function PositionsTable({ positions = [], className = '' }: PositionsTableProps) {
  if (positions.length === 0) {
    return (
      <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Active Trades</h3>
        <div className="text-center py-8">
          <div className="text-[var(--text-muted)] mb-2">No active trades</div>
          <div className="text-sm text-[var(--text-muted)]">
            Your positions will appear here when the bot enters trades
          </div>
        </div>
      </div>
    )
  }

  const formatPrice = (price: number) => {
    if (price >= 1000) {
      return `$${(price / 1000).toFixed(1)}k`
    }
    return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPnL = (pnl: number) => {
    const sign = pnl >= 0 ? '+' : ''
    return `${sign}$${pnl.toFixed(2)}`
  }

  const formatPercentage = (entry: number, current: number) => {
    const change = ((current - entry) / entry) * 100
    const sign = change >= 0 ? '+' : ''
    return `${sign}${change.toFixed(2)}%`
  }

  const getSideColor = (side: string) => {
    return side.toLowerCase() === 'long' ? 'text-[var(--success)]' : 'text-[var(--danger)]'
  }

  const getSideIcon = (side: string) => {
    return side.toLowerCase() === 'long' ? (
      <TrendingUp className="h-4 w-4" />
    ) : (
      <TrendingDown className="h-4 w-4" />
    )
  }

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-[var(--success)]' : 'text-[var(--danger)]'
  }

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const then = new Date(timestamp)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    return new Date(timestamp).toLocaleDateString()
  }

  return (
    <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Active Trades</h3>

      {/* Desktop Table */}
      <div className="hidden md:block">
        <div className="overflow-hidden">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Symbol</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Side</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Size</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Entry</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Current</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">P&L</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">%</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">SL/TP</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Age</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => (
                <tr key={position.trade_id} className="border-b border-[var(--border)] last:border-b-0">
                  <td className="py-3 px-2 text-sm text-[var(--text-primary)] font-medium">
                    {position.symbol}
                  </td>
                  <td className="py-3 px-2">
                    <div className={`flex items-center gap-1 text-sm font-medium ${getSideColor(position.side)}`}>
                      {getSideIcon(position.side)}
                      {position.side.toUpperCase()}
                    </div>
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-secondary)]">
                    ${position.size_usd.toLocaleString()}
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-secondary)]">
                    {formatPrice(position.entry_price)}
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-primary)] font-medium">
                    {formatPrice(position.current_price)}
                  </td>
                  <td className={`py-3 px-2 text-sm font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                    {formatPnL(position.unrealized_pnl)}
                  </td>
                  <td className={`py-3 px-2 text-sm font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                    {formatPercentage(position.entry_price, position.current_price)}
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-muted)]">
                    <div className="space-y-1">
                      {position.stop_loss && (
                        <div>SL: {formatPrice(position.stop_loss)}</div>
                      )}
                      {position.take_profit && (
                        <div>TP: {formatPrice(position.take_profit)}</div>
                      )}
                      {!position.stop_loss && !position.take_profit && (
                        <div className="text-xs">—</div>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-muted)]">
                    {getTimeAgo(position.opened_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-3">
        {positions.map((position) => (
          <div key={position.trade_id} className="border border-[var(--border)] rounded-xl p-4 bg-[var(--bg-primary)]">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[var(--text-primary)]">
                  {position.symbol}
                </span>
                <span className="text-[var(--text-secondary)]">•</span>
                <div className={`flex items-center gap-1 text-sm font-medium ${getSideColor(position.side)}`}>
                  {getSideIcon(position.side)}
                  {position.side.toUpperCase()}
                </div>
              </div>
              <div className={`text-sm font-semibold ${getPnLColor(position.unrealized_pnl)}`}>
                {formatPercentage(position.entry_price, position.current_price)}
              </div>
            </div>

            {/* Position Details */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Size:</span>
                <span className="text-[var(--text-secondary)]">${position.size_usd.toLocaleString()}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Price:</span>
                <span className="text-[var(--text-secondary)]">
                  {formatPrice(position.entry_price)} → {formatPrice(position.current_price)}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">P&L:</span>
                <span className={`font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                  {formatPnL(position.unrealized_pnl)}
                </span>
              </div>

              {(position.stop_loss || position.take_profit) && (
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Risk:</span>
                  <div className="text-right text-[var(--text-muted)] text-xs">
                    {position.stop_loss && <div>SL: {formatPrice(position.stop_loss)}</div>}
                    {position.take_profit && <div>TP: {formatPrice(position.take_profit)}</div>}
                  </div>
                </div>
              )}

              <div className="flex justify-between pt-1 border-t border-[var(--border)]">
                <span className="text-[var(--text-muted)] text-xs">Opened:</span>
                <span className="text-[var(--text-muted)] text-xs">{getTimeAgo(position.opened_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}