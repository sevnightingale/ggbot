'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'

interface UserProfile {
  user_id: string
  subscription_tier: 'free' | 'ggbase'
  subscription_status: 'active' | 'cancelled' | 'past_due'
  can_use_premium_features: boolean
  requires_own_llm_keys: boolean
  can_publish_telegram_signals: boolean
  can_use_signal_validation: boolean
  can_use_live_trading: boolean
  paid_data_points: string[]
}

interface PermissionContextType {
  userProfile: UserProfile | null
  loading: boolean
  canAccess: (feature: string) => boolean
  hasSubscription: (tier: 'ggbase') => boolean
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
          paid_data_points: []
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

    switch (feature) {
      case 'signals':
        return userProfile.can_use_signal_validation

      case 'ggshot':
        return userProfile.paid_data_points.includes('ggshot')

      case 'telegram_publishing':
        return userProfile.can_publish_telegram_signals

      case 'premium_llms':
      case 'openai_gpt4':
        const hasAccess = userProfile.can_use_premium_features && !userProfile.requires_own_llm_keys
        console.log('premium_llms permission check:', {
          can_use_premium_features: userProfile.can_use_premium_features,
          requires_own_llm_keys: userProfile.requires_own_llm_keys,
          hasAccess
        })
        return hasAccess

      case 'platform_llm_keys':
        return userProfile.can_use_premium_features && !userProfile.requires_own_llm_keys

      case 'signal_validation_mode':
        return userProfile.can_use_signal_validation

      case 'live_trading':
        return userProfile.can_use_live_trading

      default:
        return true // Allow access to basic features by default
    }
  }

  const hasSubscription = (tier: 'ggbase'): boolean => {
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