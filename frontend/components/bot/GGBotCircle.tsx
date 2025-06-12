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
      {/* Main GGBot Circle - Brutalist Design */}
      <div className="relative">
        <div 
          className={`
            relative w-48 h-48 rounded-full border-2 transition-all duration-500
            bg-bone-200/5 border-bone-200/30
            flex items-center justify-center cursor-pointer
            hover:border-bone-200/50 hover:bg-bone-200/8
            ${isRunning ? 'shadow-2xl' : ''}
          `}
          onClick={handleToggle}
          style={{
            backgroundImage: 'radial-gradient(circle at 30% 30%, rgba(227, 229, 230, 0.1) 0%, transparent 50%)',
            boxShadow: isRunning 
              ? '0 0 40px rgba(34, 197, 94, 0.4), 0 0 80px rgba(34, 197, 94, 0.2)'
              : '0 4px 20px rgba(0, 0, 0, 0.3)'
          }}
        >
          {/* Paper texture overlay */}
          <div 
            className="absolute inset-0 rounded-full opacity-20 mix-blend-overlay"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23e3e5e6' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
            }}
          />
          
          {/* Subtle inner border */}
          <div className="absolute inset-3 rounded-full border border-bone-200/20" />
          
          {/* Central Content */}
          <div className="text-center space-y-2 relative z-10">
            {/* GGBot Icon */}
            <Bot 
              size={64} 
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
              <div className="text-2xl font-display font-bold text-bone-200">
                GGBot
              </div>
              <div className={`text-sm font-medium ${
                isRunning 
                  ? 'text-green-400' 
                  : canStart 
                    ? 'text-bone-300' 
                    : 'text-bone-500'
              }`}>
                {isRunning ? 'ACTIVE' : canStart ? 'READY' : 'STANDBY'}
              </div>
            </div>
          </div>

          {/* Status indicator badge - Sharp edges */}
          <div className={`
            absolute -top-3 -right-3 w-12 h-12 border-2 border-charcoal-900
            flex items-center justify-center transition-all duration-300
            ${isRunning 
              ? 'bg-green-400' 
              : canStart 
                ? 'bg-bone-300' 
                : 'bg-yellow-400'
            }
          `}
          style={{
            clipPath: 'polygon(20% 0%, 80% 0%, 100% 20%, 100% 80%, 80% 100%, 20% 100%, 0% 80%, 0% 20%)'
          }}
          >
            {isRunning ? (
              <Square size={20} className="text-charcoal-900" />
            ) : canStart ? (
              <Play size={20} className="text-charcoal-900" />
            ) : (
              <AlertTriangle size={20} className="text-charcoal-900" />
            )}
          </div>
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

        {/* Action Button - Sharp edges */}
        <button
          onClick={handleToggle}
          disabled={!canStart && !isRunning}
          className={`
            px-8 py-3 font-medium transition-all duration-300
            flex items-center gap-3 mx-auto border-2
            ${isRunning
              ? 'bg-red-600 hover:bg-red-700 text-white border-red-500 hover:border-red-400'
              : canStart
                ? 'bg-green-600 hover:bg-green-700 text-white border-green-500 hover:border-green-400'
                : 'bg-charcoal-700 text-bone-500 border-bone-500/20 cursor-not-allowed'
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