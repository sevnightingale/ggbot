'use client'

import React from 'react'
import { ThemeToggle } from '../shared/ThemeToggle'

interface HeaderProps {
  // Future props for user profile, notifications, etc.
}

export function Header({}: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 text-cyan-400">🤖</div>
          <span className="font-semibold tracking-wide text-[var(--text-primary)]">ggbots • Forge</span>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          {/* Future: UserProfile component will go here */}
        </div>
      </div>
    </header>
  )
}