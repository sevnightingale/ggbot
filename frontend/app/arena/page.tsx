'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Trophy, Bot } from 'lucide-react'
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

// Brass-toned palette matching VIBE.md ceremonial design
const BOT_COLORS = [
  '#c1a87d', // brass (primary)
  '#d4bc91', // light brass
  '#a89168', // dark brass
  '#8a7859', // deep brass
  '#e6d5b8', // pale brass
  '#9c8a6a', // muted brass
  '#b5a279', // warm brass
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
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Hero Section */}
      <div className="pt-16 pb-12 px-6 text-center border-b border-[var(--border)]">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-4 mb-6">
            <Trophy className="h-8 w-8 text-[var(--accent)]" />
            <h1 className="font-display text-5xl md:text-6xl tracking-tight text-[var(--text-primary)]">
              The <span className="text-[var(--accent)]">gg</span>Arena
            </h1>
          </div>
          <p className="font-sans text-lg text-[var(--text-secondary)] mb-8 tracking-wide">
            7 AI Trading Archetypes · 21 Days · $70,000 Starting Capital
          </p>
          {!loading && data && (
            <div className="max-w-sm mx-auto">
              <div className="flex items-center justify-between text-xs font-mono text-[var(--text-muted)] mb-2 uppercase tracking-wider">
                <span>Day {daysSinceStart} of 21</span>
                <span>{daysRemaining} days remaining</span>
              </div>
              <div className="w-full bg-[var(--bg-tertiary)] rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-[var(--accent)] h-full rounded-full transition-all duration-500"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">

      {/* Controls */}
      <div className="flex items-center justify-end gap-3 mb-8">
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] text-sm font-mono focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
        >
          <option value={168}>7 days</option>
          <option value={336}>14 days</option>
          <option value={504}>21 days</option>
          <option value={720}>30 days</option>
        </select>

        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] hover:border-[var(--border-hover)] rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span className="font-sans text-sm">Refresh</span>
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-8 p-4 bg-[var(--ember)]/10 border border-[var(--ember)]/50 rounded-xl text-[var(--ember)]">
          <span className="font-sans text-sm">{error}</span>
        </div>
      )}

      {/* Loading */}
      {loading && !data && (
        <div className="flex items-center justify-center h-96">
          <RefreshCw className="h-6 w-6 animate-spin text-[var(--accent)]" />
        </div>
      )}

      {/* Live Rankings */}
      {!loading && data && rankedBots.length > 0 && (
        <div className="bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-display text-xl text-[var(--text-primary)]">Live Rankings</h2>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-[var(--ember)] rounded-full animate-pulse" />
              <span className="text-xs font-mono text-[var(--text-muted)] uppercase tracking-wider">Live</span>
            </div>
          </div>
          <div className="space-y-2">
            {rankedBots.map((bot, index) => {
              const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
              const isPositive = pnlPercent >= 0

              return (
                <div
                  key={bot.config_id}
                  className={`flex items-center gap-4 p-3 rounded-lg transition-colors ${
                    index < 3 ? 'bg-[var(--accent)]/5 border border-[var(--accent)]/20' : 'bg-[var(--bg-tertiary)]'
                  }`}
                >
                  <div className="w-8 text-center">
                    <span className={`font-mono text-sm ${
                      index === 0 ? 'text-[var(--accent)] font-semibold' :
                      index < 3 ? 'text-[var(--accent)]/70' :
                      'text-[var(--text-muted)]'
                    }`}>
                      {index + 1}
                    </span>
                  </div>
                  {bot.profile_image_url ? (
                    <img
                      src={bot.profile_image_url}
                      alt={bot.config_name}
                      className="w-9 h-9 rounded-full border border-[var(--border)] object-cover"
                    />
                  ) : (
                    <div className="w-9 h-9 rounded-full border border-[var(--border)] flex items-center justify-center bg-[var(--bg-primary)]">
                      <Bot className="h-4 w-4 text-[var(--text-muted)]" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <span className="font-sans text-sm text-[var(--text-primary)]">{bot.config_name}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-sm text-[var(--text-primary)]">{formatCurrency(bot.current_equity)}</div>
                    <div className={`text-xs font-mono ${isPositive ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
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
        <div className="bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] p-6 mb-8">
          <h2 className="font-display text-xl text-[var(--text-primary)] mb-6">Equity Over Time</h2>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
              <XAxis
                dataKey="timestamp"
                stroke="var(--text-muted)"
                tickFormatter={formatTimestamp}
                tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
                axisLine={{ stroke: 'var(--border)' }}
              />
              <YAxis
                stroke="var(--text-muted)"
                tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
                tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
                axisLine={{ stroke: 'var(--border)' }}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-primary)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px'
                }}
                labelFormatter={formatTimestamp}
                formatter={(value: number) => [formatCurrency(value), '']}
              />
              <Legend
                wrapperStyle={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)', fontSize: '12px' }}
                iconType="line"
              />
              {data.bots.map((bot, index) => (
                <Line
                  key={bot.config_id}
                  type="monotone"
                  dataKey={bot.config_name}
                  stroke={BOT_COLORS[index % BOT_COLORS.length]}
                  strokeWidth={1.5}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {data.bots.map((bot) => {
            const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
            const isPositive = pnlPercent >= 0
            const description = BOT_DESCRIPTIONS[bot.config_name]

            return (
              <div
                key={bot.config_id}
                className="bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] p-5 hover:border-[var(--border-hover)] transition-colors"
              >
                {/* Bot header */}
                <div className="flex items-start gap-3 mb-4">
                  {bot.profile_image_url ? (
                    <img
                      src={bot.profile_image_url}
                      alt={bot.config_name}
                      className="w-11 h-11 rounded-full border border-[var(--border)] object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-11 h-11 rounded-full border border-[var(--border)] flex items-center justify-center bg-[var(--bg-tertiary)] flex-shrink-0">
                      <Bot className="h-5 w-5 text-[var(--text-muted)]" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-sans text-[var(--text-primary)] font-medium truncate">{bot.config_name}</h3>
                    {description && (
                      <div className="text-xs text-[var(--text-muted)] font-mono">
                        {description.frequency} · {description.symbol}
                      </div>
                    )}
                  </div>
                </div>

                {/* Strategy tagline */}
                {description && (
                  <p className="text-sm text-[var(--text-secondary)] mb-4 leading-relaxed line-clamp-2">
                    &ldquo;{description.tagline}&rdquo;
                  </p>
                )}

                {/* Equity and P&L */}
                <div className="mb-4">
                  <div className="flex items-baseline justify-between">
                    <span className="font-mono text-xl text-[var(--text-primary)]">
                      {formatCurrency(bot.current_equity)}
                    </span>
                    <span className={`font-mono text-sm ${isPositive ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
                      {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                    </span>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3 pt-4 border-t border-[var(--border)]">
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-0.5">Trades</p>
                    <p className="font-mono text-sm text-[var(--text-primary)]">{bot.total_trades}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-0.5">Win Rate</p>
                    <p className="font-mono text-sm text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-0.5">Open</p>
                    <p className="font-mono text-sm text-[var(--text-primary)]">{bot.open_positions}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* CTA Section */}
      {!loading && data && (
        <div className="mt-16 mb-8 py-12 px-8 text-center border-t border-[var(--border)]">
          <p className="text-xs font-mono uppercase tracking-widest text-[var(--accent)] mb-4">Coming Soon</p>
          <h2 className="font-display text-3xl md:text-4xl text-[var(--text-primary)] mb-4">
            Season 1 Opens January 15, 2025
          </h2>
          <p className="font-sans text-[var(--text-secondary)] mb-8 max-w-xl mx-auto leading-relaxed">
            Create your own trading bot and compete for prizes. Watch these archetypes battle,
            then design your strategy and enter the arena.
          </p>
          <a
            href="https://ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0b0b0c] font-medium rounded-lg transition-colors"
          >
            <span className="font-sans">Create Your Bot</span>
            <span className="text-lg">→</span>
          </a>
        </div>
      )}

      </div>
    </div>
  )
}
