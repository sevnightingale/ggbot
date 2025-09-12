'use client'

import React from 'react'
import { useBotMetrics } from '../hooks/useBotMetrics'

interface PerformancePanelProps {
  botId: string | null
  className?: string
}

export default function PerformancePanel({ botId, className = '' }: PerformancePanelProps) {
  const { metrics, isLoading, error } = useBotMetrics(botId)

  if (error) {
    return (
      <div className={`performance-panel bg-charcoal-800  p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-bone-200 mb-4">Performance</h2>
        <div className="text-red-400">
          Failed to load performance data
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`performance-panel bg-charcoal-800  p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-bone-200 mb-4">Performance</h2>
        <div className="text-bone-400">
          Loading performance data...
        </div>
      </div>
    )
  }

  if (!botId) {
    return (
      <div className={`performance-panel bg-charcoal-800  p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-bone-200 mb-4">Performance</h2>
        <div className="text-bone-400">
          Select a bot to view performance metrics
        </div>
      </div>
    )
  }

  return (
    <div className={`performance-panel bg-charcoal-800  p-6 ${className}`}>
      <h2 className="text-xl font-semibold text-bone-200 mb-4">Performance</h2>
      
      {/* Account Summary */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-bone-300 mb-2">Account Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-charcoal-700 p-3 rounded">
            <div className="text-bone-400 text-sm">Balance</div>
            <div className="text-bone-200 font-semibold">
              ${metrics?.balance?.toFixed(2) || '0.00'}
            </div>
          </div>
          <div className="bg-charcoal-700 p-3 rounded">
            <div className="text-bone-400 text-sm">Total P&L</div>
            <div className={`font-semibold ${
              (metrics?.totalPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              ${metrics?.totalPnL?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>
      </div>

      {/* Trade Statistics */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-bone-300 mb-2">Trade Stats</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-bone-400">Total Trades</span>
            <span className="text-bone-200">{metrics?.totalTrades || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-bone-400">Win Rate</span>
            <span className="text-bone-200">
              {metrics?.winRate ? `${(metrics.winRate * 100).toFixed(1)}%` : '0%'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-bone-400">Avg Trade</span>
            <span className="text-bone-200">
              ${metrics?.avgTrade?.toFixed(2) || '0.00'}
            </span>
          </div>
        </div>
      </div>

      {/* Charts Placeholder */}
      <div>
        <h3 className="text-lg font-medium text-bone-300 mb-2">Performance Chart</h3>
        <div className="bg-charcoal-700 rounded p-4 h-32 flex items-center justify-center">
          <span className="text-bone-400">Chart implementation coming soon</span>
        </div>
      </div>
    </div>
  )
}