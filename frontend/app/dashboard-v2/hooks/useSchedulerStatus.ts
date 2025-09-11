'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

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
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSchedulerStatus = async () => {
    try {
      const response = await apiClient.getSchedulerStatus()
      setSchedulerStatus(response)
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
    // Initial fetch
    fetchSchedulerStatus()

    // Set up polling every 30 seconds
    const interval = setInterval(fetchSchedulerStatus, 30000)

    return () => clearInterval(interval)
  }, [])

  return {
    schedulerStatus,
    isLoading,
    error,
    refetch
  }
}