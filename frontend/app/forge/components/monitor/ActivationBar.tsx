'use client'

import React from 'react'
import { BotConfiguration } from '@/lib/api'

interface ActivationBarProps {
  selectedBot: BotConfiguration
  executionStatus: string
  statusMessage: string
  countdown: string | null
  isStarting: boolean
  isStopping: boolean
  onStart: () => void
  onStop: () => void
}

export function ActivationBar({
  selectedBot,
  executionStatus,
  statusMessage,
  countdown,
  isStarting,
  isStopping,
  onStart,
  onStop
}: ActivationBarProps) {
  const isActive = selectedBot.state === 'active'
  const isSignalDriven = selectedBot.config_data.decision?.analysis_frequency === 'signal_driven'

  return (
    <div className="sticky top-[120px] z-30 bg-[var(--bg-secondary)] border-b border-[var(--border)] p-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        {/* Left: Bot Info & Pipeline */}
        <div className="flex items-center gap-6">
          {/* Bot Status */}
          <div className="flex items-center gap-3">
            <div className={`h-3 w-3 rounded-full ${
              isActive ? 'bg-green-500' : 'bg-gray-500'
            }`} />
            <div>
              <h3 className="font-medium text-[var(--text-primary)]">{selectedBot.config_name}</h3>
              <p className="text-sm text-[var(--text-muted)]">{selectedBot.config_data.selected_pair}</p>
            </div>
          </div>

          {/* Pipeline Ticker */}
          <PipelineTicker
            executionStatus={executionStatus}
            isActive={isActive}
          />
        </div>

        {/* Right: Controls & Countdown */}
        <div className="flex items-center gap-4">
          {/* Status Message */}
          {statusMessage && (
            <div className="text-sm">
              <span className="text-[var(--text-muted)]">Status: </span>
              <span className="text-[var(--text-primary)]">{statusMessage}</span>
            </div>
          )}

          {/* Countdown */}
          {countdown && !isSignalDriven && (
            <div className="text-sm">
              <span className="text-[var(--text-muted)]">Next: </span>
              <span className="text-[var(--text-primary)]">{countdown}</span>
            </div>
          )}

          {/* Start/Stop Controls */}
          <div className="flex gap-2">
            {isActive ? (
              <button
                onClick={onStop}
                disabled={isStopping}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {isStopping ? 'Stopping...' : 'Stop Bot'}
              </button>
            ) : (
              <button
                onClick={onStart}
                disabled={isStarting}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {isStarting ? 'Starting...' : 'Start Bot'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

interface PipelineTickerProps {
  executionStatus: string
  isActive: boolean
}

function PipelineTicker({ executionStatus, isActive }: PipelineTickerProps) {
  const stages = [
    { name: 'Extraction', status: 'extraction', color: 'var(--agent-extraction)' },
    { name: 'Decision', status: 'decision', color: 'var(--agent-decision)' },
    { name: 'Trading', status: 'trading', color: 'var(--agent-trading)' }
  ]

  if (!isActive) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-[var(--text-muted)]">Pipeline inactive</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      {stages.map((stage, index) => {
        const isCurrent = executionStatus === stage.status
        const isCompleted = executionStatus !== 'idle' && stages.findIndex(s => s.status === executionStatus) > index

        return (
          <React.Fragment key={stage.name}>
            <div
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                isCurrent
                  ? 'text-white'
                  : isCompleted
                    ? 'text-[var(--text-primary)] opacity-60'
                    : 'text-[var(--text-muted)] opacity-40'
              }`}
              style={isCurrent ? { backgroundColor: stage.color } : {}}
            >
              {stage.name}
            </div>
            {index < stages.length - 1 && (
              <div className="text-[var(--text-muted)] opacity-40">→</div>
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}