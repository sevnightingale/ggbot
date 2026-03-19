'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { RefreshCw, Users, Bot, DollarSign, Activity, Server, Database, AlertCircle, ChevronRight, TrendingUp } from 'lucide-react'
import Link from 'next/link'

interface PlatformStats {
  users: {
    total: number
    pro: number
    prepaid: number
    usage_based: number
    free: number
    active_subscribers: number
  }
  bots: {
    total: number
    active: number
    inactive: number
    users_with_bots: number
    by_mode: Record<string, number>
  }
  trading: {
    total_trades: number
    win_trades: number
    loss_trades: number
    win_rate: number
    total_pnl: number
    trades_24h: number
    trades_7d: number
  }
  positions: {
    open: number
    total_exposure: number
    unrealized_pnl: number
  }
  health: {
    decisions_last_hour: number
    status: string
  }
}

interface ServiceInfo {
  pm2_services: Array<{
    name: string
    status: string
    cpu: number
    memory_mb: number
    uptime: string
    restarts: number
  }>
  vm: {
    disk?: { total: string; used: string; available: string; percent: string }
    memory?: { total: string; used: string; free: string }
    cpu_load?: { '1m': string; '5m': string; '15m': string }
  }
  redis: {
    status: string
    memory: string
  }
}

interface BillingInfo {
  period: string
  provider_cost: number
  platform_cost: number
  markup_earned: number
  unreported_count: number
  unreported_amount: number
  last_report_time: string | null
  total_input_tokens: number
  total_output_tokens: number
}

interface LogSummary {
  INFO: number
  WARNING: number
  ERROR: number
  CRITICAL: number
  total: number
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [services, setServices] = useState<ServiceInfo | null>(null)
  const [billing, setBilling] = useState<BillingInfo | null>(null)
  const [logs, setLogs] = useState<LogSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

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

      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // Fetch all data in parallel
      const [statsRes, servicesRes, billingRes, logsRes] = await Promise.all([
        fetch(`${baseUrl}/api/v2/admin/stats`, { headers }),
        fetch(`${baseUrl}/api/v2/admin/services`, { headers }),
        fetch(`${baseUrl}/api/v2/admin/billing`, { headers }),
        fetch(`${baseUrl}/api/v2/admin/logs/summary?hours=24`, { headers })
      ])

      if (!statsRes.ok) {
        const errData = await statsRes.json()
        throw new Error(errData.detail || 'Failed to fetch stats')
      }

      const [statsData, servicesData, billingData, logsData] = await Promise.all([
        statsRes.json(),
        servicesRes.json(),
        billingRes.json(),
        logsRes.json()
      ])

      setStats(statsData.stats)
      setServices(servicesData.services)
      setBilling(billingData.billing)
      setLogs(logsData.logs)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value)
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-red-400">{error}</span>
          <button
            onClick={fetchData}
            className="ml-auto px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded text-red-400 text-sm"
          >
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
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
          {lastRefresh && (
            <p className="text-sm text-gray-500">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          )}
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

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={<Users className="h-5 w-5" />}
          label="Users"
          value={stats?.users.total ?? '-'}
          subtext={`${stats?.users.active_subscribers ?? 0} subscribers`}
          loading={loading}
        />
        <StatCard
          icon={<Bot className="h-5 w-5" />}
          label="Active Bots"
          value={stats?.bots.active ?? '-'}
          subtext={`${stats?.bots.total ?? 0} total`}
          loading={loading}
        />
        <StatCard
          icon={<DollarSign className="h-5 w-5" />}
          label="Total P&L"
          value={stats ? formatCurrency(stats.trading.total_pnl) : '-'}
          subtext={`${stats?.trading.win_rate ?? 0}% win rate`}
          loading={loading}
          valueColor={stats && stats.trading.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}
        />
        <StatCard
          icon={<Activity className="h-5 w-5" />}
          label="Health"
          value={stats?.health.status === 'healthy' ? 'Healthy' : 'Low Activity'}
          subtext={`${stats?.health.decisions_last_hour ?? 0} decisions/hr`}
          loading={loading}
          valueColor={stats?.health.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PM2 Services */}
        <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
          <div className="flex items-center gap-2 mb-4">
            <Server className="h-5 w-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Services</h2>
          </div>
          {loading ? (
            <div className="animate-pulse space-y-2">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-8 bg-charcoal-800 rounded" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-left">
                    <th className="pb-2">Name</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Memory</th>
                    <th className="pb-2">CPU</th>
                    <th className="pb-2">Uptime</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {services?.pm2_services.map(svc => (
                    <tr key={svc.name} className="border-t border-charcoal-800">
                      <td className="py-2 font-medium">{svc.name}</td>
                      <td className="py-2">
                        <span className={`inline-flex items-center gap-1 ${svc.status === 'online' ? 'text-green-400' : 'text-yellow-400'}`}>
                          <span className={`w-2 h-2 rounded-full ${svc.status === 'online' ? 'bg-green-400' : 'bg-yellow-400'}`} />
                          {svc.status}
                        </span>
                      </td>
                      <td className="py-2">{svc.memory_mb}MB</td>
                      <td className="py-2">{svc.cpu}%</td>
                      <td className="py-2">{svc.uptime}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* VM Resources */}
          {services?.vm && (
            <div className="mt-4 pt-4 border-t border-charcoal-800 grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Disk</span>
                <p className="text-white">{services.vm.disk?.percent || 'N/A'}</p>
              </div>
              <div>
                <span className="text-gray-500">Memory</span>
                <p className="text-white">{services.vm.memory?.used || 'N/A'} / {services.vm.memory?.total || 'N/A'}</p>
              </div>
              <div>
                <span className="text-gray-500">Load (1m)</span>
                <p className="text-white">{services.vm.cpu_load?.['1m'] || 'N/A'}</p>
              </div>
            </div>
          )}

          {/* Redis */}
          {services?.redis && (
            <div className="mt-4 pt-4 border-t border-charcoal-800 flex items-center gap-4 text-sm">
              <Database className="h-4 w-4 text-red-400" />
              <span className="text-gray-500">Redis:</span>
              <span className={services.redis.status === 'connected' ? 'text-green-400' : 'text-red-400'}>
                {services.redis.status}
              </span>
              <span className="text-gray-400">({services.redis.memory})</span>
            </div>
          )}
        </div>

        {/* Billing & Logs */}
        <div className="space-y-6">
          {/* Billing */}
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <div className="flex items-center gap-2 mb-4">
              <DollarSign className="h-5 w-5 text-green-400" />
              <h2 className="text-lg font-semibold text-white">Billing (30d)</h2>
            </div>
            {loading ? (
              <div className="animate-pulse space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-6 bg-charcoal-800 rounded" />
                ))}
              </div>
            ) : billing && (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Provider Cost</span>
                  <span className="text-white">{formatCurrency(billing.provider_cost)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Platform Revenue</span>
                  <span className="text-green-400">{formatCurrency(billing.platform_cost)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Markup Earned</span>
                  <span className="text-green-400">{formatCurrency(billing.markup_earned)}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-charcoal-800">
                  <span className="text-gray-500">Unreported</span>
                  <span className={billing.unreported_count > 0 ? 'text-yellow-400' : 'text-gray-400'}>
                    {formatCurrency(billing.unreported_amount)} ({billing.unreported_count} activities)
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Tokens</span>
                  <span className="text-gray-500">
                    {formatNumber(billing.total_input_tokens)} in / {formatNumber(billing.total_output_tokens)} out
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Logs Summary */}
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="h-5 w-5 text-orange-400" />
              <h2 className="text-lg font-semibold text-white">Logs (24h)</h2>
            </div>
            {loading ? (
              <div className="animate-pulse h-8 bg-charcoal-800 rounded" />
            ) : logs && (
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-400">INFO: {formatNumber(logs.INFO)}</span>
                <span className="text-yellow-400">WARN: {formatNumber(logs.WARNING)}</span>
                <span className="text-orange-400">ERROR: {formatNumber(logs.ERROR)}</span>
                <span className="text-red-400">CRIT: {formatNumber(logs.CRITICAL)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats Row */}
      {stats && (
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <p className="text-gray-500 text-sm">Trades (24h)</p>
            <p className="text-2xl font-bold text-white">{stats.trading.trades_24h}</p>
          </div>
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <p className="text-gray-500 text-sm">Trades (7d)</p>
            <p className="text-2xl font-bold text-white">{stats.trading.trades_7d}</p>
          </div>
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <p className="text-gray-500 text-sm">Open Positions</p>
            <p className="text-2xl font-bold text-white">{stats.positions.open}</p>
          </div>
          <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
            <p className="text-gray-500 text-sm">Total Exposure</p>
            <p className="text-2xl font-bold text-white">{formatCurrency(stats.positions.total_exposure)}</p>
          </div>
        </div>
      )}

      {/* Navigation Links */}
      <div className="mt-6 space-y-3">
        <Link
          href="/admin/users"
          className="flex items-center justify-between p-4 bg-charcoal-900 rounded-lg border border-charcoal-700 hover:border-charcoal-600 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <Users className="h-5 w-5 text-blue-400" />
            <span className="text-white font-medium">Manage Users</span>
            <span className="text-gray-500 text-sm">Search, view, and edit user accounts</span>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-500 group-hover:text-white transition-colors" />
        </Link>

        <Link
          href="/admin/analytics"
          className="flex items-center justify-between p-4 bg-charcoal-900 rounded-lg border border-charcoal-700 hover:border-charcoal-600 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <DollarSign className="h-5 w-5 text-emerald-400" />
            <span className="text-white font-medium">Business Analytics</span>
            <span className="text-gray-500 text-sm">Revenue, funnel, engagement, LTV, cohorts</span>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-500 group-hover:text-white transition-colors" />
        </Link>

        <Link
          href="/admin/bots-comparison"
          className="flex items-center justify-between p-4 bg-charcoal-900 rounded-lg border border-charcoal-700 hover:border-charcoal-600 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <TrendingUp className="h-5 w-5 text-green-400" />
            <span className="text-white font-medium">Bot Performance Comparison</span>
            <span className="text-gray-500 text-sm">Compare equity curves across paper trading bots</span>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-500 group-hover:text-white transition-colors" />
        </Link>
      </div>
    </div>
  )
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  subtext: string
  loading: boolean
  valueColor?: string
}

function StatCard({ icon, label, value, subtext, loading, valueColor = 'text-white' }: StatCardProps) {
  return (
    <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-4">
      <div className="flex items-center gap-2 text-gray-400 mb-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      {loading ? (
        <div className="animate-pulse">
          <div className="h-8 bg-charcoal-800 rounded w-24 mb-1" />
          <div className="h-4 bg-charcoal-800 rounded w-16" />
        </div>
      ) : (
        <>
          <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
          <p className="text-sm text-gray-500">{subtext}</p>
        </>
      )}
    </div>
  )
}
