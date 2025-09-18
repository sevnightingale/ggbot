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
      <nav className="flex space-x-4 md:space-x-8 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange?.(tab.id)}
            className={`flex items-center gap-2 whitespace-nowrap border-b-2 py-4 px-2 md:px-1 text-sm font-medium transition-colors flex-shrink-0 ${
              activeTab === tab.id
                ? 'border-[var(--agent-extraction)] text-[var(--agent-extraction)]'
                : 'border-transparent text-[var(--text-muted)] hover:border-[var(--border)] hover:text-[var(--text-secondary)]'
            }`}
          >
            <span className="text-base">{tab.icon}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}