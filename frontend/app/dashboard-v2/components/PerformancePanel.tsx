'use client'

import React from 'react'
import { useBotMetrics } from '../hooks/useBotMetrics'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'

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
    <div className={`performance-panel bg-charcoal-800 corner-top-left corner-bottom-right p-6 ${className}`}>
      <h2 className="text-xl font-semibold text-bone-200 mb-4">Performance</h2>
      <div className="gradient-divider mb-4"></div>
      
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

      <div className="gradient-divider mb-4"></div>

      {/* Trade Statistics */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-bone-300 mb-2">Trade Statistics</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-gray-400"># of closed trades</span>
            <span className="text-sm text-bone-200">{metrics?.totalTrades || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-400"># and % of trades won</span>
            <span className="text-sm text-green-400">
              {metrics?.winTrades || 0} ({metrics?.winRate ? `${(metrics.winRate * 100).toFixed(0)}%` : '0%'})
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-400"># and % of trades lost</span>
            <span className="text-sm text-red-400">
              {metrics?.lossTrades || 0} ({metrics?.lossRate ? `${(metrics.lossRate * 100).toFixed(0)}%` : '0%'})
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-400"># and % of trades neutral</span>
            <span className="text-sm text-gray-400">
              {metrics?.neutralTrades || 0} ({metrics?.neutralRate ? `${(metrics.neutralRate * 100).toFixed(0)}%` : '0%'})
            </span>
          </div>
          <div className="gradient-divider my-2"></div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-400">Average profit per trade (%)</span>
            <span className="text-sm text-green-400">{metrics?.avgProfitPerTrade ? `${metrics.avgProfitPerTrade.toFixed(1)}%` : '0%'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-400">Average loss per trade (%)</span>
            <span className="text-sm text-red-400">{metrics?.avgLossPerTrade ? `${metrics.avgLossPerTrade.toFixed(1)}%` : '0%'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-400">Average trade duration</span>
            <span className="text-sm text-bone-200">{metrics?.avgTradeDuration || '0m'}</span>
          </div>
        </div>
      </div>

      <div className="gradient-divider mb-4"></div>

      {/* Performance Chart */}
      <div>
        <h3 className="text-lg font-medium text-bone-300 mb-2">Performance Chart</h3>
        {metrics?.profitLossData && metrics.profitLossData.length > 0 ? (
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics.profitLossData}>
                <XAxis 
                  dataKey="date" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                  tickFormatter={(value) => `$${value}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="profit" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-40 flex items-center justify-center text-gray-500 bg-charcoal-700">
            <div className="text-center">
              <div className="text-2xl mb-2">📈</div>
              <p className="text-sm">No trading history yet</p>
              <p className="text-xs">Start your bot to see performance data</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}