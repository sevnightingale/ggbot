'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  Swords, Eye, EyeOff, TrendingUp, TrendingDown, Minus, Clock,
  Shield, Zap, Timer, Flag, Trophy, ChevronDown, ChevronUp, AlertTriangle
} from 'lucide-react'
import { BotConfiguration, DojoMatch, apiClient } from '@/lib/api'
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

const FORMAT_INFO: Record<string, { label: string; duration: string; icon: typeof Swords }> = {
  standard: { label: 'Standard', duration: '21 days', icon: Shield },
  rapid: { label: 'Rapid', duration: '7 days', icon: Timer },
  blitz: { label: 'Blitz', duration: '1 day', icon: Zap },
}

function formatTimeRemaining(endsAt: string): string {
  const diff = new Date(endsAt).getTime() - Date.now()
  if (diff <= 0) return 'Ending...'
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  if (days > 0) return `${days}d ${hours}h left`
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  if (hours > 0) return `${hours}h ${minutes}m left`
  return `${minutes}m left`
}

export function DojoTab({ selectedBot, onConfigUpdate }: DojoTabProps) {
  const [isToggling, setIsToggling] = useState(false)
  const [eloHistory, setEloHistory] = useState<EloHistoryEntry[]>([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [houseBots, setHouseBots] = useState<HouseBot[]>([])
  const [isLoadingHouseBots, setIsLoadingHouseBots] = useState(false)

  // Match state
  const [activeMatches, setActiveMatches] = useState<DojoMatch[]>([])
  const [matchHistory, setMatchHistory] = useState<DojoMatch[]>([])
  const [dojoStats, setDojoStats] = useState<{ wins: number; losses: number; draws: number; total_matches: number } | null>(null)
  const [isLoadingMatches, setIsLoadingMatches] = useState(false)

  // Challenge state
  const [challengingBotId, setChallengingBotId] = useState<string | null>(null)
  const [selectedFormat, setSelectedFormat] = useState<string>('rapid')
  const [isSubmittingChallenge, setIsSubmittingChallenge] = useState(false)
  const [challengeError, setChallengeError] = useState<string | null>(null)

  // Forfeit state
  const [forfeitingMatchId, setForfeitingMatchId] = useState<string | null>(null)
  const [confirmForfeit, setConfirmForfeit] = useState<string | null>(null)

  // History expand
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null)

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
      console.error('Failed to fetch Elo history:', err)
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

  const fetchMatchData = useCallback(async () => {
    setIsLoadingMatches(true)
    try {
      const [activeRes, historyRes, statsRes] = await Promise.all([
        apiClient.getDojoActiveMatches(selectedBot.config_id),
        apiClient.getDojoMatchHistory(selectedBot.config_id),
        apiClient.getDojoBotStats(selectedBot.config_id),
      ])
      setActiveMatches(activeRes.matches)
      setMatchHistory(historyRes.matches)
      setDojoStats(statsRes)
    } catch (err) {
      console.error('Failed to fetch match data:', err)
    } finally {
      setIsLoadingMatches(false)
    }
  }, [selectedBot.config_id])

  useEffect(() => {
    fetchHistory()
    fetchHouseBots()
    fetchMatchData()
  }, [fetchHistory, fetchHouseBots, fetchMatchData])

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

  const handleChallenge = async (opponentConfigId: string) => {
    setIsSubmittingChallenge(true)
    setChallengeError(null)
    try {
      await apiClient.createDojoChallenge(selectedBot.config_id, opponentConfigId, selectedFormat)
      setChallengingBotId(null)
      // Refresh everything
      fetchMatchData()
      onConfigUpdate?.()
    } catch (err) {
      setChallengeError(err instanceof Error ? err.message : 'Challenge failed')
    } finally {
      setIsSubmittingChallenge(false)
    }
  }

  const handleForfeit = async (matchId: string) => {
    setForfeitingMatchId(matchId)
    try {
      await apiClient.forfeitDojoMatch(matchId)
      setConfirmForfeit(null)
      fetchMatchData()
      fetchHistory()
      onConfigUpdate?.()
    } catch (err) {
      console.error('Forfeit failed:', err)
    } finally {
      setForfeitingMatchId(null)
    }
  }

  const isLocked = selectedBot.dojo_locked || activeMatches.length > 0

  return (
    <div className="space-y-6">
      {/* Elo Header */}
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
              <div className="flex items-center gap-3">
                <p className={`text-sm ${tier.textClass}`}>{tier.name}</p>
                {dojoStats && dojoStats.total_matches > 0 && (
                  <span className="text-xs text-[var(--text-muted)]">
                    {dojoStats.wins}W / {dojoStats.losses}L / {dojoStats.draws}D
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={toggleVisibility}
            disabled={isToggling}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
            title={dojoVisible ? 'Hide from Dojo leaderboard' : 'Show on Dojo leaderboard'}
          >
            {dojoVisible ? (
              <><Eye className="h-4 w-4" /> Visible</>
            ) : (
              <><EyeOff className="h-4 w-4" /> Hidden</>
            )}
          </button>
        </div>
      </div>

      {/* Active Matches */}
      {activeMatches.length > 0 && (
        <div className="border border-[var(--accent)]/30 rounded-xl overflow-hidden bg-[var(--accent)]/5">
          <div className="px-4 py-3 border-b border-[var(--accent)]/20">
            <h3 className="text-sm font-medium text-[var(--accent)]">
              Active Match{activeMatches.length > 1 ? 'es' : ''}
            </h3>
          </div>
          <div className="divide-y divide-[var(--accent)]/20">
            {activeMatches.map((match) => {
              const isChallenger = match.challenger_config_id === selectedBot.config_id
              const opponentName = isChallenger ? match.opponent_name : match.challenger_name
              const formatInfo = FORMAT_INFO[match.format] || FORMAT_INFO.rapid
              const FormatIcon = formatInfo.icon
              return (
                <div key={match.match_id} className="px-4 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
                        <FormatIcon className="h-5 w-5 text-[var(--accent)]" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-[var(--text-primary)]">
                            vs {opponentName || 'Unknown'}
                          </span>
                          <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]">
                            {formatInfo.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          {match.ends_at && (
                            <span className="text-xs text-[var(--text-muted)] font-mono">
                              {formatTimeRemaining(match.ends_at)}
                            </span>
                          )}
                          {match.status === 'pending' && (
                            <span className="text-xs text-yellow-500">Pending</span>
                          )}
                        </div>
                      </div>
                    </div>
                    {match.status === 'active' && (
                      confirmForfeit === match.match_id ? (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-[var(--loss-color)]">Forfeit?</span>
                          <button
                            onClick={() => handleForfeit(match.match_id)}
                            disabled={forfeitingMatchId === match.match_id}
                            className="px-2 py-1 text-xs text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
                          >
                            {forfeitingMatchId === match.match_id ? 'Forfeiting...' : 'Yes'}
                          </button>
                          <button
                            onClick={() => setConfirmForfeit(null)}
                            className="px-2 py-1 text-xs text-[var(--text-muted)] border border-[var(--border)] rounded-lg hover:bg-[var(--bg-secondary)]"
                          >
                            No
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmForfeit(match.match_id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-[var(--loss-color)] border border-[var(--loss-color)]/30 rounded-lg hover:bg-red-500/10 transition-colors"
                        >
                          <Flag className="h-3 w-3" />
                          Forfeit
                        </button>
                      )
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

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

        {challengeError && (
          <div className="px-4 py-2 bg-red-500/10 border-b border-red-500/20">
            <p className="text-xs text-[var(--loss-color)] flex items-center gap-1.5">
              <AlertTriangle className="h-3 w-3" />
              {challengeError}
            </p>
          </div>
        )}

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
              const formatInfo = FORMAT_INFO[bot.format] || FORMAT_INFO.standard
              const FormatIcon = formatInfo.icon
              const isChallenging = challengingBotId === bot.config_id
              return (
                <div key={bot.config_id}>
                  <div className="px-4 py-3 flex items-center justify-between">
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
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setChallengeError(null)
                        setChallengingBotId(isChallenging ? null : bot.config_id)
                        setSelectedFormat(bot.format)
                      }}
                      disabled={isLocked || bot.state !== 'active'}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
                        isLocked || bot.state !== 'active'
                          ? 'border-[var(--border)] text-[var(--text-muted)] cursor-not-allowed opacity-50'
                          : isChallenging
                            ? 'border-[var(--accent)] text-[var(--accent)] bg-[var(--accent)]/10'
                            : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:text-[var(--accent)]'
                      }`}
                    >
                      {isChallenging ? 'Cancel' : 'Challenge'}
                    </button>
                  </div>

                  {/* Inline format picker + confirm */}
                  {isChallenging && (
                    <div className="px-4 pb-3 pt-1">
                      <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                        <div className="flex gap-1.5">
                          {(['blitz', 'rapid', 'standard'] as const).map((fmt) => {
                            const fi = FORMAT_INFO[fmt]
                            return (
                              <button
                                key={fmt}
                                onClick={() => setSelectedFormat(fmt)}
                                className={`px-2.5 py-1 text-xs rounded-md border transition-colors ${
                                  selectedFormat === fmt
                                    ? 'border-[var(--accent)] text-[var(--accent)] bg-[var(--accent)]/10'
                                    : 'border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                                }`}
                              >
                                {fi.label}
                              </button>
                            )
                          })}
                        </div>
                        <span className="text-xs text-[var(--text-muted)]">
                          {FORMAT_INFO[selectedFormat]?.duration}
                        </span>
                        <button
                          onClick={() => handleChallenge(bot.config_id)}
                          disabled={isSubmittingChallenge}
                          className="ml-auto px-3 py-1.5 text-xs font-medium bg-[var(--accent)] text-[#1a1816] dark:text-[#1a1816] rounded-lg hover:bg-[var(--accent-hover)] transition-colors disabled:opacity-50"
                        >
                          {isSubmittingChallenge ? 'Starting...' : 'Start Match'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Match History */}
      <div className="border border-[var(--border)] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)]">
          <h3 className="text-sm font-medium text-[var(--text-primary)]">
            Match History
            {dojoStats && dojoStats.total_matches > 0 && (
              <span className="text-[var(--text-muted)] font-normal ml-2">
                ({dojoStats.total_matches} {dojoStats.total_matches === 1 ? 'match' : 'matches'})
              </span>
            )}
          </h3>
        </div>

        {isLoadingMatches ? (
          <div className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">Loading...</div>
        ) : matchHistory.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Trophy className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-2" />
            <p className="text-sm text-[var(--text-muted)]">
              No matches yet. Challenge a House Bot to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {matchHistory.map((match) => {
              const isChallenger = match.challenger_config_id === selectedBot.config_id
              const opponentName = isChallenger ? match.opponent_name : match.challenger_name
              const myScore = isChallenger ? match.challenger_score : match.opponent_score
              const theirScore = isChallenger ? match.opponent_score : match.challenger_score
              const myElo = isChallenger ? match.challenger_elo : match.opponent_elo
              const won = match.winner_config_id === selectedBot.config_id
              const lost = match.winner_config_id != null && !won
              const draw = match.status === 'completed' && match.winner_config_id == null
              const forfeit = match.status === 'forfeit'
              const expanded = expandedMatchId === match.match_id

              let resultLabel: string
              let resultClass: string
              if (forfeit && won) { resultLabel = 'Win (Forfeit)'; resultClass = 'text-[var(--profit-color)]' }
              else if (forfeit) { resultLabel = 'Forfeit'; resultClass = 'text-[var(--loss-color)]' }
              else if (won) { resultLabel = 'Won'; resultClass = 'text-[var(--profit-color)]' }
              else if (lost) { resultLabel = 'Lost'; resultClass = 'text-[var(--loss-color)]' }
              else if (draw) { resultLabel = 'Draw'; resultClass = 'text-[var(--text-muted)]' }
              else { resultLabel = match.status; resultClass = 'text-[var(--text-muted)]' }

              return (
                <div key={match.match_id}>
                  <button
                    onClick={() => setExpandedMatchId(expanded ? null : match.match_id)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-[var(--bg-secondary)] transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        won ? 'bg-green-500/10' : lost ? 'bg-red-500/10' : 'bg-gray-500/10'
                      }`}>
                        {won ? <Trophy className="h-4 w-4 text-green-400" /> :
                         lost ? <TrendingDown className="h-4 w-4 text-red-400" /> :
                         <Minus className="h-4 w-4 text-gray-400" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-[var(--text-primary)]">
                            vs {opponentName}
                          </span>
                          <span className={`text-xs font-medium ${resultClass}`}>
                            {resultLabel}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-[var(--text-muted)]">
                            {FORMAT_INFO[match.format]?.label}
                          </span>
                          {match.completed_at && (
                            <>
                              <span className="text-xs text-[var(--text-muted)]">·</span>
                              <span className="text-xs text-[var(--text-muted)]">
                                {new Date(match.completed_at).toLocaleDateString(undefined, {
                                  month: 'short', day: 'numeric'
                                })}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {myElo && (
                        <span className={`font-mono text-sm ${
                          (myElo.after - myElo.before) > 0 ? 'text-[var(--profit-color)]' :
                          (myElo.after - myElo.before) < 0 ? 'text-[var(--loss-color)]' :
                          'text-[var(--text-muted)]'
                        }`}>
                          {(myElo.after - myElo.before) > 0 ? '+' : ''}{myElo.after - myElo.before}
                        </span>
                      )}
                      {expanded ? <ChevronUp className="h-4 w-4 text-[var(--text-muted)]" /> :
                                  <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />}
                    </div>
                  </button>

                  {/* Expanded detail */}
                  {expanded && (
                    <div className="px-4 pb-4 pt-1">
                      <div className="grid grid-cols-2 gap-4 p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                        <div>
                          <p className="text-xs text-[var(--text-muted)] mb-1">Your Score</p>
                          <p className="text-lg font-mono text-[var(--text-primary)]">
                            {myScore != null ? myScore.toFixed(4) : '—'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-[var(--text-muted)] mb-1">Opponent Score</p>
                          <p className="text-lg font-mono text-[var(--text-primary)]">
                            {theirScore != null ? theirScore.toFixed(4) : '—'}
                          </p>
                        </div>
                        {myElo && (
                          <>
                            <div>
                              <p className="text-xs text-[var(--text-muted)] mb-1">Elo Change</p>
                              <p className={`text-sm font-mono ${
                                (myElo.after - myElo.before) > 0 ? 'text-[var(--profit-color)]' :
                                (myElo.after - myElo.before) < 0 ? 'text-[var(--loss-color)]' :
                                'text-[var(--text-muted)]'
                              }`}>
                                {myElo.before} → {myElo.after}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-[var(--text-muted)] mb-1">Format</p>
                              <p className="text-sm text-[var(--text-primary)]">
                                {FORMAT_INFO[match.format]?.label} ({FORMAT_INFO[match.format]?.duration})
                              </p>
                            </div>
                          </>
                        )}
                        {match.result_details && (
                          <div className="col-span-2">
                            <p className="text-xs text-[var(--text-muted)] mb-2">Composite Breakdown</p>
                            <CompositeBreakdown
                              details={match.result_details}
                              isChallenger={isChallenger}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Elo History */}
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
          <div className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">Loading...</div>
        ) : eloHistory.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Clock className="h-8 w-8 text-[var(--text-muted)] mx-auto mb-2" />
            <p className="text-sm text-[var(--text-muted)]">
              No rating changes yet. Compete in matches to move your Elo.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {eloHistory.map((entry) => (
              <div key={entry.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    entry.change > 0 ? 'bg-green-500/10' :
                    entry.change < 0 ? 'bg-red-500/10' : 'bg-gray-500/10'
                  }`}>
                    {entry.change > 0 ? <TrendingUp className="h-4 w-4 text-green-400" /> :
                     entry.change < 0 ? <TrendingDown className="h-4 w-4 text-red-400" /> :
                     <Minus className="h-4 w-4 text-gray-400" />}
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
                    entry.change < 0 ? 'text-[var(--loss-color)]' : 'text-[var(--text-muted)]'
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

// ─── Sub-components ──────────────────────────────────────────────────────────

function CompositeBreakdown({
  details,
  isChallenger,
}: {
  details: Record<string, unknown>
  isChallenger: boolean
}) {
  const side = isChallenger ? 'challenger' : 'opponent'
  const data = details[side] as Record<string, unknown> | undefined
  if (!data || !data.components) return null

  const components = data.components as Record<string, number>
  const metrics = [
    { key: 'pnl_score', label: 'PnL %', value: data.pnl_pct as number, suffix: '%' },
    { key: 'sortino_score', label: 'Sortino', value: data.sortino as number, suffix: '' },
    { key: 'drawdown_score', label: 'Max DD', value: data.max_drawdown_pct as number, suffix: '%' },
    { key: 'win_rate_score', label: 'Win Rate', value: ((data.win_rate as number) * 100), suffix: '%' },
  ]

  return (
    <div className="grid grid-cols-4 gap-2">
      {metrics.map(({ key, label, value, suffix }) => (
        <div key={key} className="text-center">
          <p className="text-xs text-[var(--text-muted)]">{label}</p>
          <p className="text-sm font-mono text-[var(--text-primary)]">
            {value != null ? `${value.toFixed(1)}${suffix}` : '—'}
          </p>
          <p className="text-xs text-[var(--text-muted)] font-mono">
            ({components[key]?.toFixed(3) ?? '—'})
          </p>
        </div>
      ))}
    </div>
  )
}
