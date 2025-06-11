'use client'

import { Play, Square, AlertCircle } from 'lucide-react'
import { useBotStore } from '@/store/bot'

interface BotStatusCardProps {
  status: any // Your scheduler status type
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
    <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-400' : 'bg-bone-400'}`} />
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
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
              isRunning
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
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