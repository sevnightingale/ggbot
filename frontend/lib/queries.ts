/**
 * React Query hooks for server state management
 *
 * These hooks replace useState + useEffect patterns for fetching data,
 * providing automatic caching, deduplication, and background refetching.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'

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
