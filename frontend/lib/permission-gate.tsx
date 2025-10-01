'use client'

import React, { useState } from 'react'
import { Crown } from 'lucide-react'
import { usePermissions } from './permissions'
import { UpgradeModal } from '@/components/UpgradeModal'

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
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

  // If user has access, render children
  if (canAccess(feature)) {
    return <>{children}</>
  }

  // If custom fallback provided, use it
  if (fallback) {
    return <>{fallback}</>
  }

  // Default upgrade prompt (charcoal/bone styling)
  if (showUpgrade) {
    return (
      <>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-[var(--bg-tertiary)] p-2">
              <Crown className="h-5 w-5 text-[var(--text-muted)]" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-[var(--text-primary)]">
                Premium Feature
              </h3>
              <p className="text-xs text-[var(--text-muted)]">
                Upgrade to Pro to access {getFeatureDescription(feature)}
              </p>
            </div>
            <button
              onClick={() => setUpgradeModalOpen(true)}
              className="rounded-lg bg-[var(--profit-color)] px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 transition-opacity"
            >
              Upgrade
            </button>
          </div>
        </div>

        <UpgradeModal
          open={upgradeModalOpen}
          onOpenChange={setUpgradeModalOpen}
        />
      </>
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