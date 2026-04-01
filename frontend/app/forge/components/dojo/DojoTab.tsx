'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Swords, Eye, EyeOff, TrendingUp, TrendingDown, Minus, Clock, Shield, Zap, Timer } from 'lucide-react'
import { BotConfiguration, apiClient } from '@/lib/api'
import { EloTierBadge, getTier } from '../shared/EloTierBadge'

interface EloHistoryEntry {
  id: string
  elo_before: number
  elo_after: number
  change: number
  reason: string
  match_id: string | null
  details: Record<string, unknown> | null
  created_at: string
}

interface HouseBot {
  config_id: string
  config_name: string
  elo_rating: number
  state: string
  selected_pair: string
  frequency: string
  format: 'blitz' | 'rapid' | 'standard'
  profile_image_url: string | null
  match_record: { wins: number; losses: number; draws: number }
}

interface DojoTabProps {
  selectedBot: BotConfiguration
  onConfigUpdate?: () => void
}

const REASON_LABELS: Record<string, string> = {
  rolling_weekly: 'Weekly Rating',
  match_win: 'Match Won',
  match_loss: 'Match Lost',
  match_draw: 'Match Draw',
  match_forfeit: 'Forfeit',
}

const FORMAT_LABELS: Record<string, { label: string; duration: string; icon: typeof Swords }> = {
  standard: { label: 'Standard', duration: '21 days', icon: Shield },
  rapid: { label: 'Rapid', duration: '7 days', icon: Timer },
  blitz: { label: 'Blitz', duration: '1 day', icon: Zap },
}

export function DojoTab({ selectedBot, onConfigUpdate }: DojoTabProps) {
  const [isToggling, setIsToggling] = useState(false)
  const [eloHistory, setEloHistory] = useState<EloHistoryEntry[]>([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [houseBots, setHouseBots] = useState<HouseBot[]>([])
  const [isLoadingHouseBots, setIsLoadingHouseBots] = useState(false)

  const elo = selectedBot.elo_rating ?? 1200
  const dojoVisible = selectedBot.dojo_visible ?? true
  const tier = getTier(elo)

  const fetchHistory = useCallback(async () => {
    setIsLoadingHistory(true)
    try {
      const data = await apiClient.getEloHistory(selectedBot.config_id)
      setEloHistory(data.history)
      setHistoryTotal(data.total)
    } catch (err) {
      console.error('Failed to fetch ELO history:', err)
    } finally {
      setIsLoadingHistory(false)
    }
  }, [selectedBot.config_id])

  const fetchHouseBots = useCallback(async () => {
    setIsLoadingHouseBots(true)
    try {
      const data = await apiClient.getHouseBots()
      setHouseBots(data.bots)
    } catch (err) {
      console.error('Failed to fetch house bots:', err)
    } finally {
      setIsLoadingHouseBots(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()
    fetchHouseBots()
  }, [fetchHistory, fetchHouseBots])

  const toggleVisibility = async () => {
    setIsToggling(true)
    try {
      await apiClient.toggleDojoVisibility(selectedBot.config_id, !dojoVisible)
      onConfigUpdate?.()
    } catch (err) {
      console.error('Failed to toggle dojo visibility:', err)
    } finally {
      setIsToggling(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* ELO Header */}
      <div className="border border-[var(--border)] rounded-xl p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
              <Swords className="h-6 w-6 text-[var(--accent)]" />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                  {selectedBot.config_name}
                </h2>
                <EloTierBadge elo={elo} size="md" />
              </div>
              <p className={`text-sm ${tier.textClass}`}>
                {tier.name}
              </p>
            </div>
          </div>

          {/* Visibility Toggle */}
          <button
            onClick={toggleVisibility}
            disabled={isToggling}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
            title={dojoVisible ? 'Hide from Dojo leaderboard' : 'Show on Dojo leaderboard'}
          >
            {dojoVisible ? (
              <>
                <Eye className="h-4 w-4" />
                Visible
              </>
            ) : (
              <>
                <EyeOff className="h-4 w-4" />
                Hidden
              </>
            )}
          </button>
        </div>
      </div>

      {/* House Bots — Challenge Opponents */}
      <div className="border border-[var(--border)] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)]">
          <h3 className="text-sm font-medium text-[var(--text-primary)]">
            House Bots
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Challenge The Arbiter and its variants to earn your rank
          </p>
        </div>

        {isLoadingHouseBots ? (
          <div className="px-4 py-6 text-center text-sm text-[var(--text-muted)]">
            Loading...
          </div>
        ) : houseBots.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-[var(--text-muted)]">
            No House Bots available yet
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {houseBots.map((bot) => {
              const formatInfo = FORMAT_LABELS[bot.format] || FORMAT_LABELS.standard
              const FormatIcon = formatInfo.icon
              return (
                <div key={bot.config_id} className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
                      <FormatIcon className="h-5 w-5 text-[var(--accent)]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--text-primary)]">
                          {bot.config_name}
                        </span>
                        <EloTierBadge elo={bot.elo_rating} size="sm" />
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-[var(--text-muted)]">
                          {formatInfo.label} ({formatInfo.duration})
                        </span>
                        <span className="text-xs text-[var(--text-muted)]">·</span>
                        <span className="text-xs text-[var(--text-muted)]">
                          {bot.selected_pair}
                        </span>
                        <span className="text-xs text-[var(--text-muted)]">·</span>
                        <span className="text-xs text-[var(--text-muted)]">
                          Every {bot.frequency}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    disabled
                    className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-xs text-[var(--text-muted)] cursor-not-allowed opacity-50"
                    title="Matches coming in Phase 4"
                  >
                    Challenge
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ELO History */}
      <div className="border border-[var(--border)] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)]">
          <h3 className="text-sm font-medium text-[var(--text-primary)]">
            Rating History
            {historyTotal > 0 && (
              <span className="text-[var(--text-muted)] font-normal ml-2">
                ({historyTotal} {historyTotal === 1 ? 'event' : 'events'})
              </span>
            )}
          </h3>
        </div>

        {isLoadingHistory ? (
          <div className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">
            Loading...
          </div>
        ) : eloHistory.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Clock className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-2" />
            <p className="text-sm text-[var(--text-muted)]">
              No rating changes yet. Compete in matches to move your ELO.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {eloHistory.map((entry) => (
              <div key={entry.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    entry.change > 0 ? 'bg-green-500/10' :
                    entry.change < 0 ? 'bg-red-500/10' :
                    'bg-gray-500/10'
                  }`}>
                    {entry.change > 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-400" />
                    ) : entry.change < 0 ? (
                      <TrendingDown className="h-4 w-4 text-red-400" />
                    ) : (
                      <Minus className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <div className="text-sm text-[var(--text-primary)]">
                      {REASON_LABELS[entry.reason] || entry.reason}
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      {new Date(entry.created_at).toLocaleDateString(undefined, {
                        month: 'short', day: 'numeric', year: 'numeric'
                      })}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`font-mono text-sm font-medium ${
                    entry.change > 0 ? 'text-[var(--profit-color)]' :
                    entry.change < 0 ? 'text-[var(--loss-color)]' :
                    'text-[var(--text-muted)]'
                  }`}>
                    {entry.change > 0 ? '+' : ''}{entry.change}
                  </span>
                  <div className="text-xs text-[var(--text-muted)] font-mono">
                    {entry.elo_before} → {entry.elo_after}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
