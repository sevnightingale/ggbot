'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import {
  RefreshCw, ArrowLeft, DollarSign, Users, TrendingUp, Target,
  BarChart3, Zap, AlertCircle
} from 'lucide-react'
import Link from 'next/link'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts'

// ─── Types ───────────────────────────────────────────────────────────────────

interface RevenueMonthly {
  month: string
  llm_calls: number
  revenue: number
  cost: number
  margin: number
  paying_users: number
}

interface Analytics {
  revenue: {
    monthly: RevenueMonthly[]
    total: number
    total_cost: number
    total_margin: number
    margin_pct: number
    mtd: number
    mtd_projected: number
    mtd_paying_users: number
    last_30d: number
    last_30d_users: number
  }
  funnel: {
    total_users: number
    created_bot: number
    created_bot_pct: number
    ran_bot: number
    ran_bot_pct: number
    active_bot: number
    active_bot_pct: number
    paid: number
    paid_pct: number
  }
  cohorts: {
    monthly: Array<{ month: string; signups: number; paid: number; conversion_pct: number }>
    total_signups: number
    total_paid: number
    conversion_pct: number
  }
  engagement: {
    dau: number
    wau: number
    mau: number
    dau_wau_pct: number
    dau_mau_pct: number
    power_users: number
  }
  retention: {
    cohort_size: number
    active_7d: number
    active_7d_pct: number
    active_30d: number
    active_30d_pct: number
  }
  ltv: {
    by_tier: Array<{ tier: string; users: number; total_revenue: number; avg_ltv: number; max_ltv: number }>
    avg_all: number
    total_paid_users: number
  }
  live_trading: {
    hl_connected: number
    hl_active_bots: number
    total_trades: number
    closed_trades: number
    total_pnl: number
    total_volume: number
  }
  growth: Array<{ month: string; signups: number }>
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (n: number) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', minimumFractionDigits: 2
}).format(n)

const fmtShort = (n: number) => {
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`
  return `$${n.toFixed(0)}`
}

const fmtNum = (n: number) => new Intl.NumberFormat('en-US').format(n)

const shortMonth = (m: string) => {
  const [, month] = m.split('-')
  const names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return names[parseInt(month)] || m
}

const TOOLTIP_STYLE = {
  contentStyle: { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' },
  labelStyle: { color: '#9ca3af' },
  itemStyle: { color: '#e5e7eb' },
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) { setError('Not authenticated'); return }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${baseUrl}/api/v2/admin/analytics`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to fetch analytics')
      }

      const json = await res.json()
      setData(json.analytics)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-red-400">{error}</span>
          <button onClick={fetchData} className="ml-auto px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded text-red-400 text-sm">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-gray-500 hover:text-white transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-2xl font-bold text-white">Business Analytics</h1>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-charcoal-800 hover:bg-charcoal-700 rounded-lg text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {loading && !data ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse h-32 bg-charcoal-900 rounded-lg border border-charcoal-700" />
          ))}
        </div>
      ) : data && (
        <>
          {/* ── Revenue KPI Cards ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <KpiCard icon={<DollarSign className="h-4 w-4" />} label="All-Time Revenue" value={fmt(data.revenue.total)} sub={`${data.revenue.margin_pct}% margin`} />
            <KpiCard icon={<DollarSign className="h-4 w-4" />} label="Last 30d" value={fmt(data.revenue.last_30d)} sub={`${data.revenue.last_30d_users} paying users`} />
            <KpiCard icon={<TrendingUp className="h-4 w-4" />} label="MTD (Projected)" value={fmt(data.revenue.mtd)} sub={`~${fmt(data.revenue.mtd_projected)}/mo`} />
            <KpiCard icon={<Target className="h-4 w-4" />} label="Avg LTV" value={fmt(data.ltv.avg_all)} sub={`${data.ltv.total_paid_users} paid users`} />
          </div>

          {/* ── Revenue Chart ── */}
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4 mb-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-green-400" />
              Monthly Revenue
            </h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.revenue.monthly}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" tickFormatter={shortMonth} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <YAxis tickFormatter={fmtShort} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip {...TOOLTIP_STYLE} formatter={(v: number, name: string) => [fmt(v), name === 'revenue' ? 'Revenue' : name === 'cost' ? 'Cost' : 'Margin']} labelFormatter={shortMonth} />
                <Bar dataKey="cost" stackId="a" fill="#ef4444" name="cost" radius={[0, 0, 0, 0]} />
                <Bar dataKey="margin" stackId="a" fill="#22c55e" name="margin" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* ── Funnel + Engagement Row ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Conversion Funnel */}
            <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-400" />
                Conversion Funnel
              </h2>
              <div className="space-y-3">
                <FunnelBar label="Signups" count={data.funnel.total_users} pct={100} color="bg-blue-500" />
                <FunnelBar label="Created Bot" count={data.funnel.created_bot} pct={data.funnel.created_bot_pct} color="bg-blue-400" />
                <FunnelBar label="Ran a Bot" count={data.funnel.ran_bot} pct={data.funnel.ran_bot_pct} color="bg-cyan-400" />
                <FunnelBar label="Active Bot" count={data.funnel.active_bot} pct={data.funnel.active_bot_pct} color="bg-emerald-400" />
                <FunnelBar label="Paid" count={data.funnel.paid} pct={data.funnel.paid_pct} color="bg-green-400" />
              </div>
              <div className="mt-4 pt-3 border-t border-charcoal-800 text-sm text-gray-400">
                Post-monetization (Jan+): <span className="text-white font-medium">{data.cohorts.conversion_pct}%</span> ({data.cohorts.total_paid}/{data.cohorts.total_signups})
              </div>
            </div>

            {/* Engagement */}
            <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-400" />
                Engagement
              </h2>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-white">{data.engagement.dau}</p>
                  <p className="text-sm text-gray-500">DAU</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-white">{data.engagement.wau}</p>
                  <p className="text-sm text-gray-500">WAU</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-white">{data.engagement.mau}</p>
                  <p className="text-sm text-gray-500">MAU</p>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">DAU/WAU Stickiness</span>
                  <span className="text-white font-medium">{data.engagement.dau_wau_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">DAU/MAU Stickiness</span>
                  <span className="text-white font-medium">{data.engagement.dau_mau_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Power Users (4+/8wk)</span>
                  <span className="text-white font-medium">{data.engagement.power_users}</span>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-charcoal-800">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Retention (users 30d+ old)</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Active 7d: </span>
                    <span className="text-white">{data.retention.active_7d}/{data.retention.cohort_size} ({data.retention.active_7d_pct}%)</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Active 30d: </span>
                    <span className="text-white">{data.retention.active_30d}/{data.retention.cohort_size} ({data.retention.active_30d_pct}%)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Cohort + Growth Row ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Cohort Conversion Table */}
            <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Cohort Conversion (Jan 2026+)</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-left">
                    <th className="pb-2">Month</th>
                    <th className="pb-2 text-right">Signups</th>
                    <th className="pb-2 text-right">Paid</th>
                    <th className="pb-2 text-right">Conv %</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {data.cohorts.monthly.map(c => (
                    <tr key={c.month} className="border-t border-charcoal-800">
                      <td className="py-2">{shortMonth(c.month)}</td>
                      <td className="py-2 text-right">{c.signups}</td>
                      <td className="py-2 text-right">{c.paid}</td>
                      <td className="py-2 text-right">
                        <span className={c.conversion_pct >= 20 ? 'text-green-400' : c.conversion_pct >= 10 ? 'text-yellow-400' : 'text-gray-400'}>
                          {c.conversion_pct}%
                        </span>
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t border-charcoal-700 font-medium">
                    <td className="py-2 text-white">Total</td>
                    <td className="py-2 text-right text-white">{data.cohorts.total_signups}</td>
                    <td className="py-2 text-right text-white">{data.cohorts.total_paid}</td>
                    <td className="py-2 text-right text-green-400">{data.cohorts.conversion_pct}%</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Growth Chart */}
            <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Monthly Signups</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.growth}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" tickFormatter={shortMonth} tick={{ fill: '#9ca3af', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
                  <Tooltip {...TOOLTIP_STYLE} formatter={(v: number) => [fmtNum(v), 'Signups']} labelFormatter={shortMonth} />
                  <Bar dataKey="signups" radius={[4, 4, 0, 0]}>
                    {data.growth.map((entry, i) => (
                      <Cell key={i} fill={entry.month >= '2026-01' ? '#3b82f6' : '#6b7280'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── LTV + Live Trading Row ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* LTV by Tier */}
            <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-400" />
                Lifetime Value by Tier
              </h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-left">
                    <th className="pb-2">Tier</th>
                    <th className="pb-2 text-right">Users</th>
                    <th className="pb-2 text-right">Total Rev</th>
                    <th className="pb-2 text-right">Avg LTV</th>
                    <th className="pb-2 text-right">Max LTV</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {data.ltv.by_tier.map(t => (
                    <tr key={t.tier} className="border-t border-charcoal-800">
                      <td className="py-2 capitalize">{t.tier.replace('_', ' ')}</td>
                      <td className="py-2 text-right">{t.users}</td>
                      <td className="py-2 text-right text-green-400">{fmt(t.total_revenue)}</td>
                      <td className="py-2 text-right">{fmt(t.avg_ltv)}</td>
                      <td className="py-2 text-right">{fmt(t.max_ltv)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-3 pt-3 border-t border-charcoal-800 flex justify-between text-sm">
                <span className="text-gray-500">Overall Avg LTV</span>
                <span className="text-white font-medium">{fmt(data.ltv.avg_all)}</span>
              </div>
            </div>

            {/* Live Trading */}
            <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Zap className="h-5 w-5 text-purple-400" />
                Live Trading (Hyperliquid)
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <MetricBlock label="Connected Wallets" value={String(data.live_trading.hl_connected)} />
                <MetricBlock label="Active Bots" value={String(data.live_trading.hl_active_bots)} />
                <MetricBlock label="Total Trades" value={fmtNum(data.live_trading.total_trades)} />
                <MetricBlock label="Closed Trades" value={fmtNum(data.live_trading.closed_trades)} />
                <MetricBlock label="Total Volume" value={fmt(data.live_trading.total_volume)} />
                <MetricBlock label="Realized P&L" value={fmt(data.live_trading.total_pnl)} valueColor={data.live_trading.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'} />
              </div>
            </div>
          </div>

          {/* ── Revenue Table (detailed) ── */}
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <h2 className="text-lg font-semibold text-white mb-4">Revenue Breakdown</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-left">
                    <th className="pb-2">Month</th>
                    <th className="pb-2 text-right">LLM Calls</th>
                    <th className="pb-2 text-right">Revenue</th>
                    <th className="pb-2 text-right">Cost</th>
                    <th className="pb-2 text-right">Margin</th>
                    <th className="pb-2 text-right">Users</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {data.revenue.monthly.map(m => (
                    <tr key={m.month} className="border-t border-charcoal-800">
                      <td className="py-2">{m.month}</td>
                      <td className="py-2 text-right">{fmtNum(m.llm_calls)}</td>
                      <td className="py-2 text-right text-green-400">{fmt(m.revenue)}</td>
                      <td className="py-2 text-right text-red-400">{fmt(m.cost)}</td>
                      <td className="py-2 text-right">{fmt(m.margin)}</td>
                      <td className="py-2 text-right">{m.paying_users}</td>
                    </tr>
                  ))}
                  <tr className="border-t border-charcoal-700 font-medium text-white">
                    <td className="py-2">Total</td>
                    <td className="py-2 text-right">{fmtNum(data.revenue.monthly.reduce((s, m) => s + m.llm_calls, 0))}</td>
                    <td className="py-2 text-right text-green-400">{fmt(data.revenue.total)}</td>
                    <td className="py-2 text-right text-red-400">{fmt(data.revenue.total_cost)}</td>
                    <td className="py-2 text-right">{fmt(data.revenue.total_margin)}</td>
                    <td className="py-2 text-right">-</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Components ──────────────────────────────────────────────────────────────

function KpiCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub: string }) {
  return (
    <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
      <div className="flex items-center gap-2 text-gray-400 mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-500">{sub}</p>
    </div>
  )
}

function FunnelBar({ label, count, pct, color }: { label: string; count: number; pct: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-white">{fmtNum(count)} <span className="text-gray-500">({pct}%)</span></span>
      </div>
      <div className="h-2 bg-charcoal-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function MetricBlock({ label, value, valueColor = 'text-white' }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="bg-charcoal-800/50 rounded-lg p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-bold ${valueColor}`}>{value}</p>
    </div>
  )
}
