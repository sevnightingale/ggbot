'use client'

import React from 'react'
import { usePermissions } from './permissions'

interface PermissionGateProps {
  feature: string
  children: React.ReactNode
  fallback?: React.ReactNode
  showUpgrade?: boolean
}

export function PermissionGate({
  feature,
  children,
  fallback,
  showUpgrade = true
}: PermissionGateProps) {
  const { canAccess } = usePermissions()

  // If user has access, render children
  if (canAccess(feature)) {
    return <>{children}</>
  }

  // If custom fallback provided, use it
  if (fallback) {
    return <>{fallback}</>
  }

  // Default upgrade prompt
  if (showUpgrade) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-amber-100 p-2">
            <svg className="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m2-12a9 9 0 110 18 9 9 0 010-18z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-medium text-[var(--text-primary)]">
              Premium Feature
            </h3>
            <p className="text-xs text-[var(--text-secondary)]">
              Upgrade to ggbase to access {getFeatureDescription(feature)}
            </p>
          </div>
          <button
            onClick={() => {
              // TODO: Open upgrade modal
              alert('Upgrade to ggbase to unlock this feature!')
            }}
            className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700"
          >
            Upgrade
          </button>
        </div>
      </div>
    )
  }

  // Hide completely
  return null
}

function getFeatureDescription(feature: string): string {
  const descriptions: Record<string, string> = {
    'signals': 'signal trading',
    'ggshot': 'ggShot signals',
    'telegram_publishing': 'Telegram publishing',
    'premium_llms': 'premium AI models',
    'openai_gpt4': 'OpenAI GPT-4',
    'signal_validation_mode': 'signal validation',
    'platform_llm_keys': 'platform AI keys',
  }

  return descriptions[feature] || 'this feature'
}