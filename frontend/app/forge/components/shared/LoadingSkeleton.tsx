'use client'

import React from 'react'

interface LoadingSkeletonProps {
  variant?: 'text' | 'card' | 'circle' | 'table'
  lines?: number
  className?: string
}

export function LoadingSkeleton({ variant = 'text', lines = 1, className = '' }: LoadingSkeletonProps) {
  const baseClasses = 'animate-pulse bg-[var(--bg-tertiary)] rounded'

  if (variant === 'text') {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }, (_, i) => (
          <div key={i} className={`${baseClasses} h-4`} style={{ width: `${80 + Math.random() * 20}%` }} />
        ))}
      </div>
    )
  }

  if (variant === 'card') {
    return (
      <div className={`${baseClasses} p-6 ${className}`}>
        <div className="flex items-center gap-4 mb-4">
          <div className={`${baseClasses} h-12 w-12 rounded-full`} />
          <div className="space-y-2 flex-1">
            <div className={`${baseClasses} h-4 w-1/3`} />
            <div className={`${baseClasses} h-3 w-1/2`} />
          </div>
        </div>
        <div className="space-y-2">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className={`${baseClasses} h-3`} style={{ width: `${60 + Math.random() * 30}%` }} />
          ))}
        </div>
      </div>
    )
  }

  if (variant === 'circle') {
    return <div className={`${baseClasses} rounded-full ${className}`} />
  }

  if (variant === 'table') {
    return (
      <div className={`space-y-3 ${className}`}>
        {Array.from({ length: lines }, (_, i) => (
          <div key={i} className="flex gap-4">
            <div className={`${baseClasses} h-4 w-1/4`} />
            <div className={`${baseClasses} h-4 w-1/3`} />
            <div className={`${baseClasses} h-4 w-1/4`} />
            <div className={`${baseClasses} h-4 w-1/6`} />
          </div>
        ))}
      </div>
    )
  }

  return <div className={`${baseClasses} h-4 ${className}`} />
}