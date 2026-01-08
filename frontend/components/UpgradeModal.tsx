'use client'

import React, { useState, useMemo } from 'react'
import { Loader2, Check, Bot, ChevronLeft } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { apiClient, BotConfiguration } from '@/lib/api'
import { CreditPicker } from '@/components/CreditPicker'

interface UpgradeModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  botConfig?: BotConfiguration  // The specific bot being activated
}

type PaymentMode = 'choose' | 'usage' | 'prepay'

// Cost per decision by model and tier (with 70% markup already included)
// Based on real testing with production prompts (2026-01-05)
// Each model has 3 tiers: economy (mini/fast), standard (balanced), premium (reasoning)
const MODEL_TIER_COSTS: Record<string, { economy: number; standard: number; premium: number }> = {
  'grok': { economy: 0.0014, standard: 0.0027, premium: 0.0264 },
  'deepseek': { economy: 0.0035, standard: 0.0034, premium: 0.0167 },
  'gemini': { economy: 0.0013, standard: 0.0448, premium: 0.0595 },
  'gpt': { economy: 0.0044, standard: 0.0504, premium: 1.2022 },
  'claude': { economy: 0.0275, standard: 0.0658, premium: 0.1452 },
  'kimi': { economy: 0.0076, standard: 0.0108, premium: 0.0164 },
  'qwen': { economy: 0.0007, standard: 0.0049, premium: 0.0152 },
  'default': { economy: 0.003, standard: 0.010, premium: 0.030 }
}

// Decisions per day by frequency
const FREQUENCY_TO_DECISIONS: Record<string, number> = {
  '5m': 288,
  '15m': 96,
  '30m': 48,
  '1h': 24,
  '4h': 6,
  '1d': 1,
  '1w': 0.14,  // ~1 per week
  'signal_driven': 5  // estimate ~5 signals/day
}

export function UpgradeModal({ open, onOpenChange, botConfig }: UpgradeModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('choose')

  // Calculate estimate based on bot config
  const estimate = useMemo(() => {
    if (!botConfig) {
      // Fallback for generic modal (no specific bot)
      return { low: 5, high: 15, hasConfig: false }
    }

    // Get model from config
    const model = botConfig.config_data.llm_config?.model?.toLowerCase() || 'default'
    const modelCosts = MODEL_TIER_COSTS[model] || MODEL_TIER_COSTS['default']

    // Get reasoning tier from config (economy, standard, premium)
    // Fall back to thinking_mode for backward compatibility
    let tier: 'economy' | 'standard' | 'premium' = 'standard'
    const configTier = botConfig.config_data.llm_config?.reasoning_tier
    if (configTier && (configTier === 'economy' || configTier === 'standard' || configTier === 'premium')) {
      tier = configTier
    } else if (botConfig.config_data.llm_config?.thinking_mode) {
      tier = 'premium'
    }

    const costPerDecision = modelCosts[tier]

    // Get frequency from config
    const frequency = botConfig.config_data.decision?.analysis_frequency || '1h'
    const decisionsPerDay = FREQUENCY_TO_DECISIONS[frequency] || 24

    // Calculate monthly cost
    const baseCost = decisionsPerDay * 30 * costPerDecision

    // Add ±30% range for variance (market activity, actual decisions made)
    const low = Math.max(1, Math.round(baseCost * 0.7))
    const high = Math.round(baseCost * 1.3)

    return { low, high, hasConfig: true }
  }, [botConfig])

  const handleUpgrade = async () => {
    try {
      setLoading(true)
      setError(null)

      const { checkout_url } = await apiClient.createCheckoutSession({
        plan: 'usage'
      })

      window.location.href = checkout_url

    } catch (err) {
      console.error('Checkout error:', err)
      setError(err instanceof Error ? err.message : 'Failed to start checkout. Please try again.')
      setLoading(false)
    }
  }

  const botName = botConfig?.config_name || 'Your Bot'

  // Reset payment mode when modal closes
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setPaymentMode('choose')
      setError(null)
    }
    onOpenChange(open)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-sm p-0 gap-0 overflow-hidden">
        {/* Header */}
        <div className="p-6 pb-4">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold flex items-center gap-2">
              {paymentMode !== 'choose' && (
                <button
                  onClick={() => setPaymentMode('choose')}
                  className="p-1 -ml-1 rounded hover:bg-[var(--bg-tertiary)] transition-colors"
                >
                  <ChevronLeft size={20} className="text-[var(--text-secondary)]" />
                </button>
              )}
              <Bot size={20} className="text-[var(--accent)]" />
              {paymentMode === 'prepay' ? 'Prepay Credits' : `Activate ${botName}`}
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            {paymentMode === 'prepay'
              ? 'Buy credits upfront. Use until empty, never expires.'
              : 'Your bot will analyze markets and trade 24/7 while you sleep.'
            }
          </p>
        </div>

        {/* Choose Payment Mode */}
        {paymentMode === 'choose' && (
          <>
            <div className="px-6 pb-4 space-y-3">
              {/* Pay as you go option */}
              <button
                onClick={() => setPaymentMode('usage')}
                className="w-full p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] hover:border-[var(--accent)] transition-all text-left"
              >
                <div className="font-medium text-[var(--text-primary)]">Pay as you go</div>
                <div className="text-sm text-[var(--text-secondary)] mt-1">
                  Billed monthly for actual usage
                </div>
                <div className="text-xs text-[var(--text-tertiary)] mt-2">
                  ~${estimate.low}-{estimate.high}/mo typical
                </div>
              </button>

              {/* Prepay credits option */}
              <button
                onClick={() => setPaymentMode('prepay')}
                className="w-full p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] hover:border-[var(--accent)] transition-all text-left"
              >
                <div className="font-medium text-[var(--text-primary)]">Prepay credits</div>
                <div className="text-sm text-[var(--text-secondary)] mt-1">
                  Buy credits upfront, use until empty
                </div>
                <div className="text-xs text-[var(--text-tertiary)] mt-2">
                  Card or crypto • Never expires
                </div>
              </button>
            </div>

            {/* Trust Points */}
            <div className="px-6 pb-6 space-y-2">
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>Pay only for AI decisions</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>No base fee, cancel anytime</span>
              </div>
            </div>
          </>
        )}

        {/* Usage-based flow */}
        {paymentMode === 'usage' && (
          <>
            {/* Estimate Card */}
            <div className="px-6 pb-4">
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                <div className="text-center">
                  <div className="text-sm text-[var(--text-secondary)] mb-1">
                    Estimated cost
                  </div>
                  <div className="text-3xl font-bold text-[var(--text-primary)]">
                    ~${estimate.low}-{estimate.high}
                    <span className="text-base font-normal text-[var(--text-tertiary)]">/mo</span>
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)] mt-1">
                    {estimate.hasConfig ? 'Based on your configuration' : 'Typical range for most bots'}
                  </div>
                </div>
              </div>
            </div>

            {/* Trust Points */}
            <div className="px-6 pb-6 space-y-2">
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>Pay only for AI decisions</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>No base fee, cancel anytime</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>Full control over spending</span>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mx-6 mb-4 p-3 bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30 rounded-lg">
                <p className="text-sm text-[var(--loss-color)]">{error}</p>
              </div>
            )}

            {/* CTA */}
            <div className="p-6 pt-0">
              <button
                onClick={handleUpgrade}
                disabled={loading}
                className="w-full bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-[var(--bg-primary)] font-medium py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Starting checkout...
                  </>
                ) : (
                  'Continue to Payment'
                )}
              </button>
              <p className="text-center text-xs text-[var(--text-tertiary)] mt-3">
                Secure checkout via Stripe
              </p>
            </div>
          </>
        )}

        {/* Prepay credits flow */}
        {paymentMode === 'prepay' && (
          <div className="px-6 pb-6">
            <CreditPicker />
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
