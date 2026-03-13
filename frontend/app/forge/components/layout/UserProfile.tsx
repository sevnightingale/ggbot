'use client'

import React, { useState, useEffect } from 'react'
import { User, LogOut, Crown, Settings, Plus, Coins, AlertTriangle, Zap } from 'lucide-react'
import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { SettingsModal } from '@/components/SettingsModal'
import { AddCreditsModal } from '@/components/AddCreditsModal'
import { apiClient } from '@/lib/api'

interface UserProfileProps {
  className?: string
}

interface UserData {
  id: string
  email?: string
  user_metadata?: {
    name?: string
    full_name?: string
    avatar_url?: string
  }
}

export function UserProfile({}: UserProfileProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [userData, setUserData] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(true)
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [addCreditsOpen, setAddCreditsOpen] = useState(false)
  const [usageSummary, setUsageSummary] = useState<{
    usage_usd: number
    credits_usd: number | null
    net_balance_usd: number | null
  } | null>(null)
  const router = useRouter()
  const supabase = createClient()
  const { userProfile } = usePermissions()

  // Fetch user data
  useEffect(() => {
    const getUserData = async () => {
      try {
        const { data: { user }, error } = await supabase.auth.getUser()

        if (error) {
          console.error('Error fetching user:', error)
          return
        }

        if (user) {
          setUserData({
            id: user.id,
            email: user.email,
            user_metadata: user.user_metadata
          })
        }
      } catch (error) {
        console.error('Error in getUserData:', error)
      } finally {
        setLoading(false)
      }
    }

    getUserData()
  }, [supabase.auth])

  // Fetch Hyperliquid account status for connected users
  const [hlStatus, setHlStatus] = useState<{
    account_value: number | null
    withdrawable: number | null
  } | null>(null)

  useEffect(() => {
    if (userProfile?.hyperliquid_connected) {
      apiClient.getHyperliquidStatus()
        .then(status => {
          if (status?.connected) {
            setHlStatus({
              account_value: status.account_value,
              withdrawable: status.withdrawable ?? 0,
            })
          }
        })
        .catch(err => console.error('Failed to fetch HL status:', err))
    }
  }, [userProfile?.hyperliquid_connected])

  // Fetch usage summary for paid users (usage_based and prepaid)
  useEffect(() => {
    const fetchUsageSummary = async () => {
      const tier = userProfile?.subscription_tier
      // Fetch for both usage_based (metered) and prepaid users
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
          setUsageSummary(null)
        }
      }
    }

    fetchUsageSummary()
  }, [userProfile?.subscription_tier])

  // Logout handler
  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/login')
    } catch (error) {
      console.error('Error logging out:', error)
    }
  }

  // Check if user has paid subscription
  const hasPaidTier = userProfile?.can_activate_bots || false
  const isPro = userProfile?.subscription_tier === 'pro'
  const isUsageBased = userProfile?.subscription_tier === 'usage_based'
  const isPrepaid = userProfile?.subscription_tier === 'prepaid'
  const showCredits = isUsageBased || isPrepaid  // Both tiers can have credits

  // Get tier display name
  const getTierName = () => {
    if (isPro) return 'Pro Plan'
    if (isUsageBased) return 'Usage-Based'
    if (isPrepaid) return 'Prepaid'
    return 'Free Plan'
  }

  // Get display name from user metadata
  const getDisplayName = () => {
    if (!userData) return 'User'

    // Try full_name first (common for Google OAuth), then name, then fallback to 'User'
    return userData.user_metadata?.full_name ||
           userData.user_metadata?.name ||
           'User'
  }

  // Get display email
  const getDisplayEmail = () => {
    if (loading) return 'Loading...'
    return userData?.email || 'No email'
  }

  // Get avatar URL if available
  const getAvatarUrl = () => {
    return userData?.user_metadata?.avatar_url
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors overflow-hidden"
        title="User profile and settings"
      >
        {getAvatarUrl() ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={getAvatarUrl()}
            alt={getDisplayName()}
            className="h-full w-full object-cover"
            // Using img instead of Image for Supabase auth avatars - avoids need for domain config
          />
        ) : (
          <User className="h-4 w-4 text-[var(--text-primary)]" />
        )}
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 top-10 z-50 w-64 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-2 shadow-lg">
            {/* User Info */}
            <div className="border-b border-[var(--border)] px-3 py-2 mb-2">
              <div className="text-sm font-medium text-[var(--text-primary)]">{getDisplayName()}</div>
              <div className="text-xs text-[var(--text-muted)] truncate" title={getDisplayEmail()}>
                {getDisplayEmail()}
              </div>
              {/* Subscription Badge */}
              <div className="mt-2">
                {isPro ? (
                  <div className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-500">
                    <Crown className="h-3 w-3" />
                    {getTierName()}
                  </div>
                ) : isPrepaid ? (
                  <div className="inline-flex items-center gap-1 rounded-full bg-orange-500/20 px-2 py-0.5 text-xs font-medium text-orange-400">
                    {getTierName()}
                  </div>
                ) : isUsageBased ? (
                  <div className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs font-medium text-emerald-500">
                    {getTierName()}
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-1 rounded-full bg-[var(--bg-tertiary)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                    {getTierName()}
                  </div>
                )}
              </div>

            </div>

            {/* AI Credits Section (usage_based and prepaid users) */}
            {showCredits && usageSummary && (
              <div className="border-b border-[var(--border)] px-3 py-2 mb-2">
                <div className="flex items-center gap-1 text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">
                  <Coins className="h-2.5 w-2.5" />
                  AI Credits
                </div>
                <div className="text-[10px] text-[var(--text-muted)] mb-1.5">Powers your bot decisions</div>
                <div className="space-y-1 text-xs">
                  {usageSummary.credits_usd && usageSummary.credits_usd > 0 ? (
                    // User with credits - show balance and usage
                    <>
                      <div className="flex items-center justify-between text-[var(--text-primary)] font-medium">
                        <span>Balance</span>
                        <span className={usageSummary.net_balance_usd && usageSummary.net_balance_usd < 5 ? 'text-amber-500' : ''}>
                          ${usageSummary.net_balance_usd?.toFixed(2) ?? '0.00'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[var(--text-secondary)]">
                        <span>Used</span>
                        <span>${usageSummary.usage_usd.toFixed(2)}</span>
                      </div>
                      {isPrepaid && usageSummary.net_balance_usd !== null && usageSummary.net_balance_usd <= 0 && (
                        <div className="flex items-center gap-1 text-xs text-red-500">
                          <AlertTriangle className="h-3 w-3" />
                          <span>Depleted — bots paused</span>
                        </div>
                      )}
                    </>
                  ) : (
                    // Metered user without credits - show this month's usage
                    <div className="flex items-center justify-between text-[var(--text-secondary)]">
                      <span>This month</span>
                      <span>${usageSummary.usage_usd.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Trading Funds — Hyperliquid account overview */}
            {userProfile?.hyperliquid_connected && hlStatus && (
              <div className="border-b border-[var(--border)] px-3 py-2 mb-2">
                <div className="flex items-center gap-1 text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">
                  <Zap className="h-2.5 w-2.5" />
                  Trading Funds
                </div>
                <div className="text-[10px] text-[var(--text-muted)] mb-1.5">Your capital on Hyperliquid</div>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center justify-between text-[var(--text-secondary)]">
                    <span>Equity</span>
                    <span className="font-mono font-medium text-[var(--accent)]">
                      {hlStatus.account_value !== null ? `$${hlStatus.account_value.toFixed(2)}` : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[var(--text-muted)]">
                    <span>Withdrawable</span>
                    <span className="font-mono">
                      ${hlStatus.withdrawable?.toFixed(2) ?? '0.00'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Menu Items */}
            <div className="space-y-1">
              <MenuButton
                icon={Settings}
                label="Settings"
                onClick={() => {
                  setIsOpen(false)
                  setSettingsOpen(true)
                }}
              />
              {hasPaidTier ? (
                (isUsageBased || isPrepaid) && (
                  <MenuButton
                    icon={Plus}
                    label="Add AI Credits"
                    onClick={() => {
                      setIsOpen(false)
                      setAddCreditsOpen(true)
                    }}
                  />
                )
              ) : (
                <MenuButton
                  icon={Crown}
                  label="Subscribe"
                  onClick={() => {
                    setIsOpen(false)
                    setUpgradeModalOpen(true)
                  }}
                  highlight
                />
              )}
              <MenuButton icon={LogOut} label="Log out" onClick={handleLogout} />
            </div>
          </div>
        </>
      )}

      {/* Upgrade Modal - outside isOpen conditional so it can open when dropdown closes */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />

      {/* Settings Modal */}
      <SettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />

      {/* Add Credits Modal */}
      <AddCreditsModal
        open={addCreditsOpen}
        onOpenChange={setAddCreditsOpen}
        currentBalance={usageSummary?.net_balance_usd ?? undefined}
      />
    </div>
  )
}

interface MenuButtonProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  onClick?: () => void
  highlight?: boolean
}

function MenuButton({ icon: Icon, label, onClick, highlight = false }: MenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all ${
        highlight
          ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--border)] border border-[var(--border-hover)] font-medium'
          : 'text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  )
}