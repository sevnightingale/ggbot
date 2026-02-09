'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'

interface UserProfile {
  user_id: string
  subscription_tier: 'free' | 'prepaid' | 'usage_based' | 'pro'
  subscription_status: 'active' | 'cancelled' | 'past_due'
  can_use_premium_features: boolean
  requires_own_llm_keys: boolean
  can_publish_telegram_signals: boolean
  can_use_signal_validation: boolean
  can_use_live_trading: boolean
  can_activate_bots: boolean
  can_use_agents: boolean
  paid_data_points: string[]
  // Credit-related fields
  credit_balance_usd: number | null  // Current credit balance (null if no Stripe integration)
  has_available_credits: boolean     // True if can start bot (non-prepaid OR prepaid with credits > 0)
  // Live trading connection status
  hyperliquid_connected: boolean
}

interface PermissionContextType {
  userProfile: UserProfile | null
  loading: boolean
  canAccess: (feature: string) => boolean
  hasSubscription: (tier: 'usage_based' | 'pro') => boolean
  hasPaidDataPoint: (dataPoint: string) => boolean
}

const PermissionContext = createContext<PermissionContextType | undefined>(undefined)

export function usePermissions() {
  const context = useContext(PermissionContext)
  if (context === undefined) {
    // Return safe defaults instead of throwing during hydration/SSR
    return {
      userProfile: null,
      loading: true,
      canAccess: () => false,
      hasSubscription: () => false,
      hasPaidDataPoint: () => false,
    }
  }
  return context
}

interface PermissionProviderProps {
  children: React.ReactNode
}

export function PermissionProvider({ children }: PermissionProviderProps) {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  // Handle hydration
  useEffect(() => {
    setMounted(true)
  }, [])

  // Load user profile when mounted
  useEffect(() => {
    if (!mounted) return

    const loadUserProfile = async () => {
      try {
        setLoading(true)
        const profile = await apiClient.getUserProfile()
        setUserProfile(profile)
      } catch (error) {
        console.error('Failed to load user profile:', error)
        // Fallback to free tier on error - user_id will be set by calling component
        setUserProfile({
          user_id: '', // Will be updated by ForgeApp
          subscription_tier: 'free',
          subscription_status: 'cancelled',
          can_use_premium_features: false,
          requires_own_llm_keys: true,
          can_publish_telegram_signals: false,
          can_use_signal_validation: false,
          can_use_live_trading: false,
          can_activate_bots: false,
          can_use_agents: false,
          paid_data_points: [],
          credit_balance_usd: null,
          has_available_credits: false,
          hyperliquid_connected: false
        })
      } finally {
        setLoading(false)
      }
    }

    loadUserProfile()
  }, [mounted])

  // Permission checking functions
  const canAccess = (feature: string): boolean => {
    if (!userProfile) return false // Default to no access if profile not loaded

    // SIMPLIFIED PERMISSION MODEL
    // Only 3 features are gated:
    // 1. bot_activation - requires paid subscription + credits (for prepaid)
    // 2. agents - requires PRO tier
    // 3. ggshot - requires special data point access
    // Everything else is available to all users (configure, view, etc.)

    switch (feature) {
      case 'bot_activation':
        // Must have subscription AND available credits (for prepaid users)
        // has_available_credits is true for usage_based/pro (they get billed)
        // has_available_credits is false for prepaid users with 0 credits
        return userProfile.can_activate_bots && userProfile.has_available_credits

      case 'agents':
        return userProfile.can_use_agents

      case 'ggshot':
        return userProfile.paid_data_points.includes('ggshot')

      case 'telegram_publishing':
        return userProfile.can_publish_telegram_signals

      default:
        // All other features available to everyone
        // (LLM models, frequencies, signal validation, live trading, etc.)
        return true
    }
  }

  const hasSubscription = (tier: 'usage_based' | 'pro'): boolean => {
    if (!userProfile) return false
    return userProfile.subscription_tier === tier && userProfile.subscription_status === 'active'
  }

  const hasPaidDataPoint = (dataPoint: string): boolean => {
    if (!userProfile) return false
    return userProfile.paid_data_points.includes(dataPoint)
  }

  // Prevent flash during hydration
  if (!mounted) {
    return <div className="min-h-screen bg-[#161618]">{children}</div>
  }

  const contextValue: PermissionContextType = {
    userProfile,
    loading,
    canAccess,
    hasSubscription,
    hasPaidDataPoint,
  }

  return (
    <PermissionContext.Provider value={contextValue}>
      {children}
    </PermissionContext.Provider>
  )
}