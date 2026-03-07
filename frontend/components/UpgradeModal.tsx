'use client'

import { useState, useMemo } from 'react'
import { Loader2, Check, Bot, ChevronLeft } from 'lucide-react'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalTitle,
  ModalDescription,
} from '@/components/ui/modal'
import { apiClient, BotConfiguration } from '@/lib/api'
import { CreditPicker } from '@/components/CreditPicker'
import { usePermissions } from '@/lib/permissions'

interface UpgradeModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  botConfig?: BotConfiguration  // The specific bot being activated
}

type PaymentMode = 'choose' | 'usage' | 'prepay'

import { MODEL_TIER_COSTS, FREQUENCY_TO_DECISIONS } from '@/lib/cost-estimation'

// Human-readable frequency labels
const FREQUENCY_LABELS: Record<string, string> = {
  '5m': 'every 5 min',
  '15m': 'every 15 min',
  '30m': 'every 30 min',
  '1h': 'every hour',
  '4h': 'every 4 hours',
  '1d': 'daily',
  '1w': 'weekly',
  'signal_driven': 'signal-driven'
}

export function UpgradeModal({ open, onOpenChange, botConfig }: UpgradeModalProps) {
  const { userProfile } = usePermissions()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('choose')

  // Calculate estimate based on bot config (weekly, to match billing)
  const estimate = useMemo(() => {
    if (!botConfig) {
      // Fallback for generic modal (no specific bot) - weekly estimate
      return {
        low: 1,
        high: 4,
        hasConfig: false,
        model: 'default',
        tier: 'standard' as const,
        frequency: '1h',
        frequencyLabel: 'every hour',
        economyLow: 0,
        economyHigh: 1
      }
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
    const economyCostPerDecision = modelCosts['economy']

    // Get frequency from config
    const frequency = botConfig.config_data.decision?.analysis_frequency || '1h'
    const decisionsPerDay = FREQUENCY_TO_DECISIONS[frequency] || 24
    const decisionsPerWeek = decisionsPerDay * 7

    // Calculate weekly cost (billing is weekly)
    const baseCost = decisionsPerWeek * costPerDecision
    const economyBaseCost = decisionsPerWeek * economyCostPerDecision

    // Add ±30% range for variance (market activity, actual decisions made)
    const low = Math.max(1, Math.round(baseCost * 0.7))
    const high = Math.round(baseCost * 1.3)

    // Economy tier estimate (for the tip)
    const economyLow = Math.max(0.1, Math.round(economyBaseCost * 0.7 * 10) / 10)
    const economyHigh = Math.round(economyBaseCost * 1.3 * 10) / 10

    return {
      low,
      high,
      hasConfig: true,
      model,
      tier,
      frequency,
      frequencyLabel: FREQUENCY_LABELS[frequency] || frequency,
      economyLow,
      economyHigh
    }
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
    <Modal open={open} onOpenChange={handleOpenChange} size="sm">
      <ModalHeader onClose={() => handleOpenChange(false)}>
        <ModalTitle className="flex items-center gap-2">
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
        </ModalTitle>
        <ModalDescription>
          {paymentMode === 'prepay'
            ? 'Buy credits upfront. Use until empty, never expires.'
            : 'Your bot will analyze markets and trade 24/7 while you sleep.'
          }
        </ModalDescription>
      </ModalHeader>

      <ModalBody className="p-0">
        {/* Choose Payment Mode */}
        {paymentMode === 'choose' && (
          <>
            {/* Anchor: Most bots cost less than $1/week */}
            <div className="px-4 sm:px-6 pb-3">
              <div className="text-center text-sm text-[var(--text-secondary)]">
                Most bots cost <span className="font-medium text-[var(--text-primary)]">less than $1/week</span>
              </div>
            </div>

            <div className="px-4 sm:px-6 pb-4 space-y-3">
              {/* Pay as you go option */}
              <button
                onClick={() => setPaymentMode('usage')}
                className="w-full p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] hover:border-[var(--accent)] transition-all text-left"
              >
                <div className="font-medium text-[var(--text-primary)]">Pay as you go</div>
                <div className="text-sm text-[var(--text-secondary)] mt-1">
                  Billed weekly for actual usage
                </div>
                <div className="text-xs text-[var(--text-tertiary)] mt-2">
                  Your bot: ~${estimate.low}-{estimate.high}/week
                </div>
              </button>

              {/* Prepay credits option */}
              <button
                onClick={() => setPaymentMode('prepay')}
                className="w-full p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] hover:border-[var(--accent)] transition-all text-left"
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
            <div className="px-4 sm:px-6 pb-6 space-y-2">
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>Pay only for AI decisions</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Check size={16} className="text-[var(--profit-color)] flex-shrink-0" />
                <span>No base fee, cancel anytime</span>
              </div>
              {userProfile?.hyperliquid_connected && (
                <div className="mt-2 pt-2 border-t border-[var(--border)]">
                  <p className="text-xs text-[var(--text-tertiary)]">
                    This covers AI decisions only. Your Hyperliquid trading funds are separate.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {/* Usage-based flow */}
        {paymentMode === 'usage' && (
          <>
            {/* Estimate Card with breakdown */}
            <div className="px-4 sm:px-6 pb-4">
              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
                <div className="text-center mb-3">
                  <div className="text-3xl font-bold text-[var(--text-primary)]">
                    ~${estimate.low}-{estimate.high}
                    <span className="text-base font-normal text-[var(--text-tertiary)]">/week</span>
                  </div>
                </div>

                {/* What's driving the cost */}
                {estimate.hasConfig && (
                  <div className="text-xs text-[var(--text-tertiary)] space-y-1 border-t border-[var(--border)] pt-3">
                    <div className="flex justify-between">
                      <span>Model</span>
                      <span className="text-[var(--text-secondary)] capitalize">{estimate.model}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Reasoning</span>
                      <span className="text-[var(--text-secondary)] capitalize">{estimate.tier}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Frequency</span>
                      <span className="text-[var(--text-secondary)]">{estimate.frequencyLabel}</span>
                    </div>
                  </div>
                )}

                {/* Economy tier tip - only show if not already on economy */}
                {estimate.hasConfig && estimate.tier !== 'economy' && (
                  <div className="mt-3 pt-3 border-t border-[var(--border)]">
                    <div className="flex items-start gap-2 text-xs">
                      <span className="text-[var(--accent)]">💡</span>
                      <span className="text-[var(--text-secondary)]">
                        Switch to <span className="font-medium">economy</span> tier for ~${estimate.economyLow < 1 ? estimate.economyLow.toFixed(2) : estimate.economyLow}-{estimate.economyHigh < 1 ? estimate.economyHigh.toFixed(2) : estimate.economyHigh}/week
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Trust Points */}
            <div className="px-4 sm:px-6 pb-4 space-y-2">
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
              <div className="mx-4 sm:mx-6 mb-4 p-3 bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30 rounded-lg">
                <p className="text-sm text-[var(--loss-color)]">{error}</p>
              </div>
            )}

            {/* CTA */}
            <div className="px-4 sm:px-6 pb-6">
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
          <div className="px-4 sm:px-6 pb-6">
            <CreditPicker />
          </div>
        )}
      </ModalBody>
    </Modal>
  )
}
