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
    color: 'text-green-400',
    bg: 'bg-green-400/10 border-green-400/20',
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

const typeColors = {
  extraction: 'border-l-blue-400',
  decision: 'border-l-green-400', 
  trading: 'border-l-orange-400'
}

export function AgentCard({ type, title, description, status }: AgentCardProps) {
  const { openConfigModal } = useBotStore()
  const config = statusConfig[status]
  const StatusIcon = config.icon

  return (
    <div 
      className={`bg-charcoal-800/50 border border-bone-200/10 ${typeColors[type]} border-l-4 rounded-lg p-6 hover:bg-charcoal-800/70 transition-colors cursor-pointer group`}
      onClick={() => openConfigModal(type)}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-display font-bold text-bone-200">{title}</h3>
        <div className={`${config.bg} border rounded-lg px-3 py-1 flex items-center gap-2`}>
          <StatusIcon size={16} className={config.color} />
          <span className={`text-sm font-medium ${config.color}`}>
            {config.label}
          </span>
        </div>
      </div>
      
      <p className="text-bone-400 text-sm mb-4">{description}</p>
      
      <div className="text-xs text-bone-500 group-hover:text-bone-400 transition-colors">
        Click to configure →
      </div>
    </div>
  )
}