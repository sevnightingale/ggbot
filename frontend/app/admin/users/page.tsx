'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { Search, ArrowLeft, ChevronRight, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface User {
  user_id: string
  email: string
  subscription_tier: string
  subscription_status: string
  joined_at: string | null
  last_sign_in: string | null
  bot_count: number
  total_trades: number
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const router = useRouter()

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
    }, 500)
    return () => clearTimeout(timer)
  }, [search])

  const fetchUsers = useCallback(async () => {
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
      const params = new URLSearchParams({ limit: '50' })
      if (debouncedSearch) {
        params.set('search', debouncedSearch)
      }

      const response = await fetch(`${baseUrl}/api/v2/admin/users?${params}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to fetch users')
      }

      const data = await response.json()
      setUsers(data.users)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }, [debouncedSearch])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
    return date.toLocaleDateString()
  }

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'pro':
        return <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">Pro</span>
      case 'prepaid':
        return <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded text-xs">Prepaid</span>
      case 'usage_based':
        return <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">Usage</span>
      default:
        return <span className="px-2 py-0.5 bg-gray-500/20 text-gray-400 rounded text-xs">Free</span>
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/admin"
          className="p-2 hover:bg-charcoal-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-400" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="text-sm text-gray-500">{total} users total</p>
        </div>
        <button
          onClick={fetchUsers}
          disabled={loading}
          className="p-2 hover:bg-charcoal-800 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-5 w-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
        <input
          type="text"
          placeholder="Search by email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-charcoal-900 border border-charcoal-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-charcoal-500"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Users Table */}
      <div className="bg-charcoal-900 rounded-lg border border-charcoal-700 overflow-hidden">
        {loading && users.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
            Loading users...
          </div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {debouncedSearch ? `No users found matching "${debouncedSearch}"` : 'No users found'}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-charcoal-700 text-gray-500 text-left text-sm">
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Tier</th>
                <th className="px-4 py-3">Bots</th>
                <th className="px-4 py-3">Trades</th>
                <th className="px-4 py-3">Last Active</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr
                  key={user.user_id}
                  onClick={() => router.push(`/admin/users/${user.user_id}`)}
                  className="border-b border-charcoal-800 hover:bg-charcoal-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="text-white">{user.email}</span>
                  </td>
                  <td className="px-4 py-3">
                    {getTierBadge(user.subscription_tier)}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {user.bot_count}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {user.total_trades}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-sm">
                    {formatDate(user.last_sign_in)}
                  </td>
                  <td className="px-4 py-3">
                    <ChevronRight className="h-4 w-4 text-gray-600" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
