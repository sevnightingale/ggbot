import { useRef, useCallback, useContext, useEffect, useState } from 'react'
import { SaveStatusContext } from '@/lib/contexts/SaveStatusContext'
import { apiClient, ConfigData } from '@/lib/api'

interface UseBatchedConfigSaveOptions {
  configId: string | null
  configName?: string
  configType?: string
  delay?: number  // Debounce delay in ms (default 5000)
  enabled?: boolean
  onSaveComplete?: () => void
  onSaveError?: (error: Error) => void
}

interface UseBatchedConfigSaveReturn {
  /** Queue a config change - updates will be batched and saved after delay */
  queueChange: (updates: Partial<ConfigData>) => void
  /** Force immediate save of all pending changes */
  flush: () => Promise<void>
  /** Check if a specific field path is dirty (has unsaved changes) */
  isFieldDirty: (fieldPath: string) => boolean
  /** Get all dirty field paths */
  getDirtyFields: () => Set<string>
  /** Clear dirty tracking (call after external update like SSE) */
  clearDirtyFields: () => void
  /** Check if there are any pending changes */
  hasPendingChanges: boolean
  /** Current save status */
  status: 'idle' | 'pending' | 'saving' | 'saved' | 'error'
}

/**
 * Unified batched config save hook with dirty field tracking
 *
 * Features:
 * - Accumulates multiple changes into a single API call
 * - Tracks dirty fields to prevent SSE overwrites during editing
 * - Shows "Saving..." immediately when changes are queued
 * - Saves after `delay` ms of inactivity (default 5s)
 * - Clears dirty fields after successful save
 *
 * @example
 * const { queueChange, isFieldDirty } = useBatchedConfigSave({
 *   configId: selectedConfigId,
 *   configName: botName,
 *   configType: botType,
 *   delay: 5000,
 * })
 *
 * // Queue changes from any component
 * queueChange({ decision: { user_prompt: newText } })
 * queueChange({ extraction: { indicators: newIndicators } })
 *
 * // Check if field is dirty before applying SSE update
 * if (!isFieldDirty('decision.user_prompt')) {
 *   // Safe to apply SSE update
 * }
 */
export function useBatchedConfigSave({
  configId,
  configName,
  configType,
  delay = 5000,
  enabled = true,
  onSaveComplete,
  onSaveError,
}: UseBatchedConfigSaveOptions): UseBatchedConfigSaveReturn {
  const saveStatusContext = useContext(SaveStatusContext)

  const [status, setStatus] = useState<'idle' | 'pending' | 'saving' | 'saved' | 'error'>('idle')
  const [hasPendingChanges, setHasPendingChanges] = useState(false)

  // Accumulated changes waiting to be saved
  const pendingChangesRef = useRef<Partial<ConfigData>>({})

  // Track which top-level fields have been modified by user
  const dirtyFieldsRef = useRef<Set<string>>(new Set())

  // Debounce timer
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Track if component is mounted
  const mountedRef = useRef(true)

  // Track current configId to detect changes
  const configIdRef = useRef(configId)

  // Clear pending changes when configId changes (switching bots)
  useEffect(() => {
    if (configIdRef.current !== configId) {
      console.log('🔄 [BatchedSave] Config changed, clearing pending changes')
      pendingChangesRef.current = {}
      dirtyFieldsRef.current.clear()
      setHasPendingChanges(false)
      setStatus('idle')
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      configIdRef.current = configId
    }
  }, [configId])

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [])

  // Extract top-level field paths from an update object
  const extractFieldPaths = useCallback((updates: Partial<ConfigData>): string[] => {
    const paths: string[] = []

    for (const key of Object.keys(updates)) {
      paths.push(key)
      // Also track nested paths for more granular dirty tracking
      const value = updates[key as keyof ConfigData]
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        for (const nestedKey of Object.keys(value)) {
          paths.push(`${key}.${nestedKey}`)
        }
      }
    }

    return paths
  }, [])

  // Deep merge helper for nested config objects
  const deepMerge = useCallback((target: Partial<ConfigData>, source: Partial<ConfigData>): Partial<ConfigData> => {
    const result = { ...target }

    for (const key of Object.keys(source) as (keyof ConfigData)[]) {
      const sourceValue = source[key]
      const targetValue = result[key]

      if (
        sourceValue !== null &&
        typeof sourceValue === 'object' &&
        !Array.isArray(sourceValue) &&
        targetValue !== null &&
        typeof targetValue === 'object' &&
        !Array.isArray(targetValue)
      ) {
        // Recursively merge nested objects
        (result as Record<string, unknown>)[key] = deepMerge(
          targetValue as Partial<ConfigData>,
          sourceValue as Partial<ConfigData>
        )
      } else {
        // Overwrite with source value
        (result as Record<string, unknown>)[key] = sourceValue
      }
    }

    return result
  }, [])

  // Perform the actual save
  const performSave = useCallback(async () => {
    if (!configId || Object.keys(pendingChangesRef.current).length === 0) {
      return
    }

    const changesToSave = { ...pendingChangesRef.current }
    pendingChangesRef.current = {}
    setHasPendingChanges(false)
    setStatus('saving')

    try {
      console.log('💾 [BatchedSave] Saving batched changes:', Object.keys(changesToSave))
      await apiClient.updateConfig(configId, changesToSave, configName, configType)
      console.log('✅ [BatchedSave] Save completed successfully')

      if (mountedRef.current) {
        setStatus('saved')
        saveStatusContext?.completeSave('batched-config')

        // Clear dirty fields after successful save
        dirtyFieldsRef.current.clear()

        onSaveComplete?.()

        // Reset to idle after 2 seconds
        setTimeout(() => {
          if (mountedRef.current) {
            setStatus('idle')
          }
        }, 2000)
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Save failed')
      console.error('❌ [BatchedSave] Save failed:', error)

      if (mountedRef.current) {
        setStatus('error')
        saveStatusContext?.failSave('batched-config', error)
        onSaveError?.(error)

        // Re-queue the failed changes for retry
        pendingChangesRef.current = deepMerge(changesToSave, pendingChangesRef.current)
        setHasPendingChanges(true)

        // Reset to idle after 5 seconds
        setTimeout(() => {
          if (mountedRef.current) {
            setStatus('idle')
          }
        }, 5000)
      }
    }
  }, [configId, configName, configType, saveStatusContext, onSaveComplete, onSaveError, deepMerge])

  // Queue a change (called by child components)
  const queueChange = useCallback((updates: Partial<ConfigData>) => {
    if (!configId || !enabled) return

    // Mark fields as dirty
    const fieldPaths = extractFieldPaths(updates)
    fieldPaths.forEach(path => dirtyFieldsRef.current.add(path))

    // Merge new changes into pending queue
    pendingChangesRef.current = deepMerge(pendingChangesRef.current, updates)
    setHasPendingChanges(true)
    setStatus('pending')

    console.log('📝 [BatchedSave] Change queued:', fieldPaths, '| Dirty fields:', Array.from(dirtyFieldsRef.current))

    // Show "Saving..." indicator immediately
    saveStatusContext?.registerSave('batched-config')

    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    // Start new debounce timer
    timerRef.current = setTimeout(() => {
      performSave()
    }, delay)
  }, [configId, enabled, delay, saveStatusContext, performSave, deepMerge, extractFieldPaths])

  // Force immediate save (e.g., before navigation)
  const flush = useCallback(async () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    await performSave()
  }, [performSave])

  // Check if a specific field path is dirty
  const isFieldDirty = useCallback((fieldPath: string): boolean => {
    // Check exact match
    if (dirtyFieldsRef.current.has(fieldPath)) return true

    // Check if any parent path is dirty (e.g., 'decision' makes 'decision.user_prompt' dirty)
    const parts = fieldPath.split('.')
    for (let i = 1; i < parts.length; i++) {
      const parentPath = parts.slice(0, i).join('.')
      if (dirtyFieldsRef.current.has(parentPath)) return true
    }

    // Check if any child path is dirty (e.g., 'decision.user_prompt' makes 'decision' dirty)
    for (const dirty of dirtyFieldsRef.current) {
      if (dirty.startsWith(fieldPath + '.')) return true
    }

    return false
  }, [])

  // Get all dirty fields
  const getDirtyFields = useCallback((): Set<string> => {
    return new Set(dirtyFieldsRef.current)
  }, [])

  // Clear dirty tracking (call after external update like SSE that we want to accept)
  const clearDirtyFields = useCallback(() => {
    dirtyFieldsRef.current.clear()
  }, [])

  return {
    queueChange,
    flush,
    isFieldDirty,
    getDirtyFields,
    clearDirtyFields,
    hasPendingChanges,
    status,
  }
}
