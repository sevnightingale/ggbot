'use client'

import { useState, useEffect } from 'react'
import { Crown, CheckCircle2, Settings, Loader2, Zap, Coins, ExternalLink, Plus, AlertTriangle } from 'lucide-react'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalTitle,
} from '@/components/ui/modal'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { AddCreditsModal } from '@/components/AddCreditsModal'
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
    if (isUsageBased) return 'Pay as you go'
    return 'Free Plan'
  }

  // Live Trading state
  const [liveTradingSetupOpen, setLiveTradingSetupOpen] = useState(false)
  const [hlStatus, setHlStatus] = useState<{
    connected: boolean
    wallet_address: string | null
    account_value: number | null
    margin_used: number | null
    open_notional: number | null
    withdrawable: number | null
    positions_count: number | null
  } | null>(null)
  const [hlLoading, setHlLoading] = useState(true)

  // Upgrade modal state
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  // Add Credits modal state
  const [addCreditsOpen, setAddCreditsOpen] = useState(false)

  // Usage summary
  const [usageSummary, setUsageSummary] = useState<{
    usage_usd: number
    credits_usd: number | null
    net_balance_usd: number | null
  } | null>(null)

  // Error state
  const [error, setError] = useState('')

  // Fetch Hyperliquid status when modal opens
  useEffect(() => {
    if (open) {
      fetchHlStatus()
      fetchUsageSummary()
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

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

  const fetchUsageSummary = async () => {
    const tier = userProfile?.subscription_tier
    if (tier === 'usage_based' || tier === 'prepaid') {
      try {
        const summary = await apiClient.getUsageSummary()
        setUsageSummary({
          usage_usd: summary.usage_usd,
          credits_usd: summary.credits_usd,
          net_balance_usd: summary.net_balance_usd
        })
      } catch (err) {
        console.error('Failed to fetch usage summary:', err)
      }
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

            {/* ── AI Credits Section ── */}
            <section>
              <div className="flex items-center gap-2 mb-1">
                <Coins className="h-4 w-4 text-[var(--accent)]" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">AI Credits</h3>
              </div>
              <p className="text-xs text-[var(--text-muted)] mb-3">
                Powers your bot&apos;s AI decisions. Required to run any bot (paper or live).
              </p>

              {hasPaidTier ? (
                <div className="border border-[var(--border)] rounded-lg bg-[var(--bg-secondary)] overflow-hidden">
                  {/* Plan header */}
                  <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
                    <div className="flex items-center gap-2">
                      {isPro ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-500">
                          <Crown className="h-3 w-3" />
                          {getTierName()}
                        </span>
                      ) : isPrepaid ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-orange-500/20 px-2 py-0.5 text-xs font-medium text-orange-400">
                          {getTierName()}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs font-medium text-emerald-500">
                          {getTierName()}
                        </span>
                      )}
                      {isUsageBased && (
                        <span className="text-xs text-[var(--text-muted)]">Billed weekly for actual usage</span>
                      )}
                    </div>
                  </div>

                  {/* Usage / balance info */}
                  <div className="p-4">
                    {usageSummary ? (
                      <div className="space-y-2">
                        {usageSummary.credits_usd && usageSummary.credits_usd > 0 ? (
                          // Prepaid user — show balance breakdown
                          <>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-[var(--text-secondary)]">Credits purchased</span>
                              <span className="font-mono text-[var(--text-primary)]">${usageSummary.credits_usd.toFixed(2)}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-[var(--text-muted)]">Used</span>
                              <span className="font-mono text-[var(--text-muted)]">-${usageSummary.usage_usd.toFixed(2)}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm font-medium border-t border-[var(--border)] pt-2">
                              <span className="text-[var(--text-primary)]">Balance</span>
                              <span className={`font-mono ${usageSummary.net_balance_usd && usageSummary.net_balance_usd < 5 ? 'text-amber-500' : 'text-[var(--text-primary)]'}`}>
                                ${usageSummary.net_balance_usd?.toFixed(2) ?? '0.00'}
                              </span>
                            </div>
                            {isPrepaid && usageSummary.net_balance_usd !== null && usageSummary.net_balance_usd <= 0 && (
                              <div className="flex items-center gap-1 text-xs text-red-500 pt-1">
                                <AlertTriangle className="h-3 w-3" />
                                <span>Credits depleted — bots are paused</span>
                              </div>
                            )}
                          </>
                        ) : (
                          // Usage-based user — show this period's usage
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-[var(--text-secondary)]">This week</span>
                            <span className="font-mono text-[var(--text-primary)]">${usageSummary.usage_usd.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-sm text-[var(--text-muted)]">Loading usage...</div>
                    )}

                    {/* Action buttons */}
                    <div className="flex items-center gap-2 mt-4">
                      {(isUsageBased || isPrepaid) && (
                        <button
                          onClick={() => setAddCreditsOpen(true)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)]"
                        >
                          <Plus className="h-3 w-3" />
                          Add AI Credits
                        </button>
                      )}
                      <button
                        onClick={handleManageBilling}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Open Stripe
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                // Free user — subscribe CTA
                <div className="border border-dashed border-[var(--border)] rounded-lg p-6 text-center">
                  <p className="text-sm text-[var(--text-secondary)] mb-3">
                    Subscribe to activate your bots. Most bots cost less than $1/week.
                  </p>
                  <button
                    onClick={() => {
                      onOpenChange(false)
                      setUpgradeModalOpen(true)
                    }}
                    className="px-5 py-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] rounded-lg text-sm font-medium transition-colors"
                  >
                    Subscribe
                  </button>
                </div>
              )}
            </section>

            {/* ── Live Trading Section ── */}
            <section>
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-4 w-4 text-[var(--accent)]" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Hyperliquid live trading (self-custody)</h3>
                <span className="text-[10px] text-[var(--text-muted)] px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">Optional</span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mb-3">
                Your own Hyperliquid wallet — one live bot per user, fully
                non-custodial.
              </p>

              {hlLoading ? (
                <div className="flex items-center justify-center p-8 border border-dashed border-[var(--border)] rounded-lg">
                  <Loader2 className="h-5 w-5 animate-spin text-[var(--text-secondary)]" />
                </div>
              ) : hlStatus?.connected ? (
                /* Connected state */
                <div className="border border-[var(--signal)]/30 rounded-lg p-4 bg-[var(--signal)]/5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-[var(--signal)]" />
                      <span className="text-sm font-medium text-[var(--text-primary)]">Connected</span>
                      <span className="font-mono text-xs text-[var(--text-muted)]">
                        {hlStatus.wallet_address ? truncateAddress(hlStatus.wallet_address) : '...'}
                      </span>
                    </div>
                    <button
                      onClick={() => setLiveTradingSetupOpen(true)}
                      className="px-3 py-1 rounded-lg text-xs font-medium transition-colors bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                    >
                      Manage
                    </button>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-2.5 text-center">
                      <div className="text-[10px] text-[var(--text-muted)] mb-0.5">Equity</div>
                      <div className="text-sm font-mono font-medium text-[var(--accent)]">
                        {hlStatus.account_value !== null ? `$${hlStatus.account_value.toFixed(2)}` : '\u2014'}
                      </div>
                    </div>
                    <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-2.5 text-center">
                      <div className="text-[10px] text-[var(--text-muted)] mb-0.5">Withdrawable</div>
                      <div className="text-sm font-mono font-medium text-[var(--text-primary)]">
                        ${hlStatus.withdrawable?.toFixed(2) ?? '0.00'}
                      </div>
                    </div>
                    <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-2.5 text-center">
                      <div className="text-[10px] text-[var(--text-muted)] mb-0.5">Positions</div>
                      <div className="text-sm font-mono font-medium text-[var(--text-primary)]">
                        {hlStatus.positions_count ?? '\u2014'}
                      </div>
                    </div>
                  </div>
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

      {/* Add Credits Modal */}
      <AddCreditsModal
        open={addCreditsOpen}
        onOpenChange={setAddCreditsOpen}
        currentBalance={usageSummary?.net_balance_usd ?? undefined}
      />
    </>
  )
}
