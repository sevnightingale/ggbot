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
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const pricing = {
    monthly: { price: 29, period: 'month' },
    annual: { price: 279, period: 'year', savings: '20% off' }
  }

  const features = [
    {
      icon: '🧠',
      title: 'Frontier reasoning models',
      description: 'Tuned for market analysis and trading decisions'
    },
    {
      icon: '⚡',
      title: 'High frequency analysis',
      description: 'Run your ggbots more often so you never miss an opportunity'
    },
    {
      icon: '📱',
      title: 'Telegram publishing',
      description: 'Receive your ggbot\'s decisions to use as signals for full autonomous trading'
    },
    {
      icon: '🤖',
      title: 'Multiple bots',
      description: 'Up to 10 active ggbots so you can A/B test several strategies at once'
    }
  ]

  const handleUpgrade = async () => {
    try {
      setLoading(true)
      setError(null)

      // Call backend to create Stripe checkout session
      const { checkout_url } = await apiClient.createCheckoutSession({
        plan: billingPeriod
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
            <DialogTitle className="text-2xl">Upgrade to Pro Plan</DialogTitle>
          </div>
          <DialogDescription>
            Unlock advanced features and take your trading to the next level
          </DialogDescription>
        </DialogHeader>

        {/* Billing Period Toggle */}
        <div className="flex items-center justify-center gap-2 my-3">
          <button
            onClick={() => setBillingPeriod('monthly')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border-hover)]'
                : 'bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)]'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingPeriod('annual')}
            className={`px-6 py-2 rounded-lg font-medium transition-all relative ${
              billingPeriod === 'annual'
                ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border-hover)]'
                : 'bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)]'
            }`}
          >
            Annual
            {billingPeriod === 'annual' && (
              <span className="absolute -top-2 -right-2 bg-[var(--profit-color)] text-white text-xs px-2 py-0.5 rounded-full">
                Save 20%
              </span>
            )}
          </button>
        </div>

        {/* Pricing Display */}
        <div className="text-center mb-3 p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
          <div className="flex items-baseline justify-center gap-2 mb-1">
            <span className="text-xl font-medium text-[var(--text-muted)] line-through">
              ${pricing[billingPeriod].price}
            </span>
            <span className="text-3xl font-bold text-[var(--profit-color)]">
              ${pricing[billingPeriod].price / 2}
            </span>
            <span className="text-[var(--text-secondary)]">
              / {pricing[billingPeriod].period}
            </span>
          </div>
          <p className="text-sm text-[var(--profit-color)] font-medium">
            🎉 50% off for first 100 customers!
          </p>
          {billingPeriod === 'annual' && (
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Just $11.63/month when billed annually
            </p>
          )}
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
              Start 14-Day Free Trial
            </>
          )}
        </button>

        {/* Coupon Note & Footer */}
        <div className="text-center mt-3 space-y-1">
          <p className="text-xs text-[var(--text-secondary)]">
            💡 Use code <span className="font-semibold text-[var(--profit-color)]">FIRST100</span> at checkout for 50% off
          </p>
          <p className="text-xs text-[var(--text-tertiary)]">
            14-day free trial • No credit card required • Secure payment by Stripe
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
