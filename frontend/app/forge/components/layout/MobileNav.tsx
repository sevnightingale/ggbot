'use client'

import React from 'react'

interface MobileNavProps {
  className?: string
}

export function MobileNav({ className = '' }: MobileNavProps) {
  const navItems = [
    { key: 'bots', label: 'Bots', icon: '🤖' },
    { key: 'monitor', label: 'Monitor', icon: '📊' },
    { key: 'configure', label: 'Configure', icon: '⚙️' },
    { key: 'alerts', label: 'Alerts', icon: '🔔' }
  ]

  return (
    <nav className={`border-t border-[var(--border)] bg-[var(--bg-secondary)] ${className}`}>
      <div className="flex items-center justify-around py-2">
        {navItems.map((item) => (
          <button
            key={item.key}
            className="flex flex-col items-center gap-1 px-3 py-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  )
}