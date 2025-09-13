'use client'

import React, { useState } from 'react'
import { User, Settings, LogOut, CreditCard } from 'lucide-react'

interface UserProfileProps {
  className?: string
}

export function UserProfile({}: UserProfileProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
        title="User profile and settings"
      >
        <User className="h-4 w-4 text-[var(--text-primary)]" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-2 shadow-lg">
            <div className="border-b border-[var(--border)] px-3 py-2 mb-2">
              <div className="text-sm font-medium text-[var(--text-primary)]">User Account</div>
              <div className="text-xs text-[var(--text-muted)]">user@example.com</div>
            </div>

            <div className="space-y-1">
              <MenuButton icon={Settings} label="Settings" />
              <MenuButton icon={CreditCard} label="Subscription" />
              <MenuButton icon={LogOut} label="Log out" />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

interface MenuButtonProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  onClick?: () => void
}

function MenuButton({ icon: Icon, label, onClick }: MenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  )
}