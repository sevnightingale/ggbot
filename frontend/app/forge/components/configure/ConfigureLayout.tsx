'use client'

import React, { useState } from 'react'
import { BotConfiguration, ConfigData, DataSource } from '@/lib/api'
import { SaveStatusIndicator } from '@/components/SaveStatusIndicator'
import { StrategyAdvisorPanel } from '@/components/StrategyAdvisorPanel'
import { SaveStatusProvider, useSaveStatus } from '@/lib/contexts/SaveStatusContext'
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

function ConfigureLayoutContent({
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

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeConfigTab === 'market-data' && (
          <MarketDataSelector
            configId={selectedBot.config_id}
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
            configData={configData}
            onUpdate={onUpdateConfig}
          />
        )}

        {activeConfigTab === 'strategy' && (
          <StrategyEditor
            configId={selectedBot.config_id}
            configData={configData}
            configType={editingTableFields?.config_type || selectedBot?.config_type}
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

// Wrapper component that provides SaveStatusContext
export function ConfigureLayout(props: ConfigureLayoutProps) {
  return (
    <SaveStatusProvider>
      <ConfigureLayoutContent {...props} />
    </SaveStatusProvider>
  )
}