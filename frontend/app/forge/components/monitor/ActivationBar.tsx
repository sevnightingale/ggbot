'use client'

import React from 'react'
import { Activity, Circle, Clock, Play, PauseCircle, Zap } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'

interface ActivationBarProps {
  selectedBot: BotConfiguration
  executionStatus: string
  statusMessage: string
  countdown: string | null
  isStarting: boolean
  isStopping: boolean
  isManualTriggering: boolean
  onStart: () => void
  onStop: () => void
  onManualTrigger: () => void
}

export function ActivationBar({
  selectedBot,
  executionStatus,
  statusMessage,
  countdown,
  isStarting,
  isStopping,
  isManualTriggering,
  onStart,
  onStop,
  onManualTrigger
}: ActivationBarProps) {
  const isActive = selectedBot.state === 'active'
  const isSignalDriven = selectedBot.config_data.decision?.analysis_frequency === 'signal_driven'

  return (
    <div className="sticky top-[64px] z-30 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 mb-4">
      {/* Single Row: Pipeline + Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Pipeline Group */}
        <div className="flex flex-col items-center lg:items-start gap-2">
          <PipelineTicker
            executionStatus={executionStatus}
            isActive={isActive}
          />
          {/* Status Message with Braille Spinner - show during execution even if bot inactive */}
          {statusMessage && executionStatus !== 'idle' && (
            <StatusMessage
              message={statusMessage}
              isActive={true}
            />
          )}
        </div>

        {/* Controls Group */}
        <div className="flex items-center justify-center lg:justify-end gap-3 flex-wrap">
          {/* Countdown */}
          {countdown && !isSignalDriven && (
            <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
              <Clock className="h-4 w-4" />
              <span>{countdown}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={onManualTrigger}
              disabled={isManualTriggering || isStarting || isStopping}
              className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="h-4 w-4" />
              {isManualTriggering ? 'Triggering...' : 'Run once'}
            </button>

            <button
              onClick={isActive ? onStop : onStart}
              disabled={isStarting || isStopping}
              className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-sm font-medium shadow-sm ring-1 ring-inset transition ${
                isActive
                  ? 'bg-rose-600/90 hover:bg-rose-600 ring-rose-500 text-white'
                  : 'bg-emerald-600/90 hover:bg-emerald-600 ring-emerald-500 text-white'
              } disabled:opacity-50`}
            >
              {isActive ? (
                <>
                  <PauseCircle className="h-4 w-4" />
                  {isStopping ? 'Deactivating...' : 'Deactivate'}
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  {isStarting ? 'Activating...' : 'Activate'}
                </>
              )}
            </button>
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
    {
      key: 'extraction',
      label: 'Extraction',
      tooltip: 'Gathering market data, prices, and technical indicators for analysis'
    },
    {
      key: 'decision',
      label: 'Decision',
      tooltip: 'AI analyzing market conditions and determining optimal trading actions'
    },
    {
      key: 'trading',
      label: 'Trading',
      tooltip: 'Executing trades and managing positions based on AI decisions'
    },
    {
      key: 'idle',
      label: 'Idle',
      tooltip: 'Waiting for next scheduled analysis cycle'
    }
  ]

  return (
    <div className="flex items-center gap-2 text-xs">
      {stages.map((stage, index) => {
        const isCurrentStage = executionStatus === stage.key || (!isActive && stage.key === 'idle')
        const isIdleStage = stage.key === 'idle'
        const isLastStage = index === stages.length - 1

        return (
          <div className={`flex items-center ${isIdleStage ? 'hidden md:flex' : ''}`} key={stage.key}>
            <div
              className={`flex items-center gap-1 rounded-full px-2 py-1 transition-colors cursor-help ${
                isCurrentStage
                  ? 'bg-[var(--bg-tertiary)] border border-[var(--border)]'
                  : 'bg-[var(--bg-primary)] border border-[var(--border)] opacity-60'
              }`}
              title={stage.tooltip}
            >
              {isCurrentStage ? (
                <Activity
                  className="h-3.5 w-3.5"
                  style={{
                    color: stage.key === 'extraction' ? 'var(--agent-extraction)' :
                           stage.key === 'decision' ? 'var(--agent-decision)' :
                           stage.key === 'trading' ? 'var(--agent-trading)' :
                           'var(--agent-extraction)' // default for idle
                  }}
                />
              ) : (
                <Circle className="h-3.5 w-3.5 text-[var(--text-muted)]" />
              )}
              <span className={isCurrentStage ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}>
                {stage.label}
              </span>
            </div>
            {/* Hide arrow before idle stage on mobile, and don't show arrow after last visible stage */}
            {!isLastStage && (
              <div className={`mx-1 h-3.5 w-3.5 text-[var(--text-muted)] opacity-40 ${
                index === 2 ? 'hidden md:block' : ''
              }`}>→</div>
            )}
          </div>
        )
      })}
    </div>
  )
}

interface StatusMessageProps {
  message: string
  isActive: boolean
}

function StatusMessage({ message, isActive }: StatusMessageProps) {
  const spinnerChars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
  const [spinnerIndex, setSpinnerIndex] = React.useState(0)

  React.useEffect(() => {
    if (isActive) {
      const interval = setInterval(() => {
        setSpinnerIndex((prev) => (prev + 1) % spinnerChars.length)
      }, 80)
      return () => clearInterval(interval)
    }
    return undefined
  }, [isActive, spinnerChars.length])

  return (
    <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
      {isActive && (
        <span className="font-mono text-[var(--agent-extraction)]">
          {spinnerChars[spinnerIndex]}
        </span>
      )}
      <span>{message}</span>
    </div>
  )
}