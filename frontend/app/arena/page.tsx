'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { RefreshCw, TrendingUp, TrendingDown, Trophy } from 'lucide-react'
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
  initial_balance: number
  total_trades: number
  win_rate: number
  open_positions: number
}

interface ArenaData {
  bots: BotData[]
  hours: number
  competition_days: number
}

// Color palette for bots (brass, signal, jade, ruby, amethyst, amber)
const BOT_COLORS = [
  '#D4AF37', // brass
  '#00F0FF', // signal
  '#10b981', // jade
  '#ef4444', // ruby
  '#8b5cf6', // amethyst
  '#f59e0b', // amber
]

// Helper to get bot profile image
const getBotImage = (botName: string): string => {
  // Remove "The " prefix if present, then normalize
  const withoutThe = botName.replace(/^The\s+/i, '')
  const normalized = withoutThe.toLowerCase().replace(/\s+/g, '-')
  return `/the-${normalized}-1.png`
}

export default function ArenaPage() {
  const [data, setData] = useState<ArenaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hours, setHours] = useState(504) // Default 21 days (competition period)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/v2/public/arena/performance?hours=${hours}`)

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to fetch arena data')
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

  // Calculate rankings (by current equity)
  const rankedBots = data ? [...data.bots].sort((a, b) => b.current_equity - a.current_equity) : []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Trophy className="h-8 w-8" style={{ color: '#D4AF37' }} />
          <div>
            <h1 className="text-2xl font-bold text-white">Arena</h1>
            <p className="text-sm" style={{ color: '#6B7280' }}>
              {data ? `${data.bots.length} bots competing • ${data.competition_days} days` : 'Loading competition...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Time range selector */}
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="px-3 py-2 rounded-lg text-white text-sm focus:outline-none"
            style={{
              backgroundColor: '#0A0F1E',
              border: '1px solid #1E293B',
            }}
          >
            <option value={168}>7 days</option>
            <option value={336}>14 days</option>
            <option value={504}>21 days (Competition)</option>
            <option value={720}>30 days</option>
          </select>

          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white transition-colors disabled:opacity-50"
            style={{
              backgroundColor: '#0A0F1E',
              border: '1px solid #1E293B',
            }}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#ef4444' }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && !data && (
        <div className="flex items-center justify-center h-96">
          <RefreshCw className="h-8 w-8 animate-spin" style={{ color: '#6B7280' }} />
        </div>
      )}

      {/* Chart */}
      {!loading && data && chartData.length > 0 && (
        <div className="rounded-lg border p-6 mb-6" style={{ backgroundColor: '#0A0F1E', borderColor: '#1E293B' }}>
          <h2 className="text-lg font-semibold text-white mb-4">Performance Over Time</h2>
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

      {/* Leaderboard */}
      {!loading && data && rankedBots.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Leaderboard</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rankedBots.map((bot, index) => {
              const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
              const isPositive = pnlPercent >= 0
              const rankColor = index === 0 ? '#D4AF37' : index === 1 ? '#C0C0C0' : index === 2 ? '#CD7F32' : '#6B7280'

              return (
                <div
                  key={bot.config_id}
                  className="rounded-lg border p-4"
                  style={{ backgroundColor: '#0A0F1E', borderColor: '#1E293B' }}
                >
                  {/* Bot name with profile image, rank, and color indicator */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="relative">
                      <img
                        src={getBotImage(bot.config_name)}
                        alt={bot.config_name}
                        className="w-12 h-12 rounded-full border-2 object-cover"
                        style={{ borderColor: BOT_COLORS[data.bots.findIndex(b => b.config_id === bot.config_id) % BOT_COLORS.length] }}
                      />
                      {/* Rank badge */}
                      <div
                        className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
                        style={{ backgroundColor: rankColor, color: index < 3 ? '#000' : '#fff' }}
                      >
                        {index + 1}
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-white font-medium">{bot.config_name}</h3>
                    </div>
                  </div>

                  {/* Current equity */}
                  <div className="mb-2">
                    <p className="text-sm" style={{ color: '#6B7280' }}>Current Equity</p>
                    <p className="text-2xl font-bold text-white">
                      {formatCurrency(bot.current_equity)}
                    </p>
                  </div>

                  {/* P&L */}
                  <div className="flex items-center gap-2 mb-3">
                    {isPositive ? (
                      <TrendingUp className="h-4 w-4" style={{ color: '#10b981' }} />
                    ) : (
                      <TrendingDown className="h-4 w-4" style={{ color: '#ef4444' }} />
                    )}
                    <span style={{ color: isPositive ? '#10b981' : '#ef4444' }}>
                      {formatCurrency(bot.current_pnl)} ({pnlPercent.toFixed(2)}%)
                    </span>
                  </div>

                  {/* Stats grid */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p style={{ color: '#6B7280' }}>Trades</p>
                      <p className="text-white">{bot.total_trades}</p>
                    </div>
                    <div>
                      <p style={{ color: '#6B7280' }}>Win Rate</p>
                      <p className="text-white">{(bot.win_rate * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p style={{ color: '#6B7280' }}>Open</p>
                      <p className="text-white">{bot.open_positions}</p>
                    </div>
                    <div>
                      <p style={{ color: '#6B7280' }}>Points</p>
                      <p className="text-white">{bot.data_points.length}</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
