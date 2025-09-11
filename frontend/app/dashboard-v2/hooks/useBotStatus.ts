'use client'

import { useMemo } from 'react'
import { useSchedulerStatus } from './useSchedulerStatus'
import { useCountdownTimer } from './useCountdownTimer'
import { useBotWebSocket } from '@/hooks/useBotWebSocket'

interface BotStatusReturn {
  isActive: boolean
  currentState: 'inactive' | 'idle' | 'extraction' | 'decision' | 'trading'
  nextRun: string | null
  isExecuting: boolean
  message: string | null
  showSpinner: boolean
  countdown: string | null
}

interface BotConfig {
  config_id: string
  user_id: string
  state: 'active' | 'inactive'
  name: string
}

export function useBotStatus(
  botConfig: BotConfig | null,
  webSocketStatus: any = null
): BotStatusReturn {
  const { schedulerStatus } = useSchedulerStatus()
  
  // Find this bot's job in scheduler status
  const botJob = useMemo(() => {
    if (!botConfig || !schedulerStatus?.active_jobs) return null
    return schedulerStatus.active_jobs.find(job => job.config_id === botConfig.config_id)
  }, [schedulerStatus, botConfig?.config_id])

  // Get countdown timer for next run
  const { countdown } = useCountdownTimer(botJob?.next_run || null)

  // Determine bot status with priority: WebSocket > Scheduler > Database
  const botStatus = useMemo(() => {
    if (!botConfig) {
      return {
        isActive: false,
        currentState: 'inactive' as const,
        nextRun: null,
        isExecuting: false,
        message: null,
        showSpinner: false,
        countdown: null
      }
    }

    // Check if bot has scheduler job (indicates it's truly active)
    const hasSchedulerJob = Boolean(botJob)
    const isActive = botConfig.state === 'active' && hasSchedulerJob

    // Priority 1: WebSocket status (real-time execution)
    if (webSocketStatus?.phase && webSocketStatus.phase !== 'idle') {
      return {
        isActive,
        currentState: webSocketStatus.phase,
        nextRun: botJob?.next_run || null,
        isExecuting: true,
        message: webSocketStatus.message || 'Processing...',
        showSpinner: webSocketStatus.showSpinner ?? true,
        countdown: null // No countdown during execution
      }
    }

    // Priority 2: Active with scheduler job (idle state)
    if (isActive) {
      return {
        isActive: true,
        currentState: 'idle' as const,
        nextRun: botJob?.next_run || null,
        isExecuting: false,
        message: countdown || 'Monitoring market conditions...',
        showSpinner: false,
        countdown
      }
    }

    // Priority 3: Inactive state
    return {
      isActive: false,
      currentState: 'inactive' as const,
      nextRun: null,
      isExecuting: false,
      message: 'Bot inactive',
      showSpinner: false,
      countdown: null
    }
  }, [botConfig, botJob, webSocketStatus, countdown])

  return botStatus
}