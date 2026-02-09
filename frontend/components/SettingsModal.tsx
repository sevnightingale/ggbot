'use client'

import { useState, useEffect } from 'react'
import { Crown, CheckCircle2, Settings, Loader2, Zap, Wallet } from 'lucide-react'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalTitle,
} from '@/components/ui/modal'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { LiveTradingSetupModal } from '@/components/LiveTradingSetupModal'
import { apiClient } from '@/lib/api'

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { userProfile, refreshProfile } = usePermissions()
  const isPro = userProfile?.subscription_tier === 'pro'
  const isUsageBased = userProfile?.subscription_tier === 'usage_based'
  const isPrepaid = userProfile?.subscription_tier === 'prepaid'
  const hasPaidTier = isPro || isUsageBased || isPrepaid

  // Get tier display name
  const getTierName = () => {
    if (isPro) return 'Pro Plan'
    if (isPrepaid) return 'Prepaid'
    if (isUsageBased) return 'Usage-Based'
    return 'Free Plan'
  }

  // Live Trading state
  const [liveTradingSetupOpen, setLiveTradingSetupOpen] = useState(false)
  const [hlStatus, setHlStatus] = useState<{
    connected: boolean
    wallet_address: string | null
    account_value: number | null
    available_balance: number | null
  } | null>(null)
  const [hlLoading, setHlLoading] = useState(true)

  // Upgrade modal state
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

  // Error state
  const [error, setError] = useState('')

  // Fetch Hyperliquid status when modal opens
  useEffect(() => {
    if (open) {
      fetchHlStatus()
    }
  }, [open])

  const fetchHlStatus = async () => {
    try {
      setHlLoading(true)
      const status = await apiClient.getHyperliquidStatus()
      setHlStatus(status)
    } catch (e) {
      console.error('Failed to check Hyperliquid status:', e)
      setHlStatus(null)
    } finally {
      setHlLoading(false)
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

  const truncateAddress = (addr: string) =>
    `${addr.slice(0, 6)}...${addr.slice(-4)}`

  return (
    <>
      <Modal open={open} onOpenChange={onOpenChange} size="lg">
        <ModalHeader onClose={() => onOpenChange(false)}>
          <div className="flex items-center gap-2">
            <div className="rounded-full bg-[var(--bg-tertiary)] p-2">
              <Settings className="h-5 w-5 text-[var(--text-primary)]" />
            </div>
            <ModalTitle className="text-2xl">Settings</ModalTitle>
          </div>
        </ModalHeader>

        <ModalBody>
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
                        {getTierName()}
                      </span>
                    ) : isPrepaid ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-orange-500/20 px-2 py-1 text-xs font-medium text-orange-400">
                        {getTierName()}
                      </span>
                    ) : isUsageBased ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-1 text-xs font-medium text-emerald-500">
                        {getTierName()}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--bg-tertiary)] px-2 py-1 text-xs font-medium text-[var(--text-secondary)]">
                        {getTierName()}
                      </span>
                    )}
                  </div>
                </div>
                {hasPaidTier ? (
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
                    Subscribe
                  </button>
                )}
              </div>
            </section>

            {/* Live Trading Section */}
            <section>
              <h3 className="text-sm font-semibold mb-3 text-[var(--text-primary)]">Live Trading</h3>

              {hlLoading ? (
                <div className="flex items-center justify-center p-8 border border-dashed border-[var(--border)] rounded-lg">
                  <Loader2 className="h-5 w-5 animate-spin text-[var(--text-secondary)]" />
                </div>
              ) : hlStatus?.connected ? (
                /* Connected state */
                <div className="border border-[var(--signal)]/30 rounded-lg p-4 bg-[var(--signal)]/5">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-[var(--signal)] mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="font-medium text-[var(--text-primary)] mb-2">
                        Live Trading Connected
                      </p>
                      <div className="space-y-1 text-sm text-[var(--text-secondary)]">
                        <div className="flex items-center gap-2">
                          <Wallet className="h-3 w-3 text-[var(--text-muted)]" />
                          <span className="font-mono text-xs">
                            {hlStatus.wallet_address ? truncateAddress(hlStatus.wallet_address) : '...'}
                          </span>
                        </div>
                        {hlStatus.account_value !== null && (
                          <div className="flex items-center gap-2">
                            <span className="text-[var(--text-muted)]">Account:</span>
                            <span className="font-mono font-medium text-[var(--accent)]">
                              ${hlStatus.account_value.toFixed(2)}
                            </span>
                          </div>
                        )}
                        {hlStatus.available_balance !== null && (
                          <div className="flex items-center gap-2">
                            <span className="text-[var(--text-muted)]">Available:</span>
                            <span className="font-mono">
                              ${hlStatus.available_balance.toFixed(2)}
                            </span>
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => setLiveTradingSetupOpen(true)}
                        className="mt-3 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                      >
                        Manage Funds
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mt-3">Powered by Hyperliquid</p>
                </div>
              ) : (
                /* Not connected state */
                <div className="border border-dashed border-[var(--border)] rounded-lg p-6">
                  <div className="flex items-start gap-3 mb-4">
                    <Zap className="h-5 w-5 text-[var(--text-secondary)] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-[var(--text-primary)] mb-1">Set Up Live Trading</p>
                      <p className="text-sm text-[var(--text-secondary)]">
                        Trade real perpetual futures with your AI bots. Powered by Hyperliquid.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setLiveTradingSetupOpen(true)}
                    className="w-full px-4 py-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] rounded-lg font-medium transition-colors"
                  >
                    Set Up Live Trading
                  </button>
                </div>
              )}
            </section>

            {error && (
              <div className="text-sm text-[var(--ember)]">{error}</div>
            )}
          </div>
        </ModalBody>
      </Modal>

      {/* Live Trading Setup Modal */}
      <LiveTradingSetupModal
        open={liveTradingSetupOpen}
        onOpenChange={setLiveTradingSetupOpen}
        onComplete={() => {
          fetchHlStatus()
          refreshProfile()
        }}
      />

      {/* Upgrade Modal */}
      <UpgradeModal open={upgradeModalOpen} onOpenChange={setUpgradeModalOpen} />
    </>
  )
}
