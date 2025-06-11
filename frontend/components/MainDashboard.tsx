'use client'

import { useEffect } from 'react'
import { PageWrapper } from '@/components/ui/PageWrapper'
import { useBotStore } from '@/store/bot'
import { AgentCard } from '@/components/bot/AgentCard'
import { BotStatusCard } from '@/components/bot/BotStatusCard'
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
    const loadInitialData = async () => {
      try {
        await Promise.all([
          loadConfigurations(),
          loadTrades(),
          loadPerformance('7d'),
          checkSchedulerStatus()
        ])
      } catch (error) {
        console.error('Failed to load initial data:', error)
      }
    }

    loadInitialData()

    const interval = setInterval(() => {
      loadTrades()
      checkSchedulerStatus()
    }, 30000)

    return () => clearInterval(interval)
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
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-display font-bold mb-2">Your Trading Bot</h1>
          <p className="text-bone-400">Monitor performance, configure agents, and manage trades</p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-900/20 border border-red-500/20 rounded-lg">
            <p className="text-red-400 text-center">{error}</p>
          </div>
        )}

        {/* Agent Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

        {/* Bot Status */}
        <BotStatusCard status={schedulerStatus} />

        {/* Trading Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
            <h2 className="text-xl font-display font-bold mb-6">Active Trades</h2>
            <TradeTable />
          </div>

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