'use client'

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
  // 🔥 NEW: Use store's scheduler status (updated via SSE stream)
  const schedulerStatus = useBotStore(state => state.schedulerStatus)
  const isLoading = useBotStore(state => state.isLoading)
  
  // Build scheduler status from bot data in store (SSE provides next_run per bot)
  const bots = useBotStore(state => Array.from(state.bots.values()))
  const syntheticSchedulerStatus = {
    status: 'running',
    scheduler_running: true,
    active_jobs: bots
      .filter(bot => bot.isActive && bot.nextRun)
      .map(bot => ({
        job_id: `job-${bot.config_id}`,
        config_id: bot.config_id,
        timeframe: bot.timeframe || '1h',
        next_run: bot.nextRun,
        misfire_grace_time: 60
      })),
    job_count: bots.filter(bot => bot.isActive).length
  }

  const refetch = async () => {
    // No-op: Data comes from SSE stream now
  }

  return {
    schedulerStatus: schedulerStatus || syntheticSchedulerStatus,
    isLoading,
    error: null, // No HTTP errors since we're reading from SSE
    refetch
  }
}