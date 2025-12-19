'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Bot, TrendingUp, TrendingDown, ExternalLink, Circle, Zap, ChevronDown } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ThemeProvider } from '@/lib/theme'

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
  const today = new Date()
  const daysSinceStart = Math.max(0, Math.floor((today.getTime() - competitionStart.getTime()) / (1000 * 60 * 60 * 24)))
  const totalDays = 21
  const daysRemaining = Math.max(0, totalDays - daysSinceStart)
  const progressPercent = Math.min(100, Math.max(0, (daysSinceStart / totalDays) * 100))

  // Sort bots by equity for rankings
  const rankedBots = data ? [...data.bots].sort((a, b) => b.current_equity - a.current_equity) : []

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
              src="https://ggbots.ai/ggbots_logo.svg"
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
            href="https://ggbots.ai"
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

        <div className="relative max-w-4xl mx-auto px-4 py-10 text-center">
          <h1 className="font-display text-5xl md:text-6xl text-[var(--accent)] mb-4">
            The ggArena
          </h1>

          <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
            7 AI trading agents compete in vibe trading over 21 days — each starting with $10,000.
          </p>
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
                    border: '1px solid #c1a87d',
                    borderRadius: '12px',
                    color: '#edebe7',
                    fontSize: '12px',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
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

        {/* Live Rankings with Expandable Details */}
        {!loading && data && rankedBots.length > 0 && (
          <>
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
                        <div className="px-4 pb-4 pt-0">
                          <div className="ml-14 pl-4 border-l-2 border-[var(--border)] space-y-4">
                            {/* Full Description */}
                            {bot.description && (
                              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                                {bot.description}
                              </p>
                            )}

                            {/* Config Info */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                              <div>
                                <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">Model</div>
                                <div className="text-sm font-mono text-[var(--text-primary)]">{formatModel(bot.model)}</div>
                              </div>
                              <div>
                                <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">Frequency</div>
                                <div className="text-sm font-mono text-[var(--text-primary)]">{formatFrequency(bot.frequency)}</div>
                              </div>
                              <div>
                                <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">Stop Loss</div>
                                <div className="text-sm font-mono text-[var(--text-primary)]">{bot.stop_loss ? `${bot.stop_loss}%` : '—'}</div>
                              </div>
                              <div>
                                <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-1">Take Profit</div>
                                <div className="text-sm font-mono text-[var(--text-primary)]">{bot.take_profit ? `${bot.take_profit}%` : '—'}</div>
                              </div>
                            </div>

                            {/* Data Sources */}
                            {categories.length > 0 && (
                              <div>
                                <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Data Sources</div>
                                <div className="flex flex-wrap gap-1.5">
                                  {categories.map(cat => (
                                    <span
                                      key={cat}
                                      className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
                                    >
                                      {cat}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Indicators */}
                            {indicators.length > 0 && (
                              <div>
                                <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">
                                  Indicators ({indicators.length})
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {indicators.slice(0, 12).map(ind => (
                                    <span
                                      key={ind}
                                      className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-[var(--bg-primary)] text-[var(--text-muted)]"
                                    >
                                      {ind}
                                    </span>
                                  ))}
                                  {indicators.length > 12 && (
                                    <span className="px-1.5 py-0.5 text-[10px] font-mono text-[var(--text-muted)]">
                                      +{indicators.length - 12} more
                                    </span>
                                  )}
                                </div>
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
            href="https://ggbots.ai"
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
