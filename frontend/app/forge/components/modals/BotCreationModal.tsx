'use client'

import React, { useState } from 'react'
import { Crown } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'

type BotType = 'scheduled_trading' | 'signal_validation' | 'agent'

interface BotCreationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (botType: BotType) => void
}

export function BotCreationModal({
  open,
  onOpenChange,
  onConfirm
}: BotCreationModalProps) {
  const [selectedType, setSelectedType] = useState<BotType>('scheduled_trading')
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const { canAccess } = usePermissions()

  const hasSignalValidation = canAccess('signal_validation')

  // Check for whitelist access (agent is whitelisted only for now)
  const whitelistUserId = process.env.NEXT_PUBLIC_WHITELIST_USER_ID
  const userProfile = usePermissions().userProfile
  const isWhitelisted = userProfile?.user_id === whitelistUserId
  const hasAgentAccess = isWhitelisted

  const botTypes = [
    {
      type: 'scheduled_trading' as const,
      icon: '⏰',
      label: 'Scheduled Trading',
      description: 'Automated trading on a fixed schedule (5m, 15m, 1h, etc.)',
      color: 'var(--agent-extraction)',
      available: true,
      tier: 'Free'
    },
    {
      type: 'signal_validation' as const,
      icon: '✓',
      label: 'Signal Validation',
      description: 'Validate external signals (Telegram, webhooks) with AI analysis',
      color: 'var(--agent-decision)',
      available: hasSignalValidation,
      tier: 'Pro'
    },
    {
      type: 'agent' as const,
      icon: '🤖',
      label: 'Agent',
      description: 'Autonomous AI agent that defines its own trading strategy through conversation',
      color: '#9333ea', // purple-600
      available: hasAgentAccess,
      tier: 'Whitelist'
    }
  ]

  const handleConfirm = () => {
    const selected = botTypes.find(t => t.type === selectedType)

    if (!selected?.available) {
      setUpgradeModalOpen(true)
      return
    }

    onConfirm(selectedType)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl">Create New Bot</DialogTitle>
          <DialogDescription>
            Choose the type of bot you want to create
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {botTypes.map(({ type, icon, label, description, color, available, tier }) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                selectedType === type
                  ? 'border-emerald-500 bg-emerald-500/10'
                  : 'border-[var(--border)] hover:border-[var(--border-hover)]'
              } ${!available ? 'opacity-60' : ''}`}
            >
              <div className="flex items-start gap-3">
                <div
                  className="text-3xl flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: available ? `${color}20` : 'var(--bg-tertiary)' }}
                >
                  {icon}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-[var(--text-primary)]">
                      {label}
                    </span>
                    {!available && tier === 'Pro' && (
                      <Crown className="h-3 w-3 text-[var(--text-muted)]" />
                    )}
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                      {tier}
                    </span>
                  </div>

                  <p className="text-sm text-[var(--text-secondary)]">
                    {description}
                  </p>
                </div>

                <div className={`flex-shrink-0 w-5 h-5 rounded-full border-2 mt-1 ${
                  selectedType === type
                    ? 'border-emerald-500 bg-emerald-500'
                    : 'border-[var(--border)]'
                }`}>
                  {selectedType === type && (
                    <div className="w-full h-full flex items-center justify-center text-white text-xs">
                      ✓
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border)]">
          <button
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleConfirm}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
          >
            {botTypes.find(t => t.type === selectedType)?.available ? 'Create Bot' : 'Upgrade to Create'}
          </button>
        </div>
      </DialogContent>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </Dialog>
  )
}
