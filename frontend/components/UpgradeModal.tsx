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
      title: 'All 7 frontier AI models',
      description: 'Claude, GPT-5, Grok, Gemini, DeepSeek, Kimi, Qwen'
    },
    {
      icon: '⚡',
      title: 'Any analysis frequency',
      description: '5-minute to weekly checks - you choose'
    },
    {
      icon: '📱',
      title: 'Telegram signal publishing',
      description: 'Receive your bot decisions as trading signals'
    },
    {
      icon: '🤖',
      title: 'Unlimited active bots',
      description: 'Run as many bots as you need simultaneously'
    },
    {
      icon: '🎯',
      title: 'Paper & live trading',
      description: 'Test with virtual $10k or trade real money'
    },
    {
      icon: '📊',
      title: 'Real-time performance tracking',
      description: 'Monitor all your bots with live P&L updates'
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
            <span className="text-4xl font-bold text-[var(--text-primary)]">$0</span>
            <span className="text-lg text-[var(--text-secondary)]">base fee</span>
          </div>
          <p className="text-lg text-[var(--text-secondary)] mb-3">
            Pay only for what you use
          </p>

          {/* Cost Range Examples */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="bg-[var(--bg-tertiary)] rounded p-2">
              <div className="text-xs text-[var(--text-muted)] mb-1">Budget</div>
              <div className="font-semibold text-[var(--profit-color)]">&lt;$2/mo</div>
              <div className="text-xs text-[var(--text-tertiary)] mt-1">Hourly • Economy</div>
            </div>
            <div className="bg-[var(--bg-tertiary)] rounded p-2">
              <div className="text-xs text-[var(--text-muted)] mb-1">Active</div>
              <div className="font-semibold text-[var(--accent)]">$10-35/mo</div>
              <div className="text-xs text-[var(--text-tertiary)] mt-1">15-30min • Standard</div>
            </div>
            <div className="bg-[var(--bg-tertiary)] rounded p-2">
              <div className="text-xs text-[var(--text-muted)] mb-1">Power</div>
              <div className="font-semibold text-[var(--text-primary)]">$50-150/mo</div>
              <div className="text-xs text-[var(--text-tertiary)] mt-1">5-15min • Premium</div>
            </div>
          </div>

          <div className="text-xs text-[var(--text-muted)] space-y-1">
            <p>Your costs scale with your configuration:</p>
            <p className="text-[var(--text-tertiary)]">Reasoning tier (Economy/Standard/Premium) • Frequency • Number of bots</p>
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
              Activate Usage-Based Billing
            </>
          )}
        </button>

        {/* Footer */}
        <div className="text-center mt-3">
          <p className="text-xs text-[var(--text-tertiary)]">
            No credit card required to start • Secure payment by Stripe
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
