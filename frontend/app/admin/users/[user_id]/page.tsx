'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { ArrowLeft, Save, RefreshCw, Play, Square, RotateCcw, ChevronDown, ChevronRight, AlertCircle, CreditCard, Coins } from 'lucide-react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

interface TokenUsage {
  input_tokens: number
  output_tokens: number
  provider_cost: number
  platform_cost: number
  llm_calls: number
}

interface Config {
  config_id: string
  config_name: string
  config_type: string | null
  state: string
  trading_mode: string
  created_at: string | null
  updated_at: string | null
  config_data: Record<string, unknown>
  token_usage: TokenUsage
}

interface PaperAccount {
  account_id: string
  config_id: string
  config_name: string
  initial_balance: number
  current_balance: number
  total_pnl: number
  total_trades: number
  win_trades: number
  loss_trades: number
  win_rate: number
  open_positions: number
}

interface CreditGrant {
  id: string
  name: string
  amount: number
  category: string
  created_at: string
}

interface CreditInfo {
  total_purchased: number
  available_balance: number
  used_balance: number
  unbilled_usage: number
  unbilled_count: number
  total_usage_cost: number
  total_usage_count: number
  credit_grants: CreditGrant[]
}

interface UserDetail {
  user_id: string
  email: string
  subscription_tier: string
  subscription_status: string
  subscription_expires_at: string | null
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  paid_data_points: string[]
  telegram_user_id: string | null
  telegram_username: string | null
  joined_at: string | null
  last_sign_in: string | null
  profile_created: string | null
  profile_updated: string | null
  configurations: Config[]
  paper_accounts: PaperAccount[]
  credit_info?: CreditInfo
}

export default function UserDetailPage() {
  const params = useParams()
  const userId = params?.user_id as string

  const [user, setUser] = useState<UserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Editable fields
  const [tier, setTier] = useState('')
  const [status, setStatus] = useState('')

  // Expanded configs
  const [expandedConfigs, setExpandedConfigs] = useState<Set<string>>(new Set())

  // Confirmation modal state
  const [confirmModal, setConfirmModal] = useState<{
    show: boolean
    title: string
    message: string
    action: () => Promise<void>
  } | null>(null)

  const fetchUser = useCallback(async () => {
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
      const response = await fetch(`${baseUrl}/api/v2/admin/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to fetch user')
      }

      const data = await response.json()
      setUser(data.user)
      setTier(data.user.subscription_tier || 'free')
      setStatus(data.user.subscription_status || 'active')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user')
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const getAuthHeaders = async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) throw new Error('Not authenticated')
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  }

  const saveProfile = async () => {
    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      const headers = await getAuthHeaders()
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const response = await fetch(`${baseUrl}/api/v2/admin/users/${userId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({
          subscription_tier: tier,
          subscription_status: status
        })
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to save')
      }

      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      fetchUser() // Refresh data
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const startBot = async (configId: string, configName: string) => {
    setConfirmModal({
      show: true,
      title: 'Start Bot',
      message: `Start bot "${configName}"?`,
      action: async () => {
        const headers = await getAuthHeaders()
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const response = await fetch(`${baseUrl}/api/v2/admin/bots/${configId}/start`, {
          method: 'POST',
          headers
        })

        if (!response.ok) {
          const errData = await response.json()
          throw new Error(errData.detail || 'Failed to start bot')
        }

        fetchUser()
      }
    })
  }

  const stopBot = async (configId: string, configName: string) => {
    setConfirmModal({
      show: true,
      title: 'Stop Bot',
      message: `Stop bot "${configName}"? This will cancel any scheduled runs.`,
      action: async () => {
        const headers = await getAuthHeaders()
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const response = await fetch(`${baseUrl}/api/v2/admin/bots/${configId}/stop`, {
          method: 'POST',
          headers
        })

        if (!response.ok) {
          const errData = await response.json()
          throw new Error(errData.detail || 'Failed to stop bot')
        }

        fetchUser()
      }
    })
  }

  const resetAccount = async (configId: string, configName: string) => {
    setConfirmModal({
      show: true,
      title: 'Reset Account',
      message: `Reset paper account for "${configName}" to $10,000? This cannot be undone.`,
      action: async () => {
        const headers = await getAuthHeaders()
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const response = await fetch(`${baseUrl}/api/v2/admin/bots/${configId}/reset-account`, {
          method: 'POST',
          headers
        })

        if (!response.ok) {
          const errData = await response.json()
          throw new Error(errData.detail || 'Failed to reset account')
        }

        fetchUser()
      }
    })
  }

  const toggleConfigExpanded = (configId: string) => {
    setExpandedConfigs(prev => {
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
      currency: 'USD'
    }).format(value)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="p-6">
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 text-red-400">
          {error || 'User not found'}
        </div>
        <Link href="/admin/users" className="mt-4 inline-flex items-center gap-2 text-gray-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back to Users
        </Link>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/admin/users"
          className="p-2 hover:bg-charcoal-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-400" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">{user.email}</h1>
          <p className="text-sm text-gray-500">User ID: {user.user_id}</p>
        </div>
        <button
          onClick={fetchUser}
          className="p-2 hover:bg-charcoal-800 rounded-lg transition-colors"
        >
          <RefreshCw className="h-5 w-5 text-gray-400" />
        </button>
      </div>

      {/* Profile Section */}
      <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Profile</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Editable Fields */}
          <div>
            <label className="block text-sm text-gray-500 mb-1">Subscription Tier</label>
            <select
              value={tier}
              onChange={(e) => setTier(e.target.value)}
              className="w-full px-3 py-2 bg-charcoal-800 border border-charcoal-700 rounded-lg text-white focus:outline-none focus:border-charcoal-500"
            >
              <option value="free">Free</option>
              <option value="prepaid">Prepaid (Credit Packs)</option>
              <option value="usage_based">Usage Based</option>
              <option value="pro">Pro</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-500 mb-1">Subscription Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-3 py-2 bg-charcoal-800 border border-charcoal-700 rounded-lg text-white focus:outline-none focus:border-charcoal-500"
            >
              <option value="active">Active</option>
              <option value="canceled">Canceled</option>
              <option value="past_due">Past Due</option>
              <option value="incomplete">Incomplete</option>
            </select>
          </div>

          {/* Read-only Fields */}
          <div>
            <label className="block text-sm text-gray-500 mb-1">Joined</label>
            <p className="text-white">{formatDate(user.joined_at)}</p>
          </div>

          <div>
            <label className="block text-sm text-gray-500 mb-1">Last Sign In</label>
            <p className="text-white">{formatDate(user.last_sign_in)}</p>
          </div>

          {user.stripe_customer_id && (
            <div>
              <label className="block text-sm text-gray-500 mb-1">Stripe Customer</label>
              <p className="text-white font-mono text-sm">{user.stripe_customer_id}</p>
            </div>
          )}

          {user.telegram_username && (
            <div>
              <label className="block text-sm text-gray-500 mb-1">Telegram</label>
              <p className="text-white">@{user.telegram_username}</p>
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="mt-6 flex items-center gap-4">
          <button
            onClick={saveProfile}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 rounded-lg text-white transition-colors"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>

          {saveSuccess && (
            <span className="text-green-400 text-sm">Saved successfully!</span>
          )}

          {saveError && (
            <span className="text-red-400 text-sm">{saveError}</span>
          )}
        </div>
      </div>

      {/* Credits & Billing Section */}
      {user.credit_info && (
        <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-amber-400" />
            Credits & Billing
          </h2>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-charcoal-800/50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Total Purchased</div>
              <div className="text-2xl font-bold text-white">
                {formatCurrency(user.credit_info.total_purchased)}
              </div>
            </div>
            <div className="bg-charcoal-800/50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Available Balance</div>
              <div className={`text-2xl font-bold ${user.credit_info.available_balance > 0 ? 'text-green-400' : 'text-gray-400'}`}>
                {formatCurrency(user.credit_info.available_balance)}
              </div>
            </div>
            <div className="bg-charcoal-800/50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Total Used</div>
              <div className="text-2xl font-bold text-amber-400">
                {formatCurrency(user.credit_info.total_usage_cost)}
              </div>
              <div className="text-xs text-gray-500">{user.credit_info.total_usage_count} LLM calls</div>
            </div>
            <div className="bg-charcoal-800/50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Unbilled Usage</div>
              <div className={`text-2xl font-bold ${user.credit_info.unbilled_usage > 0 ? 'text-yellow-400' : 'text-gray-400'}`}>
                {formatCurrency(user.credit_info.unbilled_usage)}
              </div>
              <div className="text-xs text-gray-500">{user.credit_info.unbilled_count} pending</div>
            </div>
          </div>

          {/* Credit Grants History */}
          {user.credit_info.credit_grants.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                <Coins className="h-4 w-4" />
                Credit Grants ({user.credit_info.credit_grants.length})
              </h3>
              <div className="space-y-2">
                {user.credit_info.credit_grants.map(grant => (
                  <div
                    key={grant.id}
                    className="flex items-center justify-between p-3 bg-charcoal-800/30 rounded-lg border border-charcoal-700"
                  >
                    <div>
                      <div className="text-white font-medium">{grant.name}</div>
                      <div className="text-xs text-gray-500">
                        {formatDate(grant.created_at)} · {grant.category}
                      </div>
                    </div>
                    <div className="text-green-400 font-semibold">
                      +{formatCurrency(grant.amount)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {user.credit_info.credit_grants.length === 0 && (
            <div className="text-gray-500 text-sm">No credit purchases yet</div>
          )}
        </div>
      )}

      {/* Bots Section */}
      <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">
          Bots ({user.configurations.length})
        </h2>

        {user.configurations.length === 0 ? (
          <p className="text-gray-500">No bots configured</p>
        ) : (
          <div className="space-y-3">
            {user.configurations.map(config => (
              <div
                key={config.config_id}
                className="border border-charcoal-700 rounded-lg overflow-hidden"
              >
                {/* Bot Header */}
                <div
                  className="flex items-center justify-between p-4 bg-charcoal-800/50 cursor-pointer"
                  onClick={() => toggleConfigExpanded(config.config_id)}
                >
                  <div className="flex items-center gap-3">
                    {expandedConfigs.has(config.config_id) ? (
                      <ChevronDown className="h-4 w-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-500" />
                    )}
                    <span className="font-medium text-white">{config.config_name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      config.state === 'active'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {config.state}
                    </span>
                    <span className="px-2 py-0.5 bg-charcoal-700 text-gray-400 rounded text-xs">
                      {config.trading_mode}
                    </span>
                  </div>

                  <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                    {config.state === 'active' ? (
                      <button
                        onClick={() => stopBot(config.config_id, config.config_name)}
                        className="p-2 hover:bg-red-500/20 rounded text-red-400 transition-colors"
                        title="Stop Bot"
                      >
                        <Square className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => startBot(config.config_id, config.config_name)}
                        className="p-2 hover:bg-green-500/20 rounded text-green-400 transition-colors"
                        title="Start Bot"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => resetAccount(config.config_id, config.config_name)}
                      className="p-2 hover:bg-yellow-500/20 rounded text-yellow-400 transition-colors"
                      title="Reset Account"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedConfigs.has(config.config_id) && (
                  <div className="p-4 border-t border-charcoal-700">
                    {/* Token Usage */}
                    <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">LLM Calls</span>
                        <p className="text-white">{config.token_usage.llm_calls}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Input Tokens</span>
                        <p className="text-white">{config.token_usage.input_tokens.toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Provider Cost</span>
                        <p className="text-white">{formatCurrency(config.token_usage.provider_cost)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Platform Cost</span>
                        <p className="text-green-400">{formatCurrency(config.token_usage.platform_cost)}</p>
                      </div>
                    </div>

                    {/* Config Data Preview */}
                    <div>
                      <span className="text-gray-500 text-sm">Config Data</span>
                      <pre className="mt-1 p-3 bg-charcoal-950 rounded-lg text-xs text-gray-400 overflow-x-auto max-h-48">
                        {JSON.stringify(config.config_data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Paper Accounts Section */}
      <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">
          Paper Accounts ({user.paper_accounts.length})
        </h2>

        {user.paper_accounts.length === 0 ? (
          <p className="text-gray-500">No paper accounts</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-left">
                  <th className="pb-2">Bot</th>
                  <th className="pb-2">Balance</th>
                  <th className="pb-2">P&L</th>
                  <th className="pb-2">Trades</th>
                  <th className="pb-2">Win Rate</th>
                  <th className="pb-2">Open</th>
                </tr>
              </thead>
              <tbody className="text-gray-300">
                {user.paper_accounts.map(account => (
                  <tr key={account.account_id} className="border-t border-charcoal-800">
                    <td className="py-2">{account.config_name}</td>
                    <td className="py-2">{formatCurrency(account.current_balance)}</td>
                    <td className={`py-2 ${account.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatCurrency(account.total_pnl)}
                    </td>
                    <td className="py-2">{account.total_trades}</td>
                    <td className="py-2">{account.win_rate}%</td>
                    <td className="py-2">{account.open_positions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {confirmModal?.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-charcoal-900 border border-charcoal-700 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="h-6 w-6 text-yellow-400" />
              <h3 className="text-lg font-semibold text-white">{confirmModal.title}</h3>
            </div>
            <p className="text-gray-400 mb-6">{confirmModal.message}</p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmModal(null)}
                className="px-4 py-2 bg-charcoal-800 hover:bg-charcoal-700 rounded-lg text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  try {
                    await confirmModal.action()
                  } catch (err) {
                    setSaveError(err instanceof Error ? err.message : 'Action failed')
                  }
                  setConfirmModal(null)
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
