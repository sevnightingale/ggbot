'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { apiClient } from '@/lib/api'

interface VirtualsConnectButtonProps {
  onConnected?: (walletAddress?: string) => void
  className?: string
  label?: string
  pollingLabel?: string
  disabled?: boolean
}

/**
 * Popup 1 handler — Virtuals account OAuth.
 *
 * Opens the Virtuals auth URL in a centered popup, polls our backend for
 * the JWT to land in Redis, and fires onConnected when complete.
 * Used both inline from DeployLiveModal and as a standalone button in Settings.
 */
export function VirtualsConnectButton({
  onConnected,
  className,
  label = 'Connect Virtuals',
  pollingLabel = 'Waiting for approval…',
  disabled,
}: VirtualsConnectButtonProps) {
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<'idle' | 'popup' | 'polling' | 'done' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const popupRef = useRef<Window | null>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const clearPoll = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  useEffect(() => () => clearPoll(), [clearPoll])

  const open = useCallback(async () => {
    setBusy(true)
    setError(null)
    setStatus('popup')
    try {
      const { authUrl, requestId } = await apiClient.arenaV2ConnectStart()
      const width = 480
      const height = 720
      const left = Math.max(0, (window.screen.width - width) / 2)
      const top = Math.max(0, (window.screen.height - height) / 2)
      popupRef.current = window.open(
        authUrl,
        'virtuals-connect',
        `width=${width},height=${height},left=${left},top=${top},noopener=no`,
      )
      setStatus('polling')

      // Poll every 2s until backend sees the JWT, then close popup.
      clearPoll()
      pollIntervalRef.current = setInterval(async () => {
        try {
          const result = await apiClient.arenaV2ConnectPoll(requestId)
          if (result.status === 'completed') {
            clearPoll()
            if (popupRef.current && !popupRef.current.closed) {
              popupRef.current.close()
            }
            setStatus('done')
            setBusy(false)
            onConnected?.(result.walletAddress)
          }
        } catch {
          // Keep polling on transient errors — the request itself doesn't error
          // until the JWT arrives or the user cancels (max 10min).
        }
      }, 2000)

      // Stop polling after 5 minutes if the user never finishes.
      setTimeout(() => {
        if (pollIntervalRef.current) {
          clearPoll()
          setStatus('error')
          setError('Connect timed out. Please try again.')
          setBusy(false)
        }
      }, 5 * 60 * 1000)
    } catch (e) {
      setStatus('error')
      setError(e instanceof Error ? e.message : 'Failed to start Virtuals connect')
      setBusy(false)
    }
  }, [clearPoll, onConnected])

  return (
    <div className="flex flex-col gap-1">
      <button
        onClick={open}
        disabled={busy || disabled}
        className={
          className ??
          'px-4 py-2 rounded bg-[var(--accent)] text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed'
        }
      >
        {status === 'polling' || status === 'popup' ? pollingLabel : label}
      </button>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
