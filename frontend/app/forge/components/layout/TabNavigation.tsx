'use client'

import React from 'react'

type Tab = 'monitor' | 'configure'

interface TabNavigationProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
  className?: string
}

export function TabNavigation({ activeTab, onTabChange, className = '' }: TabNavigationProps) {
  const tabs: Array<{ key: Tab; label: string; description: string }> = [
    { key: 'monitor', label: 'Monitor', description: 'Real-time bot status and performance' },
    { key: 'configure', label: 'Configure', description: 'Edit bot strategy and settings' }
  ]

  return (
    <div className={`bg-[var(--bg-primary)] ${className}`}>
      <div className="flex items-center gap-2 py-2">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key)}
            className={`rounded-xl px-3 py-1.5 text-sm transition-colors ${
              activeTab === tab.key
                ? 'bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border)]'
                : 'text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
            }`}
            title={tab.description}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  )
}