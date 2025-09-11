'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useBotStore } from '@/store/botStore'

interface BotMetrics {
  balance: number
  totalPnL: number
  totalTrades: number
  winRate: number
  avgTrade: number
  maxDrawdown: number
  sharpeRatio: number
  recentTrades: Array<{
    id: string
    symbol: string
    side: string
    quantity: number
    price: number
    pnl: number
    timestamp: string
  }>
}

interface UseBotMetricsReturn {
  metrics: BotMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useBotMetrics(botId: string | null): UseBotMetricsReturn {
  // Read from store (updated via WebSocket)
  const bot = useBotStore(state => botId ? state.getBotById(botId) : null)
  const metrics = bot?.metrics || null
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchMetrics = async (configId: string) => {
    try {
      setIsLoading(true)
      setError(null)

      // Fetch metrics data from API
      const response = await apiClient.authenticatedFetch(
        `/api/v2/bot/${configId}/metrics`
      )
      
      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.status}`)
      }

      const data = await response.json()
      
      // Transform API response to expected format
      const transformedMetrics: BotMetrics = {
        balance: data.account?.balance || 10000, // Default paper balance
        totalPnL: data.performance?.total_pnl || 0,
        totalTrades: data.performance?.total_trades || 0,
        winRate: data.performance?.win_rate || 0,
        avgTrade: data.performance?.avg_trade || 0,
        maxDrawdown: data.performance?.max_drawdown || 0,
        sharpeRatio: data.performance?.sharpe_ratio || 0,
        recentTrades: data.recent_trades || []
      }

      // Store data in botStore instead of local state
      useBotStore.getState().updateBotMetrics(configId, transformedMetrics)
    } catch (err) {
      console.error('Failed to fetch bot metrics:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      
      // Provide fallback data to store
      const fallbackMetrics = {
        balance: 10000,
        totalPnL: 0,
        totalTrades: 0,
        winRate: 0,
        avgTrade: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        recentTrades: []
      }
      useBotStore.getState().updateBotMetrics(configId, fallbackMetrics)
    } finally {
      setIsLoading(false)
    }
  }

  const refetch = async () => {
    if (botId) {
      await fetchMetrics(botId)
    }
  }

  useEffect(() => {
    if (botId) {
      fetchMetrics(botId)
    } else {
      setMetrics(null)
      setError(null)
      setIsLoading(false)
    }
  }, [botId])

  return {
    metrics,
    isLoading,
    error,
    refetch
  }
}