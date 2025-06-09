'use client'

import { Check, AlertTriangle, Settings } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { AgentStatus } from '@/types'
import { cn } from '@/lib/utils/cn'

interface AgentCircleProps {
  name: string
  type: 'extraction' | 'decision' | 'trading'
  status: AgentStatus
}

const agentColors = {
  extraction: 'agents-extraction',
  decision: 'agents-decision',
  trading: 'agents-trading',
}

const statusIcons = {
  configured: Check,
  partial: AlertTriangle,
  unconfigured: Settings,
}

const statusColors = {
  configured: 'text-status-success',
  partial: 'text-status-warning',
  unconfigured: 'text-bone-400',
}

export function AgentCircle({ name, type, status }: AgentCircleProps) {
  const { openConfigModal } = useBotStore()
  const StatusIcon = statusIcons[status]
  const agentColor = agentColors[type]

  const handleClick = () => {
    openConfigModal(type)
  }

  return (
    <div className="relative group">
      {/* Main circle */}
      <button
        onClick={handleClick}
        className={cn(
          "relative w-20 h-20 border-2 rounded-full transition-all duration-300 cursor-pointer",
          "hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-bone-300",
          status === 'configured' && [
            `border-${agentColor}`,
            `bg-${agentColor}/10`,
            "animate-pulse-glow"
          ],
          status === 'partial' && [
            "border-status-warning",
            "bg-status-warning/10"
          ],
          status === 'unconfigured' && [
            "border-bone-200/30",
            "bg-charcoal-800"
          ]
        )}
        style={{
          boxShadow: status === 'configured' 
            ? `0 0 20px var(--agent-${type}), 0 0 40px var(--agent-${type})`
            : undefined
        }}
      >
        {/* Agent name */}
        <div className="text-center">
          <div className="text-xs font-display font-bold text-bone-200 leading-tight">
            {name}
          </div>
          <div className="text-xs text-bone-400 leading-tight">
            Agent
          </div>
        </div>

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-bone-200/10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
      </button>

      {/* Status indicator */}
      <div className={cn(
        "absolute -top-1 -right-1 w-6 h-6 rounded-full border-2 border-charcoal-900 flex items-center justify-center",
        status === 'configured' && `bg-${agentColor}`,
        status === 'partial' && "bg-status-warning",
        status === 'unconfigured' && "bg-bone-400"
      )}>
        <StatusIcon 
          size={12} 
          className={cn(
            status === 'configured' && "text-charcoal-900",
            status !== 'configured' && "text-charcoal-900"
          )} 
        />
      </div>

      {/* Tooltip on hover */}
      <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-charcoal-700 border border-bone-200/20 rounded text-xs text-bone-200 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
        {status === 'configured' && 'Configured - Click to edit'}
        {status === 'partial' && 'Partially configured - Click to complete'}
        {status === 'unconfigured' && 'Not configured - Click to set up'}
      </div>
    </div>
  )
}