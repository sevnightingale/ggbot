'use client'

import React from 'react'
import { Check, Loader2, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { SaveStatus } from '@/lib/hooks/useAutoSave'

interface SaveStatusIndicatorProps {
  status: SaveStatus
  error?: Error | null
  className?: string
}

/**
 * Global save status indicator for configuration auto-save
 *
 * States:
 * - idle: Hidden
 * - saving: Spinner + "Saving..."
 * - saved: Checkmark + "Saved" (auto-hides after 2s)
 * - error: Alert + error message
 */
export function SaveStatusIndicator({
  status,
  error,
  className = ''
}: SaveStatusIndicatorProps) {
  const showIndicator = status !== 'idle'

  return (
    <AnimatePresence>
      {showIndicator && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.15 }}
          className={`flex items-center justify-center gap-2 px-4 py-2 rounded-xl border text-sm ${className} ${
            status === 'saving'
              ? 'bg-[var(--bg-tertiary)] border-[var(--border)] text-[var(--text-secondary)]'
              : status === 'saved'
              ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
              : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
          }`}
        >
          {/* Icon */}
          {status === 'saving' && (
            <Loader2 className="w-4 h-4 animate-spin" />
          )}
          {status === 'saved' && (
            <Check className="w-4 h-4" />
          )}
          {status === 'error' && (
            <AlertCircle className="w-4 h-4" />
          )}

          {/* Text */}
          <span className="font-medium">
            {status === 'saving' && 'Saving...'}
            {status === 'saved' && 'Saved'}
            {status === 'error' && (error?.message || 'Save failed')}
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
