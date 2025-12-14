'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { ArrowLeft, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react'
import Link from 'next/link'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface DataPoint {
  timestamp: string
  equity: number
}

interface BotData {
  config_id: string
  config_name: string
  data_points: DataPoint[]
  current_equity: number
  current_pnl: number
  total_trades: number
  win_rate: number
  open_positions: number
}

interface ComparisonData {
  bots: BotData[]
  hours: number
  user_id: string
}

// Color palette for the 6 bots
const BOT_COLORS = [
  '#10b981', // green
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
]

// Helper to get bot profile image
const getBotImage = (botName: string): string => {
  // Remove "The " prefix if present, then normalize
  const withoutThe = botName.replace(/^The\s+/i, '')
  const normalized = withoutThe.toLowerCase().replace(/\s+/g, '-')
  return `/the-${normalized}-1.png`
}

export default function BotsComparisonPage() {
  const [data, setData] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hours, setHours] = useState(72) // Default 3 days

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        setError('Not authenticated')
        return
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/v2/admin/bots/equity-comparison?hours=${hours}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to fetch comparison data')
      }

      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [hours])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Transform data for Recharts
  const getChartData = () => {
    if (!data || data.bots.length === 0) return []

    // Create a map of timestamps to equity values for each bot
    const timestampMap = new Map<string, Record<string, string | number>>()

    data.bots.forEach((bot) => {
      bot.data_points.forEach((point) => {
        const timestamp = point.timestamp
        if (!timestampMap.has(timestamp)) {
          timestampMap.set(timestamp, { timestamp })
        }
        const entry = timestampMap.get(timestamp)
        if (entry) {
          entry[bot.config_name] = point.equity
        }
      })
    })

    // Convert to array and sort by timestamp
    const chartData = Array.from(timestampMap.values())
    chartData.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

    return chartData
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const chartData = getChartData()

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link
            href="/admin"
            className="p-2 hover:bg-charcoal-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">Bot Performance Comparison</h1>
            <p className="text-sm text-gray-500">
              {data ? `${data.bots.length} paper trading bots` : 'Loading...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Time range selector */}
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="px-3 py-2 bg-charcoal-800 border border-charcoal-700 rounded-lg text-white text-sm focus:outline-none focus:border-charcoal-500"
          >
            <option value={24}>24 hours</option>
            <option value={72}>3 days</option>
            <option value={168}>7 days</option>
            <option value={720}>30 days</option>
          </select>

          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-charcoal-800 hover:bg-charcoal-700 rounded-lg text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && !data && (
        <div className="flex items-center justify-center h-96">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-500" />
        </div>
      )}

      {/* Chart */}
      {!loading && data && chartData.length > 0 && (
        <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-4">Total Equity Over Time</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="timestamp"
                stroke="#9ca3af"
                tickFormatter={formatTimestamp}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
              />
              <YAxis
                stroke="#9ca3af"
                tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff'
                }}
                labelFormatter={formatTimestamp}
                formatter={(value: number) => [formatCurrency(value), '']}
              />
              <Legend
                wrapperStyle={{ color: '#fff' }}
                iconType="line"
              />
              {data.bots.map((bot, index) => (
                <Line
                  key={bot.config_id}
                  type="monotone"
                  dataKey={bot.config_name}
                  stroke={BOT_COLORS[index % BOT_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Stats Cards */}
      {!loading && data && data.bots.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.bots.map((bot, index) => {
            const pnlPercent = ((bot.current_equity - 10000) / 10000) * 100
            const isPositive = pnlPercent >= 0

            return (
              <div
                key={bot.config_id}
                className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4"
              >
                {/* Bot name with profile image and color indicator */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="relative">
                    <img
                      src={getBotImage(bot.config_name)}
                      alt={bot.config_name}
                      className="w-12 h-12 rounded-full border-2 object-cover"
                      style={{ borderColor: BOT_COLORS[index % BOT_COLORS.length] }}
                    />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-white font-medium">{bot.config_name}</h3>
                  </div>
                </div>

                {/* Current equity */}
                <div className="mb-2">
                  <p className="text-gray-500 text-sm">Current Equity</p>
                  <p className="text-2xl font-bold text-white">
                    {formatCurrency(bot.current_equity)}
                  </p>
                </div>

                {/* P&L */}
                <div className="flex items-center gap-2 mb-3">
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4 text-green-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                    {formatCurrency(bot.current_pnl)} ({pnlPercent.toFixed(2)}%)
                  </span>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-gray-500">Trades</p>
                    <p className="text-white">{bot.total_trades}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Win Rate</p>
                    <p className="text-white">{(bot.win_rate * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Open</p>
                    <p className="text-white">{bot.open_positions}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Points</p>
                    <p className="text-white">{bot.data_points.length}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
