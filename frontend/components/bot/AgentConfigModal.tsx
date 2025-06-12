'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { ExtractionConfigForm } from './config/ExtractionConfigForm'
import { DecisionConfigForm } from './config/DecisionConfigForm'
import { TradingConfigForm } from './config/TradingConfigForm'
import { cn } from '@/lib/utils/cn'

const agentInfo = {
  extraction: {
    name: 'Extraction Agent',
    color: 'agents-extraction',
    description: 'Configure data sources, symbols, and technical indicators'
  },
  decision: {
    name: 'Decision Agent',
    color: 'agents-decision',
    description: 'Set up trading strategy and LLM preferences'
  },
  trading: {
    name: 'Trading Agent',
    color: 'agents-trading',
    description: 'Configure risk management and execution settings'
  }
}

const tabs = {
  extraction: ['Symbols', 'Timeframes', 'Data Sources'],
  decision: ['Strategy', 'LLM Settings', 'Context'],
  trading: ['Exchange', 'Risk Management', 'Execution Rules']
}

export function AgentConfigModal() {
  const { 
    activeConfigAgent, 
    closeConfigModal, 
    extractionConfig,
    decisionConfig,
    tradingConfig,
    isLoading 
  } = useBotStore()

  const [activeTab, setActiveTab] = useState(0)

  // Reset to first tab when agent changes
  useEffect(() => {
    setActiveTab(0)
  }, [activeConfigAgent])

  if (!activeConfigAgent) return null

  const agent = agentInfo[activeConfigAgent]
  const agentTabs = tabs[activeConfigAgent]

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeConfigModal()
    }
  }


  const renderConfigForm = () => {
    switch (activeConfigAgent) {
      case 'extraction':
        return <ExtractionConfigForm activeTab={activeTab} config={extractionConfig} />
      case 'decision':
        return <DecisionConfigForm activeTab={activeTab} config={decisionConfig} />
      case 'trading':
        return <TradingConfigForm activeTab={activeTab} config={tradingConfig} />
      default:
        return null
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-charcoal-800 border border-bone-200/80 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className={cn(
          "p-6 border-b border-bone-200/60",
          activeConfigAgent === 'extraction' ? 'border-l-4 border-l-agents-extraction' :
          activeConfigAgent === 'decision' ? 'border-l-4 border-l-agents-decision' :
          activeConfigAgent === 'trading' ? 'border-l-4 border-l-agents-trading' : ''
        )}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-display font-bold text-bone-200">
                {agent.name}
              </h2>
              <p className="text-bone-400 mt-1">{agent.description}</p>
            </div>
            <button
              onClick={closeConfigModal}
              className="p-2 hover:bg-charcoal-700 transition-colors"
            >
              <X size={24} className="text-bone-400" />
            </button>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-1 mt-6">
            {agentTabs.map((tab, index) => (
              <button
                key={tab}
                onClick={() => setActiveTab(index)}
                className={cn(
                  "px-4 py-2 text-sm font-medium transition-colors",
                  activeTab === index
                    ? (activeConfigAgent === 'extraction' ? 'bg-agents-extraction text-charcoal-900' :
                       activeConfigAgent === 'decision' ? 'bg-agents-decision text-charcoal-900' :
                       activeConfigAgent === 'trading' ? 'bg-agents-trading text-charcoal-900' : '')
                    : "text-bone-300 hover:text-bone-200 hover:bg-charcoal-700"
                )}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-bone-200/80 border-t-transparent animate-spin"></div>
            </div>
          ) : (
            renderConfigForm()
          )}
        </div>
      </div>
    </div>
  )
}