'use client'

import React, { useState, useEffect } from 'react'
import { Crown, Link2, CheckCircle2, Settings, Loader2, AlertCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { apiClient } from '@/lib/api'

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { userProfile } = usePermissions()
  const isPro = userProfile?.subscription_tier === 'ggbase'

  // Symphony connection state
  const [symphonyConnected, setSymphonyConnected] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [smartAccount, setSmartAccount] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [storedSmartAccount, setStoredSmartAccount] = useState('')

  // Upgrade modal state
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

  // Check Symphony connection status on mount
  useEffect(() => {
    if (open) {
      checkSymphonyStatus()
    }
  }, [open])

  const checkSymphonyStatus = async () => {
    try {
      setLoading(true)

      // Get auth token properly
      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setLoading(false)
        return
      }

      const response = await fetch('/api/v2/symphony/status', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setSymphonyConnected(data.connected || false)
        if (data.smart_account) {
          setStoredSmartAccount(data.smart_account)
        }
      }
    } catch (e) {
      console.error('Failed to check Symphony status:', e)
    } finally {
      setLoading(false)
    }
  }

  const validateApiKey = (key: string): boolean => {
    // Format check: should start with 'sk_'
    return key.trim().startsWith('sk_') && key.trim().length > 10
  }

  const validateSmartAccount = (address: string): boolean => {
    // Format check: 0x followed by 40 hex characters
    const pattern = /^0x[a-fA-F0-9]{40}$/
    return pattern.test(address.trim())
  }

  const handleConnect = async () => {
    setConnecting(true)
    setError('')

    // Client-side validation
    if (!validateApiKey(apiKey)) {
      setError('Invalid API key format. Should start with "sk_"')
      setConnecting(false)
      return
    }

    if (!validateSmartAccount(smartAccount)) {
      setError('Invalid smart account address. Should be a valid Ethereum address (0x...)')
      setConnecting(false)
      return
    }

    try {
      // Get auth token properly
      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Authentication required. Please log in again.')
        setConnecting(false)
        return
      }

      const response = await fetch('/api/v2/symphony/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          api_key: apiKey.trim(),
          smart_account: smartAccount.trim()
        })
      })

      if (response.ok) {
        setSymphonyConnected(true)
        setStoredSmartAccount(smartAccount.trim())
        setApiKey('')  // Clear sensitive data
        setSmartAccount('')
        setError('')
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to connect Symphony account')
      }
    } catch (e) {
      console.error('Connection error:', e)
      setError('Connection error. Please try again.')
    } finally {
      setConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm('Disconnect Symphony account? Your live trading bots will stop working.')) {
      return
    }

    try {
      // Get auth token properly
      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Authentication required. Please log in again.')
        return
      }

      const response = await fetch('/api/v2/symphony/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })

      if (response.ok) {
        setSymphonyConnected(false)
        setStoredSmartAccount('')
        setError('')
      } else {
        setError('Failed to disconnect. Please try again.')
      }
    } catch (e) {
      console.error('Disconnect error:', e)
      setError('Disconnect failed. Please try again.')
    }
  }

  const handleManageBilling = async () => {
    try {
      const { portal_url } = await apiClient.createPortalSession()
      window.location.href = portal_url
    } catch (error) {
      console.error('Error opening billing portal:', error)
      setError('Failed to open billing portal. Please try again.')
    }
  }

  const isFormValid = apiKey.trim().length > 0 && smartAccount.trim().length > 0

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-2 mb-1">
              <div className="rounded-full bg-[var(--bg-tertiary)] p-2">
                <Settings className="h-5 w-5 text-[var(--text-primary)]" />
              </div>
              <DialogTitle className="text-2xl">Settings</DialogTitle>
            </div>
          </DialogHeader>

          <div className="space-y-6">
            {/* Subscription Section */}
            <section>
              <h3 className="text-sm font-semibold mb-3 text-[var(--text-primary)]">Subscription</h3>
              <div className="flex items-center justify-between p-4 border border-[var(--border)] rounded-lg bg-[var(--bg-secondary)]">
                <div>
                  <p className="font-medium text-[var(--text-primary)] mb-1">Current Plan</p>
                  <div className="mt-1">
                    {isPro ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-1 text-xs font-medium text-amber-500">
                        <Crown className="h-3 w-3" />
                        Pro Plan
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--bg-tertiary)] px-2 py-1 text-xs font-medium text-[var(--text-secondary)]">
                        Free Plan
                      </span>
                    )}
                  </div>
                </div>
                {isPro ? (
                  <button
                    onClick={handleManageBilling}
                    className="text-sm text-blue-500 hover:text-blue-600 font-medium transition-colors"
                  >
                    Manage Billing →
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      onOpenChange(false)
                      setUpgradeModalOpen(true)
                    }}
                    className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Upgrade to Pro
                  </button>
                )}
              </div>
            </section>

            {/* Symphony Live Trading Section */}
            <section>
              <h3 className="text-sm font-semibold mb-3 text-[var(--text-primary)]">Symphony Live Trading</h3>

              {loading ? (
                <div className="flex items-center justify-center p-8 border border-dashed border-[var(--border)] rounded-lg">
                  <Loader2 className="h-5 w-5 animate-spin text-[var(--text-secondary)]" />
                </div>
              ) : !symphonyConnected ? (
                <div className="border border-dashed border-[var(--border)] rounded-lg p-6">
                  <div className="flex items-start gap-3 mb-4">
                    <Link2 className="h-5 w-5 text-[var(--text-secondary)] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-[var(--text-primary)] mb-1">Connect Symphony Account</p>
                      <p className="text-sm text-[var(--text-secondary)]">
                        Execute real trades via Symphony.io with your AI strategies
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1.5 text-[var(--text-primary)]">
                        Symphony API Key *
                      </label>
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="sk_live_..."
                        className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1.5 text-[var(--text-primary)]">
                        Smart Account Address *
                      </label>
                      <input
                        value={smartAccount}
                        onChange={(e) => setSmartAccount(e.target.value)}
                        placeholder="0x..."
                        className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                      <p className="text-xs text-[var(--text-secondary)] mt-1.5">
                        Find in{' '}
                        <a
                          href="https://agent-portal.symphony.io"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-500 hover:text-blue-600 underline"
                        >
                          Symphony portal
                        </a>
                        {' '}under My Agents
                      </p>
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                        💡 Used for future balance display features. Not required for trading.
                      </p>
                    </div>

                    {error && (
                      <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                      </div>
                    )}

                    <button
                      onClick={handleConnect}
                      disabled={connecting || !isFormValid}
                      className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-[var(--bg-tertiary)] disabled:text-[var(--text-muted)] disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                    >
                      {connecting ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Connecting...
                        </>
                      ) : (
                        'Connect Account'
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="border border-[var(--border)] rounded-lg p-4 bg-green-50 dark:bg-green-950/20">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="font-medium text-green-900 dark:text-green-100 mb-1">
                        Symphony Connected
                      </p>
                      <p className="text-sm text-green-700 dark:text-green-300">
                        Smart Account: {storedSmartAccount.slice(0, 6)}...{storedSmartAccount.slice(-4)}
                      </p>
                    </div>
                    <button
                      onClick={handleDisconnect}
                      className="text-sm text-red-600 dark:text-red-400 hover:underline font-medium"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              )}
            </section>
          </div>
        </DialogContent>
      </Dialog>

      {/* Upgrade Modal */}
      <UpgradeModal open={upgradeModalOpen} onOpenChange={setUpgradeModalOpen} />
    </>
  )
}
