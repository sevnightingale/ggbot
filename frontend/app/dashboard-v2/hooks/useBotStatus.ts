'use client'

import { useMemo } from 'react'
import { useSchedulerStatus } from './useSchedulerStatus'
import { useCountdownTimer } from './useCountdownTimer'
import { Bot } from '@/store/botStore'

interface BotStatusReturn {
  isActive: boolean
  currentState: 'inactive' | 'idle' | 'extraction' | 'decision' | 'trading'
  nextRun: string | null
  isExecuting: boolean
  message: string | null
  showSpinner: boolean
  countdown: string | null
}

export function useBotStatus(bot: Bot | null): BotStatusReturn {
  const { schedulerStatus } = useSchedulerStatus()
  
  // Find this bot's job in scheduler status
  const botJob = useMemo(() => {
    if (!bot || !schedulerStatus?.active_jobs) return null
    return schedulerStatus.active_jobs.find(job => job.config_id === bot.config_id)
  }, [schedulerStatus, bot])

  // Get countdown timer for next run
  const { countdown } = useCountdownTimer(botJob?.next_run || null)

  // Determine bot status with priority: WebSocket (bot.status) > Scheduler > Default
  const botStatus = useMemo(() => {
    if (!bot) {
      return {
        isActive: false,
        currentState: 'inactive' as const,
        nextRun: null,
        isExecuting: false,
        message: 'No bot selected',
        showSpinner: false,
        countdown: null
      }
    }

    // Check if bot has scheduler job (indicates it's truly active)
    const hasSchedulerJob = Boolean(botJob)
    const isActive = bot.isActive && hasSchedulerJob

    // Priority 1: WebSocket status from bot.status (real-time execution)
    const currentPhase = bot.status?.phase || 'inactive'
    const isExecuting = ['extraction', 'decision', 'trading'].includes(currentPhase)

    if (isExecuting) {
      return {
        isActive,
        currentState: currentPhase,
        nextRun: botJob?.next_run || null,
        isExecuting: true,
        message: bot.status?.message || 'Processing...',
        showSpinner: bot.status?.showSpinner ?? true,
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
        message: countdown || bot.status?.message || 'Monitoring market conditions...',
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
      message: bot.status?.message || 'Bot inactive',
      showSpinner: false,
      countdown: null
    }
  }, [bot, botJob, countdown])

  return botStatus
}