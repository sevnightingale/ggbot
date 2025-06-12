'use client'

import { Play, Square, AlertTriangle, Bot } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { SchedulerStatus } from '@/types'

interface GGBotCircleProps {
  status: SchedulerStatus
}

export function GGBotCircle({ status }: GGBotCircleProps) {
  const { startScheduler, stopScheduler, agentStatuses } = useBotStore()
  const isRunning = status?.is_running || false
  
  // Check if all agents are configured
  const allConfigured = Object.values(agentStatuses).every(status => status === 'configured')
  const canStart = allConfigured && !isRunning

  const handleToggle = async () => {
    if (isRunning) {
      await stopScheduler()
    } else if (canStart) {
      await startScheduler()
    }
  }

  return (
    <div className="flex flex-col items-center space-y-6">
      {/* Main GGBot Circle */}
      <div className="relative">
        <div 
          className={`
            relative w-48 h-48 rounded-full border-2 transition-all duration-500
            ${isRunning 
              ? 'bg-green-400/10 border-green-400 shadow-green-400/50 shadow-2xl animate-pulse' 
              : canStart
                ? 'bg-bone-200/5 border-bone-200/50 hover:border-bone-200/80 hover:bg-bone-200/10'
                : 'bg-charcoal-800/50 border-bone-200/20'
            }
            flex items-center justify-center cursor-pointer
            hover:scale-105 transition-transform
          `}
          onClick={handleToggle}
          style={{
            boxShadow: isRunning 
              ? '0 0 40px rgba(34, 197, 94, 0.5), 0 0 80px rgba(34, 197, 94, 0.3)'
              : undefined
          }}
        >
          {/* Inner glow ring for running state */}
          {isRunning && (
            <div className="absolute inset-6 rounded-full border border-green-400 opacity-60" />
          )}
          
          {/* Central Content */}
          <div className="text-center space-y-2">
            {/* GGBot Icon */}
            <Bot 
              size={isRunning ? 80 : 64} 
              className={`mx-auto transition-all duration-300 ${
                isRunning 
                  ? 'text-green-400' 
                  : canStart 
                    ? 'text-bone-200' 
                    : 'text-bone-400'
              }`} 
            />
            
            {/* GGBot Label */}
            <div className="space-y-1">
              <div className={`text-2xl font-display font-bold ${
                isRunning ? 'text-green-400' : 'text-bone-200'
              }`}>
                GGBot
              </div>
              <div className={`text-sm ${
                isRunning 
                  ? 'text-green-300' 
                  : canStart 
                    ? 'text-bone-300' 
                    : 'text-bone-500'
              }`}>
                {isRunning ? 'ACTIVE' : canStart ? 'READY' : 'STANDBY'}
              </div>
            </div>
          </div>

          {/* Status indicator badge */}
          <div className={`
            absolute -top-3 -right-3 w-12 h-12 rounded-full border-2 border-charcoal-900
            flex items-center justify-center transition-all duration-300
            ${isRunning 
              ? 'bg-green-400' 
              : canStart 
                ? 'bg-blue-400' 
                : 'bg-yellow-400'
            }
          `}>
            {isRunning ? (
              <Square size={20} className="text-charcoal-900" />
            ) : canStart ? (
              <Play size={20} className="text-charcoal-900" />
            ) : (
              <AlertTriangle size={20} className="text-charcoal-900" />
            )}
          </div>

          {/* Hover overlay */}
          <div className="absolute inset-0 bg-bone-200/5 rounded-full opacity-0 hover:opacity-100 transition-opacity" />
        </div>
      </div>

      {/* Status Information */}
      <div className="text-center space-y-3 max-w-md">
        <h2 className={`text-xl font-display font-bold ${
          isRunning ? 'text-green-400' : 'text-bone-200'
        }`}>
          {isRunning ? 'Bot Running' : canStart ? 'Ready to Launch' : 'Configure Agents'}
        </h2>
        
        <p className="text-bone-400 text-sm leading-relaxed">
          {isRunning 
            ? 'Your bot is actively monitoring markets and executing trades'
            : canStart
              ? 'All agents configured. Click to start autonomous trading'
              : 'Configure your agents above to enable autonomous trading'
          }
        </p>

        {/* Action Button */}
        <button
          onClick={handleToggle}
          disabled={!canStart && !isRunning}
          className={`
            px-8 py-3 rounded-lg font-medium transition-all duration-300
            flex items-center gap-3 mx-auto
            ${isRunning
              ? 'bg-red-600 hover:bg-red-700 text-white hover:scale-105'
              : canStart
                ? 'bg-green-600 hover:bg-green-700 text-white hover:scale-105'
                : 'bg-charcoal-700 text-bone-500 cursor-not-allowed'
            }
          `}
        >
          {isRunning ? (
            <>
              <Square size={18} />
              Emergency Stop
            </>
          ) : canStart ? (
            <>
              <Play size={18} />
              Start Trading
            </>
          ) : (
            <>
              <AlertTriangle size={18} />
              Agents Required
            </>
          )}
        </button>
      </div>
    </div>
  )
}