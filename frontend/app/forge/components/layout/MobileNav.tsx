'use client'

import React, { useState } from 'react'
import { Bot, X, BarChart3, Settings } from 'lucide-react'
import { BotRail } from './BotRail'
import { BotConfiguration } from '@/lib/api'

interface MobileNavProps {
  className?: string
  // Bot rail props that need to be passed through
  bots: BotConfiguration[]
  selectedId: string | null
  onSelect: (configId: string) => void
  onCreateNew: () => void
  isCreatingNew: boolean
  onRename: (configId: string, newName: string) => void
  onDuplicate: (configId: string) => void
  onDelete: (configId: string) => void
  isBotAction: boolean
  // Tab navigation props
  activeTab?: 'monitor' | 'configure'
  onTabChange?: (tab: 'monitor' | 'configure') => void
}

export function MobileNav({
  className = '',
  bots,
  selectedId,
  onSelect,
  onCreateNew,
  isCreatingNew,
  onRename,
  onDuplicate,
  onDelete,
  isBotAction,
  activeTab = 'monitor',
  onTabChange
}: MobileNavProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  return (
    <>
      {/* Mobile Bottom Nav - Three buttons: Bots, Monitor, Configure */}
      <nav className={`fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--border)] bg-[var(--bg-secondary)] ${className}`}>
        <div className="flex items-center justify-around py-3">
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="flex flex-col items-center gap-1 px-4 py-2 text-xs text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors"
          >
            <Bot className="h-5 w-5" />
            <span>Your ggbots</span>
          </button>
          <button
            onClick={() => onTabChange?.('monitor')}
            className={`flex flex-col items-center gap-1 px-4 py-2 text-xs transition-colors ${
              activeTab === 'monitor'
                ? 'text-[var(--accent)]'
                : 'text-[var(--text-primary)] hover:text-[var(--accent)]'
            }`}
          >
            <BarChart3 className="h-5 w-5" />
            <span>Monitor</span>
          </button>
          <button
            onClick={() => onTabChange?.('configure')}
            className={`flex flex-col items-center gap-1 px-4 py-2 text-xs transition-colors ${
              activeTab === 'configure'
                ? 'text-[var(--accent)]'
                : 'text-[var(--text-primary)] hover:text-[var(--accent)]'
            }`}
          >
            <Settings className="h-5 w-5" />
            <span>Configure</span>
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
          <div className="fixed left-0 top-0 bottom-0 z-50 w-80 max-w-[85vw] bg-[var(--bg-primary)] border-r border-[var(--border)] shadow-2xl flex flex-col">
            {/* Drawer Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--border)] flex-shrink-0">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Your ggbots</h2>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-[var(--text-muted)]" />
              </button>
            </div>

            {/* Bot Rail Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-4">
              <BotRail
                bots={bots}
                selectedId={selectedId}
                onSelect={(configId) => {
                  onSelect(configId)
                  setIsDrawerOpen(false) // Close drawer after selection
                }}
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