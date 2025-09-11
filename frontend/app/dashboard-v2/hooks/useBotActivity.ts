'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '@/lib/api'
import { useBotStore } from '@/store/botStore'

interface Position {
  symbol: string
  side: 'LONG' | 'SHORT'
  size: number
  entryPrice: number
  currentPrice: number
  unrealizedPnL: number
  timestamp: string
}

interface Decision {
  id: string
  timestamp: string
  action: 'BUY' | 'SELL' | 'HOLD'
  reasoning: string
  confidence: number
  symbol: string
  price: number
}

interface BotActivity {
  positions: Position[]
  decisions: Decision[]
  lastUpdate: string
}

interface UseBotActivityReturn {
  activity: BotActivity | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useBotActivity(botId: string | null): UseBotActivityReturn {
  // Read from store (updated via WebSocket)
  const bot = useBotStore(state => botId ? state.getBotById(botId) : null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Combine store data into activity object
  const activity: BotActivity | null = bot ? {
    positions: bot.positions || [],
    decisions: bot.decisions || [],
    lastUpdate: bot.lastPositionUpdate || bot.lastDecisionUpdate || new Date().toISOString()
  } : null

  const fetchActivity = useCallback(async (configId: string): Promise<void> => {
    try {
      setIsLoading(true)
      setError(null)

      // Fetch both positions and decisions in parallel
      const [positionsResponse, decisionsResponse] = await Promise.allSettled([
        apiClient.authenticatedFetch(`/api/v2/bot/${configId}/positions`),
        apiClient.authenticatedFetch(`/api/v2/bot/${configId}/decisions`)
      ])

      let positions: Position[] = []
      let decisions: Decision[] = []

      // Handle positions response
      if (positionsResponse.status === 'fulfilled' && positionsResponse.value.ok) {
        const positionsData = await positionsResponse.value.json()
        positions = positionsData.positions || []
      }

      // Handle decisions response
      if (decisionsResponse.status === 'fulfilled' && decisionsResponse.value.ok) {
        const decisionsData = await decisionsResponse.value.json()
        decisions = (decisionsData.decisions || []).slice(0, 10) // Show last 10 decisions
      }

      // Store data in botStore instead of local state
      useBotStore.getState().updateBotPositions(configId, positions)
      useBotStore.getState().updateBotDecisions(configId, decisions)
      
    } catch (err) {
      console.error('Failed to fetch bot activity:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch activity')
      
      // Provide fallback empty data to store
      useBotStore.getState().updateBotPositions(configId, [])
      useBotStore.getState().updateBotDecisions(configId, [])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const refetch = async (): Promise<void> => {
    if (botId) {
      await fetchActivity(botId)
    }
  }

  useEffect(() => {
    if (botId) {
      // Initial fetch only - WebSocket will handle real-time updates
      fetchActivity(botId)
      
      // Polling removed - now handled by WebSocket in botStore
      // Real-time updates via position_update and decisions_update messages every 7 seconds
    } else {
      // Clear any existing data when no botId
      setError(null)
      setIsLoading(false)
    }
  }, [botId, fetchActivity])

  return {
    activity,
    isLoading,
    error,
    refetch
  }
}