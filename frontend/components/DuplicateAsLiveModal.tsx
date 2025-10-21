'use client'

import React, { useState, useEffect } from 'react'
import { AlertCircle, Loader2, Rocket, ExternalLink } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { BotConfiguration } from '@/lib/api'

interface DuplicateAsLiveModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceBot: BotConfiguration | null
  onSuccess?: () => void
}

export function DuplicateAsLiveModal({
  open,
  onOpenChange,
  sourceBot,
  onSuccess
}: DuplicateAsLiveModalProps) {
  const [liveBotName, setLiveBotName] = useState('')
  const [symphonyAgentId, setSymphonyAgentId] = useState('')
  const [symphonyConnected, setSymphonyConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check Symphony connection status when modal opens
  useEffect(() => {
    if (open && sourceBot) {
      // Pre-fill with suggested name
      setLiveBotName(`${sourceBot.config_name} (Live)`)
      checkSymphonyConnection()
    }
  }, [open, sourceBot])

  const checkSymphonyConnection = async () => {
    try {
      setChecking(true)

      // Get auth token properly
      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setChecking(false)
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
      }
    } catch (err) {
      console.error('Failed to check Symphony status:', err)
    } finally {
      setChecking(false)
    }
  }

  const validateForm = () => {
    if (!liveBotName.trim()) {
      setError('Live bot name is required')
      return false
    }

    if (!symphonyAgentId.trim()) {
      setError('Symphony Agent ID is required')
      return false
    }

    // Basic UUID format validation
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(symphonyAgentId.trim())) {
      setError('Invalid Symphony Agent ID format (should be a UUID)')
      return false
    }

    return true
  }

  const handleDuplicate = async () => {
    if (!sourceBot || !validateForm()) return

    try {
      setLoading(true)
      setError(null)

      // Get auth token properly
      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setError('Authentication required. Please log in again.')
        setLoading(false)
        return
      }

      const response = await fetch('/api/v2/config/duplicate-as-live', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          source_config_id: sourceBot.config_id,
          live_bot_name: liveBotName.trim(),
          symphony_agent_id: symphonyAgentId.trim()
        })
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Failed to create live bot' }))
        console.error('Backend error response:', data)
        throw new Error(data.detail || 'Failed to create live bot')
      }

      await response.json()

      // Success!
      onSuccess?.()
      onOpenChange(false)

      // Reset form
      setLiveBotName('')
      setSymphonyAgentId('')
      setError(null)

    } catch (err) {
      console.error('Duplicate as live error:', err)
      setError(err instanceof Error ? err.message : 'Failed to create live bot. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (checking) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-lg">
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-[var(--text-secondary)]" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!symphonyConnected) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <div className="flex items-center gap-2 mb-1">
              <div className="rounded-full bg-[var(--bg-tertiary)] p-2">
                <AlertCircle className="h-5 w-5 text-amber-500" />
              </div>
              <DialogTitle className="text-xl">Symphony Not Connected</DialogTitle>
            </div>
          </DialogHeader>

          <div className="space-y-4">
            <p className="text-sm text-[var(--text-secondary)]">
              You need to connect your Symphony account before creating live trading bots.
            </p>

            <div className="bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg p-4">
              <p className="text-sm text-[var(--text-primary)] mb-2 font-medium">
                To connect Symphony:
              </p>
              <ol className="list-decimal list-inside space-y-1 text-sm text-[var(--text-secondary)]">
                <li>Open Settings from your profile menu</li>
                <li>Enter your Symphony API key and smart account</li>
                <li>Return here to create your live bot</li>
              </ol>
            </div>

            <button
              onClick={() => onOpenChange(false)}
              className="w-full px-4 py-2 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm font-medium text-[var(--text-primary)] transition-colors"
            >
              Got it
            </button>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1">
            <div className="rounded-full bg-red-500/10 p-2">
              <Rocket className="h-5 w-5 text-red-500" />
            </div>
            <DialogTitle className="text-xl">Duplicate as Live Bot</DialogTitle>
          </div>
          <DialogDescription>
            Create a live trading version of &quot;{sourceBot?.config_name}&quot;
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Warning */}
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
            <p className="text-sm text-amber-600 dark:text-amber-400 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                <strong>Warning:</strong> Live trading uses real money. This bot will execute trades automatically via Symphony.
              </span>
            </p>
          </div>

          {/* Live Bot Name */}
          <div>
            <label className="block text-sm font-medium mb-1.5 text-[var(--text-primary)]">
              Live Bot Name
            </label>
            <input
              type="text"
              value={liveBotName}
              onChange={(e) => setLiveBotName(e.target.value)}
              placeholder="My BTC Bot (Live)"
              className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-red-500/50"
              disabled={loading}
            />
          </div>

          {/* Symphony Agent ID */}
          <div>
            <label className="block text-sm font-medium mb-1.5 text-[var(--text-primary)]">
              Symphony Agent ID
            </label>
            <input
              type="text"
              value={symphonyAgentId}
              onChange={(e) => setSymphonyAgentId(e.target.value)}
              placeholder="00000000-0000-0000-0000-000000000000"
              className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] placeholder:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-500/50 font-mono text-sm"
              disabled={loading}
            />
            <p className="text-xs text-[var(--text-secondary)] mt-1.5">
              Find your Agent ID in the{' '}
              <a
                href="https://agent-portal.symphony.io"
                target="_blank"
                rel="noopener noreferrer"
                className="text-red-500 hover:text-red-600 underline inline-flex items-center gap-1"
              >
                Symphony portal
                <ExternalLink className="h-3 w-3" />
              </a>
              {' '}under &quot;My Agents&quot;
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => onOpenChange(false)}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-[var(--border)] rounded-lg text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDuplicate}
              disabled={loading || !liveBotName.trim() || !symphonyAgentId.trim()}
              className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-[var(--bg-tertiary)] disabled:text-[var(--text-muted)] disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Live Bot'
              )}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
