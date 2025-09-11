'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useBotStore } from '@/store/botStore'

interface SchedulerJob {
  job_id: string
  config_id: string
  timeframe: string
  next_run: string | null
  misfire_grace_time: number
}

interface SchedulerStatus {
  status: string
  scheduler_running: boolean
  active_jobs: SchedulerJob[]
  job_count: number
}

interface UseSchedulerStatusReturn {
  schedulerStatus: SchedulerStatus | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useSchedulerStatus(): UseSchedulerStatusReturn {
  // Use store's scheduler status (updated via WebSocket)
  const schedulerStatus = useBotStore(state => state.schedulerStatus)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSchedulerStatus = async () => {
    try {
      const response = await apiClient.getSchedulerStatus()
      // Update store directly instead of local state
      useBotStore.getState().updateSchedulerStatus(response)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch scheduler status:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch scheduler status')
    } finally {
      setIsLoading(false)
    }
  }

  const refetch = async () => {
    setIsLoading(true)
    await fetchSchedulerStatus()
  }

  useEffect(() => {
    // Initial fetch only - WebSocket will handle real-time updates
    fetchSchedulerStatus()
    
    // Polling removed - now handled by WebSocket in botStore
    // Real-time updates via scheduler_update messages every 7 seconds
  }, [])

  return {
    schedulerStatus,
    isLoading,
    error,
    refetch
  }
}