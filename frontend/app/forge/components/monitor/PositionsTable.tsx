'use client'

import React, { useState, useEffect, useRef } from 'react'
import { TrendingUp, TrendingDown, X } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface Position {
  trade_id?: string
  position_id?: string  // Unified ID field (trade_id for paper, batch_id for live)
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
  source?: 'paper' | 'live'  // Track position source
}

interface PositionsTableProps {
  positions?: Position[]
  className?: string
  selectedConfigId?: string
  onPositionClosed?: () => void
}

export function PositionsTable({ positions = [], className = '', selectedConfigId, onPositionClosed }: PositionsTableProps) {
  // Track price changes for slide animations
  const [animatingPrices, setAnimatingPrices] = useState<Record<string, boolean>>({})
  const [displayPrices, setDisplayPrices] = useState<Record<string, { current: string; pnl: string; percentage: string }>>({})
  const prevPricesRef = useRef<Record<string, number>>({})

  // Track closing positions
  const [closingPositions, setClosingPositions] = useState<Record<string, boolean>>({})

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

  // Handle closing a position (paper or live)
  const handleClosePosition = async (positionId: string, source: 'paper' | 'live' = 'paper') => {
    if (!selectedConfigId) {
      console.error('No config ID selected')
      return
    }

    if (closingPositions[positionId]) {
      return // Already closing
    }

    try {
      setClosingPositions(prev => ({ ...prev, [positionId]: true }))

      if (source === 'live') {
        // Close live position via Symphony
        const headers = await apiClient.getAuthHeaders()
        const baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const response = await fetch(`${baseUrl}/api/v2/positions/live/${positionId}/close`, {
          method: 'POST',
          headers
        })

        if (!response.ok) {
          const error = await response.text()
          throw new Error(`Failed to close live position: ${error}`)
        }

        const result = await response.json()
        console.log('Live position closed:', result)
        alert('✅ Live position closed successfully!')
      } else {
        // Close paper position (existing logic)
        const result = await apiClient.closePosition(selectedConfigId, positionId)
        console.log('Paper position closed:', result)
        alert('✅ Position closed successfully!')
      }

      // Notify parent component to refresh data
      if (onPositionClosed) {
        onPositionClosed()
      }
    } catch (error) {
      console.error('Error closing position:', error)
      alert(`Failed to close position: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setClosingPositions(prev => ({ ...prev, [positionId]: false }))
    }
  }

  // Trigger slide animations on every SSE update
  useEffect(() => {
    if (positions.length === 0) return

    const newAnimations: Record<string, boolean> = {}
    const newDisplayPrices: Record<string, { current: string; pnl: string; percentage: string }> = {}

    positions.forEach(position => {
      const positionId = position.position_id || position.trade_id || 'unknown'
      const currentPrice = position.current_price

      // Format new values
      newDisplayPrices[positionId] = {
        current: formatPrice(currentPrice),
        pnl: formatPnL(position.unrealized_pnl),
        percentage: formatPercentage(position.entry_price, currentPrice)
      }

      // Always trigger animation on SSE update (like MetricsBar)
      newAnimations[positionId] = true

      // Update prev price for potential future use
      prevPricesRef.current[positionId] = currentPrice
    })

    // Start animations for all positions
    setAnimatingPrices(newAnimations)

    // After slide-out completes, update display values and slide-in
    setTimeout(() => {
      setDisplayPrices(newDisplayPrices)
      setAnimatingPrices({})
    }, 250)
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

  // Animated value component - matches MetricsBar style exactly
  const AnimatedValue = ({ value, className, isAnimating }: { value: string; className?: string; isAnimating: boolean }) => (
    <div className="relative overflow-hidden h-6">
      <div
        className={`transition-all duration-250 ease-in-out ${className || ''} ${
          isAnimating
            ? 'transform translate-y-8 opacity-0'
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
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Position</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Entry → Current</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">P&L</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">SL/TP</th>
                <th className="text-left py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Age</th>
                <th className="text-right py-3 px-2 text-sm font-medium text-[var(--text-muted)]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => {
                const positionId = position.position_id || position.trade_id || 'unknown'
                const positionSource = position.source || 'paper'
                return (
                <tr key={positionId} className="border-b border-[var(--border)] last:border-b-0">
                  <td className="py-3 px-2 text-sm text-[var(--text-primary)] font-medium">
                    {position.symbol}
                  </td>
                  <td className="py-3 px-2">
                    <div className={`flex items-center gap-1 text-sm font-medium ${getSideColor(position.side)}`}>
                      {getSideIcon(position.side)}
                      {position.side.toUpperCase()}
                    </div>
                  </td>
                  {/* Position: Size + Leverage stacked */}
                  <td className="py-3 px-2">
                    <div className="space-y-0.5">
                      <div className="text-sm text-[var(--text-primary)]">
                        ${position.size_usd.toLocaleString()}
                      </div>
                      <div className="text-xs text-[var(--text-muted)]">
                        {position.leverage}x leverage
                      </div>
                    </div>
                  </td>
                  {/* Entry → Current price */}
                  <td className="py-3 px-2">
                    <div className="space-y-0.5">
                      <div className="text-xs text-[var(--text-muted)]">
                        {formatPrice(position.entry_price)}
                      </div>
                      <div className="text-sm text-[var(--text-primary)] font-medium">
                        <AnimatedValue
                          value={displayPrices[positionId]?.current || formatPrice(position.current_price)}
                          isAnimating={animatingPrices[positionId] || false}
                        />
                      </div>
                    </div>
                  </td>
                  {/* P&L: Dollar amount + percentage stacked */}
                  <td className={`py-3 px-2 font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                    <div className="space-y-0.5">
                      <div className="text-sm">
                        <AnimatedValue
                          value={displayPrices[positionId]?.pnl || formatPnL(position.unrealized_pnl)}
                          isAnimating={animatingPrices[positionId] || false}
                        />
                      </div>
                      <div className="text-xs">
                        <AnimatedValue
                          value={displayPrices[positionId]?.percentage || formatPercentage(position.entry_price, position.current_price)}
                          isAnimating={animatingPrices[positionId] || false}
                        />
                      </div>
                    </div>
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
                  <td className="py-3 px-2 text-right">
                    <button
                      onClick={() => handleClosePosition(positionId, positionSource)}
                      disabled={closingPositions[positionId]}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-[var(--loss-color)] hover:bg-red-500/10 border border-[var(--loss-color)] rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Close position"
                    >
                      <X className="h-3 w-3" />
                      {closingPositions[positionId] ? 'Closing...' : 'Close'}
                    </button>
                  </td>
                </tr>
              )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-3">
        {positions.map((position) => {
          const positionId = position.position_id || position.trade_id || 'unknown'
          const positionSource = position.source || 'paper'
          return (
          <div key={positionId} className="border border-[var(--border)] rounded-xl p-4 bg-[var(--bg-primary)]">
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
                  value={displayPrices[positionId]?.percentage || formatPercentage(position.entry_price, position.current_price)}
                  isAnimating={animatingPrices[positionId] || false}
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
                    value={displayPrices[positionId]?.current || formatPrice(position.current_price)}
                    isAnimating={animatingPrices[positionId] || false}
                    className="inline-block ml-1"
                  />
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">P&L:</span>
                <span className={`font-medium ${getPnLColor(position.unrealized_pnl)}`}>
                  <AnimatedValue
                    value={displayPrices[positionId]?.pnl || formatPnL(position.unrealized_pnl)}
                    isAnimating={animatingPrices[positionId] || false}
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

            {/* Close Button */}
            <button
              onClick={() => handleClosePosition(positionId, positionSource)}
              disabled={closingPositions[positionId]}
              className="mt-3 w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-[var(--loss-color)] hover:bg-red-500/10 border border-[var(--loss-color)] rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <X className="h-4 w-4" />
              {closingPositions[positionId] ? 'Closing Position...' : 'Close Position'}
            </button>
          </div>
        )
        })}
      </div>
    </div>
  )
}