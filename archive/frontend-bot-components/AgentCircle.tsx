'use client'

import { Settings, CheckCircle, AlertTriangle } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { AgentStatus } from '@/types'

interface AgentCircleProps {
  type: 'extraction' | 'decision' | 'trading'
  title: string
  description: string
  status: AgentStatus
}

const statusConfig = {
  configured: {
    icon: CheckCircle,
    color: 'text-green-400',
    badge: '✓'
  },
  partial: {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    badge: '⚠'
  },
  unconfigured: {
    icon: Settings,
    color: 'text-bone-400',
    badge: '⚙'
  }
}

const typeColors = {
  extraction: {
    border: 'border-blue-400',
    accent: 'text-blue-400',
    bg: 'bg-blue-400/10',
    glow: 'shadow-blue-400/50'
  },
  decision: {
    border: 'border-green-400',
    accent: 'text-green-400',
    bg: 'bg-green-400/10',
    glow: 'shadow-green-400/50'
  },
  trading: {
    border: 'border-orange-400',
    accent: 'text-orange-400',
    bg: 'bg-orange-400/10',
    glow: 'shadow-orange-400/50'
  }
}

export function AgentCircle({ type, title, description, status }: AgentCircleProps) {
  const { openConfigModal } = useBotStore()
  const config = statusConfig[status]
  const typeColor = typeColors[type]
  const StatusIcon = config.icon

  const isConfigured = status === 'configured'

  return (
    <div className="flex flex-col items-center space-y-4 group">
      {/* Agent Info - Moved Above Circle */}
      <div className="text-center space-y-2 max-w-44">
        <h3 className={`text-lg font-display font-bold ${typeColor.accent}`}>
          {title}
        </h3>
        <p className="text-bone-400 text-sm leading-tight">
          {description}
        </p>
        
        {/* Status Label */}
        <div className={`inline-flex items-center gap-2 px-3 py-1 bg-charcoal-800/50 border ${typeColor.border} border-opacity-80`}>
          <div className={`w-2 h-2 ${isConfigured ? typeColor.bg.replace('/10', '') : 'bg-bone-400/50'}`} />
          <span className={`text-sm font-medium ${config.color}`}>
            {config.badge === '✓' ? 'Configured' : config.badge === '⚠' ? 'Partial' : 'Click to configure'}
          </span>
        </div>
      </div>

      {/* Main Circle - Now Below Info */}
      <div 
        className={`
          relative w-32 h-32 bg-charcoal-800/50 border-2 
          ${typeColor.border} 
          ${isConfigured ? `${typeColor.bg} ${typeColor.glow} shadow-lg` : 'border-opacity-50'}
          hover:bg-charcoal-800/70 hover:scale-105 hover:border-opacity-100
          transition-all duration-300 cursor-pointer
          flex items-center justify-center
          ${isConfigured ? 'animate-pulse' : ''}
        `}
        onClick={() => openConfigModal(type)}
        style={{
          boxShadow: isConfigured 
            ? `0 0 20px ${typeColor.glow.replace('shadow-', '').replace('/50', '')}, 0 0 40px ${typeColor.glow.replace('shadow-', '').replace('/50', '')}`
            : undefined
        }}
      >
        {/* Inner glow ring for configured state */}
        {isConfigured && (
          <div className={`absolute inset-3 border ${typeColor.border} opacity-40`} />
        )}
        
        {/* Status Icon */}
        <StatusIcon 
          size={isConfigured ? 48 : 40} 
          className={`${config.color} transition-all duration-300 group-hover:scale-110`} 
        />
        
        {/* Configuration Badge */}
        <div className={`
          absolute -top-2 -right-2 w-8 h-8
          bg-charcoal-800 border-2 ${typeColor.border} 
          flex items-center justify-center text-sm font-bold ${config.color}
          transition-all duration-300
        `}>
          {config.badge}
        </div>

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-bone-200/60 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </div>
  )
}