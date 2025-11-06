'use client'

import React from 'react'
import { BarChart3, Brain, Settings, Radio, LucideIcon } from 'lucide-react'

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
  const tabs: Array<{ id: ConfigTabType; label: string; Icon: LucideIcon }> = [
    { id: 'market-data' as ConfigTabType, label: 'Market Data', Icon: BarChart3 },
    { id: 'strategy' as ConfigTabType, label: 'Strategy', Icon: Brain },
    { id: 'trade-settings' as ConfigTabType, label: 'Trade Settings', Icon: Settings },
    { id: 'signals' as ConfigTabType, label: 'Signals', Icon: Radio },
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
                ? 'border-[var(--accent)] text-[var(--accent)]'
                : 'border-transparent text-[var(--text-muted)] hover:border-[var(--border)] hover:text-[var(--text-secondary)]'
            }`}
          >
            <tab.Icon className="h-4 w-4" />
            <span className="hidden sm:inline">{tab.label}</span>
            <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}