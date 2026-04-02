'use client'

import React from 'react'

interface EloTierBadgeProps {
  elo: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

interface TierInfo {
  name: string
  color: string
  icon: string
  bgClass: string
  textClass: string
}

function getTier(elo: number): TierInfo {
  if (elo >= 1800) return { name: 'Grandmaster', color: '#ef4444', icon: '♚', bgClass: 'bg-red-500/10', textClass: 'text-red-400' }
  if (elo >= 1600) return { name: 'Master', color: '#C1A87D', icon: '♛', bgClass: 'bg-[var(--accent)]/10', textClass: 'text-[var(--accent)]' }
  if (elo >= 1400) return { name: 'Expert', color: '#a855f7', icon: '♜', bgClass: 'bg-purple-500/10', textClass: 'text-purple-400' }
  if (elo >= 1200) return { name: 'Advanced', color: '#3b82f6', icon: '♞', bgClass: 'bg-blue-500/10', textClass: 'text-blue-400' }
  if (elo >= 1000) return { name: 'Intermediate', color: '#22c55e', icon: '♟', bgClass: 'bg-green-500/10', textClass: 'text-green-400' }
  return { name: 'Beginner', color: '#9ca3af', icon: '♙', bgClass: 'bg-gray-500/10', textClass: 'text-gray-400' }
}

export function EloTierBadge({ elo, size = 'sm', showLabel = false, className = '' }: EloTierBadgeProps) {
  const tier = getTier(elo)

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5 gap-1',
    md: 'text-sm px-2 py-1 gap-1.5',
    lg: 'text-base px-3 py-1.5 gap-2',
  }

  return (
    <span
      className={`inline-flex items-center rounded-md border border-[var(--border)] ${tier.bgClass} ${sizeClasses[size]} ${className}`}
      title={`${tier.name} — Elo ${elo}`}
    >
      <span className={tier.textClass}>{tier.icon}</span>
      <span className={`font-mono ${tier.textClass}`}>{elo.toLocaleString()}</span>
      {showLabel && (
        <span className={`${tier.textClass} opacity-70`}>{tier.name}</span>
      )}
    </span>
  )
}

export { getTier }
export type { TierInfo }
