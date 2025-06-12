'use client'

import { Settings, CheckCircle, AlertTriangle } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { AgentStatus } from '@/types'

interface AgentCardProps {
  type: 'extraction' | 'decision' | 'trading'
  title: string
  description: string
  status: AgentStatus
}

const statusConfig = {
  configured: {
    icon: CheckCircle,
    color: 'text-bone-200',
    bg: 'bg-bone-200/10 border-bone-200/60',
    label: 'Configured'
  },
  partial: {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    bg: 'bg-yellow-400/10 border-yellow-400/20',
    label: 'Partial'
  },
  unconfigured: {
    icon: Settings,
    color: 'text-bone-400',
    bg: 'bg-bone-400/10 border-bone-400/20',
    label: 'Configure'
  }
}


export function AgentCard({ type, title, description, status }: AgentCardProps) {
  const { openConfigModal } = useBotStore()
  const config = statusConfig[status]
  const StatusIcon = config.icon

  const isConfigured = status === 'configured'

  return (
    <div 
      className={`
        border-2 border-bone-200/80 p-6 
        hover:border-bone-200
        transition-all duration-300 cursor-pointer group
        paper-texture
        ${isConfigured ? `hover:shadow-lg animate-pulse-glow` : ''}
      `}
      style={{
        boxShadow: isConfigured 
          ? `0 0 30px ${type === 'extraction' ? 'rgba(56, 161, 199, 0.6)' : type === 'decision' ? 'rgba(44, 190, 119, 0.6)' : 'rgba(190, 106, 71, 0.6)'}, 0 0 60px ${type === 'extraction' ? 'rgba(56, 161, 199, 0.2)' : type === 'decision' ? 'rgba(44, 190, 119, 0.2)' : 'rgba(190, 106, 71, 0.2)'}`
          : undefined
      }}
      onClick={() => openConfigModal(type)}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-display font-bold text-bone-200">{title}</h3>
        <div className="bg-charcoal-700/50 border border-bone-200/60 px-3 py-1 flex items-center gap-2">
          <StatusIcon size={16} className={config.color} />
          <span className={`text-sm font-medium ${config.color}`}>
            {config.label}
          </span>
        </div>
      </div>
      
      <p className="text-bone-400 text-sm mb-4">{description}</p>
      
      {/* Minimal color accent bar */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-bone-500 group-hover:text-bone-400 transition-colors">
          Click to configure →
        </div>
        <div 
          className={`w-8 h-1 ${
            type === 'extraction' ? 'bg-blue-400' : 
            type === 'decision' ? 'bg-green-400' : 
            'bg-orange-400'
          } ${isConfigured ? 'opacity-100' : 'opacity-30'}`}
        />
      </div>
    </div>
  )
}