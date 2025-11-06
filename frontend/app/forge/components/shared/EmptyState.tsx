'use client'

import React from 'react'
import { LucideIcon, Bot } from 'lucide-react'

interface EmptyStateProps {
  Icon?: LucideIcon
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({
  Icon = Bot,
  title,
  description,
  actionLabel,
  onAction,
  className = ''
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="mb-4">
        <Icon className="h-16 w-16 text-[var(--text-muted)]" />
      </div>
      <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-[var(--text-muted)] mb-4 max-w-md">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-obsidian hover:bg-[var(--accent-hover)] transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}