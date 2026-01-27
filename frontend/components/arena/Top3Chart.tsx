'use client'

import React, { useEffect, useRef, useMemo } from 'react'
import { createChart, IChartApi, ISeriesApi, LineData, ColorType, Time } from 'lightweight-charts'
import { ArenaBot } from '@/lib/queries'

interface Top3ChartProps {
  bots: ArenaBot[]
  className?: string
}

// Podium colors - brass variants for ceremonial feel
const PODIUM_COLORS = {
  gold: '#c1a87d',    // Brass - 1st place
  silver: '#a8a8a8',  // Silver - 2nd place
  bronze: '#cd7f32',  // Bronze - 3rd place
}

/**
 * Lightweight-charts based chart showing only top 3 bots
 *
 * Clean, performant, interactive. Designed for the Arena podium.
 */
export function Top3Chart({ bots, className = '' }: Top3ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRefs = useRef<ISeriesApi<'Line'>[]>([])

  // Get top 3 bots sorted by equity
  const top3 = useMemo(() => {
    return [...bots]
      .sort((a, b) => b.current_equity - a.current_equity)
      .slice(0, 3)
  }, [bots])

  // Convert data points to lightweight-charts format
  const seriesData = useMemo(() => {
    return top3.map(bot => {
      const data: LineData<Time>[] = bot.data_points.map(point => ({
        time: Math.floor(new Date(point.timestamp).getTime() / 1000) as Time,
        value: point.equity,
      }))
      // Sort by time and remove duplicates
      const seen = new Set<number>()
      return data
        .filter(d => {
          if (seen.has(d.time as number)) return false
          seen.add(d.time as number)
          return true
        })
        .sort((a, b) => (a.time as number) - (b.time as number))
    })
  }, [top3])

  useEffect(() => {
    if (!containerRef.current || top3.length === 0) return

    // Create chart
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8a8781',
        fontFamily: "'IBM Plex Mono', monospace",
      },
      grid: {
        vertLines: { color: '#2a2a2d', style: 1 },
        horzLines: { color: '#2a2a2d', style: 1 },
      },
      crosshair: {
        mode: 0, // Normal crosshair
        vertLine: {
          color: '#c1a87d',
          width: 1,
          style: 2,
          labelBackgroundColor: '#141416',
        },
        horzLine: {
          color: '#c1a87d',
          width: 1,
          style: 2,
          labelBackgroundColor: '#141416',
        },
      },
      rightPriceScale: {
        borderColor: '#2a2a2d',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: '#2a2a2d',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: { mouseWheel: true, pinch: true },
    })

    chartRef.current = chart

    // Add series for each top 3 bot
    const colors = [PODIUM_COLORS.gold, PODIUM_COLORS.silver, PODIUM_COLORS.bronze]
    seriesRefs.current = top3.map((bot, index) => {
      const series = chart.addLineSeries({
        color: colors[index],
        lineWidth: index === 0 ? 3 : 2, // Leader gets thicker line
        priceFormat: {
          type: 'custom',
          formatter: (price: number) => `$${price.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        },
        title: bot.config_name,
        lastValueVisible: true,
        priceLineVisible: false,
      })
      series.setData(seriesData[index])
      return series
    })

    // Fit content
    chart.timeScale().fitContent()

    // Handle resize
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
      seriesRefs.current = []
    }
  }, [top3, seriesData])

  if (top3.length === 0) {
    return (
      <div className={`flex items-center justify-center h-48 ${className}`}>
        <span className="text-[var(--text-muted)]">No data available</span>
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mb-4">
        {top3.map((bot, index) => {
          const colors = [PODIUM_COLORS.gold, PODIUM_COLORS.silver, PODIUM_COLORS.bronze]
          const medals = ['🥇', '🥈', '🥉']
          const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
          return (
            <div key={bot.config_id} className="flex items-center gap-2">
              <span className="text-lg">{medals[index]}</span>
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: colors[index] }}
              />
              <span className="text-sm font-medium text-[var(--text-primary)]">
                {bot.config_name}
              </span>
              <span className={`text-sm font-mono ${pnlPercent >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
                {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(1)}%
              </span>
            </div>
          )
        })}
      </div>

      {/* Chart container */}
      <div
        ref={containerRef}
        className="w-full h-[200px] md:h-[280px]"
      />
    </div>
  )
}
