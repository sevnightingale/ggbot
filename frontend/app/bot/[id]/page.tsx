'use client'

import { useEffect } from 'react'
import { PageWrapper } from '@/components/ui/PageWrapper'
import { useBotStore } from '@/store/bot'
import { AgentFlowVisualization } from '@/components/bot/AgentFlowVisualization'
import { BotControlPanel } from '@/components/bot/BotControlPanel'
import { TradeTable } from '@/components/trades/TradeTable'
import { PerformanceChart } from '@/components/charts/PerformanceChart'
import { AgentConfigModal } from '@/components/bot/AgentConfigModal'

interface BotDetailPageProps {
  params: Promise<{ id: string }>
}

export default async function BotDetailPage({ params }: BotDetailPageProps) {
  const resolvedParams = await params
  const {
    loadConfigurations,
    loadTrades,
    loadPerformance,
    checkSchedulerStatus,
    isLoading,
    error,
    isConfigModalOpen
  } = useBotStore()

  useEffect(() => {
    // Load all initial data
    const loadInitialData = async () => {
      await Promise.all([
        loadConfigurations(),
        loadTrades(),
        loadPerformance('7d'),
        checkSchedulerStatus()
      ])
    }

    loadInitialData()

    // Set up polling for live updates
    const interval = setInterval(() => {
      loadTrades()
      checkSchedulerStatus()
    }, 30000) // Poll every 30 seconds

    return () => clearInterval(interval)
  }, [loadConfigurations, loadTrades, loadPerformance, checkSchedulerStatus])

  if (isLoading) {
    return (
      <PageWrapper>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-bone-200 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-bone-300">Loading bot configuration...</p>
          </div>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-bone-400 mb-2">
            <span>My Bots</span>
            <span>›</span>
            <span>Bot {resolvedParams.id}</span>
          </div>
          <h1 className="text-3xl font-display font-bold">Bot Dashboard</h1>
          {error && (
            <div className="mt-4 p-4 bg-red-900/20 border border-red-500/20 rounded-lg">
              <p className="text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Agent Visualization and Controls */}
        <div className="grid gap-8 mb-8">
          <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-8">
            <div className="grid lg:grid-cols-2 gap-8 items-center">
              {/* Agent Flow Visualization */}
              <div className="flex justify-center">
                <AgentFlowVisualization />
              </div>
              
              {/* Bot Control Panel */}
              <div>
                <BotControlPanel />
              </div>
            </div>
          </div>
        </div>

        {/* Performance Area */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Active Trades */}
          <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
            <h2 className="text-xl font-display font-bold mb-6">Active Trades</h2>
            <TradeTable />
          </div>

          {/* Performance Chart */}
          <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
            <h2 className="text-xl font-display font-bold mb-6">Performance</h2>
            <PerformanceChart />
          </div>
        </div>

        {/* Configuration Modal */}
        {isConfigModalOpen && <AgentConfigModal />}
      </div>
    </PageWrapper>
  )
}