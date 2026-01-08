'use client'

import React, { useState } from 'react'
import { Loader2, CreditCard, Bitcoin } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface CreditPickerProps {
  currentBalance?: number
}

const CREDIT_AMOUNTS = [
  { cents: 1000, label: '$10' },
  { cents: 2500, label: '$25' },
  { cents: 5000, label: '$50' },
  { cents: 10000, label: '$100' },
]

export function CreditPicker({ currentBalance }: CreditPickerProps) {
  const [selectedAmount, setSelectedAmount] = useState<number>(2500) // Default $25
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'crypto'>('card')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handlePurchase = async () => {
    try {
      setLoading(true)
      setError(null)

      if (paymentMethod === 'card') {
        const { checkout_url } = await apiClient.purchaseCredits(selectedAmount)
        window.location.href = checkout_url
      } else {
        const { invoice_url } = await apiClient.purchaseCreditsCrypto(selectedAmount)
        window.location.href = invoice_url
      }
    } catch (err) {
      console.error('Credit purchase error:', err)
      setError(err instanceof Error ? err.message : 'Failed to start checkout')
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Current Balance (if provided) */}
      {currentBalance !== undefined && (
        <div className="text-center py-2 px-3 rounded-lg bg-[var(--bg-tertiary)]">
          <span className="text-sm text-[var(--text-secondary)]">Current balance: </span>
          <span className="text-sm font-medium text-[var(--text-primary)]">
            ${currentBalance.toFixed(2)}
          </span>
        </div>
      )}

      {/* Amount Selection */}
      <div className="grid grid-cols-4 gap-2">
        {CREDIT_AMOUNTS.map(({ cents, label }) => (
          <button
            key={cents}
            onClick={() => setSelectedAmount(cents)}
            className={`py-2 px-3 rounded-lg text-sm font-medium transition-all ${
              selectedAmount === cents
                ? 'bg-[var(--accent)] text-[var(--bg-primary)]'
                : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--border)]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Payment Method */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => setPaymentMethod('card')}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
            paymentMethod === 'card'
              ? 'bg-[var(--bg-tertiary)] border-2 border-[var(--accent)] text-[var(--text-primary)]'
              : 'bg-[var(--bg-tertiary)] border-2 border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          <CreditCard size={18} />
          Card
        </button>
        <button
          onClick={() => setPaymentMethod('crypto')}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
            paymentMethod === 'crypto'
              ? 'bg-[var(--bg-tertiary)] border-2 border-[var(--accent)] text-[var(--text-primary)]'
              : 'bg-[var(--bg-tertiary)] border-2 border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Bitcoin size={18} />
          Crypto
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30 rounded-lg">
          <p className="text-sm text-[var(--loss-color)]">{error}</p>
        </div>
      )}

      {/* Purchase Button */}
      <button
        onClick={handlePurchase}
        disabled={loading}
        className="w-full bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-[var(--bg-primary)] font-medium py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="animate-spin" size={18} />
            {paymentMethod === 'card' ? 'Starting checkout...' : 'Creating invoice...'}
          </>
        ) : (
          `Buy $${selectedAmount / 100} Credits`
        )}
      </button>

      {/* Info Text */}
      <p className="text-center text-xs text-[var(--text-tertiary)]">
        Credits never expire
        {paymentMethod === 'card' ? ' • Secure checkout via Stripe' : ' • Pay with any cryptocurrency'}
      </p>
    </div>
  )
}
