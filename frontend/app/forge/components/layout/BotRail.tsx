'use client'

import React from 'react'
import { BotConfiguration } from '@/lib/api'

interface BotRailProps {
  bots: BotConfiguration[]
  selectedId: string | null
  onSelect: (configId: string) => void
  className?: string
}

export function BotRail({ bots, selectedId, onSelect, className = '' }: BotRailProps) {
  return (
    <aside className={`w-64 border-r border-[var(--border)] bg-[var(--bg-secondary)] ${className}`}>
      <div className="p-4">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium text-[var(--text-primary)]">
            <div className="h-4 w-4">📊</div>
            Bots
          </div>
          <button className="rounded-xl border border-[var(--border)] px-2 py-1 text-xs hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)]">
            + New
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
}

function BotRow({ bot, isSelected, onClick }: BotRowProps) {
  return (
    <div
      onClick={onClick}
      className={`flex items-center justify-between rounded-xl px-3 py-2 cursor-pointer transition-colors ${
        isSelected ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
      }`}
    >
      <div className="flex items-center gap-2">
        <div className={`h-4 w-4 ${bot.state === 'active' ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>
          {bot.state === 'active' ? '●' : '○'}
        </div>
        <div className="text-sm text-[var(--text-primary)]">{bot.config_name}</div>
      </div>
      <div className="text-xs text-[var(--text-muted)]">
        Paper
        {/* Future: P&L display will go here */}
      </div>
    </div>
  )
}