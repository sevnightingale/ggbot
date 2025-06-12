'use client'

import { useEffect } from 'react'
import { PageWrapper } from '@/components/ui/PageWrapper'
import { useBotStore } from '@/store/bot'
import { AgentCard } from '@/components/bot/AgentCard'
import { GGBotCircle } from '@/components/bot/GGBotCircle'
import { TradeTable } from '@/components/trades/TradeTable'
import { PerformanceChart } from '@/components/charts/PerformanceChart'
import { AgentConfigModal } from '@/components/bot/AgentConfigModal'

export function MainDashboard() {
  const {
    loadConfigurations,
    loadTrades,
    loadPerformance,
    checkSchedulerStatus,
    isLoading,
    error,
    isConfigModalOpen,
    agentStatuses,
    schedulerStatus
  } = useBotStore()

  useEffect(() => {
    console.log('MainDashboard: Starting initial data load...')
    
    const loadInitialData = async () => {
      console.log('MainDashboard: Loading initial data...')
      const startTime = Date.now()
      
      try {
        // Load configurations first, then other data
        console.log('MainDashboard: Loading configurations...')
        await loadConfigurations()
        console.log('MainDashboard: Configurations loaded')
        
        // Load other data in parallel
        console.log('MainDashboard: Loading trades, performance, and scheduler status...')
        await Promise.allSettled([
          loadTrades(),
          loadPerformance('7d'),
          checkSchedulerStatus()
        ])
        
        const endTime = Date.now()
        console.log(`MainDashboard: All data loaded in ${endTime - startTime}ms`)
      } catch (error) {
        console.error('MainDashboard: Failed to load initial data:', error)
      }
    }

    loadInitialData()

    // Set up periodic refresh
    console.log('MainDashboard: Setting up periodic refresh (30s)')
    const interval = setInterval(() => {
      console.log('MainDashboard: Periodic refresh triggered')
      loadTrades()
      checkSchedulerStatus()
    }, 30000)

    return () => {
      console.log('MainDashboard: Cleaning up periodic refresh')
      clearInterval(interval)
    }
  }, [loadConfigurations, loadTrades, loadPerformance, checkSchedulerStatus])

  if (isLoading) {
    return (
      <PageWrapper>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-bone-200 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-bone-300">Loading dashboard...</p>
          </div>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-900/20 border border-red-500/20 rounded-lg">
            <p className="text-red-400 text-center">{error}</p>
          </div>
        )}

        {/* Agent Flow Visualization */}
        <div className="relative">
          {/* SVG for Flow Lines */}
          <svg 
            className="absolute inset-0 w-full h-full pointer-events-none z-0"
            viewBox="0 0 1000 400"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Flow line from extraction agent card */}
            <path
              d="M 200 180 L 200 220 L 480 220 L 480 280"
              stroke={agentStatuses.extraction === 'configured' ? 'rgba(56, 161, 199, 0.6)' : 'rgba(227, 229, 230, 0.2)'}
              strokeWidth="2"
              fill="none"
              className={agentStatuses.extraction === 'configured' ? 'flow-line-active' : ''}
              style={{
                filter: agentStatuses.extraction === 'configured' 
                  ? 'drop-shadow(0 0 6px rgba(56, 161, 199, 0.4))' 
                  : undefined
              }}
            />
            
            {/* Flow line from decision agent card */}
            <path
              d="M 500 180 L 500 280"
              stroke={agentStatuses.decision === 'configured' ? 'rgba(44, 190, 119, 0.6)' : 'rgba(227, 229, 230, 0.2)'}
              strokeWidth="2"
              fill="none"
              className={agentStatuses.decision === 'configured' ? 'flow-line-active' : ''}
              style={{
                filter: agentStatuses.decision === 'configured' 
                  ? 'drop-shadow(0 0 6px rgba(44, 190, 119, 0.4))' 
                  : undefined
              }}
            />
            
            {/* Flow line from trading agent card */}
            <path
              d="M 800 180 L 800 220 L 520 220 L 520 280"
              stroke={agentStatuses.trading === 'configured' ? 'rgba(190, 106, 71, 0.6)' : 'rgba(227, 229, 230, 0.2)'}
              strokeWidth="2"
              fill="none"
              className={agentStatuses.trading === 'configured' ? 'flow-line-active' : ''}
              style={{
                filter: agentStatuses.trading === 'configured' 
                  ? 'drop-shadow(0 0 6px rgba(190, 106, 71, 0.4))' 
                  : undefined
              }}
            />
          </svg>
          
          {/* Agent Cards */}
          <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            <AgentCard
              type="extraction"
              title="Data Extraction"
              description="Collects market data and technical indicators"
              status={agentStatuses.extraction}
            />
            <AgentCard
              type="decision"
              title="Decision Engine"
              description="Analyzes data and generates trading signals"
              status={agentStatuses.decision}
            />
            <AgentCard
              type="trading"
              title="Trade Execution"
              description="Manages positions and executes trades"
              status={agentStatuses.trading}
            />
          </div>

          {/* GGBot Central Circle */}
          <div className="relative z-10 flex justify-center">
            <GGBotCircle status={schedulerStatus} />
          </div>
        </div>

        {/* Trading Dashboard - Brutalist Design */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-charcoal-800/50 border-2 border-bone-200/20 p-6">
            <h2 className="text-xl font-display font-bold mb-6 text-bone-200">Active Trades</h2>
            <TradeTable />
          </div>

          <div className="bg-charcoal-800/50 border-2 border-bone-200/20 p-6">
            <h2 className="text-xl font-display font-bold mb-6 text-bone-200">Performance</h2>
            <PerformanceChart />
          </div>
        </div>

        {/* Configuration Modal */}
        {isConfigModalOpen && <AgentConfigModal />}
      </div>
    </PageWrapper>
  )
}