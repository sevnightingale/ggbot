'use client'

import React, { useState, useEffect } from 'react'
import { X, TrendingUp, TrendingDown } from 'lucide-react'
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

interface ConfidenceDistribution {
  '5-35': { wins: number; losses: number }
  '35-45': { wins: number; losses: number }
  '45-55': { wins: number; losses: number }
  '55-65': { wins: number; losses: number }
  '65-95': { wins: number; losses: number }
}

interface TradeHistoryModalProps {
  configId: string
  isOpen: boolean
  onClose: () => void
  totalTrades: number
  winRate: number
}

export function TradeHistoryModal({ configId, isOpen, onClose, totalTrades, winRate }: TradeHistoryModalProps) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [distribution, setDistribution] = useState<ConfidenceDistribution | null>(null)
  const [summaryStats, setSummaryStats] = useState<{
    avg_confidence_wins: number
    avg_confidence_losses: number
    total_wins: number
    total_losses: number
  } | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen || !configId) return

    const loadData = async () => {
      setLoading(true)
      try {
        const [historyData, confidenceData] = await Promise.all([
          apiClient.getTradeHistoryWithDecisions(configId, 50),
          apiClient.getConfidenceAnalysis(configId)
        ])

        setTrades(historyData.trades)
        setDistribution(confidenceData.confidence_distribution)
        setSummaryStats(confidenceData.summary_stats)
      } catch (error) {
        console.error('Failed to load trade history:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [isOpen, configId])

  if (!isOpen) return null

  const formatPrice = (price: number) => {
    if (price >= 1000) return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
    if (price >= 1) return `$${price.toFixed(4)}`
    return `$${price.toFixed(6)}`
  }

  const formatPnL = (pnl: number) => {
    const sign = pnl >= 0 ? '+' : ''
    return `${sign}$${pnl.toFixed(2)}`
  }

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-[var(--profit-color)]'
    if (pnl < 0) return 'text-[var(--loss-color)]'
    return 'text-[var(--neutral-color)]'
  }

  const getSideIcon = (side: string) => {
    return side.toLowerCase() === 'long' ? (
      <TrendingUp className="h-4 w-4" />
    ) : (
      <TrendingDown className="h-4 w-4" />
    )
  }

  const getSideColor = (side: string) => {
    return side.toLowerCase() === 'long' ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
  }

  const getTimeAgo = (timestamp: string | null) => {
    if (!timestamp) return '—'
    const now = new Date()
    const then = new Date(timestamp)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 7) return `${diffDays}d ago`
    return then.toLocaleDateString()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-6xl max-h-[90vh] bg-[var(--bg-secondary)] rounded-2xl border border-[var(--border)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
          <div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">Trade History</h2>
            <p className="text-sm text-[var(--text-muted)] mt-1">
              {totalTrades} trades • {winRate.toFixed(0)}% win rate
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-[var(--text-muted)]" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-[var(--text-muted)]">Loading trade history...</div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Confidence Distribution */}
              {distribution && summaryStats && (
                <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-primary)] p-4">
                  <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Confidence Distribution</h3>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-xs text-[var(--text-muted)] mb-1">Avg Confidence (Wins)</div>
                      <div className="text-lg font-semibold text-[var(--profit-color)]">
                        {summaryStats.avg_confidence_wins.toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-[var(--text-muted)] mb-1">Avg Confidence (Losses)</div>
                      <div className="text-lg font-semibold text-[var(--loss-color)]">
                        {summaryStats.avg_confidence_losses.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {Object.entries(distribution).map(([bucket, counts]) => {
                      const total = counts.wins + counts.losses
                      if (total === 0) return null

                      const winPct = (counts.wins / total) * 100

                      return (
                        <div key={bucket} className="flex items-center gap-3">
                          <div className="text-xs text-[var(--text-muted)] w-16">{bucket}%</div>
                          <div className="flex-1 flex gap-1 h-6">
                            <div
                              className="bg-[var(--profit-color)]/20 rounded flex items-center justify-center text-xs text-[var(--profit-color)]"
                              style={{ width: `${(counts.wins / total) * 100}%` }}
                            >
                              {counts.wins > 0 && counts.wins}
                            </div>
                            <div
                              className="bg-[var(--loss-color)]/20 rounded flex items-center justify-center text-xs text-[var(--loss-color)]"
                              style={{ width: `${(counts.losses / total) * 100}%` }}
                            >
                              {counts.losses > 0 && counts.losses}
                            </div>
                          </div>
                          <div className="text-xs text-[var(--text-muted)] w-12 text-right">
                            {winPct.toFixed(0)}%
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Trades Table */}
              <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-primary)] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b border-[var(--border)]">
                        <th className="text-left py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Symbol</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Side</th>
                        <th className="text-right py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Entry</th>
                        <th className="text-right py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Size</th>
                        <th className="text-right py-3 px-4 text-xs font-medium text-[var(--text-muted)]">P&L</th>
                        <th className="text-center py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Confidence</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Reason</th>
                        <th className="text-left py-3 px-4 text-xs font-medium text-[var(--text-muted)]">Closed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trades.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="py-12 text-center text-[var(--text-muted)]">
                            No closed trades yet
                          </td>
                        </tr>
                      ) : (
                        trades.map((trade) => (
                          <tr key={trade.trade_id} className="border-b border-[var(--border)] last:border-b-0 hover:bg-[var(--bg-secondary)] transition-colors">
                            <td className="py-3 px-4 text-sm font-medium text-[var(--text-primary)]">
                              {trade.symbol}
                            </td>
                            <td className="py-3 px-4">
                              <div className={`flex items-center gap-1 text-xs font-medium ${getSideColor(trade.side)}`}>
                                {getSideIcon(trade.side)}
                                {trade.side.toUpperCase()}
                              </div>
                            </td>
                            <td className="py-3 px-4 text-right text-sm text-[var(--text-secondary)]">
                              {formatPrice(trade.entry_price)}
                            </td>
                            <td className="py-3 px-4 text-right text-sm text-[var(--text-secondary)]">
                              ${trade.size_usd.toLocaleString()}
                            </td>
                            <td className={`py-3 px-4 text-right text-sm font-semibold ${getPnLColor(trade.realized_pnl)}`}>
                              {formatPnL(trade.realized_pnl)}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="inline-block px-2 py-1 text-xs font-medium bg-[var(--bg-secondary)] rounded">
                                {trade.confidence_score ? `${(trade.confidence_score * 100).toFixed(0)}%` : '—'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-xs text-[var(--text-muted)] capitalize">
                              {trade.close_reason?.replace(/_/g, ' ') || '—'}
                            </td>
                            <td className="py-3 px-4 text-xs text-[var(--text-muted)]">
                              {getTimeAgo(trade.closed_at)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
