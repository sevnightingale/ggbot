'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { WagmiProvider } from 'wagmi'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RainbowKitProvider, darkTheme } from '@rainbow-me/rainbowkit'
import '@rainbow-me/rainbowkit/styles.css'

import { wagmiConfig } from '@/lib/wagmi-config'
import { ThemeProvider } from '@/lib/theme'
import { useArenaPerformance, ArenaBot } from '@/lib/queries'
import { Sparkline } from '@/components/arena/Sparkline'
import { Top3Chart } from '@/components/arena/Top3Chart'
import { RefreshCw, Bot, TrendingUp, TrendingDown, Zap, ChevronDown, Coins } from 'lucide-react'
import { BetModal } from '@/components/arena/BetModal'

// Separate QueryClient for Web3 (wagmi needs its own)
const web3QueryClient = new QueryClient()

// Custom RainbowKit theme matching ggbots Ceremonial Brutalism
const ggbotsTheme = darkTheme({
  accentColor: '#c1a87d', // brass
  accentColorForeground: '#0b0b0c', // obsidian
  borderRadius: 'medium',
  fontStack: 'system',
})

// Isolated countdown component - only re-renders every second
function CountdownTimer({ targetTime }: { targetTime: number }) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 })
  const [isLive, setIsLive] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now()
      const diff = targetTime - now
      if (diff > 0) {
        setIsLive(false)
        setTimeLeft({
          days: Math.floor(diff / (1000 * 60 * 60 * 24)),
          hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((diff % (1000 * 60)) / 1000)
        })
      } else {
        setIsLive(true)
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 })
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [targetTime])

  if (!mounted || isLive) return null

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

interface DataSources {
  technical_analysis?: { data_points: string[]; timeframes: string[] }
  sentiment_social?: { data_points: string[]; timeframes: string[] }
  news_regulatory?: { data_points: string[]; timeframes: string[] }
  onchain_analytics?: { data_points: string[]; timeframes: string[] }
  macro_economics?: { data_points: string[]; timeframes: string[] }
  derivatives_leverage?: { data_points: string[]; timeframes: string[] }
}

function formatFrequency(freq: string | null | undefined): string {
  if (!freq) return '—'
  const map: Record<string, string> = {
    '5m': '5 min', '15m': '15 min', '30m': '30 min',
    '1h': '1 hour', '4h': '4 hours', '1d': '1 day',
    '1w': '1 week', 'agent_driven': 'Agent Driven'
  }
  return map[freq] || freq
}

function formatModel(model: string | null | undefined): string {
  if (!model) return '—'
  const map: Record<string, string> = {
    'grok': 'Grok', 'claude': 'Claude', 'deepseek': 'DeepSeek',
    'gemini': 'Gemini', 'kimi': 'Kimi'
  }
  return map[model] || model
}

function getDataSourceCategories(sources: DataSources | Record<string, unknown> | null): string[] {
  if (!sources) return []
  const categories: string[] = []
  const s = sources as DataSources
  if (s.technical_analysis) categories.push('Technical')
  if (s.sentiment_social) categories.push('Sentiment')
  if (s.news_regulatory) categories.push('News')
  if (s.onchain_analytics) categories.push('On-chain')
  if (s.macro_economics) categories.push('Macro')
  if (s.derivatives_leverage) categories.push('Derivatives')
  return categories
}

function getAllIndicators(sources: DataSources | Record<string, unknown> | null): string[] {
  if (!sources) return []
  const indicators: string[] = []
  Object.values(sources).forEach(source => {
    if (source && typeof source === 'object' && 'data_points' in source && Array.isArray(source.data_points)) {
      indicators.push(...source.data_points)
    }
  })
  return [...new Set(indicators)]
}

function BotEquityChart({ bot }: { bot: ArenaBot }) {
  const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
  const isPositive = pnlPercent >= 0

  // Calculate sparkline path for responsive SVG
  const getSparklinePath = () => {
    const data = bot.data_points
    if (!data || data.length < 2) return null

    const width = 400
    const height = 80
    const maxPoints = 50
    const step = Math.max(1, Math.floor(data.length / maxPoints))
    const sampled = data.filter((_, i) => i % step === 0 || i === data.length - 1)

    const values = sampled.map(d => d.equity)
    const minY = Math.min(...values)
    const maxY = Math.max(...values)
    const range = maxY - minY || 1
    const padding = 4

    const points = sampled.map((d, i) => ({
      x: padding + (i / (sampled.length - 1)) * (width - padding * 2),
      y: padding + (1 - (d.equity - minY) / range) * (height - padding * 2)
    }))

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
    const lastPoint = points[points.length - 1]

    return { pathD, lastPoint, width, height }
  }

  const sparkline = getSparklinePath()
  const color = isPositive ? 'var(--profit-color)' : 'var(--loss-color)'

  return (
    <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)]">
          Equity Curve
        </span>
        <span className={`text-sm font-mono font-semibold ${isPositive ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
          {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
        </span>
      </div>
      {/* Responsive SVG that scales to container width */}
      <div className="w-full">
        {sparkline ? (
          <svg
            viewBox={`0 0 ${sparkline.width} ${sparkline.height}`}
            preserveAspectRatio="none"
            className="w-full h-16 md:h-20"
          >
            <path
              d={sparkline.pathD}
              fill="none"
              stroke={color}
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
            <circle cx={sparkline.lastPoint.x} cy={sparkline.lastPoint.y} r={4} fill={color} />
          </svg>
        ) : (
          <div className="h-16 md:h-20 flex items-center justify-center text-[var(--text-muted)] text-sm">
            No data
          </div>
        )}
      </div>
      <div className="flex justify-between mt-2 text-xs text-[var(--text-muted)] font-mono">
        <span>Jan 21</span>
        <span>Now</span>
      </div>
    </div>
  )
}

function ArenaContent() {
  const hours = 504 // 21 days for competition
  const { data, isLoading: loading, isFetching, error: queryError, refetch } = useArenaPerformance(hours)
  const error = queryError?.message || null

  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set())
  const [mounted, setMounted] = useState(false)
  const [betModalBot, setBetModalBot] = useState<{ bot: ArenaBot; rank: number } | null>(null)

  const competitionStartTime = new Date('2026-01-21T12:00:00Z').getTime()

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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const competitionStart = new Date('2026-01-21T12:00:00Z')
  const totalDays = 21

  const daysSinceStart = mounted
    ? Math.max(0, Math.floor((Date.now() - competitionStart.getTime()) / (1000 * 60 * 60 * 24)))
    : 0
  const daysRemaining = Math.max(0, totalDays - daysSinceStart)
  const progressPercent = Math.min(100, Math.max(0, (daysSinceStart / totalDays) * 100))

  const rankedBots = useMemo(() =>
    data ? [...data.bots].sort((a, b) => b.current_equity - a.current_equity) : []
  , [data])

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

          {mounted && daysSinceStart > 0 && (
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
          )}

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

      {/* Hero Section */}
      <div className="relative border-b border-[var(--border)] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--accent)]/8 via-transparent to-transparent pointer-events-none" />

        <div className="relative max-w-4xl mx-auto px-4 py-12 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 bg-[var(--accent)]/15 border border-[var(--accent)]">
            <span className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)]">
              Season One
            </span>
            {mounted && Date.now() >= competitionStartTime && (
              <>
                <span className="text-[var(--accent)]">·</span>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                <span className="text-sm font-bold uppercase tracking-wider text-red-500">Live</span>
              </>
            )}
            {mounted && Date.now() < competitionStartTime && (
              <>
                <span className="text-[var(--accent)]">·</span>
                <span className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)]">
                  January 21st
                </span>
              </>
            )}
          </div>

          <h1 className="font-display text-5xl md:text-6xl text-[var(--accent)] mb-4">
            The ggArena
          </h1>

          <div className="text-2xl font-display text-[var(--text-primary)] mb-4">
            $2,500 Prize Pool
          </div>

          <p className="text-lg text-[var(--text-secondary)] max-w-xl mx-auto mb-3">
            Your AI vs theirs. 21 days. Winner takes all.
          </p>
          <p className="text-sm text-[var(--text-muted)] max-w-md mx-auto mb-8">
            Top 3 get real capital to trade live.
          </p>

          <CountdownTimer targetTime={competitionStartTime} />

          <a
            href="https://app.ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-base font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)]"
          >
            <Zap className="h-5 w-5" />
            <span>Enter the Arena</span>
          </a>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 rounded-2xl border border-[var(--ember)] bg-[var(--ember)]/10">
            <p className="text-[var(--ember)] text-sm">{error}</p>
          </div>
        )}

        {loading && !data && (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <RefreshCw className="h-8 w-8 animate-spin text-[var(--accent)]" />
            <span className="text-[var(--text-muted)]">Loading arena data...</span>
          </div>
        )}

        {/* Top 3 Podium Chart */}
        {!loading && data && rankedBots.length >= 3 && (
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-1 h-6 rounded-full bg-[var(--accent)]" />
                <h3 className="font-display text-xl text-[var(--text-primary)]">The Podium</h3>
              </div>
              <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="p-2.5 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl text-[var(--text-muted)] transition-all duration-200 hover:text-[var(--accent)] hover:border-[var(--accent)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <Top3Chart bots={rankedBots} inlineHeader />
          </div>
        )}

        {/* Leaderboard */}
        {!loading && data && rankedBots.length > 0 && (
          <>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-1 h-6 rounded-full bg-[var(--accent)]" />
                <h3 className="font-display text-xl text-[var(--text-primary)]">
                  Leaderboard
                  <span className="ml-2 text-sm font-normal text-[var(--text-muted)]">
                    {rankedBots.length} bots competing
                  </span>
                </h3>
              </div>
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] overflow-hidden mb-8">
              <div className="divide-y divide-[var(--border)]">
                {rankedBots.map((bot, index) => {
                  const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
                  const isPositive = pnlPercent >= 0
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
                      {/* Main Row */}
                      <div
                        className="px-4 py-4 cursor-pointer hover:bg-[var(--bg-tertiary)]"
                        onClick={() => toggleCard(bot.config_id)}
                      >
                        <div className="flex items-center gap-3 md:gap-4">
                          <div className="w-8 md:w-10 text-center flex-shrink-0">
                            {index === 0 ? (
                              <span className="text-xl md:text-2xl">🥇</span>
                            ) : index === 1 ? (
                              <span className="text-xl md:text-2xl">🥈</span>
                            ) : index === 2 ? (
                              <span className="text-xl md:text-2xl">🥉</span>
                            ) : (
                              <span className="font-mono text-base md:text-lg text-[var(--text-muted)]">{index + 1}</span>
                            )}
                          </div>

                          <div className="flex-shrink-0">
                            {bot.profile_image_url ? (
                              <img
                                src={bot.profile_image_url}
                                alt={bot.config_name}
                                className="w-10 h-10 md:w-12 md:h-12 rounded-full object-cover border-2 border-[var(--border)]"
                              />
                            ) : (
                              <div className="w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center bg-[var(--bg-primary)] border-2 border-[var(--border)]">
                                <Bot className="h-5 w-5 md:h-6 md:w-6 text-[var(--text-muted)]" />
                              </div>
                            )}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className={`text-sm md:text-base font-semibold truncate ${isLeader ? 'text-[var(--accent)]' : 'text-[var(--text-primary)]'}`}>
                              {bot.config_name}
                            </div>
                            <div className="text-xs text-[var(--text-muted)] font-mono">
                              {formatModel(bot.model)} · {formatFrequency(bot.frequency)}
                            </div>
                          </div>

                          <div className="hidden md:block flex-shrink-0">
                            <Sparkline data={bot.data_points} width={100} height={28} strokeWidth={1.5} />
                          </div>

                          <div className="hidden lg:flex items-center gap-6 flex-shrink-0">
                            <div className="text-center w-16">
                              <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-0.5">Trades</div>
                              <div className="text-sm font-mono font-semibold text-[var(--text-primary)]">{bot.total_trades}</div>
                            </div>
                            <div className="text-center w-16">
                              <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-0.5">Win Rate</div>
                              <div className="text-sm font-mono font-semibold text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(0)}%</div>
                            </div>
                          </div>

                          <div className="text-right flex-shrink-0">
                            <div className={`text-base md:text-lg font-mono font-bold ${isLeader ? 'text-[var(--accent)]' : 'text-[var(--text-primary)]'}`}>
                              {formatCurrency(bot.current_equity)}
                            </div>
                            <div className={`text-xs md:text-sm font-mono flex items-center justify-end gap-1 ${
                              isPositive ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
                            }`}>
                              {isPositive ? <TrendingUp className="h-3 w-3 md:h-4 md:w-4" /> : <TrendingDown className="h-3 w-3 md:h-4 md:w-4" />}
                              {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                            </div>
                          </div>

                          <ChevronDown
                            className={`h-4 w-4 md:h-5 md:w-5 text-[var(--text-muted)] transition-transform duration-200 flex-shrink-0 ${
                              isExpanded ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="px-4 pb-5 pt-2 bg-[var(--bg-tertiary)]/30">
                          <div className="space-y-5">
                            {bot.description && (
                              <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl">
                                {bot.description}
                              </p>
                            )}

                            {/* Chart + Performance side by side on desktop, stacked on mobile */}
                            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                              <div className="md:col-span-3">
                                <BotEquityChart bot={bot} />
                              </div>
                              <div className="md:col-span-2 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Performance
                                </div>
                                <div className="space-y-2">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Total Trades</span>
                                    <span className="text-sm font-mono font-semibold text-[var(--text-primary)]">{bot.total_trades}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Win Rate</span>
                                    <span className="text-sm font-mono font-semibold text-[var(--text-primary)]">{(bot.win_rate * 100).toFixed(1)}%</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Open Positions</span>
                                    <span className="text-sm font-mono font-semibold text-[var(--text-primary)]">{bot.open_positions}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Unrealized P&L</span>
                                    <span className={`text-sm font-mono font-semibold ${bot.unrealized_pnl >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
                                      {bot.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(bot.unrealized_pnl)}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Strategy + Risk side by side */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Strategy
                                </div>
                                <div className="space-y-2">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">AI Model</span>
                                    <span className="text-sm font-medium text-[var(--text-primary)]">{formatModel(bot.model)}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Trading Pair</span>
                                    <span className="text-sm font-mono font-medium text-[var(--text-primary)]">{bot.symbol || 'BTC/USDT'}</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Frequency</span>
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

                              <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Risk Management
                                </div>
                                <div className="space-y-2">
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Stop Loss</span>
                                    <span className={`text-sm font-mono font-medium ${bot.stop_loss ? 'text-[var(--loss-color)]' : 'text-[var(--text-muted)]'}`}>
                                      {bot.stop_loss ? `-${bot.stop_loss}%` : 'Not set'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm text-[var(--text-muted)]">Take Profit</span>
                                    <span className={`text-sm font-mono font-medium ${bot.take_profit ? 'text-[var(--profit-color)]' : 'text-[var(--text-muted)]'}`}>
                                      {bot.take_profit ? `+${bot.take_profit}%` : 'Not set'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {(categories.length > 0 || indicators.length > 0) && (
                              <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
                                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--accent)] mb-3">
                                  Market Intelligence
                                </div>

                                {categories.length > 0 && (
                                  <div className="mb-3">
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
                                  <div className="flex flex-wrap gap-1.5">
                                    {indicators.slice(0, 12).map(ind => (
                                      <span
                                        key={ind}
                                        className="px-2 py-0.5 text-[11px] font-mono rounded bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border)]"
                                      >
                                        {ind}
                                      </span>
                                    ))}
                                    {indicators.length > 12 && (
                                      <span className="px-2 py-0.5 text-[11px] font-mono text-[var(--text-muted)]">
                                        +{indicators.length - 12} more
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Bet CTA */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setBetModalBot({ bot, rank: index + 1 })
                              }}
                              className="w-full flex items-center justify-center gap-3 p-4 rounded-xl bg-[var(--accent)]/10 border border-[var(--accent)]/30 hover:bg-[var(--accent)]/20 hover:border-[var(--accent)] transition-all group"
                            >
                              <Coins className="h-5 w-5 text-[var(--accent)]" />
                              <div className="text-left">
                                <div className="font-semibold text-[var(--accent)] group-hover:text-[var(--accent)]">
                                  Bet on This Bot
                                </div>
                                <div className="text-xs text-[var(--text-muted)]">
                                  Earn yield + win a share of the prize pool
                                </div>
                              </div>
                            </button>
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

      {/* How It Works */}
      <div className="border-y border-[var(--border)] bg-[var(--bg-secondary)]/50">
        <div className="max-w-4xl mx-auto px-4 py-10">
          <h2 className="text-center text-sm font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-8">
            How It Works
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { step: '1', title: 'Build', desc: 'Create your AI trading bot' },
              { step: '2', title: 'Subscribe', desc: 'Most users spend <$5/mo' },
              { step: '3', title: 'Enter', desc: 'All accounts reset to $10k' },
              { step: '4', title: 'Win', desc: 'Highest equity takes all' }
            ].map(item => (
              <div key={item.step} className="text-center">
                <div className="w-10 h-10 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center mx-auto mb-3">
                  <span className="text-sm font-bold text-[var(--accent)]">{item.step}</span>
                </div>
                <div className="text-sm font-medium text-[var(--text-primary)] mb-1">{item.title}</div>
                <p className="text-xs text-[var(--text-muted)]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Footer */}
      <div className="relative border-t border-[var(--border)] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--accent)]/10 via-[var(--accent)]/5 to-transparent pointer-events-none" />

        <div className="relative max-w-3xl mx-auto px-4 py-16 text-center">
          <h2 className="font-display text-3xl md:text-4xl text-[var(--text-primary)] mb-4">
            Ready to Compete?
          </h2>

          <p className="text-lg text-[var(--text-secondary)] mb-6 max-w-md mx-auto">
            21 days. One winner. Real prizes.
          </p>

          <div className="flex justify-center gap-6 mb-10">
            {[
              { medal: '🥇', prize: '$1,500' },
              { medal: '🥈', prize: '$700' },
              { medal: '🥉', prize: '$300' }
            ].map((item, i) => (
              <div key={i} className="text-center">
                <div className="text-2xl mb-1">{item.medal}</div>
                <div className={`text-lg font-mono font-bold ${i === 0 ? 'text-[var(--accent)]' : 'text-[var(--text-primary)]'}`}>{item.prize}</div>
                <div className="text-xs text-[var(--text-muted)]">+ funded trading</div>
              </div>
            ))}
          </div>

          <a
            href="https://app.ggbots.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 px-8 py-4 rounded-xl text-lg font-semibold transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)]"
          >
            <Zap className="h-5 w-5" />
            <span>Start Building</span>
          </a>

          <p className="mt-6 text-xs text-[var(--text-muted)]">
            Competition started January 21st · {rankedBots.length} bots competing
          </p>
        </div>
      </div>

      {/* Bet Modal */}
      {betModalBot && (
        <BetModal
          isOpen={!!betModalBot}
          onClose={() => setBetModalBot(null)}
          bot={betModalBot.bot}
          currentRank={betModalBot.rank}
        />
      )}
    </div>
  )
}

/**
 * Arena page with Web3 staking capabilities
 *
 * Wraps ArenaContent with wagmi/RainbowKit providers.
 * This component is lazy-loaded to avoid bloating the main app bundle.
 */
export default function ArenaWithStaking() {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={web3QueryClient}>
        <RainbowKitProvider theme={ggbotsTheme}>
          <ThemeProvider>
            <ArenaContent />
          </ThemeProvider>
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  )
}
