'use client'

import React from 'react'

type Tab = 'monitor' | 'configure' | 'dojo'

interface TabNavigationProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
  showDojoTab?: boolean
  className?: string
}

export function TabNavigation({ activeTab, onTabChange, showDojoTab = false, className = '' }: TabNavigationProps) {
  const tabs: Array<{ key: Tab; label: string; description: string }> = [
    { key: 'monitor', label: 'Monitor', description: 'Real-time bot status and performance' },
    { key: 'configure', label: 'Configure', description: 'Edit bot strategy and settings' },
    ...(showDojoTab ? [{ key: 'dojo' as Tab, label: 'Dojo', description: 'Competitive matches and ELO rating' }] : [])
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
            {...(tab.key === 'configure' ? { 'data-tour': 'configure-tab' } : {})}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  )
}
