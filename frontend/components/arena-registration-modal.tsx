'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Trophy, Calendar, DollarSign, Zap, AlertCircle } from 'lucide-react'
import { createClient } from '@/lib/supabase'

interface ArenaRegistrationModalProps {
  isOpen: boolean
  onClose: () => void
  configId: string
  configName: string
  onSuccess: () => void
}

export function ArenaRegistrationModal({
  isOpen,
  onClose,
  configId,
  configName,
  onSuccess
}: ArenaRegistrationModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRegister = async () => {
    setLoading(true)
    setError(null)

    try {
      // Get auth session for API call
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('Please sign in to register for the Arena')
      }

      const response = await fetch(`/api/v2/bot/${configId}/arena/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        }
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Registration failed')
      }

      onSuccess()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-[var(--accent)]" />
            Enter the ggArena
          </DialogTitle>
          <DialogDescription>
            Register &quot;{configName}&quot; for Season 1 competition
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Competition Details */}
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-[var(--text-primary)]">
              <Calendar className="h-4 w-4 text-[var(--text-muted)]" />
              <span className="text-sm">Jan 21 - Feb 11, 2026 (21 days)</span>
            </div>
            <div className="flex items-center gap-3 text-[var(--text-primary)]">
              <DollarSign className="h-4 w-4 text-[var(--text-muted)]" />
              <span className="text-sm">$2,500 prize pool in USX</span>
            </div>
            <div className="flex items-center gap-3 text-[var(--text-primary)]">
              <Zap className="h-4 w-4 text-[var(--text-muted)]" />
              <span className="text-sm">Top 3 get funded live trading on Symphony</span>
            </div>
          </div>

          {/* Important Notice */}
          <div className="rounded-lg bg-[var(--bg-tertiary)] p-3 text-sm">
            <div className="flex gap-2">
              <AlertCircle className="h-4 w-4 text-[var(--accent)] flex-shrink-0 mt-0.5" />
              <p className="text-[var(--text-secondary)]">
                <strong className="text-[var(--text-primary)]">Note:</strong> Your paper trading
                account will be reset to $10,000 on January 21st when the competition begins.
              </p>
            </div>
          </div>

          {error && (
            <div className="rounded-lg bg-[var(--ember)]/10 border border-[var(--ember)] p-3">
              <p className="text-sm text-[var(--ember)]">{error}</p>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleRegister}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-[var(--accent)] text-[var(--bg-primary)] font-medium hover:bg-[var(--accent-hover)] disabled:opacity-50 transition-colors"
          >
            {loading ? 'Registering...' : 'Enter Arena'}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
