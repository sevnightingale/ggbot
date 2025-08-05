'use client'

import { useEffect, useState } from 'react'
import { PageWrapper } from '@/components/ui/PageWrapper'
import { useBotStore } from '@/store/bot'
import { AgentCard } from '@/components/bot/AgentCard'
import { GGBotCircle } from '@/components/bot/GGBotCircle'
import { TradeTable } from '@/components/trades/TradeTable'
import { PerformanceChart } from '@/components/charts/PerformanceChart'
import { AgentConfigModal } from '@/components/bot/AgentConfigModal'

export function MainDashboard() {
  const {
    loadBots,
    loadTrades,
    loadPerformance,
    checkSchedulerStatus,
    isLoading,
    error,
    isConfigModalOpen,
    agentStatuses,
    schedulerStatus,
    currentBotId
  } = useBotStore()

  // Use a ref to track if initial load has been completed
  const [hasInitialized, setHasInitialized] = useState(false)

  useEffect(() => {
    // Only run once on component mount
    if (hasInitialized) return

    console.log('MainDashboard: Starting initial data load...')
    
    const loadInitialData = async () => {
      console.log('MainDashboard: Loading initial data...')
      const startTime = Date.now()
      
      try {
        // Load bots first, then configurations and other data
        console.log('MainDashboard: Loading bots...')
        await loadBots()
        console.log('MainDashboard: Bots loaded')
        
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
      } finally {
        setHasInitialized(true)
      }
    }

    loadInitialData()
  }, [hasInitialized])

  // Separate effect for periodic refresh
  useEffect(() => {
    if (!hasInitialized) return

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
  }, [hasInitialized])

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
          <div className="p-4 bg-red-900/20 border border-red-500/60">
            <p className="text-red-400 text-center">{error}</p>
          </div>
        )}

        {/* Agent Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <AgentCard
            type="extraction"
            title="Extraction Agent"
            description="Collects market data and technical indicators"
            status={agentStatuses.extraction}
          />
          <AgentCard
            type="decision"
            title="Decision Agent"
            description="Analyzes data and generates trading signals"
            status={agentStatuses.decision}
          />
          <AgentCard
            type="trading"
            title="Trading Agent"
            description="Manages positions and executes trades"
            status={agentStatuses.trading}
          />
        </div>

        {/* GGBot Emblem Section */}
        <div className="flex justify-center mb-16">
          <GGBotCircle status={schedulerStatus} />
        </div>

        {/* Trading Dashboard - Brutalist Design */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="border-2 border-bone-200/80 p-6 paper-texture">
            <h2 className="text-xl font-display font-bold mb-6 text-bone-200">Active Trades</h2>
            <TradeTable />
          </div>

          <div className="border-2 border-bone-200/80 p-6 paper-texture">
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