'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { RefreshCw, Bot, TrendingUp, TrendingDown, ExternalLink, Circle, Zap, ChevronDown } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ThemeProvider } from '@/lib/theme'

// Isolated countdown component - only this re-renders every second, not the whole page
function CountdownTimer({ targetTime }: { targetTime: number }) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 })
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now()
      const diff = targetTime - now
      if (diff > 0) {
        setTimeLeft({
          days: Math.floor(diff / (1000 * 60 * 60 * 24)),
          hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((diff % (1000 * 60)) / 1000)
        })
      } else {
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 })
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [targetTime])

  if (!mounted || (timeLeft.days + timeLeft.hours + timeLeft.minutes + timeLeft.seconds === 0)) {
    return null
  }

  return (
    <div className="flex justify-center gap-3 mb-8">
      <div className="flex flex-col items-center px-4 py-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] min-w-[70px]">
        <span className="text-2xl font-mono font-bold text-[var(--accent)]">{timeLeft.days}</span>
        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Days</span>
      </div>
      <div className="flex flex-col items-center px-4 py-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] min-w-[70px]">
        <span className="text-2xl font-mono font-bold text-[var(--text-primary)]">{String(timeLeft.hours).padStart(2, '0')}</span>
        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Hours</span>
      </div>
      <div className="flex flex-col items-center px-4 py-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] min-w-[70px]">
        <span className="text-2xl font-mono font-bold text-[var(--text-primary)]">{String(timeLeft.minutes).padStart(2, '0')}</span>
        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Min</span>
      </div>
      <div className="flex flex-col items-center px-4 py-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] min-w-[70px]">
        <span className="text-2xl font-mono font-bold text-[var(--text-primary)]">{String(timeLeft.seconds).padStart(2, '0')}</span>
        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Sec</span>
      </div>
    </div>
  )
}

interface DataPoint {
  timestamp: string
  equity: number
}

interface DataSources {
  technical_analysis?: { data_points: string[]; timeframes: string[] }
  sentiment_social?: { data_points: string[]; timeframes: string[] }
  news_regulatory?: { data_points: string[]; timeframes: string[] }
  onchain_analytics?: { data_points: string[]; timeframes: string[] }
  macro_economics?: { data_points: string[]; timeframes: string[] }
  derivatives_leverage?: { data_points: string[]; timeframes: string[] }
}

interface BotData {
  config_id: string
  config_name: string
  profile_image_url: string | null
  description: string | null
  data_points: DataPoint[]
  current_equity: number
  current_pnl: number
  initial_balance: number
  total_trades: number
  win_rate: number
  open_positions: number
  current_balance: number
  unrealized_pnl: number
  // Config details
  frequency: string | null
  model: string | null
  symbol: string | null
  data_sources: DataSources | null
  stop_loss: string | null
  take_profit: string | null
  max_margin: string | null
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

// Helper to format frequency display
function formatFrequency(freq: string | null): string {
  if (!freq) return '—'
  const map: Record<string, string> = {
    '5m': '5 min',
    '15m': '15 min',
    '30m': '30 min',
    '1h': '1 hour',
    '4h': '4 hours',
    '1d': '1 day',
    '1w': '1 week',
    'agent_driven': 'Agent Driven'
  }
  return map[freq] || freq
}

// Helper to format model name
function formatModel(model: string | null): string {
  if (!model) return '—'
  const map: Record<string, string> = {
    'grok': 'Grok',
    'claude': 'Claude',
    'deepseek': 'DeepSeek',
    'gemini': 'Gemini',
    'kimi': 'Kimi'
  }
  return map[model] || model
}

// Helper to get data source categories
function getDataSourceCategories(sources: DataSources | null): string[] {
  if (!sources) return []
  const categories: string[] = []
  if (sources.technical_analysis) categories.push('Technical')
  if (sources.sentiment_social) categories.push('Sentiment')
  if (sources.news_regulatory) categories.push('News')
  if (sources.onchain_analytics) categories.push('On-chain')
  if (sources.macro_economics) categories.push('Macro')
  if (sources.derivatives_leverage) categories.push('Derivatives')
  return categories
}

// Helper to get all indicators
function getAllIndicators(sources: DataSources | null): string[] {
  if (!sources) return []
  const indicators: string[] = []
  Object.values(sources).forEach(source => {
    if (source?.data_points) {
      indicators.push(...source.data_points)
    }
  })
  return [...new Set(indicators)] // Remove duplicates
}

function ArenaContent() {
  const [data, setData] = useState<ArenaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hours, setHours] = useState(504)
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set())
  const [mounted, setMounted] = useState(false)

  // Competition start time for countdown (static, no state needed here)
  const competitionStartTime = new Date('2026-01-21T12:00:00Z').getTime()

  // Fix hydration mismatch - only calculate date-based values on client
  useEffect(() => {
    setMounted(true)
  }, [])

  const toggleCard = (configId: string) => {
    setExpandedCards(prev => {
      const next = new Set(prev)
      if (next.has(configId)) {
        next.delete(configId)
      } else {
        next.add(configId)
      }
      return next
    })
  }

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Use relative URL to go through Next.js rewrites (avoids CORS issues)
      const response = await fetch(`/api/v2/public/arena/performance?hours=${hours}`)

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

    const timestampMap = new Map<number, Record<string, number>>()

    data.bots.forEach((bot) => {
      bot.data_points.forEach((point) => {
        const timestamp = new Date(point.timestamp).getTime()
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
    chartData.sort((a, b) => a.timestamp - b.timestamp)

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

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Memoize expensive calculations to avoid re-computing on accordion toggle
  const chartData = useMemo(() => getChartData(), [data])

  // Competition timeline - Season 1 dates (no hydration mismatch)
  const competitionStart = new Date('2026-01-21T12:00:00Z')
  const competitionEnd = new Date('2026-02-11T12:00:00Z') // 21 days later
  const totalDays = 21

  // Chart domain timestamps for fixed x-axis (static, safe for SSR)
  const chartDomainStart = competitionStart.getTime()
  const chartDomainEnd = competitionEnd.getTime()

  // Dynamic values - only calculate on client to avoid hydration mismatch
  const daysSinceStart = mounted
    ? Math.max(0, Math.floor((Date.now() - competitionStart.getTime()) / (1000 * 60 * 60 * 24)))
    : 0
  const daysRemaining = Math.max(0, totalDays - daysSinceStart)
  const progressPercent = Math.min(100, Math.max(0, (daysSinceStart / totalDays) * 100))

  // Sort bots by equity for rankings (memoized)
  const rankedBots = useMemo(() =>
    data ? [...data.bots].sort((a, b) => b.current_equity - a.current_equity) : []
  , [data])

  // Get color for a bot by its original index
  const getBotColor = (botName: string) => {
    if (!data) return BOT_COLORS[0]
    const index = data.bots.findIndex(b => b.config_name === botName)
    return BOT_COLORS[index % BOT_COLORS.length]
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header with progress bar */}
      <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur">
        <div className="relative flex items-center justify-between px-4 py-3 max-w-7xl mx-auto">
          <a href="https://ggbots.ai" className="flex items-center gap-2 z-10">
            <img
              src="https://ggbots.ai/ggbots_logo.png"
              alt="ggbots logo"
              width={28}
              height={28}
              className="h-7 w-auto"
            />
          </a>

          {/* Progress bar - absolutely centered */}
          <div className="hidden sm:flex items-center gap-3 absolute left-1/2 -translate-x-1/2 w-64">
            <span className="text-xs font-mono text-[var(--text-muted)] whitespace-nowrap">Day {daysSinceStart}</span>
            <div className="flex-1 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden border border-[var(--border)]">
              <div
                className="h-full bg-[var(--accent)] rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="text-xs font-mono text-[var(--text-muted)] whitespace-nowrap">{daysRemaining} left</span>
          </div>

          <a
            href="https://app.ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] z-10"
          >
            <Zap className="h-4 w-4" />
            <span>Create Your ggbot</span>
          </a>
        </div>
      </header>

      {/* Hero Section with brass gradient */}
      <div className="relative border-b border-[var(--border)] overflow-hidden">
        {/* Brass gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--accent)]/8 via-transparent to-transparent pointer-events-none" />

        <div className="relative max-w-4xl mx-auto px-4 py-12 text-center">
          {/* Season 1 Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 bg-[var(--accent)]/15 border border-[var(--accent)]">
            <span className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)]">
              Season 1 · January 21st
            </span>
          </div>

          <h1 className="font-display text-5xl md:text-6xl text-[var(--accent)] mb-4">
            The ggArena
          </h1>

          {/* Prize Pool */}
          <div className="text-2xl font-display text-[var(--text-primary)] mb-4">
            $2,500 Prize Pool
          </div>

          <p className="text-[var(--text-secondary)] max-w-xl mx-auto mb-8">
            Build your AI trading bot and compete against the best.
            21 days. Top 3 get funded live trading on Symphony.
          </p>

          {/* Countdown Timer - isolated component so it doesn't re-render the whole page */}
          <CountdownTimer targetTime={competitionStartTime} />

          {/* CTA Button */}
          <a
            href="https://app.ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-base font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)]"
          >
            <Zap className="h-5 w-5" />
            <span>Create Your ggbot</span>
          </a>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Error */}
        {error && (
          <div className="mb-6 p-4 rounded-2xl border border-[var(--ember)] bg-[var(--ember)]/10">
            <p className="text-[var(--ember)] text-sm">{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && !data && (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <RefreshCw className="h-8 w-8 animate-spin text-[var(--accent)]" />
            <span className="text-[var(--text-muted)]">Loading arena data...</span>
          </div>
        )}

        {/* Chart Card - First */}
        {!loading && data && chartData.length > 0 && (
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-1 h-6 rounded-full bg-[var(--accent)]" />
                <h3 className="font-display text-xl text-[var(--text-primary)]">Performance Over Time</h3>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={hours}
                  onChange={(e) => setHours(Number(e.target.value))}
                  className="px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] text-sm font-mono transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-[var(--accent)] hover:border-[var(--accent)]"
                >
                  <option value={168}>7 days</option>
                  <option value={336}>14 days</option>
                  <option value={504}>21 days</option>
                </select>
                <button
                  onClick={fetchData}
                  disabled={loading}
                  className="p-2.5 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl text-[var(--text-muted)] transition-all duration-200 hover:text-[var(--accent)] hover:border-[var(--accent)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2d" />
                <XAxis
                  dataKey="timestamp"
                  type="number"
                  domain={[chartDomainStart, chartDomainEnd]}
                  stroke="#8a8781"
                  tickFormatter={formatTimestamp}
                  tick={{ fill: '#8a8781', fontSize: 11 }}
                  axisLine={{ stroke: '#2a2a2d' }}
                  scale="time"
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
                    border: '1px solid #c1a87d',
                    borderRadius: '12px',
                    color: '#edebe7',
                    fontSize: '12px',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
                  }}
                  labelFormatter={(value: number) => formatTimestamp(value)}
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

        {/* Training Ground - Prototype Bots */}
        {!loading && data && rankedBots.length > 0 && (
          <>
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-tertiary)]/50 p-6 mb-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-1 h-6 rounded-full bg-[var(--text-muted)]" />
                <h3 className="font-display text-xl text-[var(--text-primary)]">Training Ground</h3>
              </div>
              <p className="text-[var(--text-secondary)] text-sm mb-6 max-w-2xl">
                Study these prototype bots to see what&apos;s possible. Each showcases a different trading strategy —
                from technical analysis purists to sentiment-driven contrarians. Use them as inspiration for your own build.
              </p>
            </div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1 h-6 rounded-full bg-[var(--accent)]" />
              <h3 className="font-display text-xl text-[var(--text-primary)]">The Archetypes</h3>
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] overflow-hidden mb-8">
              <div className="divide-y divide-[var(--border)]">
                {rankedBots.map((bot, index) => {
                  const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
                  const isPositive = pnlPercent >= 0
                  const color = getBotColor(bot.config_name)
                  const isLeader = index === 0
                  const isExpanded = expandedCards.has(bot.config_id)
                  const categories = getDataSourceCategories(bot.data_sources)
                  const indicators = getAllIndicators(bot.data_sources)

                  return (
                    <div
                      key={bot.config_id}
                      className={`transition-all duration-200 ${
                        isLeader ? 'bg-[var(--accent)]/10 border-l-4 border-l-[var(--accent)]' : ''
                      }`}
                    >
                      {/* Main Row - Always visible */}
                      <div
                        className="px-4 py-4 cursor-pointer hover:bg-[var(--bg-tertiary)]"
                        onClick={() => toggleCard(bot.config_id)}
                      >
                        <div className="flex items-center gap-4">
                          {/* Rank with medal for top 3 */}
                          <div className="w-10 text-center flex-shrink-0">
                            {index === 0 ? (
                              <span className="text-2xl">🥇</span>
                            ) : index === 1 ? (
                              <span className="text-2xl">🥈</span>
                            ) : index === 2 ? (
                              <span className="text-2xl">🥉</span>
                            ) : (
                              <span className="font-mono text-lg text-[var(--text-muted)]">{index + 1}</span>
                            )}
                          </div>

                          {/* Avatar with color border */}
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <Circle className="h-3 w-3" style={{ color, fill: color }} />
                            {bot.profile_image_url ? (
                              <img
                                src={bot.profile_image_url}
                                alt={bot.config_name}
                                className="w-12 h-12 rounded-full object-cover border-2"
                                style={{ borderColor: color }}
                              />
                            ) : (
                              <div
                                className="w-12 h-12 rounded-full flex items-center justify-center bg-[var(--bg-primary)] border-2"
                                style={{ borderColor: color }}
                              >
                                <Bot className="h-6 w-6 text-[var(--text-muted)]" />
                              </div>
                            )}
                          </div>

                          {/* Name + Meta */}
                          <div className="flex-1 min-w-0">
                            <div className={`text-base font-semibold ${isLeader ? 'text-[var(--accent)]' : 'text-[var(--text-primary)]'}`}>
                              {bot.config_name}
                            </div>
                            <div className="text-xs text-[var(--text-muted)] font-mono">
                              {formatFrequency(bot.frequency)} · {bot.symbol || 'BTC/USDT'}
                            </div>
                          </div>

                          {/* Stats - hidden on mobile */}
                          <div className="hidden md:flex items-center gap-8 flex-shrink-0">
                            <div className="text-center">
                              <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">Trades</div>
                              <div className="text-sm font-mono font-semibold text-[var(--text-primary)]">{bot.total_trades}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">Win Rate</div>
                              <div className="text-sm font-mono font-semibold text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(0)}%</div>
                            </div>
                          </div>

                          {/* Equity + P&L */}
                          <div className="text-right flex-shrink-0">
                            <div className={`text-lg font-mono font-bold ${isLeader ? 'text-[var(--accent)]' : 'text-[var(--text-primary)]'}`}>
                              {formatCurrency(bot.current_equity)}
                            </div>
                            <div className={`text-sm font-mono flex items-center justify-end gap-1 ${
                              isPositive ? 'text-green-500' : 'text-red-500'
                            }`}>
                              {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                              {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                            </div>
                          </div>

                          {/* Expand toggle */}
                          <ChevronDown
                            className={`h-5 w-5 text-[var(--text-muted)] transition-transform duration-200 flex-shrink-0 ${
                              isExpanded ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="px-4 pb-5 pt-2">
                          <div className="ml-14 space-y-5">
                            {/* Description */}
                            {bot.description && (
                              <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl">
                                {bot.description}
                              </p>
                            )}

                            {/* Two-column layout for Strategy + Risk */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              {/* Strategy Configuration */}
                              <div className="rounded-xl bg-[var(--bg-tertiary)]/50 p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Strategy
                                </div>
                                <div className="space-y-3">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">AI Model</span>
                                    <span className="text-sm font-medium text-[var(--text-primary)]">{formatModel(bot.model)}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Trading Pair</span>
                                    <span className="text-sm font-mono font-medium text-[var(--text-primary)]">{bot.symbol || 'BTC/USDT'}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Decision Frequency</span>
                                    <span className="text-sm font-medium text-[var(--text-primary)]">{formatFrequency(bot.frequency)}</span>
                                  </div>
                                  {bot.max_margin && (
                                    <div className="flex justify-between items-center">
                                      <span className="text-sm text-[var(--text-muted)]">Max Position</span>
                                      <span className="text-sm font-medium text-[var(--text-primary)]">{bot.max_margin}%</span>
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Risk Management */}
                              <div className="rounded-xl bg-[var(--bg-tertiary)]/50 p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Risk Management
                                </div>
                                <div className="space-y-3">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Stop Loss</span>
                                    <span className={`text-sm font-mono font-medium ${bot.stop_loss ? 'text-red-400' : 'text-[var(--text-muted)]'}`}>
                                      {bot.stop_loss ? `-${bot.stop_loss}%` : 'Not set'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Take Profit</span>
                                    <span className={`text-sm font-mono font-medium ${bot.take_profit ? 'text-green-400' : 'text-[var(--text-muted)]'}`}>
                                      {bot.take_profit ? `+${bot.take_profit}%` : 'Not set'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Open Positions</span>
                                    <span className="text-sm font-mono font-medium text-[var(--text-primary)]">{bot.open_positions}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Unrealized P&L</span>
                                    <span className={`text-sm font-mono font-medium ${bot.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                      {bot.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(bot.unrealized_pnl)}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Data Sources & Indicators */}
                            {(categories.length > 0 || indicators.length > 0) && (
                              <div className="rounded-xl bg-[var(--bg-tertiary)]/50 p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Market Intelligence
                                </div>

                                {categories.length > 0 && (
                                  <div className="mb-3">
                                    <div className="text-xs text-[var(--text-muted)] mb-2">Data Sources</div>
                                    <div className="flex flex-wrap gap-2">
                                      {categories.map(cat => (
                                        <span
                                          key={cat}
                                          className="px-3 py-1 text-xs rounded-lg bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border)]"
                                        >
                                          {cat}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {indicators.length > 0 && (
                                  <div>
                                    <div className="text-xs text-[var(--text-muted)] mb-2">
                                      Technical Indicators ({indicators.length})
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                      {indicators.slice(0, 15).map(ind => (
                                        <span
                                          key={ind}
                                          className="px-2 py-0.5 text-[11px] font-mono rounded bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border)]"
                                        >
                                          {ind}
                                        </span>
                                      ))}
                                      {indicators.length > 15 && (
                                        <span className="px-2 py-0.5 text-[11px] font-mono text-[var(--text-muted)]">
                                          +{indicators.length - 15} more
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </>
        )}
      </div>

      {/* CTA Footer with brass gradient */}
      <div className="relative border-t border-[var(--border)] overflow-hidden">
        {/* Brass gradient background */}
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--accent)]/10 via-[var(--accent)]/5 to-transparent pointer-events-none" />

        <div className="relative max-w-3xl mx-auto px-4 py-16 text-center">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--signal) 15%, transparent)',
              border: '1px solid var(--signal)'
            }}
          >
            <span className="text-sm font-semibold uppercase tracking-wider text-[var(--signal)]">
              Season 1 · January 2026
            </span>
          </div>

          <h2 className="font-display text-3xl md:text-4xl text-[var(--text-primary)] mb-4">
            Ready to Compete?
          </h2>

          <p className="text-lg text-[var(--text-secondary)] mb-10 max-w-md mx-auto">
            Build your own AI trading bot and enter the arena.
          </p>

          <a
            href="https://app.ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 px-8 py-4 rounded-xl text-lg font-semibold transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)]"
          >
            <Zap className="h-5 w-5" />
            <span>Create Your ggbot</span>
            <ExternalLink className="h-5 w-5" />
          </a>
        </div>
      </div>
    </div>
  )
}

export default function ArenaPage() {
  return (
    <ThemeProvider>
      <ArenaContent />
    </ThemeProvider>
  )
}
