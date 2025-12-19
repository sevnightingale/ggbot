'use client'

import React, { useState } from 'react'
import { Sparkles, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { apiClient } from '@/lib/api'

interface UpgradeModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function UpgradeModal({ open, onOpenChange }: UpgradeModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const features = [
    {
      icon: '🤖',
      title: 'Unlimited active bots',
      description: 'Run as many bots as you need'
    },
    {
      icon: '🧠',
      title: 'All 7 AI models',
      description: 'Claude, Grok, Gemini & more'
    },
    {
      icon: '🎯',
      title: 'Paper & live trading',
      description: 'Test or trade real money'
    }
  ]

  const handleUpgrade = async () => {
    try {
      setLoading(true)
      setError(null)

      // Call backend to create Stripe checkout session for usage-based plan
      const { checkout_url } = await apiClient.createCheckoutSession({
        plan: 'usage'
      })

      // Redirect to Stripe checkout
      window.location.href = checkout_url

    } catch (err) {
      console.error('Checkout error:', err)
      setError(err instanceof Error ? err.message : 'Failed to start checkout. Please try again.')
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg flex flex-col max-h-[85vh]">
        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-2 mb-1">
              <div className="rounded-full bg-[var(--bg-tertiary)] p-2">
                <Sparkles className="h-5 w-5 text-[var(--text-primary)]" />
              </div>
              <DialogTitle className="text-2xl">Activate Your ggbots</DialogTitle>
            </div>
            <DialogDescription>
              Pay only for what you use
            </DialogDescription>
          </DialogHeader>

          {/* Pricing Display */}
          <div className="text-center my-4 p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
            <div className="flex items-baseline justify-center gap-2 mb-3">
              <span className="text-4xl font-bold text-[var(--text-primary)]">$0</span>
              <span className="text-lg text-[var(--text-secondary)]">base fee</span>
            </div>

            {/* Cost Range Examples */}
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-[var(--bg-tertiary)] rounded p-2">
                <div className="text-xs text-[var(--text-muted)] mb-1">Budget</div>
                <div className="font-semibold text-[var(--profit-color)]">&lt;$2/mo</div>
                <div className="text-xs text-[var(--text-tertiary)] mt-1">Hourly</div>
              </div>
              <div className="bg-[var(--bg-tertiary)] rounded p-2">
                <div className="text-xs text-[var(--text-muted)] mb-1">Active</div>
                <div className="font-semibold text-[var(--accent)]">$10-35/mo</div>
                <div className="text-xs text-[var(--text-tertiary)] mt-1">15-30min</div>
              </div>
              <div className="bg-[var(--bg-tertiary)] rounded p-2">
                <div className="text-xs text-[var(--text-muted)] mb-1">Power</div>
                <div className="font-semibold text-[var(--text-primary)]">$50-150/mo</div>
                <div className="text-xs text-[var(--text-tertiary)] mt-1">5-15min</div>
              </div>
            </div>
          </div>

          {/* Features List - horizontal */}
          <div className="flex justify-center gap-6 mb-4">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="text-lg">{feature.icon}</span>
                <span className="text-sm text-[var(--text-secondary)]">{feature.title}</span>
              </div>
            ))}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-3 p-2 bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30 rounded-lg">
              <p className="text-sm text-[var(--loss-color)]">{error}</p>
            </div>
          )}
        </div>

        {/* Sticky CTA */}
        <div className="flex-shrink-0 pt-4 border-t border-[var(--border)]">
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-[var(--bg-primary)] font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Starting checkout...
              </>
            ) : (
              'Activate Usage-Based Billing'
            )}
          </button>
          <p className="text-center text-xs text-[var(--text-tertiary)] mt-2">
            Secure payment via Stripe
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
