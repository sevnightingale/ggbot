'use client'

import React from 'react'
import { Activity, Circle, Clock, Play, PauseCircle, Zap } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'

interface Account {
  config_id: string
  account_id: string
  current_balance: number
  total_pnl: number
  total_trades: number
  win_trades: number
  loss_trades: number
  open_positions: number
  updated_at: string
}

interface ActivationBarProps {
  selectedBot: BotConfiguration
  executionStatus: string
  statusMessage: string
  countdown: string | null
  account?: Account | null
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
  account,
  isStarting,
  isStopping,
  onStart,
  onStop
}: ActivationBarProps) {
  const isActive = selectedBot.state === 'active'
  const isSignalDriven = selectedBot.config_data.decision?.analysis_frequency === 'signal_driven'
  const configType = selectedBot.config_data.config_type === 'signal_validation' ? 'Signal validation' : 'Autonomous trading'

  // Get real frequency from config
  const analysisFreq = selectedBot.config_data.decision?.analysis_frequency || '1h'
  const frequency = isSignalDriven ? 'Signal driven' : `Every ${analysisFreq}`

  // Get real balance from account data
  const balance = account?.current_balance ?? 10000
  const balanceText = `Paper • $${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

  return (
    <div className="sticky top-[64px] z-30 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 mb-4 max-w-6xl mx-auto">
      {/* Row 1: Info Group (always visible) */}
      <div className="flex flex-wrap items-center gap-3 mb-3 lg:mb-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-[var(--text-muted)]">Bot:</span>
          <span className="font-medium text-[var(--text-primary)]">{selectedBot.config_name}</span>
        </div>

        <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
          {configType}
        </span>

        <span className="rounded-full bg-[var(--agent-extraction)]/10 border border-[var(--agent-extraction)]/30 px-2 py-0.5 text-xs" style={{ color: 'var(--agent-extraction)' }}>
          {balanceText}
        </span>

        <span className="text-xs text-[var(--text-muted)]">{frequency}</span>
      </div>

      {/* Row 2 (Desktop) / Row 2-3 (Mobile): Pipeline + Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Pipeline Group */}
        <div className="flex flex-col items-center gap-2">
          <PipelineTicker
            executionStatus={executionStatus}
            isActive={isActive}
          />
          {/* Status Message with Braille Spinner */}
          {statusMessage && isActive && executionStatus !== 'idle' && (
            <StatusMessage
              message={statusMessage}
              isActive={true}
            />
          )}
        </div>

        {/* Controls Group */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Countdown */}
          {countdown && !isSignalDriven && (
            <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
              <Clock className="h-4 w-4" />
              <span>Next in {countdown}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
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

            <button
              onClick={() => {
                // TODO: Implement run once functionality
                console.log('Run once triggered')
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
            >
              <Zap className="h-4 w-4" />
              Run once
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
    { key: 'extraction', label: 'Extraction' },
    { key: 'decision', label: 'Decision' },
    { key: 'trading', label: 'Trading' },
    { key: 'idle', label: 'Idle' }
  ]

  return (
    <div className="flex items-center gap-2 text-xs">
      {stages.map((stage, index) => {
        const isCurrentStage = executionStatus === stage.key || (!isActive && stage.key === 'idle')

        return (
          <div className="flex items-center" key={stage.key}>
            <div className={`flex items-center gap-1 rounded-full px-2 py-1 transition-colors ${
              isCurrentStage
                ? 'bg-[var(--bg-tertiary)] border border-[var(--border)]'
                : 'bg-[var(--bg-primary)] border border-[var(--border)] opacity-60'
            }`}>
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
            {index < stages.length - 1 && (
              <div className="mx-1 h-3.5 w-3.5 text-[var(--text-muted)] opacity-40">→</div>
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

  const truncatedMessage = message.length > 40 ? `${message.substring(0, 40)}...` : message

  return (
    <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
      {isActive && (
        <span className="font-mono text-[var(--agent-extraction)]">
          {spinnerChars[spinnerIndex]}
        </span>
      )}
      <span>{truncatedMessage}</span>
    </div>
  )
}