'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { RefreshCw, TrendingUp, TrendingDown, Trophy, Upload } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface DataPoint {
  timestamp: string
  equity: number
}

interface BotData {
  config_id: string
  config_name: string
  profile_image_url: string | null
  data_points: DataPoint[]
  current_equity: number
  current_pnl: number
  initial_balance: number
  total_trades: number
  win_rate: number
  open_positions: number
  current_balance: number
  unrealized_pnl: number
}

interface ArenaData {
  bots: BotData[]
  hours: number
  competition_days: number
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

// Bot descriptions from NOTE.md - hardcoded by name
const BOT_DESCRIPTIONS: Record<string, { frequency: string; symbol: string; tagline: string }> = {
  'The Technician': {
    frequency: '5min',
    symbol: 'BTC',
    tagline: 'Price is truth. A rapid-fire technical trader living in the charts. Trades actively, reacting to momentum shifts with precision.'
  },
  'The Sentinel': {
    frequency: '15min',
    symbol: 'BTC',
    tagline: 'Guards capital above all else. A conservative tactician with tight stops and careful entries. Defense wins wars.'
  },
  'The Herald': {
    frequency: '30min',
    symbol: 'BTC',
    tagline: 'Markets move on narrative. Watches sentiment and news, catching stories before price catches up.'
  },
  'The Contrarian': {
    frequency: '1hr',
    symbol: 'BTC',
    tagline: 'The crowd is wrong at extremes. Waits for peak fear or peak greed, then bets against the herd.'
  },
  'The Arbiter': {
    frequency: '4hr',
    symbol: 'BTC',
    tagline: 'Waits for the verdict. Weighs all evidence and acts only when every domain agrees. Patience is edge.'
  },
  'The Compass': {
    frequency: '1d',
    symbol: 'BTC',
    tagline: 'Macro sets the tide. Reads dollar strength, fear indices, and global risk appetite. Positions for regimes, not moves.'
  },
  'The Nomad': {
    frequency: '1w',
    symbol: 'Self-Evolving',
    tagline: 'No fixed path. Wanders the markets, learns, adapts, rewrites its own rules. Built to evolve.'
  }
}

export default function ArenaPage() {
  const [data, setData] = useState<ArenaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hours, setHours] = useState(504) // Default 21 days

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

  // Calculate progress
  const competitionStart = new Date('2024-12-18')
  const today = new Date()
  const daysSinceStart = Math.floor((today.getTime() - competitionStart.getTime()) / (1000 * 60 * 60 * 24))
  const daysRemaining = Math.max(0, 21 - daysSinceStart)
  const progressPercent = Math.min(100, (daysSinceStart / 21) * 100)

  // Sort bots by equity for rankings
  const rankedBots = data ? [...data.bots].sort((a, b) => b.current_equity - a.current_equity) : []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Trophy className="h-10 w-10 text-[var(--accent)]" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">THE ggARENA</h1>
        </div>
        <p className="text-xl text-[var(--text-secondary)] mb-4">
          7 AI Trading Archetypes • 21 Days • $70,000 Starting Capital
        </p>
        {!loading && data && (
          <div className="max-w-md mx-auto">
            <div className="flex items-center justify-between text-sm text-[var(--text-muted)] mb-2">
              <span>Day {daysSinceStart} of 21</span>
              <span>{daysRemaining} days remaining</span>
            </div>
            <div className="w-full bg-[var(--bg-tertiary)] rounded-full h-2">
              <div
                className="bg-[var(--accent)] h-2 rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-end gap-4 mb-6">
        {/* Time range selector */}
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--accent)]"
        >
          <option value={168}>7 days</option>
          <option value={336}>14 days</option>
          <option value={504}>21 days (Full)</option>
          <option value={720}>30 days</option>
        </select>

        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
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

      {/* Live Rankings */}
      {!loading && data && rankedBots.length > 0 && (
        <div className="bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)] p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Live Rankings</h2>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-sm text-[var(--text-muted)]">LIVE</span>
            </div>
          </div>
          <div className="space-y-3">
            {rankedBots.map((bot, index) => {
              const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
              const isPositive = pnlPercent >= 0
              const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : null

              return (
                <div
                  key={bot.config_id}
                  className="flex items-center gap-4 p-3 rounded-lg bg-[var(--bg-tertiary)]"
                >
                  <div className="flex items-center gap-2 w-12">
                    {medal ? (
                      <span className="text-2xl">{medal}</span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-mono">#{index + 1}</span>
                    )}
                  </div>
                  {bot.profile_image_url ? (
                    <img
                      src={bot.profile_image_url}
                      alt={bot.config_name}
                      className="w-10 h-10 rounded-full border-2 object-cover"
                      style={{ borderColor: BOT_COLORS[index % BOT_COLORS.length] }}
                    />
                  ) : (
                    <div
                      className="w-10 h-10 rounded-full border-2 flex items-center justify-center bg-[var(--bg-primary)]"
                      style={{ borderColor: BOT_COLORS[index % BOT_COLORS.length] }}
                    >
                      <Upload className="h-4 w-4 text-[var(--text-muted)]" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-[var(--text-primary)]">{bot.config_name}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-[var(--text-primary)]">{formatCurrency(bot.current_equity)}</div>
                    <div className={`text-sm font-mono ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                      {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Chart */}
      {!loading && data && chartData.length > 0 && (
        <div className="bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)] p-6 mb-6">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Total Equity Over Time</h2>
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

      {/* Bot Cards */}
      {!loading && data && data.bots.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.bots.map((bot, index) => {
            const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
            const isPositive = pnlPercent >= 0
            const description = BOT_DESCRIPTIONS[bot.config_name]

            return (
              <div
                key={bot.config_id}
                className="bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)] p-4"
              >
                {/* Bot name with profile image and color indicator */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="relative">
                    {bot.profile_image_url ? (
                      <img
                        src={bot.profile_image_url}
                        alt={bot.config_name}
                        className="w-12 h-12 rounded-full border-2 object-cover"
                        style={{ borderColor: BOT_COLORS[index % BOT_COLORS.length] }}
                      />
                    ) : (
                      <div
                        className="w-12 h-12 rounded-full border-2 flex items-center justify-center bg-[var(--bg-tertiary)]"
                        style={{ borderColor: BOT_COLORS[index % BOT_COLORS.length] }}
                      >
                        <Upload className="h-5 w-5 text-[var(--text-muted)]" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-[var(--text-primary)] font-medium">{bot.config_name}</h3>
                    {description && (
                      <div className="text-xs text-[var(--text-muted)] font-mono">
                        {description.frequency} · {description.symbol}
                      </div>
                    )}
                  </div>
                </div>

                {/* Strategy Description */}
                {description && (
                  <p className="text-sm text-[var(--text-secondary)] italic mb-3 leading-relaxed">
                    {description.tagline}
                  </p>
                )}

                {/* Current equity */}
                <div className="mb-2">
                  <p className="text-[var(--text-muted)] text-sm">Current Equity</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
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

                {/* Stats grid - 6 metrics */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-[var(--text-muted)]">Trades</p>
                    <p className="text-[var(--text-primary)]">{bot.total_trades}</p>
                  </div>
                  <div>
                    <p className="text-[var(--text-muted)]">Win Rate</p>
                    <p className="text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-[var(--text-muted)]">Open</p>
                    <p className="text-[var(--text-primary)]">{bot.open_positions}</p>
                  </div>
                  <div>
                    <p className="text-[var(--text-muted)]">Initial</p>
                    <p className="text-[var(--text-primary)]">{formatCurrency(bot.initial_balance)}</p>
                  </div>
                  <div>
                    <p className="text-[var(--text-muted)]">Balance</p>
                    <p className="text-[var(--text-primary)]">{formatCurrency(bot.current_balance)}</p>
                  </div>
                  <div>
                    <p className="text-[var(--text-muted)]">Unrealized</p>
                    <p className={bot.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {formatCurrency(bot.unrealized_pnl)}
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* CTA Section */}
      {!loading && data && (
        <div className="mt-12 mb-8 bg-[var(--bg-secondary)] rounded-lg border-2 border-[var(--accent)] p-8 text-center">
          <Trophy className="h-12 w-12 text-[var(--accent)] mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
            Season 1 Opens January 15, 2025
          </h2>
          <p className="text-lg text-[var(--text-secondary)] mb-6 max-w-2xl mx-auto">
            Create your own trading bot and compete for prizes. Watch these archetypes battle, then design your strategy and enter the arena.
          </p>
          <a
            href="https://ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-8 py-4 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#1a1816] dark:text-[#1a1816] font-semibold rounded-xl transition-colors text-lg"
          >
            Create Your Bot on ggbots.ai →
          </a>
        </div>
      )}
    </div>
  )
}
