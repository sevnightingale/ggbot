'use client'

import React, { useState } from 'react'
import { BotConfiguration, ConfigData, DataSource } from '@/lib/api'
import { SaveStatusIndicator } from '@/components/SaveStatusIndicator'
import { StrategyAdvisorPanel } from '@/components/StrategyAdvisorPanel'
import { useSaveStatus } from '@/lib/contexts/SaveStatusContext'
import { ConfigTabs, ConfigTabType } from './ConfigTabs'
import { MarketDataSelector } from './MarketDataSelector'
import { SignalsConfiguration } from './SignalsConfiguration'
import { StrategyEditor } from './StrategyEditor'
import { TradeSettings } from './TradeSettings'
import { EmptyState } from '../shared/EmptyState'
import { Settings } from 'lucide-react'

// DataSource will be passed from parent page.tsx
interface ConfigureLayoutProps {
  selectedBot?: BotConfiguration | null
  editingConfigData?: ConfigData | null
  editingTableFields?: { config_name?: string; config_type?: string } | null
  dataSources?: DataSource[]
  onUpdateConfig?: (updates: Partial<ConfigData>) => void
  onConfigUpdate?: () => void
  className?: string
}

/**
 * ConfigureLayout - Layout wrapper for bot configuration tabs
 *
 * This component is a pure pass-through for config changes.
 * All save logic is handled by page.tsx via useBatchedConfigSave.
 *
 * Data flow:
 * 1. Child component calls onUpdateConfig(updates)
 * 2. page.tsx handleConfigChange updates local state + queues batched save
 * 3. After 5s idle, batched save fires to API
 * 4. SSE may push updates for non-dirty fields
 */
export function ConfigureLayout({
  selectedBot,
  editingConfigData,
  editingTableFields,
  dataSources = [],
  onUpdateConfig,
  onConfigUpdate,
  className = ''
}: ConfigureLayoutProps) {
  const [activeConfigTab, setActiveConfigTab] = useState<ConfigTabType>('strategy')
  const { globalStatus, globalError } = useSaveStatus()

  // Local state for MarketDataSelector
  const [marketDataActiveTab, setMarketDataActiveTab] = useState('technical_analysis')
  const [marketDataSearchTerm, setMarketDataSearchTerm] = useState('')

  if (!selectedBot) {
    return (
      <div className={className}>
        <EmptyState
          Icon={Settings}
          title="Select a Bot"
          description="Choose a bot from the sidebar to configure its settings"
        />
      </div>
    )
  }

  // Use editing config data if available, otherwise use selected bot's config
  const configData = editingConfigData || selectedBot.config_data

  // Determine bot type for Strategy Advisor
  const botType = editingTableFields?.config_type || selectedBot.config_type
  const mappedBotType: 'agent' | 'scheduled' | 'signal_validation' =
    botType === 'scheduled_trading' ? 'scheduled' :
    botType === 'agent' ? 'agent' :
    'signal_validation'

  return (
    <div className={`${className} relative`}>
      {/* Save Status Indicator - Floating in corner */}
      <div className="fixed top-4 right-4 z-50">
        <SaveStatusIndicator
          status={globalStatus}
          error={globalError}
        />
      </div>

      {/* Strategy Advisor Panel - Always visible */}
      <StrategyAdvisorPanel
        configId={selectedBot.config_id}
        botType={mappedBotType}
        onConfigUpdate={onConfigUpdate || (() => {})}
        className="mb-6"
      />

      {/* Configuration Tabs */}
      <ConfigTabs
        activeTab={activeConfigTab}
        onTabChange={setActiveConfigTab}
        className="mb-6"
      />

      {/* Tab Content - All components receive onUpdateConfig directly */}
      <div className="min-h-[400px]">
        {activeConfigTab === 'market-data' && (
          <MarketDataSelector
            configId={selectedBot.config_id}
            configName={editingTableFields?.config_name || selectedBot?.config_name}
            configType={editingTableFields?.config_type || selectedBot?.config_type}
            configData={configData}
            onUpdate={onUpdateConfig}
            dataSources={dataSources}
            activeTab={marketDataActiveTab}
            searchTerm={marketDataSearchTerm}
            onTabChange={setMarketDataActiveTab}
            onSearchChange={setMarketDataSearchTerm}
          />
        )}

        {activeConfigTab === 'signals' && (
          <SignalsConfiguration
            configId={selectedBot.config_id}
            configName={editingTableFields?.config_name || selectedBot?.config_name}
            configType={editingTableFields?.config_type || selectedBot?.config_type}
            configData={configData}
            onUpdate={onUpdateConfig}
          />
        )}

        {activeConfigTab === 'strategy' && (
          <StrategyEditor
            configData={configData}
            onUpdate={onUpdateConfig}
          />
        )}

        {activeConfigTab === 'trade-settings' && (
          <TradeSettings
            configData={configData}
            configId={selectedBot?.config_id}
            tradingMode={selectedBot?.trading_mode}
            onUpdate={onUpdateConfig}
          />
        )}
      </div>
    </div>
  )
}
