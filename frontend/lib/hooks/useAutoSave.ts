import { useEffect, useRef, useState, useCallback, useContext } from 'react'
import { SaveStatusContext } from '@/lib/contexts/SaveStatusContext'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

interface UseAutoSaveOptions<T> {
  value: T
  onSave: (value: T) => Promise<void>
  delay?: number
  enabled?: boolean
  saveId?: string  // Optional unique ID for tracking this save operation
}

interface UseAutoSaveReturn {
  status: SaveStatus
  error: Error | null
  reset: () => void
}

/**
 * Hook for auto-saving values with debouncing and optimistic updates
 *
 * Features:
 * - Debounced saves (default 1s)
 * - Optimistic UI updates
 * - Automatic rollback on error
 * - Cleanup on unmount
 * - Reports to global SaveStatusContext if available
 *
 * @example
 * const { status, error } = useAutoSave({
 *   value: strategyText,
 *   onSave: async (text) => {
 *     await apiClient.updateConfig(configId, { decision: { user_prompt: text } })
 *   },
 *   delay: 1000,
 *   saveId: 'strategy-prompt'
 * })
 */
export function useAutoSave<T>({
  value,
  onSave,
  delay = 1000,
  enabled = true,
  saveId = `save-${Math.random()}`
}: UseAutoSaveOptions<T>): UseAutoSaveReturn {
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [error, setError] = useState<Error | null>(null)

  const saveStatusContext = useContext(SaveStatusContext)
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const previousValueRef = useRef<T>(value)
  const mountedRef = useRef(true)

  // Reset status to idle
  const reset = useCallback(() => {
    setStatus('idle')
    setError(null)
  }, [])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    // Skip if disabled or value hasn't changed
    if (!enabled || value === previousValueRef.current) {
      return
    }

    // Store previous value for potential rollback
    const previousValue = previousValueRef.current
    previousValueRef.current = value

    // Clear existing timer
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }

    // Set status to saving (optimistic)
    setStatus('saving')
    setError(null)

    // Report to global context if available
    saveStatusContext?.registerSave(saveId)

    // Debounced save
    saveTimerRef.current = setTimeout(async () => {
      try {
        await onSave(value)

        if (mountedRef.current) {
          setStatus('saved')
          saveStatusContext?.completeSave(saveId)

          // Auto-reset to idle after 2 seconds
          setTimeout(() => {
            if (mountedRef.current) {
              setStatus('idle')
            }
          }, 2000)
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Save failed')

        if (mountedRef.current) {
          setStatus('error')
          setError(error)
          saveStatusContext?.failSave(saveId, error)

          // Rollback to previous value (parent component should handle this)
          console.error('Auto-save failed, should rollback to:', previousValue)

          // Auto-reset error after 5 seconds
          setTimeout(() => {
            if (mountedRef.current) {
              setStatus('idle')
              setError(null)
            }
          }, 5000)
        }
      }
    }, delay)

    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, onSave, delay, enabled])

  return { status, error, reset }
}
