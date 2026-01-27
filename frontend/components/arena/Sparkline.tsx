'use client'

import React, { useMemo } from 'react'

interface SparklineProps {
  data: Array<{ timestamp: string; equity: number }>
  width?: number
  height?: number
  className?: string
  strokeColor?: string
  strokeWidth?: number
  showEndDot?: boolean
}

/**
 * Lightweight SVG sparkline for showing equity trends
 *
 * Downsamples data to ~50 points for performance while preserving
 * the visual shape of the curve. Pure SVG, no library dependencies.
 */
export function Sparkline({
  data,
  width = 120,
  height = 32,
  className = '',
  strokeColor,
  strokeWidth = 1.5,
  showEndDot = true,
}: SparklineProps) {
  const { path, endPoint, isPositive } = useMemo(() => {
    if (!data || data.length < 2) {
      return { path: '', endPoint: null, isPositive: true, minY: 0, maxY: 0 }
    }

    // Downsample to ~50 points if needed
    const maxPoints = 50
    const step = Math.max(1, Math.floor(data.length / maxPoints))
    const sampled = data.filter((_, i) => i % step === 0 || i === data.length - 1)

    // Calculate bounds
    const values = sampled.map(d => d.equity)
    const minY = Math.min(...values)
    const maxY = Math.max(...values)
    const range = maxY - minY || 1 // Avoid division by zero

    // Padding to prevent clipping
    const padding = 2

    // Generate path
    const points = sampled.map((d, i) => {
      const x = padding + (i / (sampled.length - 1)) * (width - padding * 2)
      const y = padding + (1 - (d.equity - minY) / range) * (height - padding * 2)
      return { x, y }
    })

    // Create SVG path
    const pathCommands = points.map((p, i) =>
      `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
    ).join(' ')

    const startValue = data[0]?.equity || 0
    const endValue = data[data.length - 1]?.equity || 0
    const isPositive = endValue >= startValue

    return {
      path: pathCommands,
      endPoint: points[points.length - 1],
      isPositive,
      minY,
      maxY,
    }
  }, [data, width, height])

  if (!path) {
    return (
      <svg width={width} height={height} className={className}>
        <line
          x1={0}
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="var(--text-muted)"
          strokeWidth={1}
          strokeDasharray="2 2"
          opacity={0.3}
        />
      </svg>
    )
  }

  const color = strokeColor || (isPositive ? 'var(--profit-color)' : 'var(--loss-color)')

  return (
    <svg width={width} height={height} className={className}>
      {/* Sparkline path */}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End dot */}
      {showEndDot && endPoint && (
        <circle
          cx={endPoint.x}
          cy={endPoint.y}
          r={2.5}
          fill={color}
        />
      )}
    </svg>
  )
}
