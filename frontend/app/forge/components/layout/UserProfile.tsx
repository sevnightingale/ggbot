'use client'

import React, { useState, useEffect } from 'react'
import { User, LogOut, Crown, CreditCard, Settings } from 'lucide-react'
import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'
import { SettingsModal } from '@/components/SettingsModal'
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

  // Logout handler
  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/login')
    } catch (error) {
      console.error('Error logging out:', error)
    }
  }

  // Billing portal handler
  const handleManageBilling = async () => {
    try {
      const { portal_url } = await apiClient.createPortalSession()
      window.location.href = portal_url
    } catch (error) {
      console.error('Error opening billing portal:', error)
      alert('Failed to open billing portal. Please try again.')
    }
  }

  // Check if user has paid subscription (usage_based or pro)
  const hasPaidTier = userProfile?.can_activate_bots || false
  const isPro = userProfile?.subscription_tier === 'pro'
  const isUsageBased = userProfile?.subscription_tier === 'usage_based'

  // Get tier display name
  const getTierName = () => {
    if (isPro) return 'Pro Plan'
    if (isUsageBased) return 'Usage-Based'
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
          <div className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-2 shadow-lg">
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
                <MenuButton
                  icon={CreditCard}
                  label="Manage Billing"
                  onClick={handleManageBilling}
                />
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