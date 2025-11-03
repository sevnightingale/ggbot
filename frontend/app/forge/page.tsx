'use client'

import React, { useState, useEffect, useRef } from 'react'
import { createClient } from '@/lib/supabase'
import { apiClient, BotConfiguration, ConfigData, DataSource } from '@/lib/api'
import { ThemeProvider } from '@/lib/theme'
import { PermissionProvider, usePermissions } from '@/lib/permissions'
import { Header } from './components/layout/Header'
import { BotRail } from './components/layout/BotRail'
import { TabNavigation } from './components/layout/TabNavigation'
import { MobileNav } from './components/layout/MobileNav'
import { EmptyState } from './components/shared/EmptyState'
import { ActivationBar } from './components/monitor/ActivationBar'
// import { MetricsBar } from './components/monitor/MetricsBar' // Replaced with PerformanceChart
import { PerformanceChart } from './components/monitor/PerformanceChart'
import { DecisionFeed } from './components/monitor/DecisionFeed'
import { PositionsTable } from './components/monitor/PositionsTable'
import { TradeHistoryModal } from './components/monitor/TradeHistoryModal'
import { ConfigureLayout } from './components/configure/ConfigureLayout'
import { AgentConfigurator } from './components/configure/AgentConfigurator'
import { DuplicateAsLiveModal } from '@/components/DuplicateAsLiveModal'
import { BotCreationModal } from './components/modals/BotCreationModal'

interface Position {
  trade_id: string
  symbol: string
  side: string
  entry_price: number
  current_price: number
  size_usd: number
  unrealized_pnl: number
  status: string
  opened_at: string
  leverage: number
}

interface Decision {
  decision_id: string
  symbol: string
  action: string
  confidence: number
  reasoning: string
  created_at: string
}


function ForgeApp() {
  const [user, setUser] = useState<{ id: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sseConnected, setSseConnected] = useState(false)

  // Permission loading - always call hook, but only use when user exists
  const { loading: permissionsLoading } = usePermissions()

  // Core bot data - all local state with multi-bot support
  const [allBots, setAllBots] = useState<BotConfiguration[]>([])
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [accounts, setAccounts] = useState<Array<{
    config_id: string
    account_id: string
    current_balance: number
    total_pnl: number
    total_trades: number
    win_trades: number
    loss_trades: number
    open_positions: number
    updated_at: string
    // Enhanced portfolio analytics from SSE
    unrealized_pnl?: number
    current_pnl?: number  // Aggregate unrealized P&L of open positions
    portfolio_return_pct?: number
    total_balance?: number
    win_rate?: number
    avg_win?: number
    avg_loss?: number
    largest_win?: number
    largest_loss?: number
    sharpe_ratio?: number
  }>>([])
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [isManualTriggering, setIsManualTriggering] = useState(false)
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [isBotAction, setIsBotAction] = useState(false)
  const [isTradeHistoryModalOpen, setIsTradeHistoryModalOpen] = useState(false)
  const [duplicateAsLiveModalOpen, setDuplicateAsLiveModalOpen] = useState(false)
  const [botCreationModalOpen, setBotCreationModalOpen] = useState(false)
  const [sourceBotForLive, setSourceBotForLive] = useState<BotConfiguration | null>(null)

  // Use ref to track selectedConfigId for SSE filtering without causing reconnections
  const selectedConfigIdRef = useRef(selectedConfigId)
  selectedConfigIdRef.current = selectedConfigId

  // Get currently selected bot
  const selectedBot = selectedConfigId
    ? allBots.find(bot => bot.config_id === selectedConfigId) || null
    : null

  // Get account data for selected bot
  const selectedAccount = selectedBot
    ? accounts.find(account => account.config_id === selectedBot.config_id) || null
    : null


  
  // Real-time status tracking
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'extraction' | 'decision' | 'trading'>('idle')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [nextRun, setNextRun] = useState<string | null>(null)
  const [countdown, setCountdown] = useState<string>('')

  // Tab navigation state
  const [activeTab, setActiveTab] = useState<'monitor' | 'configure'>('monitor')

  // Configuration editing state - sandboxed from operational display
  const [isEditingConfig, setIsEditingConfig] = useState(false)
  const [editingConfigData, setEditingConfigData] = useState<ConfigData | null>(null)
  const [editingTableFields, setEditingTableFields] = useState<{
    config_name?: string
    config_type?: string
  } | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [originalConfig, setOriginalConfig] = useState<BotConfiguration | null>(null)

  // Agent conversation state (for agentic config type)
  const [agentMessages, setAgentMessages] = useState<Array<{
    role: 'user' | 'agent'
    content: string
    timestamp: string
  }>>([])
  const [agentInputValue, setAgentInputValue] = useState('')
  const [isWaitingForAgent, setIsWaitingForAgent] = useState(false)
  const [showConfirmButton, setShowConfirmButton] = useState(false)

  // Start editing mode when configure tab is activated
  useEffect(() => {
    if (activeTab === 'configure' && selectedBot && !isEditingConfig) {
      console.log('🔧 Starting edit mode for bot:', selectedBot.config_id)
      console.log('🔧 Bot data being loaded into editing state:', JSON.stringify(selectedBot, null, 2))

      // Enter editing mode - load selected bot config into editing state
      setIsEditingConfig(true)
      setEditingConfigData(selectedBot.config_data ? JSON.parse(JSON.stringify(selectedBot.config_data)) : null)
      setEditingTableFields({
        config_name: selectedBot.config_name,
        config_type: selectedBot.config_type
      })
      setOriginalConfig(selectedBot)
      setHasUnsavedChanges(false)
    }
  }, [activeTab, selectedBot, isEditingConfig])

  // Clear component data immediately when switching bots for instant UI update
  useEffect(() => {
    if (selectedConfigId && selectedBot) {
      // Clear operational data that should be bot-specific
      setPositions([])
      setDecisions([])
      setExecutionStatus('idle')
      setStatusMessage('')
      setCountdown('')
      setNextRun(null)

      console.log('🔄 Switched to bot:', selectedBot.config_id, selectedBot.config_name)
    }
  }, [selectedConfigId, selectedBot]) // Clear data when switching bots

  // Real auth check
  useEffect(() => {
    const getUser = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      
      setUser(user ? { id: user.id } : null)
      setLoading(false)
    }

    getUser()
  }, [])

  // Get auth token for API calls
  const getAuthToken = async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token
  }

  // Create default bot with RSI strategy using proper API client
  const createDefaultBot = async (botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading'): Promise<BotConfiguration> => {
    // Base config for all types
    const baseConfig = {
      schema_version: '2.1',
      config_type: botType,
      trading: {
        execution_mode: 'paper',
        leverage: 1,
        position_sizing: {
          method: 'fixed_usd',
          fixed_amount_usd: 100,
          account_percent: 5.0,
          max_position_percent: 10.0
        },
        risk_management: {
          max_positions: 1,
          default_stop_loss_percent: 5.0,
          default_take_profit_percent: 10.0,
          max_daily_loss_usd: 500
        }
      }
    }

    // Type-specific config
    if (botType === 'agent') {
      // Agent bots don't need selected_pair, extraction, or decision at creation
      // Agent will define everything through conversation
      const agentConfig = {
        ...baseConfig,
        decision: {
          analysis_frequency: 'agent_driven'
        },
        llm_config: {
          provider: 'default',
          model: 'default',
          use_platform_keys: true,
          use_own_key: false
        }
      }
      const newConfig = await apiClient.createConfig('Agent Bot', agentConfig)
      return newConfig
    }

    // Standard scheduled_trading and signal_validation configs
    const defaultConfigData = {
      ...baseConfig,
      selected_pair: 'BTC/USDT',
      extraction: {
        selected_data_sources: {
          technical_analysis: {
            data_points: ['RSI'],
            timeframes: ['1h']
          }
        }
      },
      decision: {
        analysis_frequency: botType === 'signal_validation' ? 'signal_driven' : '1h',
        system_prompt: 'You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.',
        user_prompt: botType === 'signal_validation'
          ? 'Validate the provided signal and decide whether to approve or reject it'
          : 'if RSI 1hr below 50 enter long, if above enter short'
      },
      llm_config: {
        provider: 'default',
        model: 'default',
        use_platform_keys: true,
        use_own_key: false
      },
      trading: {
        execution_mode: 'paper',
        leverage: 1,
        position_sizing: {
          method: 'fixed_usd',
          fixed_amount_usd: 100,
          account_percent: 5.0,
          max_position_percent: 10.0
        },
        risk_management: {
          max_positions: 1,
          default_stop_loss_percent: 5.0,
          default_take_profit_percent: 10.0,
          max_daily_loss_usd: 500
        }
      },
      telegram_integration: {
        listener: {
          enabled: false,
          api_id: '',
          api_hash: '',
          session_name: 'ggbot_session',
          source_channels: []
        },
        publisher: {
          enabled: false,
          bot_token: '',
          filter_channel: '',
          confidence_threshold: 0.7,
          include_reasoning: true,
          include_market_context: true,
          message_template: '🔥 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}'
        }
      }
    }

    const newConfig = await apiClient.createConfig('Default ggbot', defaultConfigData)
    console.log('🔨 Created default bot:', newConfig)
    console.log('🔨 Bot config_id:', newConfig.config_id)
    console.log('🔨 Bot structure:', JSON.stringify(newConfig, null, 2))

    // No transformation needed - return directly
    return newConfig
  }

  // Load or create bot when user is ready
  useEffect(() => {
    if (!user) return

    const loadOrCreateBot = async () => {
      setLoadError(null)

      try {
        // Get user's existing bots using proper API client
        const configs = await apiClient.listConfigs()

        if (configs.length > 0) {
          // Load all configs and select first one
          setAllBots(configs)
          setSelectedConfigId(configs[0].config_id)
          setLoadError(null)
        } else {
          // Create default bot
          console.log('🔨 No bots found, creating default bot')
          const newBot = await createDefaultBot()

          // Verify the bot was actually created by fetching it back
          try {
            const verifyBot = await apiClient.getConfig(newBot.config_id)
            console.log('✅ Bot creation verified:', verifyBot.config_id)
            setAllBots([newBot])
            setSelectedConfigId(newBot.config_id)
            setLoadError(null)
          } catch (verifyError) {
            console.error('❌ Bot creation verification failed:', verifyError)
            // Try to refresh the list in case there's a timing issue
            const refreshedConfigs = await apiClient.listConfigs()
            if (refreshedConfigs.length > 0) {
              setAllBots(refreshedConfigs)
              setSelectedConfigId(refreshedConfigs[0].config_id)
              setLoadError(null)
            } else {
              console.error('❌ No bots found after creation attempt')
              setLoadError('Failed to create default bot. Please refresh the page.')
            }
          }
        }

        // Fetch available data sources for configuration
        try {
          const dataSourcesResponse = await apiClient.getDataSourcesWithPoints()
          setDataSources(dataSourcesResponse)
        } catch (dataSourceError) {
          console.error('Failed to fetch data sources:', dataSourceError)
          // Continue without data sources - MarketDataSelector will show empty state
        }

      } catch (error) {
        console.error('❌ Failed to load/create bot:', error)
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        setLoadError(`Failed to load bots: ${errorMessage}`)
      }
    }

    loadOrCreateBot()
  }, [user])

  // Real-time SSE connection for status updates with auto-reconnect
  useEffect(() => {
    if (!user) return

    let stream: EventSource | null = null
    let reconnectAttempt = 0
    let reconnectTimeout: NodeJS.Timeout | null = null
    let isCleanedUp = false

    const connectSSE = async () => {
      if (isCleanedUp) return

      try {
        const token = await getAuthToken()
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        stream = new EventSource(`${apiUrl}/api/dashboard-stream?token=${encodeURIComponent(token)}`)

        stream.onopen = () => {
          console.log('✅ SSE connected')
          reconnectAttempt = 0 // Reset on successful connection
          setSseConnected(true)
        }

        stream.addEventListener('dashboard', (event) => {
          try {
            const data = JSON.parse(event.data)

            // Only process data if we have a selected bot
            const currentSelectedId = selectedConfigIdRef.current
            if (!currentSelectedId) return

            // Update bot execution status (extraction/decision/trading phases)
            if (data.bots) {
              const myBot = data.bots.find((b: { config_id: string }) => b.config_id === currentSelectedId)
              if (myBot?.execution_status) {
                const phase = myBot.execution_status.phase
                if (phase === 'extracting') setExecutionStatus('extraction')
                else if (phase === 'deciding') setExecutionStatus('decision')
                else if (phase === 'trading') setExecutionStatus('trading')
                else setExecutionStatus('idle')

                setStatusMessage(myBot.execution_status.message || '')
              }

              // Update next run time
              if (myBot?.next_run) {
                setNextRun(myBot.next_run)
              } else if (myBot?.is_scheduled) {
                // Bot is scheduled but next_run is null - show waiting state
                setNextRun(null)
                setCountdown('Waiting for next run...')
              }
            }

            // Update live positions with P&L
            if (data.positions) {
              const myPositions = data.positions.filter((p: { config_id: string }) => p.config_id === currentSelectedId)
              setPositions(myPositions)
            }

            // Update recent decisions
            if (data.decisions) {
              const myDecisions = data.decisions.filter((d: { config_id: string }) => d.config_id === currentSelectedId)
              setDecisions(myDecisions.slice(0, 10)) // Keep last 10
            }

            // Update accounts data
            if (data.accounts) {
              setAccounts(data.accounts)
            }

          } catch (error) {
            console.error('❌ Failed to parse SSE data:', error)
          }
        })

        stream.onerror = (error) => {
          console.error('❌ SSE connection error:', error)
          stream?.close()
          setSseConnected(false)

          if (isCleanedUp) return

          // Exponential backoff: 5s, 10s, 30s, 60s (max)
          const delays = [5000, 10000, 30000, 60000]
          const delay = delays[Math.min(reconnectAttempt, delays.length - 1)]

          reconnectAttempt++
          console.log(`🔄 SSE reconnecting in ${delay / 1000}s (attempt ${reconnectAttempt})...`)

          reconnectTimeout = setTimeout(() => {
            connectSSE()
          }, delay)
        }

      } catch (error) {
        console.error('❌ Failed to connect SSE:', error)

        if (isCleanedUp) return

        // Retry after 5 seconds on connection failure
        reconnectTimeout = setTimeout(() => {
          connectSSE()
        }, 5000)
      }
    }

    connectSSE()

    // Cleanup function
    return () => {
      console.log('🛑 Cleaning up SSE connection')
      isCleanedUp = true
      stream?.close()
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
    }
  }, [user]) // Only reconnect when user changes, not when switching bots

  // Countdown timer for next run
  useEffect(() => {
    if (!nextRun) {
      // If no next_run but countdown was manually set (e.g., "Waiting for next run..."), keep it
      return
    }

    const updateCountdown = () => {
      const now = new Date()
      const next = new Date(nextRun)
      const diff = next.getTime() - now.getTime()

      if (diff <= 0) {
        setCountdown('Running soon...')
        return
      }

      const minutes = Math.floor(diff / 60000)
      const seconds = Math.floor((diff % 60000) / 1000)

      // Get timeframe from bot config for better context
      const timeframe = selectedBot?.config_data?.decision?.analysis_frequency
      const timeframeLabel = timeframe === 'signal_driven' ? '' :
        timeframe ? ` ${timeframe} candle close` : ''

      if (timeframeLabel) {
        setCountdown(`Waiting for${timeframeLabel} in ${minutes}m ${seconds}s`)
      } else {
        setCountdown(`Next run in ${minutes}m ${seconds}s`)
      }
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [nextRun, selectedBot])

  // Page visibility retry - retry failed loads when user returns to page
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible') {
        console.log('👁️ Page became visible')

        // Retry loading if there was an error and no bots loaded
        if (loadError || (user && allBots.length === 0)) {
          console.log('🔄 Retrying failed load...')
          setLoadError(null)

          try {
            const configs = await apiClient.listConfigs()
            if (configs.length > 0) {
              setAllBots(configs)
              if (!selectedConfigId) {
                setSelectedConfigId(configs[0].config_id)
              }
              setLoadError(null)
            }
          } catch (error) {
            console.error('❌ Retry failed:', error)
            const errorMessage = error instanceof Error ? error.message : 'Unknown error'
            setLoadError(`Failed to load bots: ${errorMessage}`)
          }
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [loadError, user, allBots.length, selectedConfigId])

  // Handle selectedConfigId changes while in editing mode (programmatic bot switches)
  useEffect(() => {
    if (isEditingConfig && selectedBot && editingConfigData) {
      // If the selected bot changed while editing, we need to update the editing state
      const isEditingDifferentBot = originalConfig?.config_id !== selectedBot.config_id

      if (isEditingDifferentBot) {
        console.log('🔄 Bot changed while editing - switching editing state to new bot')

        // Load the new bot's config into editing state
        setEditingConfigData(JSON.parse(JSON.stringify(selectedBot.config_data)))
        setEditingTableFields({
          config_name: selectedBot.config_name,
          config_type: selectedBot.config_type
        })
        setOriginalConfig(selectedBot)
        setHasUnsavedChanges(false)
      }
    }
  }, [selectedConfigId, selectedBot, isEditingConfig, editingConfigData, originalConfig])

  // Start bot function using proper API client
  const startBot = async () => {
    if (!selectedBot) return
    setIsStarting(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'

      // Route to different endpoints based on config type
      const isAgent = selectedBot.config_type === 'agent'
      const endpoint = isAgent
        ? `${apiUrl}/api/v2/agent/${selectedBot.config_id}/start?mode=autonomous`
        : `${apiUrl}/api/v2/bot/${selectedBot.config_id}/start`

      const response = await apiClient.authenticatedFetch(endpoint, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Failed to start ${isAgent ? 'agent' : 'bot'}: ${response.status}`)
      }

      const result = await response.json()

      // Update local bot state and next run from API response
      setAllBots(prev => prev.map(bot =>
        bot.config_id === selectedBot.config_id
          ? { ...bot, state: 'active' as const }
          : bot
      ))
      if (result.next_run) {
        setNextRun(result.next_run)
      }

    } catch (error) {
      console.error('❌ Failed to start bot:', error)
    } finally {
      setIsStarting(false)
    }
  }

  // Stop bot function using proper API client
  const stopBot = async () => {
    if (!selectedBot) return
    setIsStopping(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'

      // Route to different endpoints based on config type
      const isAgent = selectedBot.config_type === 'agent'
      const endpoint = isAgent
        ? `${apiUrl}/api/v2/agent/${selectedBot.config_id}/stop`
        : `${apiUrl}/api/v2/bot/${selectedBot.config_id}/stop`

      const response = await apiClient.authenticatedFetch(endpoint, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Failed to stop ${isAgent ? 'agent' : 'bot'}: ${response.status}`)
      }

      await response.json()

      // Update local bot state and clear scheduling info
      setAllBots(prev => prev.map(bot =>
        bot.config_id === selectedBot.config_id
          ? { ...bot, state: 'inactive' as const }
          : bot
      ))
      setExecutionStatus('idle')
      setStatusMessage('')
      setNextRun(null)
      setCountdown('')

    } catch (error) {
      console.error('❌ Failed to stop bot:', error)
    } finally {
      setIsStopping(false)
    }
  }

  // Manual trigger function using proper API client
  const triggerBotManually = async () => {
    if (!selectedBot) return
    setIsManualTriggering(true)

    try {
      console.log('🔥 Manual trigger started for bot:', selectedBot.config_id)
      const result = await apiClient.triggerBotManually(selectedBot.config_id)
      console.log('✅ Manual trigger result:', result)

      // Set execution status to show it's running
      setExecutionStatus('extraction')
      setStatusMessage('Manual execution started...')

    } catch (error) {
      console.error('❌ Failed to trigger bot manually:', error)
    } finally {
      setIsManualTriggering(false)
    }
  }

  // Handler functions for ActivationBar
  const handleStart = () => {
    startBot()
  }

  const handleStop = () => {
    stopBot()
  }

  const handleManualTrigger = () => {
    triggerBotManually()
  }

  // Configuration editing handlers - removed startEditingConfig as we now always start in editing mode

  // Unified config update function with deep merging
  const updateEditingConfig = (updates: {
    configData?: Partial<ConfigData>
    tableFields?: { config_name?: string; config_type?: string }
  }) => {
    if (!isEditingConfig) return

    // Update JSONB config_data if provided
    if (updates.configData) {
      setEditingConfigData(prev => {
        if (!prev) return null

        // Deep merge the updates into existing config
        const configUpdates = updates.configData!
        return {
          ...prev,
          ...configUpdates,
          // Handle nested objects specifically with guards for optional fields
          ...(configUpdates.extraction && {
            extraction: {
              ...(prev.extraction || {}),  // Guard: fallback to empty object
              ...configUpdates.extraction
            }
          }),
          ...(configUpdates.decision && {
            decision: {
              ...(prev.decision || {}),  // Guard: fallback to empty object
              ...configUpdates.decision
            }
          }),
          ...(configUpdates.trading && {
            trading: {
              ...prev.trading,
              ...configUpdates.trading
            }
          }),
          ...(configUpdates.llm_config && {
            llm_config: {
              ...(prev.llm_config || {}),  // Guard: fallback to empty object
              ...configUpdates.llm_config
            }
          }),
          ...(configUpdates.telegram_integration && {
            telegram_integration: {
              ...prev.telegram_integration,
              ...configUpdates.telegram_integration
            }
          }),
          ...(configUpdates.agent_strategy && {
            agent_strategy: {
              ...(prev.agent_strategy || {}),  // Guard: handle agent configs
              ...configUpdates.agent_strategy
            }
          })
        } as ConfigData
      })
    }

    // Update table fields if provided
    if (updates.tableFields) {
      setEditingTableFields(prev => ({
        ...prev,
        ...updates.tableFields
      }))
    }

    // Mark as having changes
    setHasUnsavedChanges(true)
  }

  // Handle bot switching with clean state reset
  const handleBotSelection = (configId: string) => {
    // If currently editing and has unsaved changes, show warning
    if (isEditingConfig && hasUnsavedChanges) {
      console.warn('⚠️ Switching bots - discarding unsaved changes')
    }

    // Always reset to monitor tab when switching bots
    setActiveTab('monitor')

    // Clear any editing state
    setIsEditingConfig(false)
    setEditingConfigData(null)
    setEditingTableFields(null)
    setHasUnsavedChanges(false)
    setOriginalConfig(null)

    // Switch to the new bot
    setSelectedConfigId(configId)
  }

  // Save configuration changes
  const saveConfigurationChanges = async () => {
    if (!selectedBot || !editingConfigData || !editingTableFields || !hasUnsavedChanges) return

    console.log('💾 Attempting to save config for bot:', selectedBot.config_id)
    console.log('💾 Selected bot structure:', JSON.stringify(selectedBot, null, 2))
    console.log('💾 Editing config data:', JSON.stringify(editingConfigData, null, 2))
    console.log('💾 Table fields:', editingTableFields)

    try {
      // Call API with both JSONB config_data and table fields
      const updatedBot = await apiClient.updateConfig(
        selectedBot.config_id,
        editingConfigData,                     // JSONB config_data
        editingTableFields.config_name,        // Table field
        editingTableFields.config_type         // Table field
      )

      // Update the selected bot in allBots array
      setAllBots(prev => prev.map(bot =>
        bot.config_id === selectedBot.config_id ? updatedBot : bot
      ))

      // Clear editing state
      setIsEditingConfig(false)
      setEditingConfigData(null)
      setEditingTableFields(null)
      setHasUnsavedChanges(false)
      setOriginalConfig(null)

      // Show save confirmation
      alert('✅ Configuration saved successfully!')

    } catch (error) {
      console.error('❌ Failed to save configuration:', error)

      // If 404 error, the bot was likely deleted - refresh bot list
      if (error instanceof Error && error.message.includes('404')) {
        console.warn('⚠️ Bot not found (404) - refreshing bot list from server')
        await refreshBotList()
      }

      // Show error alert
      alert('❌ Failed to save configuration. Please try again.')
    }
  }

  // Cancel configuration editing
  const cancelConfigurationEditing = () => {
    // Discard all editing state
    setIsEditingConfig(false)
    setEditingConfigData(null)
    setEditingTableFields(null)
    setHasUnsavedChanges(false)
    setOriginalConfig(null)
  }

  // Reset configuration to original values
  const resetConfigurationChanges = () => {
    if (!originalConfig) return

    // Reload original config into editing state
    setEditingConfigData(JSON.parse(JSON.stringify(originalConfig.config_data)))
    setEditingTableFields({
      config_name: originalConfig.config_name,
      config_type: originalConfig.config_type
    })
    setHasUnsavedChanges(false)
  }

  // Handler function for creating new bot
  const handleCreateNewBot = async (botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading') => {
    setIsCreatingNew(true)

    try {
      // Generate a unique name for the new bot based on type
      const botCount = allBots.length + 1
      const typeNames = {
        scheduled_trading: 'ggbot',
        signal_validation: 'signal validator',
        agent: 'agent'
      }
      const newBotName = `${typeNames[botType]} ${botCount}`

      // Create new bot with specified type
      const newBot = await createDefaultBot(botType)

      // Update name to be more descriptive
      const updatedBot = await apiClient.updateConfig(newBot.config_id, {}, newBotName)

      // Verify bot was created successfully by fetching it back
      try {
        const verifyBot = await apiClient.getConfig(updatedBot.config_id)
        console.log('✅ New bot creation verified:', verifyBot.config_id, verifyBot.config_name)

        // Add to local state and select it
        setAllBots(prev => [...prev, verifyBot])
        setSelectedConfigId(verifyBot.config_id)
      } catch (verifyError) {
        console.error('❌ New bot verification failed, refreshing bot list:', verifyError)
        // If verification fails, refresh from server to ensure we have latest data
        const refreshedBots = await apiClient.listConfigs()
        setAllBots(refreshedBots)

        // Try to select the newly created bot if it exists in the refreshed list
        const createdBot = refreshedBots.find(bot => bot.config_id === updatedBot.config_id)
        if (createdBot) {
          setSelectedConfigId(createdBot.config_id)
        } else {
          setSelectedConfigId(refreshedBots.length > 0 ? refreshedBots[0].config_id : null)
        }
      }

    } catch (error) {
      console.error('❌ Failed to create new bot:', error)

      // Check if it's a unique constraint violation
      if (error instanceof Error && error.message.includes('unique constraint')) {
        console.warn('⚠️ Cannot create multiple bots of the same type - database constraint limitation')
        // TODO: Show user-friendly message about single bot limitation
        // TODO: Remove this once database constraint is fixed
      }

      // On creation failure, don't modify state - let user try again
    } finally {
      setIsCreatingNew(false)
    }
  }

  // Handler function for renaming bot
  const handleRenameBot = async (configId: string, newName: string) => {
    // Prevent renaming if there are unsaved configuration changes
    if (hasUnsavedChanges) {
      console.warn('Cannot rename bot while configuration changes are unsaved')
      return
    }

    setIsBotAction(true)

    try {
      const updatedBot = await apiClient.updateConfig(configId, {}, newName)
      setAllBots(prev => prev.map(bot =>
        bot.config_id === configId ? updatedBot : bot
      ))
    } catch (error) {
      console.error('❌ Failed to rename bot:', error)
    } finally {
      setIsBotAction(false)
    }
  }

  // Handler function for duplicating bot
  const handleDuplicateBot = async (configId: string) => {
    setIsBotAction(true)

    try {
      const originalBot = allBots.find(bot => bot.config_id === configId)
      if (!originalBot) return

      const duplicateName = `Copy of ${originalBot.config_name}`
      const newBot = await apiClient.createConfig(duplicateName, originalBot.config_data)

      setAllBots(prev => [...prev, newBot])
      setSelectedConfigId(newBot.config_id)
    } catch (error) {
      console.error('❌ Failed to duplicate bot:', error)
    } finally {
      setIsBotAction(false)
    }
  }

  // Handler function for duplicating bot as live
  const handleDuplicateAsLive = (configId: string) => {
    const sourceBot = allBots.find(bot => bot.config_id === configId)
    if (sourceBot) {
      setSourceBotForLive(sourceBot)
      setDuplicateAsLiveModalOpen(true)
    }
  }

  // Handler for when live bot is successfully created
  const handleLiveBotCreated = async () => {
    // Refresh bot list to show new live bot
    await refreshBotList()
  }

  // Handler function for deleting bot
  const handleDeleteBot = async (configId: string) => {
    setIsBotAction(true)

    try {
      await apiClient.deleteConfig(configId)

      setAllBots(prev => {
        const updatedBots = prev.filter(bot => bot.config_id !== configId)

        if (selectedConfigId === configId) {
          setSelectedConfigId(updatedBots.length > 0 ? updatedBots[0].config_id : null)
          // Clear editing state if deleting currently editing bot
          setIsEditingConfig(false)
          setEditingConfigData(null)
          setEditingTableFields(null)
          setHasUnsavedChanges(false)
          setOriginalConfig(null)
        }

        return updatedBots
      })
    } catch (error) {
      console.error('❌ Failed to delete bot:', error)
    } finally {
      setIsBotAction(false)
    }
  }

  // Handler function for resetting bot account
  const handleResetAccount = async (configId: string) => {
    setIsBotAction(true)

    try {
      const result = await apiClient.resetAccount(configId)

      console.log(`✅ Account reset: ${result.message}`)
      console.log(`📊 Positions closed: ${result.positions_closed}, New balance: $${result.new_balance}`)

      // Refresh accounts data to show new balance
      // The SSE stream will automatically update the UI with the new account state

    } catch (error) {
      console.error('❌ Failed to reset account:', error)
    } finally {
      setIsBotAction(false)
    }
  }

  // ============================================================================
  // AGENT CONVERSATION HANDLERS
  // ============================================================================

  // Handler for sending message to agent
  const handleSendAgentMessage = async () => {
    if (!selectedConfigId || !agentInputValue.trim() || isWaitingForAgent) return

    try {
      // Add user message to UI immediately
      const userMessage = {
        role: 'user' as const,
        content: agentInputValue.trim(),
        timestamp: new Date().toISOString()
      }
      setAgentMessages(prev => [...prev, userMessage])
      setAgentInputValue('')
      setIsWaitingForAgent(true)

      // Send to backend API
      const token = await getAuthToken()
      const response = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: agentInputValue.trim() })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      console.log('✅ Message sent to agent')
    } catch (error) {
      console.error('❌ Failed to send message:', error)
      setIsWaitingForAgent(false)
    }
  }

  // Handler for starting strategy discussion
  const handleStartStrategyDiscussion = async () => {
    console.log('🎯 handleStartStrategyDiscussion called')
    console.log('🎯 selectedConfigId:', selectedConfigId)
    console.log('🎯 user?.id:', user?.id)

    if (!selectedConfigId || !user?.id) {
      console.error('❌ Early return: missing selectedConfigId or user.id')
      return
    }

    try {
      const token = await getAuthToken()
      console.log('🎯 Got auth token:', token ? 'yes' : 'no')

      // Check agent status first
      const statusResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!statusResponse.ok) {
        console.error('Failed to check agent status')
        return
      }

      const statusData = await statusResponse.json()
      console.log('🎯 Agent status:', statusData.status)

      // Start agent in strategy_definition mode if not running
      if (statusData.status === 'inactive' || statusData.status === 'stopped') {
        console.log('🤖 Agent is stopped, starting in strategy_definition mode...')

        const startResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/start?mode=strategy_definition`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (!startResponse.ok) {
          console.error('Failed to start agent')
          return
        }

        console.log('✅ Agent started successfully')
        // Wait a moment for agent to initialize
        await new Promise(resolve => setTimeout(resolve, 2000))
      } else {
        console.log('✅ Agent is already running')
      }

      // Send context message if there's an existing strategy
      if (editingConfigData?.agent_strategy?.content) {
        console.log('📤 Sending existing strategy as context...')

        const contextMessage = `Here is my current strategy:\n\n${editingConfigData.agent_strategy.content}\n\nI'd like to refine or update it. What improvements would you suggest?`

        const messageResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ message: contextMessage })
        })

        console.log('📤 Message sent, status:', messageResponse.status)

        // Add user message to display
        setAgentMessages(prev => {
          const updated = [...prev, {
            role: 'user' as const,
            content: contextMessage,
            timestamp: new Date().toISOString()
          }]
          console.log('📤 Updated agentMessages:', updated.length, 'messages')
          return updated
        })

        setIsWaitingForAgent(true)
        console.log('📤 UI state updated, waiting for agent response...')
      } else {
        // No existing strategy - send greeting to start conversation
        console.log('📤 No existing strategy, sending initial greeting...')

        const greetingMessage = "Hi! I'm ready to build a trading strategy. What do you recommend based on the available data sources?"

        const messageResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ message: greetingMessage })
        })

        console.log('📤 Greeting sent, status:', messageResponse.status)

        // Add user message to display
        setAgentMessages([{
          role: 'user' as const,
          content: greetingMessage,
          timestamp: new Date().toISOString()
        }])

        setIsWaitingForAgent(true)
      }
    } catch (error) {
      console.error('Error starting strategy discussion:', error)
    }
  }

  // Handler for confirming strategy
  const handleConfirmStrategy = async (autonomouslyEditable: boolean) => {
    if (!selectedConfigId) return

    try {
      // Send confirmation with autonomously_editable setting as JSON
      const token = await getAuthToken()
      const confirmationData = {
        confirm: true,
        autonomously_editable: autonomouslyEditable
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: JSON.stringify(confirmationData) })  // Stringify once for the message field
      })

      if (!response.ok) {
        throw new Error('Failed to confirm strategy')
      }

      setShowConfirmButton(false)
      console.log('✅ Strategy confirmed')

      // Refresh the bot config to get updated strategy
      setTimeout(async () => {
        const refreshedBots = await apiClient.listConfigs()
        setAllBots(refreshedBots)
      }, 2000)
    } catch (error) {
      console.error('❌ Failed to confirm strategy:', error)
    }
  }

  // Connect to already-running agent and fetch conversation history
  useEffect(() => {
    if (!selectedConfigId || editingTableFields?.config_type !== 'agent' || !user?.id) return
    if (activeTab !== 'configure') return

    const connectToRunningAgent = async () => {
      try {
        const token = await getAuthToken()

        // Check if agent is running
        const statusResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (!statusResponse.ok) return

        const statusData = await statusResponse.json()
        console.log('🔌 Agent status on mount:', statusData.status, 'mode:', statusData.mode)

        // If running in strategy_definition mode, fetch conversation history
        if (statusData.status === 'online' && statusData.mode === 'strategy_definition') {
          console.log('🔌 Fetching conversation history...')

          const historyResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/conversation-history`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })

          if (historyResponse.ok) {
            const historyData = await historyResponse.json()
            console.log('🔌 Got history:', historyData.count, 'messages')

            // Transform history to agentMessages format
            const formattedMessages = historyData.messages.map((msg: { role: 'user' | 'agent'; content: string; timestamp: string }) => ({
              role: msg.role,
              content: msg.content,
              timestamp: msg.timestamp
            }))

            setAgentMessages(formattedMessages)
            console.log('🔌 Connected to running agent with', formattedMessages.length, 'messages')
          }
        }
      } catch (error) {
        console.error('Error connecting to running agent:', error)
      }
    }

    connectToRunningAgent()
  }, [selectedConfigId, editingTableFields?.config_type, activeTab, user?.id])

  // Poll for agent responses (when agent mode is active)
  useEffect(() => {
    if (!selectedConfigId || editingTableFields?.config_type !== 'agent' || !user?.id) {
      console.log('🔄 Poll skipped:', { selectedConfigId, configType: editingTableFields?.config_type, userId: user?.id })
      return
    }

    console.log('🔄 Starting agent response polling...')

    const pollInterval = setInterval(async () => {
      try {
        const token = await getAuthToken()
        const response = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/poll-response`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        console.log('🔄 Poll response status:', response.status)

        if (!response.ok) return

        const data = await response.json()
        console.log('🔄 Poll data:', data)

        if (data.status === 'success' && data.text) {
          console.log('✅ Got agent message, adding to UI')
          // Add agent message to UI
          const agentMessage = {
            role: 'agent' as const,
            content: data.text,
            timestamp: data.timestamp || new Date().toISOString()
          }
          setAgentMessages(prev => [...prev, agentMessage])
          setIsWaitingForAgent(false)

          // Check for confirmation button flag
          if (data.show_confirm_button) {
            setShowConfirmButton(true)
          }
        }
      } catch (error) {
        console.error('❌ Poll agent response failed:', error)
      }
    }, 2000) // Poll every 2 seconds

    return () => {
      console.log('🔄 Stopping agent response polling')
      clearInterval(pollInterval)
    }
  }, [selectedConfigId, editingTableFields?.config_type, user?.id])

  // Helper function to refresh bot list from server (for error recovery)
  const refreshBotList = async () => {
    try {
      const refreshedBots = await apiClient.listConfigs()
      setAllBots(refreshedBots)

      // Check if currently selected bot still exists
      if (selectedConfigId) {
        const stillExists = refreshedBots.find(bot => bot.config_id === selectedConfigId)
        if (!stillExists) {
          setSelectedConfigId(refreshedBots.length > 0 ? refreshedBots[0].config_id : null)
          // Clear editing state since selected bot no longer exists
          setIsEditingConfig(false)
          setEditingConfigData(null)
          setEditingTableFields(null)
          setHasUnsavedChanges(false)
          setOriginalConfig(null)
        }
      }

      return refreshedBots
    } catch (error) {
      console.error('❌ Failed to refresh bot list:', error)
      throw error
    }
  }

  if (loading) {
    return (
      <ThemeProvider>
        <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
          <div className="text-[var(--text-secondary)]">Loading forge...</div>
        </div>
      </ThemeProvider>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="text-[var(--text-secondary)]">Please log in</div>
      </div>
    )
  }

  if (user && permissionsLoading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="text-[var(--text-secondary)]">Loading permissions...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Header />

      {/* Error Banner */}
      {loadError && (
        <div className="max-w-7xl mx-auto px-4 pt-4">
          <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Failed to load</h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">{loadError}</p>
            </div>
          </div>
        </div>
      )}

      {/* SSE Connection Status - only show when disconnected */}
      {!sseConnected && !loadError && (
        <div className="max-w-7xl mx-auto px-4 pt-4">
          <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 flex items-center gap-3">
            <div className="flex-shrink-0">
              <svg className="h-4 w-4 text-amber-600 dark:text-amber-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-sm text-amber-700 dark:text-amber-300">Connecting to real-time updates...</p>
          </div>
        </div>
      )}

        {/* 12-column grid container */}
        <div className="grid max-w-7xl grid-cols-12 gap-4 px-4 py-4 min-h-[calc(100vh-64px)]">
          {/* Bot Rail */}
          <BotRail
            bots={allBots}
            selectedId={selectedConfigId}
            onSelect={handleBotSelection}
            accounts={accounts}
            onCreateNew={() => setBotCreationModalOpen(true)}
            isCreatingNew={isCreatingNew}
            onRename={handleRenameBot}
            onDuplicate={handleDuplicateBot}
            onDuplicateAsLive={handleDuplicateAsLive}
            onDelete={handleDeleteBot}
            onResetAccount={handleResetAccount}
            isBotAction={isBotAction}
            className="col-span-12 hidden md:col-span-3 md:block"
          />

          {/* Main Content */}
          <main className="col-span-12 md:col-span-9 flex flex-col pb-16 md:pb-0">
            {/* ActivationBar - persistent across all tabs */}
            {selectedBot && (
              <ActivationBar
                selectedBot={selectedBot}
                executionStatus={executionStatus}
                statusMessage={statusMessage}
                countdown={countdown}
                isStarting={isStarting}
                isStopping={isStopping}
                isManualTriggering={isManualTriggering}
                onStart={handleStart}
                onStop={handleStop}
                onManualTrigger={handleManualTrigger}
              />
            )}

            <TabNavigation
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            <div className="flex-1 mt-4 pb-32">
              {selectedBot ? (
                activeTab === 'monitor' ? (
                  <div className="space-y-4">
                    {/* Top Row: DecisionFeed + PerformanceChart side-by-side */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* DecisionFeed - Decision carousel */}
                      <DecisionFeed
                        decisions={decisions}
                      />

                      {/* PerformanceChart - Equity curve with trade markers */}
                      <PerformanceChart
                        account={selectedAccount}
                        configId={selectedConfigId ?? ''}
                      />

                      {/* Old MetricsBar - Keeping code for reference
                      <MetricsBar
                        account={selectedAccount}
                        positions={positions}
                        onTotalTradesClick={() => setIsTradeHistoryModalOpen(true)}
                      />
                      */}
                    </div>

                    {/* PositionsTable - Active trades (full width) */}
                    <PositionsTable
                      positions={positions}
                      selectedConfigId={selectedConfigId ?? undefined}
                      onPositionClosed={() => {
                        // SSE will automatically refresh positions, but log the event
                        console.log('Position closed, waiting for SSE update...')
                      }}
                    />
                  </div>
                ) : editingTableFields?.config_type === 'agent' ? (
                  // Agent mode: State machine based on strategy existence and agent activity
                  <div className="space-y-4">
                    {/* State 1-3: Show button + optional strategy display */}
                    {agentMessages.length === 0 ? (
                      <div className="flex flex-col items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-12">
                        {/* Show existing strategy if available */}
                        {editingConfigData?.agent_strategy ? (
                          <div className="w-full max-w-3xl space-y-6">
                            {/* Strategy Display */}
                            <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] p-6">
                              <h3 className="text-lg font-medium text-[var(--text-primary)] mb-3 flex items-center gap-2">
                                <span>📋</span>
                                <span>Current Strategy</span>
                              </h3>
                              <div className="prose prose-sm dark:prose-invert max-w-none">
                                <div className="whitespace-pre-wrap text-[var(--text-secondary)]">
                                  {editingConfigData.agent_strategy.content}
                                </div>
                              </div>
                              <div className="mt-4 pt-4 border-t border-[var(--border)] text-xs text-[var(--text-muted)] space-y-1">
                                <div>Version: {editingConfigData.agent_strategy.version || 1}</div>
                                <div>Autonomously editable: {editingConfigData.agent_strategy.autonomously_editable ? 'Yes' : 'No'}</div>
                              </div>
                            </div>

                            {/* Start Discussion Button */}
                            <button
                              onClick={handleStartStrategyDiscussion}
                              disabled={selectedBot?.state === 'active'}
                              className={`w-full py-4 rounded-lg font-medium transition-colors ${
                                selectedBot?.state === 'active'
                                  ? 'bg-gray-400 cursor-not-allowed opacity-60'
                                  : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                              }`}
                              title={selectedBot?.state === 'active' ? 'Deactivate bot first to edit strategy' : 'Start conversation to refine strategy'}
                            >
                              {selectedBot?.state === 'active' ? '🔒 Bot Active - Deactivate to Edit' : '💬 Refine Strategy'}
                            </button>
                          </div>
                        ) : (
                          // No strategy yet
                          <div className="text-center space-y-6">
                            <div className="text-6xl">🤖</div>
                            <div>
                              <h3 className="text-xl font-medium text-[var(--text-primary)] mb-2">
                                Define Your Trading Strategy
                              </h3>
                              <p className="text-sm text-[var(--text-muted)] max-w-md">
                                Start a conversation with your AI agent to build a custom trading strategy
                              </p>
                            </div>
                            <button
                              onClick={handleStartStrategyDiscussion}
                              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors"
                            >
                              Start Strategy Discussion
                            </button>
                          </div>
                        )}
                      </div>
                    ) : (
                      // State 4: Agent is running - show chat interface
                      <AgentConfigurator
                        messages={agentMessages}
                        inputValue={agentInputValue}
                        isWaiting={isWaitingForAgent}
                        showConfirmButton={showConfirmButton}
                        currentStrategy={null}
                        onSendMessage={handleSendAgentMessage}
                        onConfirmStrategy={handleConfirmStrategy}
                        onInputChange={setAgentInputValue}
                      />
                    )}
                  </div>
                ) : (
                  // Normal mode: Show regular config tabs
                  <ConfigureLayout
                    selectedBot={selectedBot}
                    editingConfigData={editingConfigData}
                    editingTableFields={editingTableFields}
                    hasUnsavedChanges={hasUnsavedChanges}
                    dataSources={dataSources}
                    onSaveConfig={saveConfigurationChanges}
                    onCancelConfig={cancelConfigurationEditing}
                    onResetConfig={resetConfigurationChanges}
                    onUpdateConfig={(updates) => {
                      updateEditingConfig({ configData: updates })
                    }}
                  />
                )
              ) : (
                <EmptyState
                  title="Setting up your ggbot"
                  description="Please wait while we create your bot..."
                  icon="🔧"
                />
              )}
            </div>
          </main>
        </div>

      <MobileNav
        className="md:hidden"
        bots={allBots}
        selectedId={selectedConfigId}
        onSelect={handleBotSelection}
        accounts={accounts}
        onCreateNew={() => setBotCreationModalOpen(true)}
        isCreatingNew={isCreatingNew}
        onRename={handleRenameBot}
        onDuplicate={handleDuplicateBot}
        onDelete={handleDeleteBot}
        isBotAction={isBotAction}
      />

      {/* Trade History Modal */}
      {selectedBot && selectedAccount && (
        <TradeHistoryModal
          configId={selectedBot.config_id}
          isOpen={isTradeHistoryModalOpen}
          onClose={() => setIsTradeHistoryModalOpen(false)}
          totalTrades={selectedAccount.total_trades || 0}
          winRate={selectedAccount.win_rate || 0}
        />
      )}

      {/* Duplicate as Live Modal */}
      <DuplicateAsLiveModal
        open={duplicateAsLiveModalOpen}
        onOpenChange={setDuplicateAsLiveModalOpen}
        sourceBot={sourceBotForLive}
        onSuccess={handleLiveBotCreated}
      />

      {/* Bot Creation Modal */}
      <BotCreationModal
        open={botCreationModalOpen}
        onOpenChange={setBotCreationModalOpen}
        onConfirm={handleCreateNewBot}
      />
    </div>
  )
}

export default function ForgePage() {
  return (
    <ThemeProvider>
      <PermissionProvider>
        <ForgeApp />
      </PermissionProvider>
    </ThemeProvider>
  )
}