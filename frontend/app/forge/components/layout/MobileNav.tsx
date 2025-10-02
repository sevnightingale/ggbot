'use client'

import React, { useState } from 'react'
import { Bot, X } from 'lucide-react'
import { BotRail } from './BotRail'
import { BotConfiguration } from '@/lib/api'

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
  unrealized_pnl?: number
  current_pnl?: number  // Aggregate unrealized P&L of open positions
  portfolio_return_pct?: number  // Total P&L as % of initial balance
  total_balance?: number
  win_rate?: number
  avg_win?: number
  avg_loss?: number
  largest_win?: number
  largest_loss?: number
  sharpe_ratio?: number
}

interface MobileNavProps {
  className?: string
  // Bot rail props that need to be passed through
  bots: BotConfiguration[]
  selectedId: string | null
  onSelect: (configId: string) => void
  accounts: Account[]
  onCreateNew: () => void
  isCreatingNew: boolean
  onRename: (configId: string, newName: string) => void
  onDuplicate: (configId: string) => void
  onDelete: (configId: string) => void
  isBotAction: boolean
}

export function MobileNav({
  className = '',
  bots,
  selectedId,
  onSelect,
  accounts,
  onCreateNew,
  isCreatingNew,
  onRename,
  onDuplicate,
  onDelete,
  isBotAction
}: MobileNavProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  return (
    <>
      {/* Mobile Bottom Nav - Just the bot button */}
      <nav className={`fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--border)] bg-[var(--bg-secondary)] ${className}`}>
        <div className="flex items-center justify-center py-3">
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="flex flex-col items-center gap-1 px-6 py-2 text-xs text-[var(--text-primary)] hover:text-[var(--text-accent)] transition-colors"
          >
            <Bot className="h-5 w-5" />
            <span>Bots</span>
          </button>
        </div>
      </nav>

      {/* Mobile Drawer Overlay */}
      {isDrawerOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsDrawerOpen(false)}
          />

          {/* Drawer */}
          <div className="fixed left-0 top-0 bottom-0 z-50 w-80 max-w-[85vw] bg-[var(--bg-primary)] border-r border-[var(--border)] shadow-2xl">
            {/* Drawer Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Your Bots</h2>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-[var(--text-muted)]" />
              </button>
            </div>

            {/* Bot Rail Content */}
            <div className="flex-1 overflow-y-auto">
              <BotRail
                bots={bots}
                selectedId={selectedId}
                onSelect={(configId) => {
                  onSelect(configId)
                  setIsDrawerOpen(false) // Close drawer after selection
                }}
                accounts={accounts}
                onCreateNew={onCreateNew}
                isCreatingNew={isCreatingNew}
                onRename={onRename}
                onDuplicate={onDuplicate}
                onDelete={onDelete}
                isBotAction={isBotAction}
                className="w-full" // Remove grid classes for mobile
              />
            </div>
          </div>
        </>
      )}
    </>
  )
}