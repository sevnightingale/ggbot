'use client'

import React from 'react'
import { ConfigData } from '@/lib/api'

interface MarketDataSelectorProps {
  configData?: ConfigData
  onUpdate?: (updates: Partial<ConfigData>) => void
  className?: string
}

export function MarketDataSelector({
  configData,
  onUpdate,
  className = ''
}: MarketDataSelectorProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Data Sources Section */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Data Sources
        </h3>

        {/* Technical Analysis */}
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--agent-extraction)]/10 flex items-center justify-center">
                <span className="text-sm">📈</span>
              </div>
              <div>
                <div className="font-medium text-[var(--text-primary)]">Technical Analysis</div>
                <div className="text-sm text-[var(--text-muted)]">Core technical indicators</div>
              </div>
            </div>
            <div className="text-sm text-emerald-500 font-medium">FREE</div>
          </div>

          {/* Placeholder for data points */}
          <div className="ml-11 space-y-2">
            <div className="text-sm text-[var(--text-muted)]">Selected Indicators:</div>
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 rounded-md bg-[var(--agent-extraction)]/20 text-[var(--agent-extraction)] text-xs">
                RSI
              </span>
              {/* More indicators will be added here */}
            </div>
          </div>
        </div>

        {/* Signal Sources (Premium) */}
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] opacity-60">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--agent-decision)]/10 flex items-center justify-center">
                <span className="text-sm">📡</span>
              </div>
              <div>
                <div className="font-medium text-[var(--text-primary)]">Signal Sources</div>
                <div className="text-sm text-[var(--text-muted)]">ggShot and premium signals</div>
              </div>
            </div>
            <div className="text-sm text-amber-500 font-medium">PREMIUM</div>
          </div>
        </div>
      </div>

      {/* Timeframes Section */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Analysis Timeframes
        </h3>

        <div className="grid grid-cols-4 lg:grid-cols-7 gap-2">
          {['5m', '15m', '30m', '1h', '4h', '1d', '1w'].map((timeframe) => (
            <button
              key={timeframe}
              className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                timeframe === '1h'
                  ? 'bg-[var(--agent-extraction)] text-white border-[var(--agent-extraction)]'
                  : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-tertiary)]'
              }`}
            >
              {timeframe}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}