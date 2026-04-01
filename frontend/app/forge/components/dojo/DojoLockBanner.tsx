'use client'

import React from 'react'
import { Lock, Timer } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'

interface DojoLockBannerProps {
  bot: BotConfiguration
}

export function DojoLockBanner({ bot }: DojoLockBannerProps) {
  if (!bot.dojo_locked || !bot.dojo_matches_active?.length) return null

  const match = bot.dojo_matches_active[0]
  const timeLeft = match.ends_at
    ? formatTimeLeft(match.ends_at)
    : null

  return (
    <div className="rounded-xl border border-[var(--accent)]/20 bg-[var(--accent)]/5 px-4 py-3 mb-4">
      <div className="flex items-center gap-3">
        <Lock className="h-4 w-4 text-[var(--accent)] flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--accent)]">
            Locked for Dojo Match
          </p>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            vs {match.opponent_name || 'House Bot'}
            {' · '}
            {match.format?.charAt(0).toUpperCase()}{match.format?.slice(1)}
            {timeLeft && (
              <>
                {' · '}
                <Timer className="h-3 w-3 inline" />
                {' '}{timeLeft}
              </>
            )}
          </p>
        </div>
        <p className="text-xs text-[var(--text-muted)] flex-shrink-0">
          Forfeit in Dojo tab to unlock
        </p>
      </div>
    </div>
  )
}

function formatTimeLeft(endsAt: string): string {
  const diff = new Date(endsAt).getTime() - Date.now()
  if (diff <= 0) return 'Ending soon'
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  if (days > 0) return `${days}d ${hours}h left`
  return `${hours}h left`
}
