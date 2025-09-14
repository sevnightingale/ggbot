'use client'

import React from 'react'
import { BotConfiguration } from '@/lib/api'
import { BotManagementMenu } from './BotManagementMenu'

interface BotRailProps {
  bots: BotConfiguration[]
  selectedId: string | null
  onSelect: (configId: string) => void
  onCreateNew?: () => void
  isCreatingNew?: boolean
  onRename?: (configId: string, newName: string) => void
  onDuplicate?: (configId: string) => void
  onDelete?: (configId: string) => void
  isBotAction?: boolean
  hasUnsavedChanges?: boolean
  className?: string
}

export function BotRail({
  bots,
  selectedId,
  onSelect,
  onCreateNew,
  isCreatingNew = false,
  onRename,
  onDuplicate,
  onDelete,
  isBotAction = false,
  hasUnsavedChanges = false,
  className = ''
}: BotRailProps) {
  return (
    <aside className={className}>
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium text-[var(--text-primary)]">
            <div className="h-4 w-4">📊</div>
            Bots
          </div>
          <button
            onClick={onCreateNew}
            disabled={isCreatingNew}
            className="rounded-xl border border-[var(--border)] px-2 py-1 text-xs hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreatingNew ? '⟳ Creating...' : '+ New'}
          </button>
        </div>

        <div className="space-y-2">
          {bots.length === 0 ? (
            <div className="text-sm text-[var(--text-muted)] p-4 text-center">
              No bots yet
            </div>
          ) : (
            bots.map((bot) => (
              <BotRow
                key={bot.config_id}
                bot={bot}
                isSelected={bot.config_id === selectedId}
                onClick={() => onSelect(bot.config_id)}
                onRename={onRename}
                onDuplicate={onDuplicate}
                onDelete={onDelete}
                isBotAction={isBotAction}
              />
            ))
          )}
        </div>
      </div>
    </aside>
  )
}

interface BotRowProps {
  bot: BotConfiguration
  isSelected: boolean
  onClick: () => void
  onRename?: (configId: string, newName: string) => void
  onDuplicate?: (configId: string) => void
  onDelete?: (configId: string) => void
  isBotAction: boolean
}

function BotRow({
  bot,
  isSelected,
  onClick,
  onRename,
  onDuplicate,
  onDelete,
  isBotAction
}: BotRowProps) {
  return (
    <div
      className={`flex items-center justify-between rounded-xl px-3 py-2 transition-colors relative ${
        isSelected ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
      }`}
    >
      <div
        onClick={onClick}
        className="flex items-center gap-2 flex-1 cursor-pointer"
      >
        <div className={`h-4 w-4 ${bot.state === 'active' ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>
          {bot.state === 'active' ? '●' : '○'}
        </div>
        <div className="text-sm text-[var(--text-primary)]">{bot.config_name}</div>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-xs text-[var(--text-muted)]">
          Paper
          {/* Future: P&L display will go here */}
        </div>
        {(onRename || onDuplicate || onDelete) && (
          <BotManagementMenu
            bot={bot}
            onRename={onRename || (() => {})}
            onDuplicate={onDuplicate || (() => {})}
            onDelete={onDelete || (() => {})}
            isBotAction={isBotAction}
            hasUnsavedChanges={hasUnsavedChanges}
          />
        )}
      </div>
    </div>
  )
}