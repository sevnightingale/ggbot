'use client'

import React from 'react'

export type ConfigTabType = 'market-data' | 'strategy' | 'trade-settings' | 'signals'

interface ConfigTabsProps {
  activeTab?: ConfigTabType
  onTabChange?: (tab: ConfigTabType) => void
  className?: string
}

export function ConfigTabs({
  activeTab = 'strategy',
  onTabChange,
  className = ''
}: ConfigTabsProps) {
  const tabs = [
    { id: 'market-data' as ConfigTabType, label: 'Market Data', icon: '📊' },
    { id: 'strategy' as ConfigTabType, label: 'Strategy', icon: '🧠' },
    { id: 'trade-settings' as ConfigTabType, label: 'Trade Settings', icon: '⚙️' },
    { id: 'signals' as ConfigTabType, label: 'Signals', icon: '📡' },
  ]

  return (
    <div className={`border-b border-[var(--border)] ${className}`}>
      <nav className="flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange?.(tab.id)}
            className={`flex items-center gap-2 whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-[var(--agent-extraction)] text-[var(--agent-extraction)]'
                : 'border-transparent text-[var(--text-muted)] hover:border-[var(--border)] hover:text-[var(--text-secondary)]'
            }`}
          >
            <span className="text-base">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  )
}