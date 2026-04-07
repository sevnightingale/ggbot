'use client'

/**
 * ActivityExportModal
 *
 * Owner-only modal that lets the user download a gzipped JSON export of a bot's
 * activity log for a selected time range (max 90 days).
 *
 * Hits `GET /api/v2/activities/{config_id}/export`, which returns an
 * `application/json` body with `Content-Encoding: gzip` and a
 * `Content-Disposition: attachment; filename="..."` header.
 *
 * The browser handles gzip decompression and file save automatically via the
 * anchor download trick.
 */

import { Download, AlertCircle } from 'lucide-react'
import { useState, useEffect, useMemo } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalTitle,
  ModalDescription,
} from '@/components/ui/modal'

interface ActivityExportModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  configId: string
  botName: string
}

const MAX_RANGE_DAYS = 90
const MS_PER_DAY = 24 * 60 * 60 * 1000

// Convert a Date to the `YYYY-MM-DDTHH:mm` string format expected by
// <input type="datetime-local">. This format is local-time (no timezone).
function toDatetimeLocal(d: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return (
    d.getFullYear() +
    '-' +
    pad(d.getMonth() + 1) +
    '-' +
    pad(d.getDate()) +
    'T' +
    pad(d.getHours()) +
    ':' +
    pad(d.getMinutes())
  )
}

// Parse a `YYYY-MM-DDTHH:mm` local-time string back to a Date. The Date
// constructor interprets this as local time, which matches what the picker shows.
function fromDatetimeLocal(s: string): Date {
  return new Date(s)
}

type Preset = { label: string; days: number }

const PRESETS: Preset[] = [
  { label: 'Last 24h', days: 1 },
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 },
]

export function ActivityExportModal({
  open,
  onOpenChange,
  configId,
  botName,
}: ActivityExportModalProps) {
  // Default range: last 7 days
  const [startTime, setStartTime] = useState<string>('')
  const [endTime, setEndTime] = useState<string>('')
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset to "Last 7 days" whenever the modal opens
  useEffect(() => {
    if (open) {
      const now = new Date()
      const sevenDaysAgo = new Date(now.getTime() - 7 * MS_PER_DAY)
      setStartTime(toDatetimeLocal(sevenDaysAgo))
      setEndTime(toDatetimeLocal(now))
      setError(null)
    }
  }, [open])

  // Validation
  const validation = useMemo(() => {
    if (!startTime || !endTime) return { valid: false, error: null }
    const start = fromDatetimeLocal(startTime)
    const end = fromDatetimeLocal(endTime)
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      return { valid: false, error: 'Invalid date' }
    }
    if (end <= start) {
      return { valid: false, error: 'End time must be after start time' }
    }
    if (end > new Date(Date.now() + 5 * 60 * 1000)) {
      return { valid: false, error: 'End time cannot be in the future' }
    }
    const rangeDays = (end.getTime() - start.getTime()) / MS_PER_DAY
    if (rangeDays > MAX_RANGE_DAYS) {
      return {
        valid: false,
        error: `Range is ${Math.round(rangeDays)} days — max ${MAX_RANGE_DAYS} days`,
      }
    }
    return { valid: true, error: null, rangeDays }
  }, [startTime, endTime])

  function applyPreset(days: number) {
    const now = new Date()
    const start = new Date(now.getTime() - days * MS_PER_DAY)
    setStartTime(toDatetimeLocal(start))
    setEndTime(toDatetimeLocal(now))
    setError(null)
  }

  async function handleDownload() {
    if (!validation.valid) return
    setIsDownloading(true)
    setError(null)

    try {
      const supabase = createClientComponentClient()
      const {
        data: { session },
      } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('Not signed in')
      }

      // Convert local-time strings to UTC ISO timestamps for the API
      const startIso = fromDatetimeLocal(startTime).toISOString()
      const endIso = fromDatetimeLocal(endTime).toISOString()

      const url =
        `/api/v2/activities/${configId}/export` +
        `?start_time=${encodeURIComponent(startIso)}` +
        `&end_time=${encodeURIComponent(endIso)}`

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      })

      if (!response.ok) {
        let detail = `Export failed (HTTP ${response.status})`
        try {
          const errJson = await response.json()
          detail = errJson.error || errJson.detail || detail
        } catch {
          // Non-JSON error body — keep default message
        }
        throw new Error(detail)
      }

      // Extract filename from Content-Disposition header
      const disposition = response.headers.get('Content-Disposition') || ''
      const filenameMatch = disposition.match(/filename="([^"]+)"/)
      const filename =
        filenameMatch?.[1] || `${configId}_activities.json.gz`

      // Download via anchor click (browser handles gzip via Content-Encoding)
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      onOpenChange(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setIsDownloading(false)
    }
  }

  const downloadDisabled = !validation.valid || isDownloading

  return (
    <Modal open={open} onOpenChange={onOpenChange} size="sm">
      <ModalHeader onClose={() => onOpenChange(false)}>
        <ModalTitle className="flex items-center gap-2">
          <Download size={20} className="text-[var(--accent)]" />
          Export Activity Log
        </ModalTitle>
        <ModalDescription>
          Download {botName ? <span className="font-medium">{botName}</span> : 'this bot'}&apos;s activity data as a JSON file for analysis.
        </ModalDescription>
      </ModalHeader>

      <ModalBody className="space-y-4">
        {/* Quick presets */}
        <div>
          <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
            Quick select
          </label>
          <div className="grid grid-cols-4 gap-2">
            {PRESETS.map((preset) => (
              <button
                key={preset.days}
                onClick={() => applyPreset(preset.days)}
                disabled={isDownloading}
                className="px-2 py-2 text-xs rounded-md border border-[var(--border)] bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Custom range */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label
              htmlFor="export-start"
              className="block text-xs font-medium text-[var(--text-secondary)] mb-1"
            >
              From (local time)
            </label>
            <input
              id="export-start"
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              disabled={isDownloading}
              className="w-full px-3 py-2 text-sm rounded-md border border-[var(--border)] bg-[var(--bg-tertiary)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] disabled:opacity-50"
            />
          </div>
          <div>
            <label
              htmlFor="export-end"
              className="block text-xs font-medium text-[var(--text-secondary)] mb-1"
            >
              To (local time)
            </label>
            <input
              id="export-end"
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              disabled={isDownloading}
              className="w-full px-3 py-2 text-sm rounded-md border border-[var(--border)] bg-[var(--bg-tertiary)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] disabled:opacity-50"
            />
          </div>
        </div>

        {/* Range summary */}
        {validation.valid && validation.rangeDays !== undefined && (
          <p className="text-xs text-[var(--text-muted)]">
            Range: {validation.rangeDays < 1
              ? `${Math.round(validation.rangeDays * 24)} hour${Math.round(validation.rangeDays * 24) === 1 ? '' : 's'}`
              : `${Math.round(validation.rangeDays * 10) / 10} day${validation.rangeDays === 1 ? '' : 's'}`}
            &nbsp;· Max {MAX_RANGE_DAYS} days per export
          </p>
        )}

        {/* Validation error */}
        {validation.error && (
          <div className="flex items-start gap-2 text-xs text-red-400">
            <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
            <span>{validation.error}</span>
          </div>
        )}

        {/* Request error */}
        {error && (
          <div className="flex items-start gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-md p-2">
            <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <p className="text-xs text-[var(--text-muted)] italic">
          Downloads as a <code className="px-1 bg-[var(--bg-tertiary)] rounded">.json</code> file. Billing and cost data are not included.
        </p>
      </ModalBody>

      <ModalFooter>
        <button
          onClick={() => onOpenChange(false)}
          disabled={isDownloading}
          className="px-4 py-2 text-sm rounded-md text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={handleDownload}
          disabled={downloadDisabled}
          className="px-4 py-2 text-sm rounded-md bg-[var(--accent)] text-[var(--bg-primary)] font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isDownloading ? (
            <>
              <span className="inline-block w-3 h-3 border-2 border-[var(--bg-primary)] border-t-transparent rounded-full animate-spin" />
              Exporting…
            </>
          ) : (
            <>
              <Download size={14} />
              Download
            </>
          )}
        </button>
      </ModalFooter>
    </Modal>
  )
}
