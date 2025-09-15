'use client'

import React, { useState } from 'react'
import { BotConfiguration, ConfigData } from '@/lib/api'
import { SaveConfigBar } from './SaveConfigBar'
import { ConfigTabs, ConfigTabType } from './ConfigTabs'
import { MarketDataSelector } from './MarketDataSelector'
import { SignalsConfiguration } from './SignalsConfiguration'
import { StrategyEditor } from './StrategyEditor'
import { TradeSettings } from './TradeSettings'
import { EmptyState } from '../shared/EmptyState'

interface ConfigureLayoutProps {
  selectedBot?: BotConfiguration | null
  editingConfigData?: ConfigData | null
  hasUnsavedChanges?: boolean
  onSaveConfig?: () => void
  onCancelConfig?: () => void
  onResetConfig?: () => void
  onUpdateConfig?: (updates: Partial<ConfigData>) => void
  onBotTypeChange?: (newType: 'autonomous_trading' | 'signal_validation') => void
  className?: string
}

export function ConfigureLayout({
  selectedBot,
  editingConfigData,
  hasUnsavedChanges = false,
  onSaveConfig,
  onCancelConfig,
  onResetConfig,
  onUpdateConfig,
  onBotTypeChange,
  className = ''
}: ConfigureLayoutProps) {
  const [activeConfigTab, setActiveConfigTab] = useState<ConfigTabType>('strategy')

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
        hasUnsavedChanges={hasUnsavedChanges}
        isEditingConfig={true}
        onSave={onSaveConfig}
        onCancel={onCancelConfig}
        onReset={onResetConfig}
        onBotTypeChange={onBotTypeChange}
      />

      {selectedBot ? (
        <>
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
                dataSources={[
                  {
                    source_id: 'technical_analysis',
                    name: 'technical_analysis',
                    display_name: 'Technical Analysis',
                    description: 'Technical indicators and chart analysis',
                    enabled: true,
                    requires_premium: false,
                    data_points: [
                      { data_point_id: 'rsi', name: 'RSI', display_name: 'RSI (14)', description: 'Relative Strength Index', requires_premium: false, enabled: true, sort_order: 1 },
                      { data_point_id: 'macd', name: 'MACD', display_name: 'MACD (12,26,9)', description: 'Moving Average Convergence Divergence', requires_premium: false, enabled: true, sort_order: 2 },
                      { data_point_id: 'bb', name: 'BB', display_name: 'Bollinger Bands', description: 'Bollinger Bands (20)', requires_premium: false, enabled: true, sort_order: 3 },
                      { data_point_id: 'adx', name: 'ADX', display_name: 'ADX (14)', description: 'Average Directional Index', requires_premium: false, enabled: true, sort_order: 4 },
                      { data_point_id: 'atr', name: 'ATR', display_name: 'ATR (14)', description: 'Average True Range', requires_premium: false, enabled: true, sort_order: 5 },
                      { data_point_id: 'aroon', name: 'Aroon', display_name: 'Aroon (14)', description: 'Aroon Oscillator', requires_premium: false, enabled: true, sort_order: 6 }
                    ]
                  },
                  {
                    source_id: 'fundamental_analysis',
                    name: 'fundamental_analysis',
                    display_name: 'Fundamental Analysis',
                    description: 'Financial metrics and company fundamentals',
                    enabled: false,
                    requires_premium: true,
                    data_points: []
                  },
                  {
                    source_id: 'sentiment_and_trends',
                    name: 'sentiment_and_trends',
                    display_name: 'Sentiment & Trends',
                    description: 'Social media sentiment and trending topics',
                    enabled: false,
                    requires_premium: true,
                    data_points: []
                  }
                ]}
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
                onUpdate={onUpdateConfig}
              />
            )}

            {activeConfigTab === 'trade-settings' && (
              <TradeSettings
                configData={configData}
                onUpdate={onUpdateConfig}
              />
            )}
          </div>
        </>
      )}
    </div>
  )
}