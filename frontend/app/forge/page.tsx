'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { apiClient, BotConfiguration, ConfigData } from '@/lib/api'
import { useDataSources, useLatestActivity, useBotList } from '@/lib/queries'
import { ThemeProvider } from '@/lib/theme'
import { PermissionProvider, usePermissions } from '@/lib/permissions'
import { LiveTradingSetupModal } from '@/components/LiveTradingSetupModal'
import { SaveStatusProvider, useSaveStatus } from '@/lib/contexts/SaveStatusContext'
import { useBatchedConfigSave } from '@/lib/hooks/useBatchedConfigSave'
import { Header } from './components/layout/Header'
import { BotRail } from './components/layout/BotRail'
import { TabNavigation } from './components/layout/TabNavigation'
import { MobileNav } from './components/layout/MobileNav'
import { EmptyState } from './components/shared/EmptyState'
import { LoadingSkeleton } from './components/shared/LoadingSkeleton'
import { ActivationBar } from './components/monitor/ActivationBar'
import { PositionsTable } from './components/monitor/PositionsTable'
import TVTimeline from '@/components/tv-timeline'
import { ConfigureLayout } from './components/configure/ConfigureLayout'
import { BotCreationModal } from './components/modals/BotCreationModal'
import { Wrench, X } from 'lucide-react'
import Link from 'next/link'
import { OnboardingTour } from '@/components/OnboardingTour'

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

interface AccountData {
  config_id: string
  current_balance: number
  available_balance?: number
  margin_used?: number
  total_pnl: number
  unrealized_pnl?: number
  total_trades: number
  win_rate?: number
  win_trades?: number
  open_positions?: number
  performance_pct?: number  // Performance % calculated from first/latest activities
}

function ForgeApp() {
  const [user, setUser] = useState<{ id: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sseConnected, setSseConnected] = useState(false)

  // Permission loading - always call hook, but only use when user exists
  const { loading: permissionsLoading, userProfile, refreshProfile } = usePermissions()

  // Save status context - for operation feedback (optimistic updates)
  const { registerSave, completeSave, failSave } = useSaveStatus()

  // Core bot data - all local state with multi-bot support
  const [allBots, setAllBots] = useState<BotConfiguration[]>([])
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [accounts, setAccounts] = useState<AccountData[]>([])  // Account data from SSE

  // React Query hooks — replace manual useEffect fetching with cached queries
  const { data: dataSources = [] } = useDataSources(!!user)
  const { data: latestActivity = null } = useLatestActivity(selectedConfigId)
  const { data: initialBots } = useBotList(!!user)
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [isManualTriggering, setIsManualTriggering] = useState(false)
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [isBotAction, setIsBotAction] = useState(false)
  const [isBotSwitching, setIsBotSwitching] = useState(false)  // Show skeleton during bot switch
  const [botCreationModalOpen, setBotCreationModalOpen] = useState(false)
  const [showArenaBanner, setShowArenaBanner] = useState(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('arena-banner-dismissed') !== 'true'
  })
  const [showOnboardingTour, setShowOnboardingTour] = useState(false)
  const [liveTradingSetupOpen, setLiveTradingSetupOpen] = useState(false)

  // Onboarding tour steps - shown after first bot creation
  // Steps auto-navigate between tabs to show key features
  const ONBOARDING_STEPS = [
    {
      target: '[data-tour="activity-timeline"]',
      title: "Your Bot's Activity",
      content: "This timeline shows every action your bot takes. Click the icons on the chart to see details about each trade and decision.",
      onEnter: () => setActiveTab('monitor')
    },
    {
      target: '[data-tour="configure-tab"]',
      title: "Customize Your Bot",
      content: "Click Configure anytime to edit your bot's strategy, change indicators, or adjust trading settings.",
      onEnter: () => setActiveTab('monitor')
    },
    {
      target: '[data-tour="strategy-advisor"]',
      title: "Strategy Advisor",
      content: "Chat with the Strategy Advisor to understand your strategy, get suggestions, or analyze your bot's performance.",
      onEnter: () => setActiveTab('configure')
    },
    {
      target: '[data-tour="config-tabs"]',
      title: "Manual Configuration",
      content: "Use these tabs to manually adjust your market data sources, edit your strategy prompt, or fine-tune trade settings like leverage and position sizing.",
      onEnter: () => setActiveTab('configure')
    },
    {
      target: '[data-tour="activity-timeline"]',
      title: "You're All Set!",
      content: "Your bot is ready to trade. Watch its activity here, and come back to Configure anytime to refine your strategy. Good luck!",
      onEnter: () => setActiveTab('monitor')
    }
  ]

  // Use ref to track selectedConfigId for SSE filtering without causing reconnections
  const selectedConfigIdRef = useRef(selectedConfigId)
  selectedConfigIdRef.current = selectedConfigId

  // Track previous config ID to detect ACTUAL bot switches (not just SSE reference changes)
  const prevConfigIdForEditingRef = useRef<string | null>(null)
  const prevConfigIdForClearingRef = useRef<string | null>(null)

  // Get currently selected bot
  const selectedBot = selectedConfigId
    ? allBots.find(bot => bot.config_id === selectedConfigId) || null
    : null

  // Derive live bot from allBots (single live bot slot)
  const liveBot = allBots.find(bot => bot.trading_mode === 'hyperliquid') || null
  const hyperliquidConnected = !!userProfile?.hyperliquid_connected

  // Real-time status tracking
  const [nextRun, setNextRun] = useState<string | null>(null)
  const [countdown, setCountdown] = useState<string>('')

  // Tab navigation state
  const [activeTab, setActiveTab] = useState<'monitor' | 'configure'>('monitor')

  // Configuration editing state - simplified for auto-save
  const [editingConfigData, setEditingConfigData] = useState<ConfigData | null>(null)
  const [editingTableFields, setEditingTableFields] = useState<{
    config_name?: string
    config_type?: string
  } | null>(null)

  // Unified batched config save with dirty field tracking
  const {
    queueChange: queueConfigChange,
    isFieldDirty,
  } = useBatchedConfigSave({
    configId: selectedConfigId,
    configName: editingTableFields?.config_name,
    configType: editingTableFields?.config_type,
    delay: 5000,  // 5 second debounce for batched saves
    enabled: activeTab === 'configure',  // Only save when on configure tab
  })

  // Unified config change handler - used by ALL config components
  const handleConfigChange = useCallback((updates: Partial<ConfigData>) => {
    // 1. Update local state immediately for optimistic UI
    setEditingConfigData(prev => {
      if (!prev) return null

      // Deep merge the updates into existing config
      return {
        ...prev,
        ...updates,
        // Handle nested objects specifically
        ...(updates.extraction && {
          extraction: { ...(prev.extraction || {}), ...updates.extraction }
        }),
        ...(updates.decision && {
          decision: { ...(prev.decision || {}), ...updates.decision }
        }),
        ...(updates.trading && {
          trading: { ...prev.trading, ...updates.trading }
        }),
        ...(updates.llm_config && {
          llm_config: { ...(prev.llm_config || {}), ...updates.llm_config }
        }),
        ...(updates.telegram_integration && {
          telegram_integration: { ...prev.telegram_integration, ...updates.telegram_integration }
        }),
        ...(updates.agent_strategy && {
          agent_strategy: { ...(prev.agent_strategy || {}), ...updates.agent_strategy }
        })
      } as ConfigData
    })

    // 2. Queue for batched save (will be saved after 5s of inactivity)
    queueConfigChange(updates)
  }, [queueConfigChange])

  // Load bot config into editing state when configure tab is activated OR bot changes
  // IMPORTANT: Use ref to prevent SSE updates from triggering this (SSE updates allBots
  // which creates new selectedBot reference even when config_id is the same)
  useEffect(() => {
    if (activeTab !== 'configure' || !selectedBot) return

    // Only load config if:
    // 1. This is the first time loading for this config_id, OR
    // 2. The config_id actually changed (user switched bots)
    const configIdChanged = prevConfigIdForEditingRef.current !== selectedBot.config_id
    if (!configIdChanged && editingConfigData !== null) {
      // Same config_id and we already have editing data - skip (SSE triggered this)
      return
    }

    console.log('🔧 Loading config for editing:', selectedBot.config_id)
    prevConfigIdForEditingRef.current = selectedBot.config_id

    // Load bot config into editing state
    // IMPORTANT: Merge trading_mode from top level into config_data
    const configDataWithTradingMode = selectedBot.config_data
      ? {
          ...JSON.parse(JSON.stringify(selectedBot.config_data)),
          trading_mode: selectedBot.trading_mode,
        }
      : null

    setEditingConfigData(configDataWithTradingMode)
    setEditingTableFields({
      config_name: selectedBot.config_name,
      config_type: selectedBot.config_type
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, selectedBot])

  // Clear component data immediately when switching bots for instant UI update
  // IMPORTANT: Use ref to only run when config_id ACTUALLY changes (not on SSE updates)
  useEffect(() => {
    if (!selectedConfigId) return

    // Only clear data if the config_id actually changed
    if (prevConfigIdForClearingRef.current === selectedConfigId) {
      // Same config_id - this is just an SSE update, don't clear anything
      return
    }

    // Config ID actually changed - user switched bots
    prevConfigIdForClearingRef.current = selectedConfigId

    // Clear operational data that should be bot-specific
    setPositions([])
    setCountdown('')
    setNextRun(null)

    console.log('🔄 Switched to bot:', selectedConfigId, selectedBot?.config_name)
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
    tradingMode: 'paper' | 'hyperliquid' = 'paper',
  ): Promise<BotConfiguration> => {
    // Base config for all types
    const baseConfig = {
      schema_version: '2.1',
      config_type: botType,
      trading_mode: tradingMode,
      trading: {
        leverage: 5,
        position_sizing: {
          max_margin_percent: 20.0
        },
        risk_management: {
          default_stop_loss_percent: 1.5,
          default_take_profit_percent: 3.0
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
            max_margin_percent: 25.0   // Allow up to 25% risk per trade
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
        leverage: 5,
        position_sizing: {
          max_margin_percent: 20.0
        },
        risk_management: {
          default_stop_loss_percent: 1.5,
          default_take_profit_percent: 3.0
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

  // Seed local bot state from React Query cache when initial data arrives
  useEffect(() => {
    if (!initialBots) return

    if (initialBots.length > 0) {
      setAllBots(initialBots)
      // Only auto-select if nothing selected yet
      setSelectedConfigId(prev => prev ?? initialBots[0].config_id)
      setLoadError(null)
    } else {
      // No bots - open the bot creation modal for onboarding
      console.log('🎯 No bots found, opening bot creation modal for onboarding')
      setAllBots([])
      setSelectedConfigId(null)
      setBotCreationModalOpen(true)
      setLoadError(null)
    }
  }, [initialBots])

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
              // Update allBots with fresh data from SSE (includes profile_image_url updates)
              setAllBots(prev => {
                const updatedBots = [...prev]
                data.bots.forEach((sseBot: BotConfiguration) => {
                  const index = updatedBots.findIndex(b => b.config_id === sseBot.config_id)
                  if (index !== -1) {
                    // Merge SSE data with existing bot to preserve any local-only state
                    updatedBots[index] = { ...updatedBots[index], ...sseBot }
                  }
                })
                return updatedBots
              })

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

              // Update config fields from SSE (for AI Assistant changes, external updates)
              // Only apply updates to fields that user is NOT currently editing (dirty fields)
              if (myBot?.config_data && editingConfigData) {
                const serverConfig = myBot.config_data

                setEditingConfigData(prev => {
                  if (!prev) return null

                  const merged = { ...prev }
                  let hasChanges = false

                  // List of top-level config fields to check for SSE updates
                  const fieldsToCheck = [
                    'decision',
                    'extraction',
                    'trading',
                    'llm_config',
                    'agent_strategy',
                    'telegram_integration',
                    'selected_pair'
                  ] as const

                  for (const field of fieldsToCheck) {
                    // Skip if user is editing this field
                    if (isFieldDirty(field)) {
                      console.log(`🔒 SSE: Skipping ${field} (dirty - user is editing)`)
                      continue
                    }

                    // Check if server has a different value
                    const serverValue = serverConfig[field]
                    const currentValue = prev[field]

                    if (serverValue !== undefined &&
                        JSON.stringify(serverValue) !== JSON.stringify(currentValue)) {
                      console.log(`📝 SSE: Updating ${field} from server`)
                      ;(merged as Record<string, unknown>)[field] = serverValue
                      hasChanges = true
                    }
                  }

                  return hasChanges ? merged : prev
                })
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

  // Latest activity is now fetched via useLatestActivity() React Query hook
  // with 30s refetchInterval — no manual polling needed

  // Page visibility retry is now handled by React Query's built-in
  // refetchOnWindowFocus and retry logic

  // NOTE: Config loading for editing is handled by the useEffect at line 164-184
  // which fires when activeTab === 'configure' && selectedBot changes.
  //
  // REMOVED: Broken useEffect that compared config_id to selected_pair (always mismatched)
  // and fired on every SSE update, overwriting user's pending edits.
  // Bug introduced: config_id (UUID) !== selected_pair ("BTC/USDT") was always true.

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

      // Optimistically decrement free_runs_remaining for instant UI feedback
      // (SSE will sync the actual value within 5 seconds)
      if (selectedBot.first_run_used && (selectedBot.free_runs_remaining ?? 0) > 0) {
        setAllBots(prev => prev.map(bot =>
          bot.config_id === selectedBot.config_id
            ? { ...bot, free_runs_remaining: Math.max(0, (bot.free_runs_remaining ?? 0) - 1) }
            : bot
        ))
      }

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

  // Configuration editing handlers
  // Note: Config data changes now go through handleConfigChange (defined above with batched save)

  // Handle bot switching with clean state reset
  const handleBotSelection = (configId: string) => {
    // Skip if already on this bot
    if (configId === selectedConfigId) return

    // Always reset to monitor tab when switching bots
    setActiveTab('monitor')

    // Clear editing state
    setEditingConfigData(null)
    setEditingTableFields(null)

    // Show skeleton during transition (SSE will clear it via data push)
    setIsBotSwitching(true)

    // Switch to the new bot
    setSelectedConfigId(configId)

    // Clear switching state after SSE has time to populate (~500ms)
    setTimeout(() => setIsBotSwitching(false), 500)
  }

  // Config update callback for AI Assistant and child components
  const handleConfigUpdate = async () => {
    // Reload the selected bot's config after AI or auto-save updates
    // Skip temp IDs (optimistic placeholders)
    if (selectedConfigId && !selectedConfigId.startsWith('temp-')) {
      try {
        const updatedBot = await apiClient.getConfig(selectedConfigId)
        setAllBots(prev => prev.map(bot =>
          bot.config_id === selectedConfigId ? updatedBot : bot
        ))
        // Also update editingConfigData to refresh form fields
        setEditingConfigData(updatedBot.config_data)
      } catch (error) {
        console.error('Failed to reload bot config after update:', error)
      }
    }
  }

  // Handler function for creating new bot
  const handleCreateNewBot = async (
    botType: 'scheduled_trading' | 'signal_validation' | 'agent' = 'scheduled_trading',
    tradingMode: 'paper' | 'hyperliquid' = 'paper',
    botName?: string,
    configData?: Record<string, unknown>  // Full config from new typeform modal
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
        const modeLabel = tradingMode === 'hyperliquid' ? ' (Live)' : ''
        return `${typeNames[botType]} ${botCount}${modeLabel}`
      })()

      let newBot;
      if (configData) {
        // New typeform flow: create bot with full config directly
        newBot = await apiClient.createConfig(finalBotName, configData as Partial<ConfigData>, {
          config_type: botType,
          trading_mode: tradingMode,
        })
      } else {
        // Legacy flow: use createDefaultBot
        newBot = await createDefaultBot(botType, tradingMode)
        // Update name for legacy flow
        newBot = await apiClient.updateConfig(newBot.config_id, {}, finalBotName)
      }

      const updatedBot = newBot

      // Verify bot was created successfully by fetching it back
      try {
        const verifyBot = await apiClient.getConfig(updatedBot.config_id)
        console.log('✅ New bot creation verified:', verifyBot.config_id, verifyBot.config_name)

        // Check if this is the user's first bot (for onboarding tour)
        const isFirstBot = allBots.length === 0

        // Add to local state and select it
        setAllBots(prev => [...prev, verifyBot])
        setSelectedConfigId(verifyBot.config_id)

        // Close the modal
        setBotCreationModalOpen(false)

        // Trigger onboarding tour for first-time users after a short delay
        if (isFirstBot) {
          setTimeout(() => setShowOnboardingTour(true), 1500)
        }

        // Trigger first run automatically only for the user's very first bot
        if (isFirstBot && configData) {
          console.log('🚀 Triggering first run for new bot:', verifyBot.config_id)
          try {
            await apiClient.triggerBotManually(verifyBot.config_id)
            console.log('✅ First run triggered successfully')
          } catch (runError) {
            // Don't fail creation if first run fails - user can retry manually
            console.warn('⚠️ First run failed (non-blocking):', runError)
          }
        }
      } catch (verifyError) {
        console.error('❌ New bot verification failed, refreshing bot list:', verifyError)
        // If verification fails, refresh from server to ensure we have latest data
        const refreshedBots = await apiClient.listConfigs()
        setAllBots(refreshedBots)

        // Try to select the newly created bot if it exists in the refreshed list
        const createdBot = refreshedBots.find(bot => bot.config_id === updatedBot.config_id)
        if (createdBot) {
          setSelectedConfigId(createdBot.config_id)
          setBotCreationModalOpen(false)
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
    setIsBotAction(true)

    // 1. Capture previous name for rollback
    const previousBot = allBots.find(bot => bot.config_id === configId)
    if (!previousBot) {
      setIsBotAction(false)
      return
    }
    const previousName = previousBot.config_name

    // 2. Optimistic update - IMMEDIATE (name changes instantly)
    setAllBots(prev => prev.map(bot =>
      bot.config_id === configId ? { ...bot, config_name: newName } : bot
    ))

    // 3. API call
    try {
      await apiClient.updateConfig(configId, {}, newName)
      // Silent success - UI already updated
    } catch (error) {
      // 4. Rollback + error feedback
      console.error('❌ Failed to rename bot:', error)
      setAllBots(prev => prev.map(bot =>
        bot.config_id === configId ? { ...bot, config_name: previousName } : bot
      ))
      failSave('rename-bot', new Error('Failed to rename bot'))
    } finally {
      setIsBotAction(false)
    }
  }

  // Handler function for duplicating bot
  const handleDuplicateBot = async (configId: string) => {
    setIsBotAction(true)

    const originalBot = allBots.find(bot => bot.config_id === configId)
    if (!originalBot) {
      setIsBotAction(false)
      return
    }

    // 1. Create optimistic placeholder with temp ID
    const tempId = `temp-${Date.now()}`
    const optimisticBot: BotConfiguration = {
      ...originalBot,
      config_id: tempId,
      config_name: `Copy of ${originalBot.config_name}`,
      state: 'inactive'
    }

    // 2. Optimistic add - IMMEDIATE (new bot appears instantly)
    setAllBots(prev => [...prev, optimisticBot])
    setSelectedConfigId(tempId)

    // 3. API call
    try {
      const newBot = await apiClient.createConfig(
        optimisticBot.config_name,
        originalBot.config_data,
        {
          config_type: originalBot.config_type,
          trading_mode: originalBot.trading_mode,
          symphony_agent_id: originalBot.symphony_agent_id
        }
      )

      // 4. Replace placeholder with real bot (silent success)
      setAllBots(prev => prev.map(bot =>
        bot.config_id === tempId ? newBot : bot
      ))
      setSelectedConfigId(newBot.config_id)
    } catch (error) {
      // 5. Rollback + error feedback
      console.error('❌ Failed to duplicate bot:', error)
      setAllBots(prev => prev.filter(bot => bot.config_id !== tempId))
      setSelectedConfigId(configId)  // Back to original
      failSave('duplicate-bot', new Error('Failed to duplicate bot'))
    } finally {
      setIsBotAction(false)
    }
  }

  // Handler function for deleting bot
  const handleDeleteBot = async (configId: string) => {
    setIsBotAction(true)

    // 1. Capture previous state for rollback
    const previousBots = allBots
    const wasSelected = selectedConfigId === configId

    // 2. Optimistic update - IMMEDIATE (bot disappears instantly)
    setAllBots(prev => {
      const updatedBots = prev.filter(bot => bot.config_id !== configId)
      if (wasSelected) {
        setSelectedConfigId(updatedBots.length > 0 ? updatedBots[0].config_id : null)
        setEditingConfigData(null)
        setEditingTableFields(null)
      }
      return updatedBots
    })

    // 3. API call (async, user already sees update)
    try {
      await apiClient.deleteConfig(configId)
      // Success: No feedback needed - UI already updated
    } catch (error) {
      // 4. Rollback + show error feedback
      console.error('❌ Failed to delete bot:', error)
      setAllBots(previousBots)
      if (wasSelected) {
        setSelectedConfigId(configId)
      }
      failSave('delete-bot', new Error('Failed to delete bot'))
    } finally {
      setIsBotAction(false)
    }
  }

  // Handler function for resetting bot account
  const handleResetAccount = async (configId: string) => {
    setIsBotAction(true)

    // 1. Capture previous account state for rollback
    const previousAccounts = accounts

    // 2. Optimistic update - IMMEDIATE + show feedback
    registerSave('reset-account', 'Resetting...')
    setAccounts(prev => prev.map(account =>
      account.config_id === configId
        ? {
            ...account,
            current_balance: 10000,
            available_balance: 10000,
            total_pnl: 0,
            unrealized_pnl: 0,
            total_equity: 10000,
            win_rate: 0,
            total_trades: 0,
            open_positions: 0,
            performance_pct: 0,
          }
        : account
    ))

    // 3. API call
    try {
      const result = await apiClient.resetAccount(configId)
      console.log(`✅ Account reset: ${result.message}`)
      console.log(`📊 Positions closed: ${result.positions_closed}, New balance: $${result.new_balance}`)
      completeSave('reset-account', 'Account reset')
    } catch (error) {
      // 4. Rollback + error feedback
      console.error('❌ Failed to reset account:', error)
      setAccounts(previousAccounts)
      failSave('reset-account', new Error('Failed to reset account'))
    } finally {
      setIsBotAction(false)
    }
  }

  const handlePromoteToLive = async (configId: string) => {
    setIsBotAction(true)
    try {
      const result = await apiClient.promoteToLive(configId)
      if (result.live_config_id) {
        // Refresh bot list to pick up the updated live bot
        const configs = await apiClient.listConfigs()
        setAllBots(configs)
        setSelectedConfigId(result.live_config_id)
      }
    } catch (error) {
      console.error('Failed to promote to live:', error)
    } finally {
      setIsBotAction(false)
    }
  }

  if (loading) {
    return (
      <ThemeProvider>
        <div className="min-h-screen bg-[var(--bg-primary)]">
          {/* Skeleton Header */}
          <div className="h-16 border-b border-[var(--border)] px-4 flex items-center justify-between">
            <LoadingSkeleton variant="text" className="w-24 h-6" />
            <div className="flex gap-4">
              <LoadingSkeleton variant="circle" className="w-8 h-8" />
              <LoadingSkeleton variant="circle" className="w-8 h-8" />
            </div>
          </div>

          {/* Skeleton Grid */}
          <div className="max-w-7xl mx-auto grid grid-cols-12 gap-4 px-4 py-4">
            {/* BotRail skeleton */}
            <div className="col-span-3 hidden md:block space-y-2">
              {[1, 2, 3].map(i => (
                <LoadingSkeleton key={i} variant="card" className="h-16" />
              ))}
            </div>

            {/* Main content skeleton */}
            <div className="col-span-12 md:col-span-9 space-y-4">
              <LoadingSkeleton variant="card" className="h-24" />
              <LoadingSkeleton variant="card" className="h-[400px]" />
            </div>
          </div>
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
      <div className="min-h-screen bg-[var(--bg-primary)]">
        {/* Skeleton Header */}
        <div className="h-16 border-b border-[var(--border)] px-4 flex items-center justify-between">
          <LoadingSkeleton variant="text" className="w-24 h-6" />
          <div className="flex gap-4">
            <LoadingSkeleton variant="circle" className="w-8 h-8" />
            <LoadingSkeleton variant="circle" className="w-8 h-8" />
          </div>
        </div>

        {/* Skeleton Grid */}
        <div className="max-w-7xl mx-auto grid grid-cols-12 gap-4 px-4 py-4">
          {/* BotRail skeleton */}
          <div className="col-span-3 hidden md:block space-y-2">
            {[1, 2, 3].map(i => (
              <LoadingSkeleton key={i} variant="card" className="h-16" />
            ))}
          </div>

          {/* Main content skeleton */}
          <div className="col-span-12 md:col-span-9 space-y-4">
            <LoadingSkeleton variant="card" className="h-24" />
            <LoadingSkeleton variant="card" className="h-[400px]" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Header />

      {/* ggArena Season 1 Announcement Banner */}
      {showArenaBanner && (
        <div className="bg-[var(--accent)]/10 border-b border-[var(--accent)]/20">
          <div className="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between">
            <p className="text-sm text-[var(--text-primary)]">
              <span className="font-semibold">ggArena Season 1 Complete</span>
              <span className="text-[var(--text-secondary)]"> — </span>
              <Link href="/arena" className="text-[var(--accent)] hover:underline">
                See the results →
              </Link>
            </p>
            <button
              onClick={() => { localStorage.setItem('arena-banner-dismissed', 'true'); setShowArenaBanner(false) }}
              className="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

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
            liveBot={liveBot}
            hyperliquidConnected={hyperliquidConnected}
            selectedId={selectedConfigId}
            onSelect={handleBotSelection}
            onCreateNew={() => setBotCreationModalOpen(true)}
            onOpenHyperliquidSetup={() => setLiveTradingSetupOpen(true)}
            onPromoteToLive={handlePromoteToLive}
            isCreatingNew={isCreatingNew}
            onRename={handleRenameBot}
            onDuplicate={handleDuplicateBot}
            onDelete={handleDeleteBot}
            onResetAccount={handleResetAccount}
            isBotAction={isBotAction}
            accounts={accounts}
            className="col-span-12 hidden md:col-span-3 md:block"
          />

          {/* Main Content */}
          <main className="col-span-12 md:col-span-9 flex flex-col pb-16 md:pb-0">
            {/* ActivationBar - persistent across all tabs */}
            {selectedBot && (() => {
              // Calculate metrics from accounts data for selected bot
              const account = accounts.find(a => a.config_id === selectedConfigId)
              const isLegacyLive = ['symphony', 'aster'].includes(selectedBot?.trading_mode || '')
              const metrics = account ? {
                totalEquity: isLegacyLive
                  ? Number(account.total_pnl || 0)  // Cumulative P&L for legacy live modes
                  : Number(account.current_balance || 0) + Number(account.unrealized_pnl || 0),
                availableBalance: isLegacyLive ? 0 : Number(account.available_balance || 0),
                pnl: Number(account.unrealized_pnl || 0),
                trades: Number(account.total_trades || 0),
                winRate: account.win_rate ? Number(account.win_rate) * 100 : 0,
                performance: Number(account.performance_pct || 0)
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

            <div className="flex items-center justify-between my-3">
              <TabNavigation
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />
            </div>

            <div className="flex-1 pb-8">
              {selectedBot ? (
                activeTab === 'monitor' ? (
                  isBotSwitching ? (
                    // Skeleton during bot switch - prevents showing stale data
                    <div className="space-y-3">
                      <LoadingSkeleton variant="card" className="h-[400px]" />
                      <LoadingSkeleton variant="card" className="h-48" />
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {/* Activity Timeline - Full Width */}
                      {/* Guard: Skip rendering for temp IDs (optimistic placeholders during duplication) */}
                      {selectedConfigId && !selectedConfigId.startsWith('temp-') && (
                        <div data-tour="activity-timeline">
                          <TVTimeline
                            configId={selectedConfigId}
                            title={selectedBot.config_name}
                            variant="embedded"
                          />
                        </div>
                      )}

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
                  )
                ) : (
                  // Configure mode: ConfigureLayout handles ALL bot types
                  // (agent mode shows simplified UI via conditional rendering in ConfigureLayout)
                  <ConfigureLayout
                    selectedBot={selectedBot}
                    editingConfigData={editingConfigData}
                    editingTableFields={editingTableFields}
                    dataSources={dataSources}
                    onUpdateConfig={handleConfigChange}
                    onConfigUpdate={handleConfigUpdate}
                  />
                )
              ) : (
                <EmptyState
                  Icon={Wrench}
                  title="Create your first ggbot"
                  description="Click the + button to get started with your first trading bot."
                />
              )}
            </div>
          </main>
        </div>

      <MobileNav
        className="md:hidden"
        bots={allBots}
        liveBot={liveBot}
        hyperliquidConnected={hyperliquidConnected}
        selectedId={selectedConfigId}
        onSelect={handleBotSelection}
        onCreateNew={() => setBotCreationModalOpen(true)}
        onOpenHyperliquidSetup={() => setLiveTradingSetupOpen(true)}
        onPromoteToLive={handlePromoteToLive}
        isCreatingNew={isCreatingNew}
        onRename={handleRenameBot}
        onDuplicate={handleDuplicateBot}
        onDelete={handleDeleteBot}
        onResetAccount={handleResetAccount}
        isBotAction={isBotAction}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Bot Creation Modal */}
      <BotCreationModal
        open={botCreationModalOpen}
        onOpenChange={(open) => {
          // Don't allow closing if user has no bots
          if (!open && allBots.length === 0) {
            return
          }
          setBotCreationModalOpen(open)
        }}
        onConfirm={handleCreateNewBot}
        existingBotCount={allBots.length}
        forceOpen={allBots.length === 0}
      />

      {/* Live Trading Setup Modal (opened from BotRail live slot) */}
      <LiveTradingSetupModal
        open={liveTradingSetupOpen}
        onOpenChange={setLiveTradingSetupOpen}
        onComplete={async () => {
          setLiveTradingSetupOpen(false)
          // Refresh profile so hyperliquid_connected updates
          await refreshProfile()
          // Refresh bot list to pick up the auto-created live bot
          const configs = await apiClient.listConfigs()
          setAllBots(configs)
          // Select the new live bot
          const newLiveBot = configs.find(b => b.trading_mode === 'hyperliquid')
          if (newLiveBot) {
            setSelectedConfigId(newLiveBot.config_id)
          }
        }}
      />

      {/* Onboarding Tour - shown after first bot creation */}
      <OnboardingTour
        steps={ONBOARDING_STEPS}
        storageKey="ggbots-onboarding-complete"
        active={showOnboardingTour}
        onComplete={() => setShowOnboardingTour(false)}
      />
    </div>
  )
}

export default function ForgePage() {
  return (
    <ThemeProvider>
      <PermissionProvider>
        <SaveStatusProvider>
          <ForgeApp />
        </SaveStatusProvider>
      </PermissionProvider>
    </ThemeProvider>
  )
}