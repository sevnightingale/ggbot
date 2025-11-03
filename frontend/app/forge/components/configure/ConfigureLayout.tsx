'use client'

import React, { useState } from 'react'
import { BotConfiguration, ConfigData, DataSource } from '@/lib/api'
import { SaveConfigBar } from './SaveConfigBar'
import { ConfigTabs, ConfigTabType } from './ConfigTabs'
import { MarketDataSelector } from './MarketDataSelector'
import { SignalsConfiguration } from './SignalsConfiguration'
import { StrategyEditor } from './StrategyEditor'
import { TradeSettings } from './TradeSettings'
import { EmptyState } from '../shared/EmptyState'

// DataSource will be passed from parent page.tsx
interface ConfigureLayoutProps {
  selectedBot?: BotConfiguration | null
  editingConfigData?: ConfigData | null
  editingTableFields?: { config_name?: string; config_type?: string } | null
  hasUnsavedChanges?: boolean
  dataSources?: DataSource[]
  onSaveConfig?: () => void
  onCancelConfig?: () => void
  onResetConfig?: () => void
  onUpdateConfig?: (updates: Partial<ConfigData>) => void
  className?: string
}

export function ConfigureLayout({
  selectedBot,
  editingConfigData,
  editingTableFields,
  hasUnsavedChanges = false,
  dataSources = [],
  onSaveConfig,
  onCancelConfig,
  onResetConfig,
  onUpdateConfig,
  className = ''
}: ConfigureLayoutProps) {
  const [activeConfigTab, setActiveConfigTab] = useState<ConfigTabType>('strategy')

  // Local state for MarketDataSelector
  const [marketDataActiveTab, setMarketDataActiveTab] = useState('technical_analysis')
  const [marketDataSearchTerm, setMarketDataSearchTerm] = useState('')

  if (!selectedBot) {
    return (
      <div className={className}>
        <EmptyState
          title="Select a Bot"
          description="Choose a bot from the sidebar to configure its settings"
          icon="⚙️"
        />
      </div>
    )
  }

  // Use editing config data if available, otherwise use selected bot's config
  const configData = editingConfigData || selectedBot.config_data

  return (
    <div className={className}>
      {/* Save Config Bar - Always visible */}
      <SaveConfigBar
        selectedBot={selectedBot}
        editingTableFields={editingTableFields}
        hasUnsavedChanges={hasUnsavedChanges}
        isEditingConfig={true}
        onSave={onSaveConfig}
        onCancel={onCancelConfig}
        onReset={onResetConfig}
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
            configData={configData}
            onUpdate={onUpdateConfig}
          />
        )}

        {activeConfigTab === 'strategy' && (
          <StrategyEditor
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