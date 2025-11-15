'use client'

import React from 'react'
import { BarChart2, Loader2, Circle } from 'lucide-react'
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
  onResetAccount?: (configId: string) => void
  isBotAction?: boolean
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
  onResetAccount,
  isBotAction = false,
  className = ''
}: BotRailProps) {
  const botLimit = 10  // Everyone gets 10 bots
  const currentBotCount = bots.length
  const atLimit = currentBotCount >= botLimit

  const handleCreateNew = () => {
    if (atLimit) {
      alert('You have reached the maximum of 10 bots. Please delete a bot to create a new one.')
      return
    }
    onCreateNew?.()
  }

  return (
    <aside className={className}>
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium text-[var(--text-primary)]">
            <BarChart2 className="h-4 w-4" />
            <div className="flex items-center gap-2">
              <span>Bots</span>
              <span className="text-xs text-[var(--text-muted)] font-normal">
                {currentBotCount}/{botLimit}
              </span>
            </div>
          </div>
          <button
            onClick={handleCreateNew}
            disabled={isCreatingNew || atLimit}
            className="rounded-xl border border-[var(--border)] px-2 py-1 text-xs transition-all text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--bg-tertiary)]"
          >
            {isCreatingNew ? (
              <span className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" /> Creating...
              </span>
            ) : '+ New'}
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
                onResetAccount={onResetAccount}
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
  onResetAccount?: (configId: string) => void
  isBotAction: boolean
}

function BotRow({
  bot,
  isSelected,
  onClick,
  onRename,
  onDuplicate,
  onDelete,
  onResetAccount,
  isBotAction
}: BotRowProps) {
  // Get bot metadata
  const isSignalDriven = bot.config_data.decision?.analysis_frequency === 'signal_driven'
  const configType =
    bot.config_type === 'signal_validation' ? 'Signal validation' :
    bot.config_type === 'agent' ? 'Agent strategy' :
    'Autonomous trading'
  const analysisFreq = bot.config_data.decision?.analysis_frequency || '1h'
  const frequency = isSignalDriven ? 'Signal driven' : `Every ${analysisFreq}`
  const isSymphony = bot.trading_mode === 'symphony'
  const isAster = bot.trading_mode === 'aster'

  return (
    <div
      className={`rounded-xl px-3 py-3 transition-colors relative ${
        isSelected ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
      }`}
    >
      <div
        onClick={onClick}
        className="cursor-pointer mb-2"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Circle
              className={`h-3 w-3 ${bot.state === 'active' ? 'text-[var(--accent)] fill-[var(--accent)]' : 'text-[var(--text-muted)]'}`}
            />
            <div className="text-sm font-medium text-[var(--text-primary)]">{bot.config_name}</div>
          </div>
          {(onRename || onDuplicate || onDelete || onResetAccount) && (
            <BotManagementMenu
              bot={bot}
              onRename={onRename || (() => {})}
              onDuplicate={onDuplicate || (() => {})}
              onDelete={onDelete || (() => {})}
              onResetAccount={onResetAccount}
              isBotAction={isBotAction}
            />
          )}
        </div>

        {/* Metadata badges */}
        <div className="flex flex-wrap gap-1 mb-2">
          <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
            {configType === 'Signal validation' ? 'Signal' : configType === 'Agent strategy' ? 'Agent' : 'Auto'}
          </span>
          {isSymphony && (
            <span
              className="rounded-full px-2 py-0.5 text-xs font-semibold"
              style={{
                backgroundColor: 'color-mix(in srgb, var(--signal) 10%, transparent)',
                borderWidth: '1px',
                borderStyle: 'solid',
                borderColor: 'color-mix(in srgb, var(--signal) 30%, transparent)',
                color: 'var(--signal)'
              }}
            >
              SYMPHONY
            </span>
          )}
          {isAster && (
            <span
              className="rounded-full px-2 py-0.5 text-xs font-semibold"
              style={{
                backgroundColor: 'color-mix(in srgb, var(--ember) 10%, transparent)',
                borderWidth: '1px',
                borderStyle: 'solid',
                borderColor: 'color-mix(in srgb, var(--ember) 30%, transparent)',
                color: 'var(--ember)'
              }}
            >
              ASTERDEX
            </span>
          )}
        </div>

        {/* Frequency */}
        <div className="text-xs text-[var(--text-muted)]">{frequency}</div>
      </div>
    </div>
  )
}