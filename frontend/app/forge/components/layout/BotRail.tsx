'use client'

import React, { useState } from 'react'
import { Crown } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'
import { BotManagementMenu } from './BotManagementMenu'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'

interface Account {
  config_id: string
  account_id: string
  current_balance: number
  total_pnl: number
  total_trades: number
  win_trades: number
  loss_trades: number
  open_positions: number
  updated_at: string
}

interface BotRailProps {
  bots: BotConfiguration[]
  selectedId: string | null
  onSelect: (configId: string) => void
  accounts?: Account[]
  onCreateNew?: () => void
  isCreatingNew?: boolean
  onRename?: (configId: string, newName: string) => void
  onDuplicate?: (configId: string) => void
  onDuplicateAsLive?: (configId: string) => void
  onDelete?: (configId: string) => void
  onResetAccount?: (configId: string) => void
  isBotAction?: boolean
  className?: string
}

export function BotRail({
  bots,
  selectedId,
  onSelect,
  accounts = [],
  onCreateNew,
  isCreatingNew = false,
  onRename,
  onDuplicate,
  onDuplicateAsLive,
  onDelete,
  onResetAccount,
  isBotAction = false,
  className = ''
}: BotRailProps) {
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const { hasSubscription } = usePermissions()

  const isPro = hasSubscription('ggbase')
  const botLimit = isPro ? 10 : 1
  const currentBotCount = bots.length
  const atLimit = currentBotCount >= botLimit

  const handleCreateNew = () => {
    if (atLimit && !isPro) {
      setUpgradeModalOpen(true)
      return
    }
    onCreateNew?.()
  }

  return (
    <aside className={className}>
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium text-[var(--text-primary)]">
            <div className="h-4 w-4">📊</div>
            <div className="flex items-center gap-2">
              <span>Bots</span>
              <span className="text-xs text-[var(--text-muted)] font-normal">
                {currentBotCount}/{botLimit}
              </span>
            </div>
          </div>
          <button
            onClick={handleCreateNew}
            disabled={isCreatingNew}
            className={`rounded-xl border border-[var(--border)] px-2 py-1 text-xs transition-all text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed ${
              atLimit && !isPro ? 'hover:opacity-80 opacity-60' : 'hover:bg-[var(--bg-tertiary)]'
            }`}
          >
            {isCreatingNew ? '⟳ Creating...' : atLimit && !isPro ? (
              <span className="flex items-center gap-1">
                + New <Crown className="h-3 w-3" />
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
                account={accounts.find(acc => acc.config_id === bot.config_id)}
                isSelected={bot.config_id === selectedId}
                onClick={() => onSelect(bot.config_id)}
                onRename={onRename}
                onDuplicate={onDuplicate}
                onDuplicateAsLive={onDuplicateAsLive}
                onDelete={onDelete}
                onResetAccount={onResetAccount}
                isBotAction={isBotAction}
              />
            ))
          )}
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </aside>
  )
}

interface BotRowProps {
  bot: BotConfiguration
  account?: Account
  isSelected: boolean
  onClick: () => void
  onRename?: (configId: string, newName: string) => void
  onDuplicate?: (configId: string) => void
  onDuplicateAsLive?: (configId: string) => void
  onDelete?: (configId: string) => void
  onResetAccount?: (configId: string) => void
  isBotAction: boolean
}

function BotRow({
  bot,
  account,
  isSelected,
  onClick,
  onRename,
  onDuplicate,
  onDuplicateAsLive,
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
  const balance = account?.current_balance ?? 10000
  const balanceText = `$${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  const isLive = bot.trading_mode === 'live'
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
            <div className={`h-3 w-3 ${bot.state === 'active' ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>
              {bot.state === 'active' ? '●' : '○'}
            </div>
            <div className="text-sm font-medium text-[var(--text-primary)]">{bot.config_name}</div>
          </div>
          {(onRename || onDuplicate || onDuplicateAsLive || onDelete || onResetAccount) && (
            <BotManagementMenu
              bot={bot}
              onRename={onRename || (() => {})}
              onDuplicate={onDuplicate || (() => {})}
              onDuplicateAsLive={onDuplicateAsLive}
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
          {isLive ? (
            <span className="rounded-full bg-red-500/10 border border-red-500/30 px-2 py-0.5 text-xs font-semibold text-red-500">
              LIVE TRADING
            </span>
          ) : isAster ? (
            <span className="rounded-full bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 text-xs font-semibold text-purple-500">
              ASTER
            </span>
          ) : (
            <span className="rounded-full bg-[var(--agent-extraction)]/10 border border-[var(--agent-extraction)]/30 px-2 py-0.5 text-xs" style={{ color: 'var(--agent-extraction)' }}>
              {balanceText}
            </span>
          )}
        </div>

        {/* Frequency */}
        <div className="text-xs text-[var(--text-muted)]">{frequency}</div>
      </div>
    </div>
  )
}