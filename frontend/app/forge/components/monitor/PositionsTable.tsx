'use client'

import React, { useState, useEffect, useRef } from 'react'
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
  leverage: number
}

interface PositionsTableProps {
  positions?: Position[]
  className?: string
}

export function PositionsTable({ positions = [], className = '' }: PositionsTableProps) {
  // Track price changes for slide animations
  const [animatingPrices, setAnimatingPrices] = useState<Record<string, boolean>>({})
  const [displayPrices, setDisplayPrices] = useState<Record<string, { current: string; pnl: string; percentage: string }>>({})
  const prevPricesRef = useRef<Record<string, number>>({})

  // Helper functions
  const formatPrice = (price: number) => {
    // Smart crypto price formatting based on price range
    if (price >= 10000) {
      return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
    } else if (price >= 1000) {
      return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
    } else if (price >= 100) {
      return `$${price.toFixed(2)}`
    } else if (price >= 1) {
      return `$${price.toFixed(4)}`
    } else if (price >= 0.01) {
      return `$${price.toFixed(6)}`
    } else if (price >= 0.0001) {
      return `$${price.toFixed(8)}`
    } else {
      return `$${price.toFixed(10)}`
    }
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

  // Trigger slide animations on every SSE update
  useEffect(() => {
    if (positions.length === 0) return

    const newAnimations: Record<string, boolean> = {}
    const newDisplayPrices: Record<string, { current: string; pnl: string; percentage: string }> = {}

    positions.forEach(position => {
      const prevPrice = prevPricesRef.current[position.trade_id]
      const currentPrice = position.current_price

      // Format new values
      newDisplayPrices[position.trade_id] = {
        current: formatPrice(currentPrice),
        pnl: formatPnL(position.unrealized_pnl),
        percentage: formatPercentage(position.entry_price, currentPrice)
      }

      // Trigger animation on price change or initial load
      if (prevPrice === undefined || prevPrice !== currentPrice) {
        newAnimations[position.trade_id] = true

        // After slide-out completes, update display and slide-in
        setTimeout(() => {
          setDisplayPrices(prev => ({
            ...prev,
            [position.trade_id]: newDisplayPrices[position.trade_id]
          }))
          setAnimatingPrices(prev => ({
            ...prev,
            [position.trade_id]: false
          }))
        }, 150)
      }

      // Update prev price
      prevPricesRef.current[position.trade_id] = currentPrice
    })

    // Start animations
    setAnimatingPrices(newAnimations)
  }, [positions])
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


  const getSideColor = (side: string) => {
    return side.toLowerCase() === 'long' ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
  }

  const getSideIcon = (side: string) => {
    return side.toLowerCase() === 'long' ? (
      <TrendingUp className="h-4 w-4" />
    ) : (
      <TrendingDown className="h-4 w-4" />
    )
  }

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-[var(--profit-color)]'
    if (pnl < 0) return 'text-[var(--loss-color)]'
    return 'text-[var(--neutral-color)]'
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

  // Animated value component
  const AnimatedValue = ({ value, className, isAnimating }: { value: string; className?: string; isAnimating: boolean }) => (
    <div className="relative overflow-hidden h-5">
      <div
        className={`transition-all duration-150 ease-out ${className} ${
          isAnimating
            ? 'transform translate-y-6 opacity-0'
            : 'transform translate-y-0 opacity-100'
        }`}
      >
        {value}
      </div>
    </div>
  )

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
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Leverage</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Collateral</th>
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
                    {position.leverage}x
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-secondary)]">
                    ${(position.size_usd / position.leverage).toLocaleString()}
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-secondary)]">
                    {formatPrice(position.entry_price)}
                  </td>
                  <td className="py-3 px-2 text-sm text-[var(--text-primary)] font-medium">
                    <AnimatedValue
                      value={displayPrices[position.trade_id]?.current || formatPrice(position.current_price)}
                      isAnimating={animatingPrices[position.trade_id] || false}
                    />
                  </td>
                  <td className={`py-3 px-2 text-sm font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                    <AnimatedValue
                      value={displayPrices[position.trade_id]?.pnl || formatPnL(position.unrealized_pnl)}
                      isAnimating={animatingPrices[position.trade_id] || false}
                    />
                  </td>
                  <td className={`py-3 px-2 text-sm font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                    <AnimatedValue
                      value={displayPrices[position.trade_id]?.percentage || formatPercentage(position.entry_price, position.current_price)}
                      isAnimating={animatingPrices[position.trade_id] || false}
                    />
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
                <AnimatedValue
                  value={displayPrices[position.trade_id]?.percentage || formatPercentage(position.entry_price, position.current_price)}
                  isAnimating={animatingPrices[position.trade_id] || false}
                />
              </div>
            </div>

            {/* Position Details */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Size:</span>
                <span className="text-[var(--text-secondary)]">${position.size_usd.toLocaleString()}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Leverage:</span>
                <span className="text-[var(--text-secondary)]">{position.leverage}x</span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Collateral:</span>
                <span className="text-[var(--text-secondary)]">${(position.size_usd / position.leverage).toLocaleString()}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Price:</span>
                <span className="text-[var(--text-secondary)]">
                  {formatPrice(position.entry_price)} →
                  <AnimatedValue
                    value={displayPrices[position.trade_id]?.current || formatPrice(position.current_price)}
                    isAnimating={animatingPrices[position.trade_id] || false}
                    className="inline-block ml-1"
                  />
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">P&L:</span>
                <span className={`font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                  <AnimatedValue
                    value={displayPrices[position.trade_id]?.pnl || formatPnL(position.unrealized_pnl)}
                    isAnimating={animatingPrices[position.trade_id] || false}
                  />
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