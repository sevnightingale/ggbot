'use client'

import React, { useState } from 'react'
import { Save, X, RotateCcw, Crown, Bot } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'
import { UpgradeModal } from '@/components/UpgradeModal'
import { usePermissions } from '@/lib/permissions'

interface SaveConfigBarProps {
  selectedBot?: BotConfiguration | null
  editingTableFields?: { config_name?: string; config_type?: string } | null
  hasUnsavedChanges?: boolean
  isEditingConfig?: boolean
  onSave?: () => void
  onCancel?: () => void
  onReset?: () => void
  onBotTypeChange?: (newType: 'scheduled_trading' | 'signal_validation' | 'agentic') => void
}

export function SaveConfigBar({
  selectedBot,
  editingTableFields,
  hasUnsavedChanges = false,
  isEditingConfig = false,
  onSave,
  onCancel,
  onReset,
  onBotTypeChange
}: SaveConfigBarProps) {
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const { canAccess, userProfile } = usePermissions()

  // Use editing config type if available, otherwise fall back to selected bot config type
  const currentBotType = editingTableFields?.config_type || selectedBot?.config_type || 'scheduled_trading'
  const hasSignalValidation = canAccess('signal_validation_mode')

  // Check if user is whitelisted for agentic mode
  const whitelistUserId = process.env.NEXT_PUBLIC_WHITELIST_USER_ID
  const isWhitelisted = userProfile?.user_id === whitelistUserId
  const hasAgenticAccess = isWhitelisted // For now, only whitelisted users

  return (
    <div className="sticky top-[64px] z-30 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 mb-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">

        {/* Left Section: Bot Type Selector (3 buttons) */}
        <div className="flex items-center gap-4">
          <div className="text-sm text-[var(--text-muted)]">Bot Type:</div>
          <div className="flex items-center rounded-xl border border-[var(--border)] bg-[var(--bg-primary)]">
            {/* Scheduled Trading */}
            <button
              onClick={() => onBotTypeChange?.('scheduled_trading')}
              className={`px-3 py-2 text-sm rounded-l-xl transition-colors flex items-center gap-1.5 ${
                currentBotType === 'scheduled_trading'
                  ? 'bg-[var(--agent-extraction)] text-white'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
              title="Automated trading on fixed schedule"
            >
              ⏰ Scheduled Trading
            </button>

            {/* Signal Validation */}
            {hasSignalValidation ? (
              <button
                onClick={() => onBotTypeChange?.('signal_validation')}
                className={`px-3 py-2 text-sm transition-colors border-l border-r border-[var(--border)] flex items-center gap-1.5 ${
                  currentBotType === 'signal_validation'
                    ? 'bg-[var(--agent-decision)] text-white'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
                title="Validate external signals with AI"
              >
                ✓ Signal Validation
              </button>
            ) : (
              <button
                onClick={() => setUpgradeModalOpen(true)}
                className="px-3 py-2 text-sm opacity-60 hover:opacity-80 transition-opacity text-[var(--text-muted)] border-l border-r border-[var(--border)] flex items-center gap-1.5"
                title="Requires Pro Plan"
              >
                ✓ Signal Validation
                <Crown className="h-3 w-3" />
              </button>
            )}

            {/* Agentic */}
            {hasAgenticAccess ? (
              <button
                onClick={() => onBotTypeChange?.('agentic')}
                className={`px-3 py-2 text-sm rounded-r-xl transition-colors flex items-center gap-1.5 ${
                  currentBotType === 'agentic'
                    ? 'bg-purple-600 text-white'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
                title="Autonomous AI agent with conversation"
              >
                🤖 Agentic
              </button>
            ) : (
              <button
                disabled
                className="px-3 py-2 text-sm rounded-r-xl opacity-40 cursor-not-allowed text-[var(--text-muted)] flex items-center gap-1.5"
                title="Coming soon"
              >
                🤖 Agentic
                <Crown className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Right Section: Unsaved Changes + Actions */}
        <div className="flex items-center gap-4">
          {/* Unsaved Changes Indicator */}
          {hasUnsavedChanges && (
            <div className="flex items-center gap-2 text-sm text-amber-500">
              <div className="h-2 w-2 rounded-full bg-amber-500"></div>
              Unsaved changes
            </div>
          )}

          {/* Action Buttons */}
          {isEditingConfig && (
            <div className="flex items-center gap-2">
              <button
                onClick={onReset}
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-2 text-sm hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
              >
                <RotateCcw className="h-4 w-4" />
                Reset
              </button>

              <button
                onClick={onCancel}
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-2 text-sm hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
              >
                <X className="h-4 w-4" />
                Cancel
              </button>

              <button
                onClick={onSave}
                disabled={!hasUnsavedChanges}
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-4 w-4" />
                Save Changes
              </button>
            </div>
          )}

          {/* Edit Button (when not editing) */}
          {!isEditingConfig && (
            <button
              onClick={() => {}} // TODO: Start editing
              className="inline-flex items-center gap-2 rounded-xl bg-[var(--agent-extraction)] px-3 py-2 text-sm font-medium text-white shadow-sm hover:opacity-90"
            >
              Configure Bot
            </button>
          )}
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </div>
  )
}