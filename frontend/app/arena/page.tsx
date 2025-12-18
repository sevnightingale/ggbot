'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'
import { RefreshCw, Trophy, Bot, TrendingUp, TrendingDown, ExternalLink, Circle } from 'lucide-react'
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

// Vibrant distinct colors for chart lines
const BOT_COLORS = [
  '#c1a87d', // brass (lead)
  '#3ca6e0', // signal blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
]

// Bot descriptions from NOTE.md
const BOT_DESCRIPTIONS: Record<string, { frequency: string; symbol: string; tagline: string }> = {
  'The Technician': {
    frequency: '5min',
    symbol: 'BTC',
    tagline: 'Price is truth. A rapid-fire technical trader living in the charts.'
  },
  'The Sentinel': {
    frequency: '15min',
    symbol: 'BTC',
    tagline: 'Guards capital above all else. A conservative tactician with tight stops.'
  },
  'The Herald': {
    frequency: '30min',
    symbol: 'BTC',
    tagline: 'Markets move on narrative. Catches stories before price catches up.'
  },
  'The Contrarian': {
    frequency: '1hr',
    symbol: 'BTC',
    tagline: 'The crowd is wrong at extremes. Bets against the herd with conviction.'
  },
  'The Arbiter': {
    frequency: '4hr',
    symbol: 'BTC',
    tagline: 'Waits for the verdict. Acts only when every domain agrees.'
  },
  'The Compass': {
    frequency: '1d',
    symbol: 'BTC',
    tagline: 'Macro sets the tide. Positions for regimes, not moves.'
  },
  'The Nomad': {
    frequency: '1w',
    symbol: 'Self-Evolving',
    tagline: 'No fixed path. Learns, adapts, rewrites its own rules.'
  }
}

export default function ArenaPage() {
  const [data, setData] = useState<ArenaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hours, setHours] = useState(504)

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

  const getChartData = () => {
    if (!data || data.bots.length === 0) return []

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

    const chartData = Array.from(timestampMap.values())
    chartData.sort((a, b) => new Date(a.timestamp as string).getTime() - new Date(b.timestamp as string).getTime())

    return chartData
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const chartData = getChartData()

  // Competition timeline
  const competitionStart = new Date('2025-12-18')
  const competitionEnd = new Date('2026-01-08')
  const today = new Date()
  const daysSinceStart = Math.max(0, Math.floor((today.getTime() - competitionStart.getTime()) / (1000 * 60 * 60 * 24)))
  const totalDays = 21
  const daysRemaining = Math.max(0, totalDays - daysSinceStart)
  const progressPercent = Math.min(100, Math.max(0, (daysSinceStart / totalDays) * 100))
  const isLive = today >= competitionStart && today <= competitionEnd

  // Sort bots by equity for rankings
  const rankedBots = data ? [...data.bots].sort((a, b) => b.current_equity - a.current_equity) : []

  // Get color for a bot by its original index (consistent across rankings and chart)
  const getBotColor = (botName: string) => {
    if (!data) return BOT_COLORS[0]
    const index = data.bots.findIndex(b => b.config_name === botName)
    return BOT_COLORS[index % BOT_COLORS.length]
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header - matches Forge */}
      <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur">
        <div className="flex items-center justify-between px-4 py-3 max-w-7xl mx-auto">
          <a href="https://ggbots.ai" className="flex items-center gap-2">
            <Image
              src="/ggbots_logo.svg"
              alt="ggbots logo"
              width={28}
              height={28}
              className="h-7 w-auto"
              style={{
                filter: 'brightness(0) saturate(100%) invert(var(--logo-invert, 89%)) sepia(12%) saturate(584%) hue-rotate(200deg) brightness(95%) contrast(89%)'
              }}
            />
          </a>
          <a
            href="https://ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] transition-colors"
          >
            <span>Create Your Bot</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </header>

      {/* Hero Section */}
      <div className="border-b border-[var(--border)]">
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          {/* Live Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-6"
            style={{
              backgroundColor: isLive ? 'color-mix(in srgb, var(--ember) 15%, transparent)' : 'color-mix(in srgb, var(--accent) 15%, transparent)',
              border: `1px solid ${isLive ? 'color-mix(in srgb, var(--ember) 40%, transparent)' : 'color-mix(in srgb, var(--accent) 40%, transparent)'}`
            }}
          >
            {isLive && <Circle className="h-2 w-2 fill-[var(--ember)] text-[var(--ember)] animate-pulse" />}
            <Trophy className="h-3.5 w-3.5" style={{ color: isLive ? 'var(--ember)' : 'var(--accent)' }} />
            <span className="text-xs font-medium uppercase tracking-wider" style={{ color: isLive ? 'var(--ember)' : 'var(--accent)' }}>
              {isLive ? 'Live Competition' : 'Prototype Season'}
            </span>
          </div>

          <h1 className="font-display text-4xl md:text-5xl text-[var(--text-primary)] mb-4">
            The <span className="text-[var(--accent)]">gg</span>Arena
          </h1>

          <p className="text-[var(--text-secondary)] mb-8 max-w-lg mx-auto">
            7 AI trading archetypes compete over 21 days with $70,000 starting capital.
          </p>

          {/* Progress Bar */}
          <div className="max-w-md mx-auto">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-2">
              <span className="font-mono">Day {daysSinceStart} of {totalDays}</span>
              <span className="font-mono">{daysRemaining} days remaining</span>
            </div>
            <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden border border-[var(--border)]">
              <div
                className="h-full bg-[var(--accent)] rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Controls Row */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display text-xl text-[var(--text-primary)]">Rankings</h2>
          <div className="flex items-center gap-2">
            <select
              value={hours}
              onChange={(e) => setHours(Number(e.target.value))}
              className="px-3 py-1.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] text-sm font-mono focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            >
              <option value={168}>7 days</option>
              <option value={336}>14 days</option>
              <option value={504}>21 days</option>
            </select>
            <button
              onClick={fetchData}
              disabled={loading}
              className="p-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 rounded-2xl border"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--ember) 10%, transparent)',
              borderColor: 'color-mix(in srgb, var(--ember) 30%, transparent)'
            }}
          >
            <p className="text-[var(--ember)] text-sm">{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && !data && (
          <div className="flex items-center justify-center py-32">
            <RefreshCw className="h-6 w-6 animate-spin text-[var(--accent)]" />
          </div>
        )}

        {/* Rankings Card - matches BotRail styling */}
        {!loading && data && rankedBots.length > 0 && (
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 mb-6">
            <div className="space-y-2">
              {rankedBots.map((bot, index) => {
                const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
                const isPositive = pnlPercent >= 0
                const color = getBotColor(bot.config_name)
                const description = BOT_DESCRIPTIONS[bot.config_name]

                return (
                  <div
                    key={bot.config_id}
                    className={`rounded-xl px-4 py-3 transition-colors ${
                      index === 0 ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      {/* Rank */}
                      <div className="w-8 text-center">
                        <span className={`font-mono text-sm font-semibold ${
                          index === 0 ? 'text-[var(--accent)]' :
                          index < 3 ? 'text-[var(--text-secondary)]' :
                          'text-[var(--text-muted)]'
                        }`}>
                          {index + 1}
                        </span>
                      </div>

                      {/* Status + Avatar */}
                      <div className="flex items-center gap-2">
                        <Circle
                          className="h-2.5 w-2.5"
                          style={{ color, fill: color }}
                        />
                        {bot.profile_image_url ? (
                          <img
                            src={bot.profile_image_url}
                            alt={bot.config_name}
                            className="w-10 h-10 rounded-full object-cover border-2"
                            style={{ borderColor: color }}
                          />
                        ) : (
                          <div
                            className="w-10 h-10 rounded-full flex items-center justify-center bg-[var(--bg-primary)] border-2"
                            style={{ borderColor: color }}
                          >
                            <Bot className="h-5 w-5 text-[var(--text-muted)]" />
                          </div>
                        )}
                      </div>

                      {/* Name + Meta */}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-[var(--text-primary)]">{bot.config_name}</div>
                        {description && (
                          <div className="text-xs text-[var(--text-muted)] font-mono">
                            {description.frequency} · {description.symbol}
                          </div>
                        )}
                      </div>

                      {/* Stats - hidden on mobile */}
                      <div className="hidden sm:flex items-center gap-6">
                        <div className="text-right">
                          <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Trades</div>
                          <div className="text-sm font-mono text-[var(--text-primary)]">{bot.total_trades}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Win Rate</div>
                          <div className="text-sm font-mono text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(0)}%</div>
                        </div>
                      </div>

                      {/* Equity + P&L */}
                      <div className="text-right">
                        <div className="text-sm font-mono text-[var(--text-primary)]">{formatCurrency(bot.current_equity)}</div>
                        <div className={`text-xs font-mono flex items-center justify-end gap-1 ${
                          isPositive ? 'text-green-500' : 'text-red-500'
                        }`}>
                          {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                          {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Chart Card */}
        {!loading && data && chartData.length > 0 && (
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 mb-6">
            <h3 className="font-display text-lg text-[var(--text-primary)] mb-4">Performance</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2d" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#8a8781"
                  tickFormatter={formatTimestamp}
                  tick={{ fill: '#8a8781', fontSize: 11 }}
                  axisLine={{ stroke: '#2a2a2d' }}
                />
                <YAxis
                  stroke="#8a8781"
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  tick={{ fill: '#8a8781', fontSize: 11 }}
                  axisLine={{ stroke: '#2a2a2d' }}
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#141416',
                    border: '1px solid #2a2a2d',
                    borderRadius: '12px',
                    color: '#edebe7',
                    fontSize: '12px'
                  }}
                  labelFormatter={formatTimestamp}
                  formatter={(value: number) => [formatCurrency(value), '']}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px', color: '#d6d3ce' }}
                  iconType="circle"
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

        {/* Bot Cards Grid */}
        {!loading && data && data.bots.length > 0 && (
          <>
            <h3 className="font-display text-lg text-[var(--text-primary)] mb-4">The Archetypes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
              {data.bots.map((bot, index) => {
                const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
                const isPositive = pnlPercent >= 0
                const description = BOT_DESCRIPTIONS[bot.config_name]
                const color = BOT_COLORS[index % BOT_COLORS.length]

                return (
                  <div
                    key={bot.config_id}
                    className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 hover:border-[var(--border-hover)] transition-colors"
                  >
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-3">
                      <Circle className="h-2.5 w-2.5" style={{ color, fill: color }} />
                      {bot.profile_image_url ? (
                        <img
                          src={bot.profile_image_url}
                          alt={bot.config_name}
                          className="w-10 h-10 rounded-full object-cover border-2"
                          style={{ borderColor: color }}
                        />
                      ) : (
                        <div
                          className="w-10 h-10 rounded-full flex items-center justify-center bg-[var(--bg-tertiary)] border-2"
                          style={{ borderColor: color }}
                        >
                          <Bot className="h-5 w-5 text-[var(--text-muted)]" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-[var(--text-primary)] truncate">{bot.config_name}</div>
                        {description && (
                          <div className="text-xs text-[var(--text-muted)] font-mono">
                            {description.frequency} · {description.symbol}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Tagline */}
                    {description && (
                      <p className="text-xs text-[var(--text-secondary)] mb-3 leading-relaxed line-clamp-2">
                        {description.tagline}
                      </p>
                    )}

                    {/* Equity */}
                    <div className="flex items-baseline justify-between mb-3">
                      <span className="text-lg font-mono text-[var(--text-primary)]">
                        {formatCurrency(bot.current_equity)}
                      </span>
                      <span className={`text-sm font-mono ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                        {isPositive ? '+' : ''}{pnlPercent.toFixed(1)}%
                      </span>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-2 pt-3 border-t border-[var(--border)]">
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Trades</div>
                        <div className="text-sm font-mono text-[var(--text-primary)]">{bot.total_trades}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Win</div>
                        <div className="text-sm font-mono text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">Open</div>
                        <div className="text-sm font-mono text-[var(--text-primary)]">{bot.open_positions}</div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>

      {/* CTA Footer - Always visible */}
      <div className="border-t border-[var(--border)] bg-[var(--bg-secondary)]">
        <div className="max-w-3xl mx-auto px-4 py-12 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full mb-4"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--signal) 15%, transparent)',
              border: '1px solid color-mix(in srgb, var(--signal) 40%, transparent)'
            }}
          >
            <span className="text-xs font-medium uppercase tracking-wider text-[var(--signal)]">
              Coming January 2026
            </span>
          </div>

          <h2 className="font-display text-2xl md:text-3xl text-[var(--text-primary)] mb-4">
            Season 1 Opens Soon
          </h2>

          <p className="text-[var(--text-secondary)] mb-8 max-w-md mx-auto">
            Create your own AI trading bot and compete for prizes.
          </p>

          <a
            href="https://ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium shadow-sm ring-1 ring-inset transition bg-[var(--accent)] hover:bg-[var(--accent-hover)] ring-[var(--accent)] text-[#edebe7] dark:text-[#1a1816]"
          >
            <span>Create Your Bot</span>
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </div>
  )
}
