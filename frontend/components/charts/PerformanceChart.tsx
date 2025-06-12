'use client'

import { useBotStore } from '@/store/bot'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function PerformanceChart() {
  const { performance, loadPerformance, isLoading } = useBotStore()

  const handlePeriodChange = (period: string) => {
    loadPerformance(period)
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 bg-charcoal-700/50 animate-pulse w-1/3" />
        <div className="h-64 bg-charcoal-700/50 animate-pulse" />
      </div>
    )
  }

  if (!performance) {
    return (
      <div className="text-center py-8 text-bone-400">
        <p>No performance data available</p>
        <p className="text-sm mt-1">Start trading to see performance metrics</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {['1d', '7d', '30d'].map((period) => (
            <button
              key={period}
              onClick={() => handlePeriodChange(period)}
              className="px-3 py-1 text-sm bg-charcoal-700 hover:bg-charcoal-600 text-bone-200 transition-colors"
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="text-lg font-display font-bold text-bone-200">
            ${performance.total_pnl?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-bone-400">Total P&L</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-display font-bold text-bone-200">
            {((performance.win_rate || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-bone-400">Win Rate</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-display font-bold text-bone-200">
            {performance.total_trades || 0}
          </div>
          <div className="text-xs text-bone-400">Total Trades</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-display font-bold text-bone-200">
            {performance.total_pnl_percentage?.toFixed(2) || '0.00'}%
          </div>
          <div className="text-xs text-bone-400">Return %</div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        {performance.daily_pnl && performance.daily_pnl.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={performance.daily_pnl}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(227, 229, 230, 0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="rgba(227, 229, 230, 0.6)"
                fontSize={12}
              />
              <YAxis 
                stroke="rgba(227, 229, 230, 0.6)"
                fontSize={12}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1c',
                  border: '1px solid rgba(227, 229, 230, 0.2)',
                  borderRadius: '0px',
                  color: '#e3e5e6'
                }}
              />
              <Line
                type="monotone"
                dataKey="pnl"
                stroke="#2cbe77"
                strokeWidth={2}
                dot={{ fill: '#2cbe77', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full text-bone-400">
            <p>No chart data available</p>
          </div>
        )}
      </div>
    </div>
  )
}