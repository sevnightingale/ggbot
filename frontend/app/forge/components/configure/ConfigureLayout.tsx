'use client'

import React, { useState, useRef, useEffect } from 'react'
import { BotConfiguration, ConfigData, DataSource } from '@/lib/api'
import { SaveStatusIndicator } from '@/components/SaveStatusIndicator'
import { StrategyAdvisorPanel } from '@/components/StrategyAdvisorPanel'
import { useSaveStatus } from '@/lib/contexts/SaveStatusContext'
import { ConfigTabs, ConfigTabType } from './ConfigTabs'
import { MarketDataSelector } from './MarketDataSelector'
// SignalsConfiguration hidden - ggShot integration disabled (2026-01-23)
// import { SignalsConfiguration } from './SignalsConfiguration'
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
  allBots?: BotConfiguration[]
}

/**
 * AgentStrategySection - Simplified strategy editor for agent bots
 *
 * Agent bots only need a strategy textarea - they don't need:
 * - Analysis frequency (they decide when to trade)
 * - LLM selection (they use the autonomous agent's model)
 * - Market data config (they query dynamically)
 */
function AgentStrategySection({
  configData,
  onUpdate
}: {
  configData?: ConfigData | null
  onUpdate?: (updates: Partial<ConfigData>) => void
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [strategy, setStrategy] = useState(configData?.decision?.user_prompt || '')

  // Sync from configData when it changes (e.g., AI updates)
  useEffect(() => {
    if (configData?.decision?.user_prompt !== undefined) {
      setStrategy(configData.decision.user_prompt)
    }
  }, [configData?.decision?.user_prompt])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [strategy])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value.length > 10000 ? e.target.value.substring(0, 10000) : e.target.value
    setStrategy(value)

    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = `${e.target.scrollHeight}px`

    // Notify parent for batched save
    onUpdate?.({
      decision: {
        ...(configData?.decision || {}),
        user_prompt: value,
        analysis_frequency: 'agent_driven',
        system_prompt: configData?.decision?.system_prompt || ''
      }
    })
  }

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
        Agent Trading Strategy
      </h3>
      <p className="text-sm text-[var(--text-muted)] mb-4">
        Define your agent&apos;s trading rules and risk parameters. The agent will autonomously analyze markets and execute trades based on this strategy.
      </p>

      <textarea
        ref={textareaRef}
        value={strategy}
        onChange={handleChange}
        rows={12}
        maxLength={10000}
        className="w-full p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] resize-none overflow-hidden font-mono text-sm"
        placeholder={`Example agent strategy:

## Trading Rules
- Trade BTC/USDT and ETH/USDT only
- Enter long when RSI < 30 and price above 20-day MA
- Enter short when RSI > 70 and price below 20-day MA
- Maximum 2 positions open at once

## Risk Management
- Position size: 5% of account per trade
- Stop loss: 3% below entry for longs, 3% above for shorts
- Take profit: 6% (2:1 risk/reward)
- Maximum daily loss: 10% of account

## Market Conditions
- Avoid trading during high-impact news events
- Reduce position size in high volatility (VIX > 25)`}
        style={{ minHeight: '300px' }}
      />

      <div className="mt-2 flex justify-between items-center">
        <div className="text-xs text-[var(--text-muted)]">
          Be specific about entry/exit conditions, position sizing, and risk limits.
        </div>
        <div className="text-xs text-[var(--text-muted)]">
          {strategy.length}/10,000
        </div>
      </div>
    </div>
  )
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
  className = '',
  allBots
}: ConfigureLayoutProps) {
  const [activeConfigTab, setActiveConfigTab] = useState<ConfigTabType>('strategy')
  const { globalStatus, globalError, globalMessage } = useSaveStatus()

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

  // Check if this is an agent bot - agents get simplified UI
  const isAgentMode = botType === 'agent'

  return (
    <div className={`${className} relative`}>
      {/* Save Status Indicator - Floating in corner */}
      <div className="fixed top-4 right-4 z-50">
        <SaveStatusIndicator
          status={globalStatus}
          error={globalError}
          message={globalMessage}
        />
      </div>

      {/* Strategy Advisor Panel - Always visible for all bot types */}
      <StrategyAdvisorPanel
        configId={selectedBot.config_id}
        botType={mappedBotType}
        onConfigUpdate={onConfigUpdate || (() => {})}
        className="mb-6"
      />

      {isAgentMode ? (
        // Agent Mode: Only show strategy section - no tabs, no other config
        <AgentStrategySection
          configData={configData}
          onUpdate={onUpdateConfig}
        />
      ) : (
        // Normal Mode: Show full configuration tabs
        <>
          {/* Configuration Tabs */}
          <div data-tour="config-tabs">
            <ConfigTabs
              activeTab={activeConfigTab}
              onTabChange={setActiveConfigTab}
              className="mb-6"
            />
          </div>

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

            {/* Signals tab hidden - ggShot integration disabled (2026-01-23) */}

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
                allBots={allBots}
                currentConfigId={selectedBot?.config_id}
              />
            )}
          </div>
        </>
      )}
    </div>
  )
}
