'use client'

import { Play, Square, AlertTriangle } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { SchedulerStatus } from '@/types'

interface BotStatusCardProps {
  status: SchedulerStatus
}

export function BotStatusCard({ status }: BotStatusCardProps) {
  const { startScheduler, stopScheduler } = useBotStore()
  const isRunning = status?.is_running || false

  const handleToggle = async () => {
    if (isRunning) {
      await stopScheduler()
    } else {
      await startScheduler()
    }
  }

  return (
    <div className="bg-charcoal-800/50 border border-bone-200/60 p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-3 h-3 ${isRunning ? 'bg-bone-200' : 'bg-bone-400'}`} />
            <h2 className="text-xl font-display font-bold">
              Bot Status: {isRunning ? 'Running' : 'Stopped'}
            </h2>
          </div>
          <p className="text-bone-400 text-sm">
            {isRunning 
              ? 'Your bot is actively monitoring markets and executing trades'
              : 'Configure your agents and start autonomous trading'
            }
          </p>
        </div>

        <div className="flex items-center gap-4">
          {!isRunning && (
            <div className="flex items-center gap-2 text-yellow-400 text-sm">
              <AlertTriangle size={16} />
              <span>Configure agents to start</span>
            </div>
          )}
          
          <button
            onClick={handleToggle}
            className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
              isRunning
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-bone-200 hover:bg-bone-300 text-charcoal-900'
            }`}
          >
            {isRunning ? (
              <>
                <Square size={16} />
                Stop Bot
              </>
            ) : (
              <>
                <Play size={16} />
                Start Bot
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}