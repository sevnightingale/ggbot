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
import { PositionsTable } from './components/monitor/PositionsTable'
import TVTimeline from '@/components/tv-timeline'
import { ConfigureLayout } from './components/configure/ConfigureLayout'
import { AgentConfigurator } from './components/configure/AgentConfigurator'
import { BotCreationModal } from './components/modals/BotCreationModal'
import { UniversalAIAssistant } from '@/components/UniversalAIAssistant'
import { Wrench } from 'lucide-react'

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

interface Activity {
  id: string
  timestamp: string
  type: string
  priority: number
  data: {
    summary?: string
    details?: Record<string, unknown>
    symbol?: string
    importance?: number
    trade_id?: string
    trade_type?: string
    confidence?: number
    leverage?: number
    entry_price?: number
    stop_loss_price?: number
  }
}

interface AccountData {
  config_id: string
  current_balance: number
  total_pnl: number
  total_trades: number
  win_rate?: number
  win_trades?: number
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
  const [accounts, setAccounts] = useState<AccountData[]>([])  // Account data from SSE
  const [latestActivity, setLatestActivity] = useState<Activity | null>(null)  // Latest activity for status display
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [isManualTriggering, setIsManualTriggering] = useState(false)
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [isBotAction, setIsBotAction] = useState(false)
  const [botCreationModalOpen, setBotCreationModalOpen] = useState(false)

  // Use ref to track selectedConfigId for SSE filtering without causing reconnections
  const selectedConfigIdRef = useRef(selectedConfigId)
  selectedConfigIdRef.current = selectedConfigId

  // Get currently selected bot
  const selectedBot = selectedConfigId
    ? allBots.find(bot => bot.config_id === selectedConfigId) || null
    : null


  // Real-time status tracking
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
  const [agentStarted, setAgentStarted] = useState(false)

  // Debounce timer for auto-save
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null)

  // AI Assistant state
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false)

  // Start editing mode when configure tab is activated
  useEffect(() => {
    if (activeTab === 'configure' && selectedBot && !isEditingConfig) {
      console.log('🔧 Starting edit mode for bot:', selectedBot.config_id)
      console.log('🔧 Bot data being loaded into editing state:', JSON.stringify(selectedBot, null, 2))

      // Enter editing mode - load selected bot config into editing state
      // IMPORTANT: Merge trading_mode and symphony_agent_id from top level into config_data
      const configDataWithTradingMode = selectedBot.config_data
        ? {
            ...JSON.parse(JSON.stringify(selectedBot.config_data)),
            trading_mode: selectedBot.trading_mode,
            symphony_agent_id: selectedBot.symphony_agent_id
          }
        : null

      setIsEditingConfig(true)
      setEditingConfigData(configDataWithTradingMode)
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
  const createDefaultBot = async (
    botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading',
    tradingMode: 'paper' | 'symphony' | 'aster' = 'paper',
    symphonyAgentId?: string
  ): Promise<BotConfiguration> => {
    // Base config for all types
    const baseConfig = {
      schema_version: '2.1',
      config_type: botType,
      trading_mode: tradingMode,
      symphony_agent_id: symphonyAgentId,
      trading: {
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
        trading: {
          ...baseConfig.trading,
          leverage: 10,  // Higher default for agents
          position_sizing: {
            method: 'confidence_based',  // Always use confidence-based for agents
            max_position_percent: 25.0   // Allow up to 25% risk per trade
          }
        },
        decision: {
          analysis_frequency: 'agent_driven'
        },
        llm_config: {
          provider: 'openrouter',
          model: 'grok',
          thinking_mode: false,
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
        provider: 'openrouter',
        model: 'grok',
        thinking_mode: false,
        use_platform_keys: true,
        use_own_key: false
      },
      trading: {
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
              // Execution status tracking removed - now shown via latestActivity in ActivationBar

              // Update next run time
              if (myBot?.next_run) {
                setNextRun(myBot.next_run)
              } else if (myBot?.is_scheduled) {
                // Bot is scheduled but next_run is null - show waiting state
                setNextRun(null)
                setCountdown('Waiting for next run...')
              }

              // Update agent strategy if changed (for real-time collaborative editing)
              if (myBot?.config_data?.agent_strategy && editingConfigData) {
                const newStrategyContent = myBot.config_data.agent_strategy.content
                const currentStrategyContent = editingConfigData.agent_strategy?.content

                if (newStrategyContent !== currentStrategyContent) {
                  console.log('📝 Agent strategy updated via SSE')
                  setEditingConfigData(prev => {
                    if (!prev) return null
                    return {
                      ...prev,
                      agent_strategy: myBot.config_data.agent_strategy
                    }
                  })
                }
              }
            }

            // Update live positions with P&L
            if (data.positions) {
              const myPositions = data.positions.filter((p: { config_id: string }) => p.config_id === currentSelectedId)
              setPositions(myPositions)
            }

            // Update accounts data (for KPIs in ActivationBar)
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
    // editingConfigData is intentionally omitted - adding it would cause SSE reconnection on every edit
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // Fetch latest activity for selected bot (for status display when idle)
  useEffect(() => {
    if (!selectedConfigId || !user) {
      setLatestActivity(null)
      return
    }

    const fetchLatestActivity = async () => {
      try {
        const token = await getAuthToken()
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const response = await fetch(`${apiUrl}/api/v2/activities/${selectedConfigId}?limit=1`, {
          headers: { Authorization: `Bearer ${token}` }
        })

        if (response.ok) {
          const data = await response.json()
          if (data.activities && data.activities.length > 0) {
            setLatestActivity(data.activities[0])
          } else {
            setLatestActivity(null)
          }
        }
      } catch (error) {
        console.error('Failed to fetch latest activity:', error)
      }
    }

    fetchLatestActivity()
    // Refresh every 30 seconds
    const interval = setInterval(fetchLatestActivity, 30000)
    return () => clearInterval(interval)
  }, [selectedConfigId, user])

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
        // IMPORTANT: Merge trading_mode and symphony_agent_id from top level into config_data
        const configDataWithTradingMode = {
          ...JSON.parse(JSON.stringify(selectedBot.config_data)),
          trading_mode: selectedBot.trading_mode,
          symphony_agent_id: selectedBot.symphony_agent_id
        }

        setEditingConfigData(configDataWithTradingMode)
        setEditingTableFields({
          config_name: selectedBot.config_name,
          config_type: selectedBot.config_type
        })
        setOriginalConfig(selectedBot)
        setHasUnsavedChanges(false)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedConfigId, selectedBot, isEditingConfig, originalConfig])

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

      // Manual execution started - status will be tracked via SSE updates

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
  const handleCreateNewBot = async (
    botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading',
    tradingMode: 'paper' | 'symphony' | 'aster' = 'paper',
    symphonyAgentId?: string,
    botName?: string
  ) => {
    setIsCreatingNew(true)

    try {
      // Use provided name or generate default (fallback shouldn't be needed since modal provides it)
      const finalBotName = botName?.trim() || (() => {
        const botCount = allBots.length + 1
        const typeNames = {
          scheduled_trading: 'ggbot',
          signal_validation: 'signal validator',
          agent: 'agent'
        }
        const modeLabel = tradingMode === 'symphony' ? ' (Symphony)' : tradingMode === 'aster' ? ' (Aster)' : ''
        return `${typeNames[botType]} ${botCount}${modeLabel}`
      })()

      // Create new bot with specified type and trading mode
      const newBot = await createDefaultBot(botType, tradingMode, symphonyAgentId)

      // Update name
      const updatedBot = await apiClient.updateConfig(newBot.config_id, {}, finalBotName)

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

  // Handler for strategy content changes (with debounced auto-save)
  const handleStrategyChange = async (newContent: string) => {
    if (!selectedConfigId) return

    // Update local editing state immediately for responsive UI
    setEditingConfigData(prev => {
      if (!prev) return null
      return {
        ...prev,
        agent_strategy: {
          content: newContent,
          autonomously_editable: prev.agent_strategy?.autonomously_editable ?? false,
          version: prev.agent_strategy?.version ?? 1,
          last_updated_at: prev.agent_strategy?.last_updated_at ?? new Date().toISOString(),
          last_updated_by: prev.agent_strategy?.last_updated_by ?? 'user',
          performance_log: prev.agent_strategy?.performance_log ?? []
        }
      }
    })

    // Clear existing timer
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }

    // Set new timer for auto-save (1 second debounce)
    saveTimerRef.current = setTimeout(async () => {
      try {
        console.log('💾 Auto-saving strategy...')
        // ⚠️ CRITICAL: Always pass config_name and config_type to prevent overwriting with defaults
        await apiClient.updateConfig(
          selectedConfigId,
          {
            agent_strategy: {
              content: newContent
            }
          },
          editingTableFields?.config_name,  // Preserve bot name
          editingTableFields?.config_type    // Preserve config type
        )
        console.log('✅ Strategy auto-saved')
      } catch (error) {
        console.error('❌ Failed to auto-save strategy:', error)
      }
    }, 1000)
  }

  // Handler for starting strategy builder agent
  const handleStartStrategyBuilder = async () => {
    if (!selectedConfigId) return

    try {
      const token = await getAuthToken()

      // Start agent in strategy_definition mode
      const response = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/start?mode=strategy_definition`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to start strategy builder')
      }

      setAgentStarted(true)
      console.log('✅ Strategy builder started')

      // Send initial greeting if no existing strategy
      const currentStrategy = editingConfigData?.agent_strategy?.content
      const greetingMessage = currentStrategy
        ? `Here is my current strategy:\n\n${currentStrategy}\n\nI'd like to refine or update it. What improvements would you suggest?`
        : "Hi! I'm ready to build a trading strategy. What do you recommend based on the available data sources?"

      const messageResponse = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}/api/v2/agent/${selectedConfigId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: greetingMessage })
      })

      if (messageResponse.ok) {
        setAgentMessages([{
          role: 'user' as const,
          content: greetingMessage,
          timestamp: new Date().toISOString()
        }])
        setIsWaitingForAgent(true)
      }
    } catch (error) {
      console.error('❌ Failed to start strategy builder:', error)
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
          // TODO: Re-enable when showConfirmButton state is added
          // if (data.show_confirm_button) {
          //   setShowConfirmButton(true)
          // }
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
            onCreateNew={() => setBotCreationModalOpen(true)}
            isCreatingNew={isCreatingNew}
            onRename={handleRenameBot}
            onDuplicate={handleDuplicateBot}
            onDelete={handleDeleteBot}
            onResetAccount={handleResetAccount}
            isBotAction={isBotAction}
            className="col-span-12 hidden md:col-span-3 md:block"
          />

          {/* Main Content */}
          <main className="col-span-12 md:col-span-9 flex flex-col pb-16 md:pb-0">
            {/* ActivationBar - persistent across all tabs */}
            {selectedBot && (() => {
              // Calculate metrics from accounts data for selected bot
              const account = accounts.find(a => a.config_id === selectedConfigId)
              const metrics = account ? {
                balance: Number(account.current_balance || 0),
                pnl: Number(account.total_pnl || 0),
                trades: Number(account.total_trades || 0),
                winRate: account.win_rate ? Number(account.win_rate) :
                         (account.total_trades > 0 ? (Number(account.win_trades || 0) / Number(account.total_trades)) * 100 : 0),
                performance: Number(account.total_pnl || 0)  // Performance in absolute USD for now
              } : null

              return (
                <ActivationBar
                  selectedBot={selectedBot}
                  countdown={countdown}
                  isStarting={isStarting}
                  isStopping={isStopping}
                  isManualTriggering={isManualTriggering}
                  onStart={handleStart}
                  onStop={handleStop}
                  onManualTrigger={handleManualTrigger}
                  metrics={metrics}
                  latestActivity={latestActivity}
                />
              )
            })()}

            <div className="flex items-center justify-between">
              <TabNavigation
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />
            </div>

            <div className="flex-1 mt-4 pb-32">
              {selectedBot ? (
                activeTab === 'monitor' ? (
                  <div className="space-y-4">
                    {/* Activity Timeline - Full Width */}
                    <TVTimeline
                      configId={selectedConfigId || ''}
                      title={selectedBot.config_name}
                      variant="embedded"
                    />

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
                  // Agent mode: Always show 2-column collaborative editor
                  <AgentConfigurator
                    messages={agentMessages}
                    inputValue={agentInputValue}
                    isWaiting={isWaitingForAgent}
                    strategyContent={editingConfigData?.agent_strategy?.content || ''}
                    onSendMessage={handleSendAgentMessage}
                    onInputChange={setAgentInputValue}
                    onStrategyChange={handleStrategyChange}
                    onStartAgent={handleStartStrategyBuilder}
                    agentStarted={agentStarted}
                  />
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
                    onOpenAIAssistant={() => setAiAssistantOpen(true)}
                  />
                )
              ) : (
                <EmptyState
                  Icon={Wrench}
                  title="Setting up your ggbot"
                  description="Please wait while we create your bot..."
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
        onCreateNew={() => setBotCreationModalOpen(true)}
        isCreatingNew={isCreatingNew}
        onRename={handleRenameBot}
        onDuplicate={handleDuplicateBot}
        onDelete={handleDeleteBot}
        isBotAction={isBotAction}
      />

      {/* Bot Creation Modal */}
      <BotCreationModal
        open={botCreationModalOpen}
        onOpenChange={setBotCreationModalOpen}
        onConfirm={handleCreateNewBot}
        existingBotCount={allBots.length}
      />

      {/* Universal AI Assistant */}
      {selectedBot && activeTab === 'configure' && (
        <UniversalAIAssistant
          configId={selectedBot.config_id}
          botType={
            selectedBot.config_type === 'scheduled_trading'
              ? 'scheduled'
              : selectedBot.config_type as "agent" | "scheduled" | "signal_validation"
          }
          isOpen={aiAssistantOpen}
          onClose={() => setAiAssistantOpen(false)}
          onConfigUpdate={async () => {
            // Reload the selected bot's config when AI updates it
            if (selectedConfigId) {
              try {
                const updatedBot = await apiClient.getConfig(selectedConfigId)
                setAllBots(prev => prev.map(bot =>
                  bot.config_id === selectedConfigId ? updatedBot : bot
                ))
              } catch (error) {
                console.error('Failed to reload bot config after AI update:', error)
              }
            }
          }}
        />
      )}
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