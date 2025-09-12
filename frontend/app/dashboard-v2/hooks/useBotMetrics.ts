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
  
  // NEW: Additional fields for enhanced PerformancePanel
  winTrades?: number
  lossTrades?: number
  neutralTrades?: number
  lossRate?: number
  neutralRate?: number
  avgProfitPerTrade?: number
  avgLossPerTrade?: number
  avgTradeDuration?: string
  profitLossData?: Array<{
    date: string
    profit: number
  }>
  
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
      
      // Check if this is new V2 monitoring service data or legacy API data
      let transformedMetrics: BotMetrics
      
      if (data.balance !== undefined) {
        // New V2 data structure from monitoring service (already in correct format)
        transformedMetrics = {
          balance: data.balance || 10000,
          totalPnL: data.totalPnL || 0,
          totalTrades: data.totalTrades || 0,
          winRate: data.winRate || 0,
          avgTrade: data.avgTrade || 0,
          maxDrawdown: data.maxDrawdown || 0,
          sharpeRatio: data.sharpeRatio || 0,
          
          // NEW: Enhanced fields from V2 monitoring service
          winTrades: data.winTrades || 0,
          lossTrades: data.lossTrades || 0,
          neutralTrades: data.neutralTrades || 0,
          lossRate: data.lossRate || 0,
          neutralRate: data.neutralRate || 0,
          avgProfitPerTrade: data.avgProfitPerTrade || 0,
          avgLossPerTrade: data.avgLossPerTrade || 0,
          avgTradeDuration: data.avgTradeDuration || '0m',
          profitLossData: data.profitLossData || [],
          
          recentTrades: data.recentTrades || []
        }
      } else {
        // Legacy API data structure (nested)
        transformedMetrics = {
          balance: data.account?.balance || 10000,
          totalPnL: data.performance?.total_pnl || 0,
          totalTrades: data.performance?.total_trades || 0,
          winRate: data.performance?.win_rate || 0,
          avgTrade: data.performance?.avg_trade || 0,
          maxDrawdown: data.performance?.max_drawdown || 0,
          sharpeRatio: data.performance?.sharpe_ratio || 0,
          recentTrades: data.recent_trades || []
        }
      }

      // Store data in botStore instead of local state
      useBotStore.getState().updateBotMetrics(configId, transformedMetrics)
    } catch (err) {
      console.error('Failed to fetch bot metrics:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      
      // Provide fallback data to store with all fields
      const fallbackMetrics: BotMetrics = {
        balance: 10000,
        totalPnL: 0,
        totalTrades: 0,
        winRate: 0,
        avgTrade: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        
        // NEW: Fallback for enhanced fields
        winTrades: 0,
        lossTrades: 0,
        neutralTrades: 0,
        lossRate: 0,
        neutralRate: 0,
        avgProfitPerTrade: 0,
        avgLossPerTrade: 0,
        avgTradeDuration: '0m',
        profitLossData: [],
        
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
      // Clear any existing errors when no botId
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