'use client'

import { useState, useEffect } from 'react'

interface UseCountdownTimerReturn {
  countdown: string | null
  timeRemaining: number // seconds remaining
}

export function useCountdownTimer(nextRunISO: string | null): UseCountdownTimerReturn {
  const [countdown, setCountdown] = useState<string | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  useEffect(() => {
    if (!nextRunISO) {
      setCountdown(null)
      setTimeRemaining(0)
      return
    }

    const updateCountdown = () => {
      try {
        const now = new Date()
        const nextRun = new Date(nextRunISO)
        
        if (isNaN(nextRun.getTime())) {
          setCountdown('Schedule pending')
          setTimeRemaining(0)
          return
        }

        const diff = nextRun.getTime() - now.getTime()
        setTimeRemaining(Math.max(0, Math.floor(diff / 1000)))

        if (diff <= 0) {
          setCountdown('Running soon...')
          return
        }

        // Format countdown based on time remaining
        const totalSeconds = Math.floor(diff / 1000)
        const hours = Math.floor(totalSeconds / 3600)
        const minutes = Math.floor((totalSeconds % 3600) / 60)
        const seconds = totalSeconds % 60

        if (hours > 0) {
          setCountdown(`Next run in ${hours}h ${minutes}m`)
        } else if (minutes > 0) {
          setCountdown(`Next run in ${minutes}m ${seconds}s`)
        } else if (seconds > 0) {
          setCountdown(`Next run in ${seconds}s`)
        } else {
          setCountdown('Starting now...')
        }
      } catch (error) {
        console.error('Error calculating countdown:', error)
        setCountdown('Schedule error')
        setTimeRemaining(0)
      }
    }

    // Update immediately
    updateCountdown()

    // Update every second
    const interval = setInterval(updateCountdown, 1000)

    return () => clearInterval(interval)
  }, [nextRunISO])

  return {
    countdown,
    timeRemaining
  }
}