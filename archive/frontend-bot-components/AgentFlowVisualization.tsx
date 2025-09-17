'use client'

import { useBotStore } from '@/store/bot'
import { AgentCircle } from './AgentCircle'
import { FlowLine } from './FlowLine'

export function AgentFlowVisualization() {
  const { agentStatuses } = useBotStore()

  return (
    <div className="relative w-full max-w-md h-96 mx-auto">
      {/* SVG for flow lines */}
      <svg 
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 400 400"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Flow lines from agents to central bot */}
        <FlowLine
          from={{ x: 100, y: 100 }}
          to={{ x: 200, y: 250 }}
          color="var(--agent-extraction)"
          isActive={agentStatuses.extraction === 'configured'}
        />
        <FlowLine
          from={{ x: 200, y: 60 }}
          to={{ x: 200, y: 180 }}
          color="var(--agent-decision)"
          isActive={agentStatuses.decision === 'configured'}
        />
        <FlowLine
          from={{ x: 300, y: 100 }}
          to={{ x: 200, y: 250 }}
          color="var(--agent-trading)"
          isActive={agentStatuses.trading === 'configured'}
        />
      </svg>

      {/* Agent circles positioned absolutely */}
      <div className="absolute inset-0">
        {/* Extraction Agent - Top Left */}
        <div className="absolute" style={{ left: '60px', top: '60px' }}>
          <AgentCircle
            title="Data Extraction"
            description="Collects market data"
            type="extraction"
            status={agentStatuses.extraction}
          />
        </div>

        {/* Decision Agent - Top Center */}
        <div className="absolute" style={{ left: '160px', top: '20px' }}>
          <AgentCircle
            title="Decision Engine"
            description="Analyzes data"
            type="decision"
            status={agentStatuses.decision}
          />
        </div>

        {/* Trading Agent - Top Right */}
        <div className="absolute" style={{ left: '260px', top: '60px' }}>
          <AgentCircle
            title="Trade Execution"
            description="Executes trades"
            type="trading"
            status={agentStatuses.trading}
          />
        </div>

        {/* Central GGBot */}
        <div className="absolute" style={{ left: '140px', top: '200px' }}>
          <div className="w-24 h-24 bg-charcoal-700 border-2 border-bone-200/80 flex items-center justify-center">
            <div className="text-center">
              <div className="text-sm font-display font-bold text-bone-200">your</div>
              <div className="text-xs font-display font-bold text-bone-300">ggbot</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}