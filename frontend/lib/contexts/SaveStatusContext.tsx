'use client'

import React, { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react'
import { SaveStatus } from '@/lib/hooks/useAutoSave'

interface SaveStatusContextType {
  globalStatus: SaveStatus
  globalError: Error | null
  globalMessage: string | null  // Custom message for operations (e.g., "Resetting...", "Account reset")
  registerSave: (id: string, message?: string) => void
  completeSave: (id: string, message?: string) => void
  failSave: (id: string, error: Error) => void
}

export const SaveStatusContext = createContext<SaveStatusContextType | null>(null)

export function SaveStatusProvider({ children }: { children: ReactNode }) {
  const [activeSaves, setActiveSaves] = useState<Set<string>>(new Set())
  const [lastError, setLastError] = useState<Error | null>(null)
  const [lastCompleteTime, setLastCompleteTime] = useState<number>(0)
  const [currentMessage, setCurrentMessage] = useState<string | null>(null)  // Custom operation message
  const [, forceUpdate] = useState({})  // Dummy state to force re-render
  const hideTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Register that a save operation started
  const registerSave = useCallback((id: string, message?: string) => {
    setActiveSaves(prev => new Set(prev).add(id))
    setLastError(null)
    setCurrentMessage(message || null)  // Set custom message if provided
    // Clear any pending hide timer
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current)
      hideTimerRef.current = null
    }
  }, [])

  // Mark a save operation as complete
  const completeSave = useCallback((id: string, message?: string) => {
    setActiveSaves(prev => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    setLastCompleteTime(Date.now())
    setCurrentMessage(message || null)  // Set custom success message if provided

    // Schedule a re-render after 2s to hide the "Saved" indicator
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current)
    }
    hideTimerRef.current = setTimeout(() => {
      setCurrentMessage(null)  // Clear message when indicator hides
      forceUpdate({})  // Force re-render to transition from 'saved' to 'idle'
    }, 2100)  // Slightly longer than 2s to ensure the check passes
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

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (hideTimerRef.current) {
        clearTimeout(hideTimerRef.current)
      }
    }
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
        globalMessage: currentMessage,
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
