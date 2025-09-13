'use client'

import React from 'react'

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({
  icon = '🤖',
  title,
  description,
  actionLabel,
  onAction,
  className = ''
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-[var(--text-muted)] mb-4 max-w-md">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="rounded-xl bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-700 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}