'use client'

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { SaveStatus } from '@/lib/hooks/useAutoSave'

interface SaveStatusContextType {
  globalStatus: SaveStatus
  globalError: Error | null
  registerSave: (id: string) => void
  completeSave: (id: string) => void
  failSave: (id: string, error: Error) => void
}

export const SaveStatusContext = createContext<SaveStatusContextType | null>(null)

export function SaveStatusProvider({ children }: { children: ReactNode }) {
  const [activeSaves, setActiveSaves] = useState<Set<string>>(new Set())
  const [lastError, setLastError] = useState<Error | null>(null)
  const [lastCompleteTime, setLastCompleteTime] = useState<number>(0)

  // Register that a save operation started
  const registerSave = useCallback((id: string) => {
    setActiveSaves(prev => new Set(prev).add(id))
    setLastError(null)
  }, [])

  // Mark a save operation as complete
  const completeSave = useCallback((id: string) => {
    setActiveSaves(prev => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    setLastCompleteTime(Date.now())
  }, [])

  // Mark a save operation as failed
  const failSave = useCallback((id: string, error: Error) => {
    setActiveSaves(prev => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    setLastError(error)
  }, [])

  // Determine global status
  const globalStatus: SaveStatus = (() => {
    if (activeSaves.size > 0) return 'saving'
    if (lastError) return 'error'
    // Show "saved" for 2 seconds after last save completes
    if (Date.now() - lastCompleteTime < 2000) return 'saved'
    return 'idle'
  })()

  return (
    <SaveStatusContext.Provider
      value={{
        globalStatus,
        globalError: lastError,
        registerSave,
        completeSave,
        failSave,
      }}
    >
      {children}
    </SaveStatusContext.Provider>
  )
}

export function useSaveStatus() {
  const context = useContext(SaveStatusContext)
  if (!context) {
    throw new Error('useSaveStatus must be used within SaveStatusProvider')
  }
  return context
}
