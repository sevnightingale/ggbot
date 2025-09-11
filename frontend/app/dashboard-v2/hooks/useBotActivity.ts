'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '@/lib/api'

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
  const [activity, setActivity] = useState<BotActivity | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

      const activityData: BotActivity = {
        positions,
        decisions,
        lastUpdate: new Date().toISOString()
      }

      setActivity(activityData)
    } catch (err) {
      console.error('Failed to fetch bot activity:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch activity')
      
      // Provide fallback empty data
      setActivity({
        positions: [],
        decisions: [],
        lastUpdate: new Date().toISOString()
      })
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
      fetchActivity(botId)

      // Set up polling every 30 seconds for live updates
      const interval = setInterval(() => fetchActivity(botId), 30000)
      return () => clearInterval(interval)
    } else {
      setActivity(null)
      setError(null)
      setIsLoading(false)
      return () => {} // Empty cleanup function
    }
  }, [botId, fetchActivity])

  return {
    activity,
    isLoading,
    error,
    refetch
  }
}