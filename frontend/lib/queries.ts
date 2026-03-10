/**
 * React Query hooks for server state management
 *
 * These hooks replace useState + useEffect patterns for fetching data,
 * providing automatic caching, deduplication, and background refetching.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { DataSource, BotConfiguration } from '@/lib/api'

// Types for Arena performance data
export interface ArenaBot {
  config_id: string
  config_name: string
  profile_image_url: string | null
  description: string | null
  data_points: Array<{ timestamp: string; equity: number }>
  current_equity: number
  current_pnl: number
  initial_balance: number
  total_trades: number
  win_rate: number
  open_positions: number
  current_balance: number
  unrealized_pnl: number
  frequency: string
  model: string
  symbol: string
  data_sources: Record<string, unknown>
  stop_loss: string
  take_profit: string
  max_margin: string
  manual_closes: number
}

export interface ArenaPerformanceResponse {
  success: boolean
  hours: number
  competition_days: number
  bots: ArenaBot[]
}

/**
 * Fetch arena performance data with caching
 *
 * - First load: fetches from API
 * - Subsequent loads within 30s: returns cached data instantly
 * - After 30s: background refetch while showing cached data
 */
export function useArenaPerformance(hours: number = 504) {
  return useQuery<ArenaPerformanceResponse>({
    queryKey: ['arena', 'performance', hours],
    queryFn: async () => {
      const res = await fetch(`/api/v2/public/arena/performance?hours=${hours}`)
      if (!res.ok) {
        throw new Error(`Failed to fetch arena data: ${res.status}`)
      }
      return res.json()
    },
    staleTime: 30 * 1000, // 30 seconds - data considered fresh
    // gcTime inherited from defaults (5 minutes)
  })
}

/**
 * Hook to get queryClient for manual cache updates
 *
 * Useful for:
 * - Optimistic updates after user actions
 * - SSE updates that should update the cache directly
 * - Manual refetch triggers
 */
export function useArenaQueryClient() {
  const queryClient = useQueryClient()

  return {
    /** Force refetch arena data */
    invalidateArena: () => {
      queryClient.invalidateQueries({ queryKey: ['arena'] })
    },
    /** Directly update cached arena data (for SSE) */
    setArenaData: (data: ArenaPerformanceResponse) => {
      queryClient.setQueryData(['arena', 'performance', 504], data)
    },
  }
}

// ─────────────────────────────────────────────────────────
// Arena Season 2 Hooks
// ─────────────────────────────────────────────────────────

export interface CurrentSeasonResponse {
  success: boolean
  season_id: number
  name: string
  phase: 'training' | 'registration' | 'competition' | 'completed'
  training_start: string
  registration_start: string
  registration_end: string
  competition_start: string
  competition_end: string
  prize_description: string
  registration_count: number
}

export interface SeasonLeaderboardBot {
  registration_id: string
  config_id: string
  user_id: string
  registered_at: string | null
  starting_balance: number
  config_name: string
  profile_image_url: string | null
  description: string | null
  frequency: string
  model: string
  symbol: string
  data_sources: Record<string, unknown>
  stop_loss: string
  take_profit: string
  max_margin: string
  current_equity: number
  current_pnl: number
  pnl_pct: number
  total_trades: number
  win_rate: number
  active_days: number
  is_eligible: boolean
  rank: number | null
}

export interface SeasonLeaderboardResponse {
  success: boolean
  season_id: number
  phase: string
  bot_count: number
  bots: SeasonLeaderboardBot[]
}

/**
 * Fetch current arena season metadata + phase.
 * Public endpoint, cached 60s server-side.
 */
export function useCurrentSeason() {
  return useQuery<CurrentSeasonResponse>({
    queryKey: ['arena', 'season', 'current'],
    queryFn: async () => {
      const res = await fetch('/api/v2/public/arena/season/current')
      if (!res.ok) throw new Error(`Failed to fetch season: ${res.status}`)
      return res.json()
    },
    staleTime: 60 * 1000, // 60 seconds — matches server cache
  })
}

/**
 * Fetch leaderboard for a specific arena season.
 * Public endpoint, cached 300s during competition.
 */
export function useSeasonLeaderboard(seasonId: number, enabled: boolean = true) {
  return useQuery<SeasonLeaderboardResponse>({
    queryKey: ['arena', 'season', seasonId, 'leaderboard'],
    queryFn: async () => {
      const res = await fetch(`/api/v2/public/arena/season/${seasonId}/leaderboard`)
      if (!res.ok) throw new Error(`Failed to fetch leaderboard: ${res.status}`)
      return res.json()
    },
    staleTime: 60 * 1000,
    enabled,
  })
}

// ─────────────────────────────────────────────────────────
// Forge Page Hooks
// ─────────────────────────────────────────────────────────

/**
 * Fetch available data sources with their data points.
 * These rarely change during a session so we cache aggressively (10 min).
 */
export function useDataSources(enabled: boolean = true) {
  return useQuery<DataSource[]>({
    queryKey: ['data-sources'],
    queryFn: () => apiClient.getDataSourcesWithPoints(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000,    // Keep in cache 30 minutes
    enabled,
  })
}

/**
 * Fetch the user's bot list. Used for initial load only —
 * SSE handles real-time updates after that.
 */
export function useBotList(enabled: boolean = true) {
  return useQuery<BotConfiguration[]>({
    queryKey: ['bots'],
    queryFn: () => apiClient.listConfigs(),
    staleTime: 30 * 1000,  // 30 seconds
    enabled,
  })
}

/**
 * Activity type for latest activity display
 */
export interface ForgeActivity {
  id: string
  timestamp: string
  type: string
  priority: number
  data: {
    summary?: string
    details?: Record<string, unknown>
    symbol?: string
    importance?: number
    trade_id?: string
    trade_type?: string
    confidence?: number
    leverage?: number
    entry_price?: number
    stop_loss_price?: number
  }
}

/**
 * Fetch the latest activity for a bot. Replaces manual 30s setInterval polling
 * with React Query's built-in refetchInterval.
 */
export function useLatestActivity(configId: string | null) {
  return useQuery<ForgeActivity | null>({
    queryKey: ['latest-activity', configId],
    queryFn: async () => {
      if (!configId) return null
      const response = await apiClient.authenticatedFetch(
        `${process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'}/api/v2/activities/${configId}?limit=1`
      )
      if (!response.ok) return null
      const data = await response.json()
      return data.activities?.[0] ?? null
    },
    enabled: !!configId && !configId.startsWith('temp-'),
    staleTime: 15 * 1000,       // 15 seconds
    refetchInterval: 30 * 1000, // Poll every 30 seconds (same as before)
  })
}

/**
 * Fetch config usage/cost data for a bot.
 */
export function useConfigUsage(configId: string | null) {
  return useQuery({
    queryKey: ['config-usage', configId],
    queryFn: () => apiClient.getConfigUsage(configId!),
    enabled: !!configId && !configId.startsWith('temp-'),
    staleTime: 2 * 60 * 1000,       // 2 minutes
    refetchInterval: 5 * 60 * 1000,  // Refresh every 5 minutes
  })
}

/**
 * Helpers for manual cache updates (SSE integration, optimistic updates)
 */
export function useForgeQueryClient() {
  const queryClient = useQueryClient()

  return {
    /** Update bot list cache directly (for SSE merges) */
    setBots: (updater: (prev: BotConfiguration[] | undefined) => BotConfiguration[]) => {
      queryClient.setQueryData<BotConfiguration[]>(['bots'], updater)
    },
    /** Get current cached bots */
    getBots: (): BotConfiguration[] | undefined => {
      return queryClient.getQueryData<BotConfiguration[]>(['bots'])
    },
    /** Invalidate bot list to trigger refetch */
    invalidateBots: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
    },
    /** Invalidate latest activity for a config */
    invalidateActivity: (configId: string) => {
      queryClient.invalidateQueries({ queryKey: ['latest-activity', configId] })
    },
  }
}
