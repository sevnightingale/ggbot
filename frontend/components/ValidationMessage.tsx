'use client'

import React from 'react'
import { AlertCircle, AlertTriangle } from 'lucide-react'

interface ValidationMessageProps {
  error?: string | null
  warning?: string | null
  className?: string
}

export function ValidationMessage({ error, warning, className = '' }: ValidationMessageProps) {
  if (!error && !warning) return null

  if (error) {
    return (
      <div className={`flex items-start gap-2 mt-2 text-sm text-red-500 ${className}`}>
        <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
        <span>{error}</span>
      </div>
    )
  }

  if (warning) {
    return (
      <div className={`flex items-start gap-2 mt-2 text-sm text-yellow-500 ${className}`}>
        <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
        <span>{warning}</span>
      </div>
    )
  }

  return null
}
