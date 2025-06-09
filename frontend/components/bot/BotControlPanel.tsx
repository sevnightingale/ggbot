'use client'

import { Play, Pause, TestTube, AlertTriangle } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { api } from '@/lib/api/client'
import { cn } from '@/lib/utils/cn'

export function BotControlPanel() {
  const { 
    schedulerStatus, 
    startScheduler, 
    stopScheduler, 
    agentStatuses,
    isLoading,
    setError 
  } = useBotStore()

  const isRunning = schedulerStatus.is_running
  const allConfigured = Object.values(agentStatuses).every(status => status === 'configured')

  const handleStart = async () => {
    if (!allConfigured) {
      setError('Please configure all agents before starting the bot')
      return
    }
    await startScheduler()
  }

  const handleStop = async () => {
    await stopScheduler()
  }

  const handleTestRun = async () => {
    try {
      setError(null)
      await api.triggerExtraction()
      // Could show a success message here
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Test run failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Bot Status */}
      <div>
        <h3 className="text-lg font-display font-bold mb-4">Bot Status</h3>
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-3 h-3 rounded-full",
            isRunning ? "bg-status-success animate-pulse" : "bg-bone-400"
          )} />
          <span className="text-bone-200">
            {isRunning ? 'Running Autonomously' : 'Stopped'}
          </span>
        </div>
        {schedulerStatus.last_run && (
          <p className="text-sm text-bone-400 mt-2">
            Last run: {new Date(schedulerStatus.last_run).toLocaleString()}
          </p>
        )}
      </div>

      {/* Configuration Status */}
      <div>
        <h4 className="text-sm font-medium text-bone-300 mb-2">Configuration Status</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm">
            <div className={cn(
              "w-2 h-2 rounded-full",
              agentStatuses.extraction === 'configured' ? "bg-status-success" : "bg-status-warning"
            )} />
            <span>Extraction Agent</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className={cn(
              "w-2 h-2 rounded-full",
              agentStatuses.decision === 'configured' ? "bg-status-success" : "bg-status-warning"
            )} />
            <span>Decision Agent</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className={cn(
              "w-2 h-2 rounded-full",
              agentStatuses.trading === 'configured' ? "bg-status-success" : "bg-status-warning"
            )} />
            <span>Trading Agent</span>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-bone-300">Controls</h4>
        
        {/* Start/Stop Button */}
        <div className="flex gap-3">
          {!isRunning ? (
            <button
              onClick={handleStart}
              disabled={!allConfigured || isLoading}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                allConfigured 
                  ? "bg-status-success hover:bg-status-success/80 text-charcoal-900"
                  : "bg-bone-400/20 text-bone-400 cursor-not-allowed"
              )}
            >
              <Play size={16} />
              Start Autonomous Mode
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-status-error hover:bg-status-error/80 text-white rounded-lg font-medium transition-colors"
            >
              <Pause size={16} />
              Stop Bot
            </button>
          )}
        </div>

        {/* Test Run Button */}
        <button
          onClick={handleTestRun}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-charcoal-700 hover:bg-charcoal-600 border border-bone-200/20 text-bone-200 rounded-lg font-medium transition-colors"
        >
          <TestTube size={16} />
          Manual Test Run
        </button>

        {/* Warning if not all configured */}
        {!allConfigured && (
          <div className="flex items-start gap-2 p-3 bg-status-warning/10 border border-status-warning/20 rounded-lg">
            <AlertTriangle size={16} className="text-status-warning mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="text-status-warning font-medium">Configuration Required</p>
              <p className="text-bone-300">Please configure all agents before starting autonomous mode.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}