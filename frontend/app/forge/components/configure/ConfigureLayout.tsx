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
  isEditingConfig?: boolean
  editingConfigData?: ConfigData | null
  hasUnsavedChanges?: boolean
  onStartEditing?: () => void
  onSaveConfig?: () => void
  onCancelConfig?: () => void
  onResetConfig?: () => void
  onUpdateConfig?: (updates: Partial<ConfigData>) => void
  onBotTypeChange?: (newType: 'autonomous_trading' | 'signal_validation') => void
  className?: string
}

export function ConfigureLayout({
  selectedBot,
  isEditingConfig = false,
  editingConfigData,
  hasUnsavedChanges = false,
  onStartEditing,
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
        isEditingConfig={isEditingConfig}
        onSave={onSaveConfig}
        onCancel={onCancelConfig}
        onReset={onResetConfig}
        onBotTypeChange={onBotTypeChange}
      />

      {isEditingConfig ? (
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
      ) : (
        /* Configuration Overview (when not editing) */
        <div className="space-y-6">
          {/* Bot Summary */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              {selectedBot.config_name} Configuration
            </h3>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
                <div className="text-sm text-[var(--text-muted)]">Bot Type</div>
                <div className="font-medium text-[var(--text-primary)] capitalize">
                  {selectedBot.config_type?.replace('_', ' ') || 'Autonomous Trading'}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
                <div className="text-sm text-[var(--text-muted)]">Analysis Frequency</div>
                <div className="font-medium text-[var(--text-primary)]">
                  Every {configData?.decision?.analysis_frequency || '1h'}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
                <div className="text-sm text-[var(--text-muted)]">Trading Pair</div>
                <div className="font-medium text-[var(--text-primary)]">
                  {configData?.selected_pair || 'BTC/USDT'}
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div className="text-sm text-[var(--text-muted)] mb-2">Current Strategy</div>
              <div className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {configData?.decision?.user_prompt || 'No strategy configured'}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Quick Actions
            </h3>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={onStartEditing}
                className="inline-flex items-center gap-2 rounded-xl bg-[var(--agent-extraction)] px-4 py-2 text-sm font-medium text-white shadow-sm hover:opacity-90"
              >
                ⚙️ Configure Settings
              </button>

              <button
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
                disabled
              >
                📊 View Performance
              </button>

              <button
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
                disabled
              >
                📋 Export Config
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}