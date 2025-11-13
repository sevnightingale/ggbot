'use client'

import React, { useState } from 'react'
import { Check, Sparkles, Loader2 } from 'lucide-react'
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
      icon: '🧠',
      title: 'Frontier reasoning models',
      description: 'Access to Claude, GPT-5, Grok, Gemini, and more'
    },
    {
      icon: '⚡',
      title: 'High frequency analysis',
      description: 'Run your ggbots as often as you need'
    },
    {
      icon: '📱',
      title: 'Telegram signal publishing',
      description: 'Receive your ggbot\'s decisions as trading signals'
    },
    {
      icon: '🤖',
      title: 'Multiple active bots',
      description: 'Run up to 10 ggbots simultaneously'
    },
    {
      icon: '🔍',
      title: 'Signal validation mode',
      description: 'Validate external signals before execution'
    },
    {
      icon: '📊',
      title: 'Live trading (Symphony)',
      description: 'Execute real trades on supported exchanges'
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
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1">
            <div className="rounded-full bg-[var(--bg-tertiary)] p-2">
              <Sparkles className="h-5 w-5 text-[var(--text-primary)]" />
            </div>
            <DialogTitle className="text-2xl">Activate Your ggbots</DialogTitle>
          </div>
          <DialogDescription>
            Pay only for what you use - simple, transparent pricing
          </DialogDescription>
        </DialogHeader>

        {/* Pricing Display */}
        <div className="text-center mb-3 p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
          <div className="flex items-baseline justify-center gap-2 mb-2">
            <span className="text-4xl font-bold text-[var(--text-primary)]">
              Usage-Based
            </span>
          </div>
          <p className="text-lg text-[var(--text-secondary)] mb-3">
            No monthly fee • Pay per LLM call
          </p>
          <div className="text-sm text-[var(--text-muted)] space-y-1">
            <p>Typical costs: <span className="font-semibold text-[var(--text-primary)]">~$0.05 per decision</span></p>
            <p className="text-xs">Exact cost depends on model choice and market data complexity</p>
          </div>
        </div>

        {/* Features List - 2 column grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          {features.map((feature, index) => (
            <div key={index} className="flex gap-2 items-start">
              <div className="text-xl mt-0.5">{feature.icon}</div>
              <div className="flex-1">
                <h4 className="font-medium text-[var(--text-primary)] text-sm mb-0.5">
                  {feature.title}
                </h4>
                <p className="text-xs text-[var(--text-secondary)]">
                  {feature.description}
                </p>
              </div>
              <Check className="text-[var(--profit-color)] flex-shrink-0 mt-0.5" size={18} />
            </div>
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-3 p-2 bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30 rounded-lg">
            <p className="text-sm text-[var(--loss-color)]">{error}</p>
          </div>
        )}

        {/* CTA Button */}
        <button
          onClick={handleUpgrade}
          disabled={loading}
          className="w-full bg-[var(--profit-color)] hover:opacity-90 disabled:opacity-50 text-white font-medium py-3 px-6 rounded-lg transition-opacity flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Starting checkout...
            </>
          ) : (
            <>
              Subscribe & Activate Bots
            </>
          )}
        </button>

        {/* Footer */}
        <div className="text-center mt-3">
          <p className="text-xs text-[var(--text-tertiary)]">
            Secure payment by Stripe • Cancel anytime
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
