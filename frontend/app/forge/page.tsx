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
import { MetricsBar } from './components/monitor/MetricsBar'
import { DecisionFeed } from './components/monitor/DecisionFeed'
import { PositionsTable } from './components/monitor/PositionsTable'
import { ConfigureLayout } from './components/configure/ConfigureLayout'

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
    daily_pnl?: number
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

  // Start editing mode when configure tab is activated
  useEffect(() => {
    if (activeTab === 'configure' && selectedBot && !isEditingConfig) {
      console.log('🔧 Starting edit mode for bot:', selectedBot.config_id)
      console.log('🔧 Bot data being loaded into editing state:', JSON.stringify(selectedBot, null, 2))

      // Enter editing mode - load selected bot config into editing state
      setIsEditingConfig(true)
      setEditingConfigData(JSON.parse(JSON.stringify(selectedBot.config_data)))
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
  const createDefaultBot = async (): Promise<BotConfiguration> => {
    const defaultConfigData = {
      schema_version: '2.1',
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
        analysis_frequency: '1h',
        system_prompt: 'You are an expert cryptocurrency trader. Analyze the provided market data and provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.',
        user_prompt: 'if RSI 1hr below 50 enter long, if above enter short'
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
        },
        exchange_config: {
          exchange_type: 'cex',
          selected_exchange: 'binance',
          api_key: '',
          secret_key: ''
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
      
      try {
        // Get user's existing bots using proper API client
        const configs = await apiClient.listConfigs()

        if (configs.length > 0) {
          // Load all configs and select first one
          setAllBots(configs)
          setSelectedConfigId(configs[0].config_id)
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
          } catch (verifyError) {
            console.error('❌ Bot creation verification failed:', verifyError)
            // Try to refresh the list in case there's a timing issue
            const refreshedConfigs = await apiClient.listConfigs()
            if (refreshedConfigs.length > 0) {
              setAllBots(refreshedConfigs)
              setSelectedConfigId(refreshedConfigs[0].config_id)
            } else {
              console.error('❌ No bots found after creation attempt')
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
      }
    }

    loadOrCreateBot()
  }, [user])

  // Real-time SSE connection for status updates
  useEffect(() => {
    if (!user) return

    const connectSSE = async () => {
      try {
        const token = await getAuthToken()
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const stream = new EventSource(`${apiUrl}/api/dashboard-stream?token=${encodeURIComponent(token)}`)

        stream.onopen = () => {
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
            } else {
            }

          } catch (error) {
            console.error('❌ Failed to parse SSE data:', error)
          }
        })

        stream.onerror = (error) => {
          console.error('❌ SSE connection error:', error)
        }

      } catch (error) {
        console.error('❌ Failed to connect SSE:', error)
      }
    }

    connectSSE()

    // Cleanup function
    return () => {
      console.log('🛑 Cleaning up SSE connection')
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
      setCountdown(`Next run: ${minutes}m ${seconds}s`)
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [nextRun])

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
      const response = await apiClient.authenticatedFetch(`${apiUrl}/api/v2/bot/${selectedBot.config_id}/start`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Failed to start bot: ${response.status}`)
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
      const response = await apiClient.authenticatedFetch(`${apiUrl}/api/v2/bot/${selectedBot.config_id}/stop`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Failed to stop bot: ${response.status}`)
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
          // Handle nested objects specifically
          ...(configUpdates.extraction && {
            extraction: {
              ...prev.extraction,
              ...configUpdates.extraction
            }
          }),
          ...(configUpdates.decision && {
            decision: {
              ...prev.decision,
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
              ...prev.llm_config,
              ...configUpdates.llm_config
            }
          }),
          ...(configUpdates.telegram_integration && {
            telegram_integration: {
              ...prev.telegram_integration,
              ...configUpdates.telegram_integration
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

  // Handle bot type changes with warning
  const handleBotTypeChange = (newType: 'autonomous_trading' | 'signal_validation') => {
    if (!isEditingConfig) return

    // TODO: Show warning about field resets when changing bot type
    updateEditingConfig({
      tableFields: { config_type: newType },
      configData: {
        // Update analysis_frequency based on type
        decision: {
          ...editingConfigData?.decision,
          analysis_frequency: newType === 'signal_validation' ? 'signal_driven' : '1h'
        }
      }
    })
  }

  // Handler function for creating new bot
  const handleCreateNewBot = async () => {
    setIsCreatingNew(true)

    try {
      // Generate a unique name for the new bot
      const botCount = allBots.length + 1
      const newBotName = `ggbot ${botCount}`

      // Create new bot using existing createDefaultBot logic
      const newBot = await createDefaultBot()

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

        {/* 12-column grid container */}
        <div className="grid max-w-7xl grid-cols-12 gap-4 px-4 py-4 min-h-[calc(100vh-64px)]">
          {/* Bot Rail */}
          <BotRail
            bots={allBots}
            selectedId={selectedConfigId}
            onSelect={handleBotSelection}
            accounts={accounts}
            onCreateNew={handleCreateNewBot}
            isCreatingNew={isCreatingNew}
            onRename={handleRenameBot}
            onDuplicate={handleDuplicateBot}
            onDelete={handleDeleteBot}
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
                    {/* Top Row: DecisionFeed + MetricsBar side-by-side */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* DecisionFeed - Decision carousel */}
                      <DecisionFeed
                        decisions={decisions}
                      />

                      {/* MetricsBar - Professional KPI grid (2x2) */}
                      <MetricsBar
                        account={selectedAccount}
                        positions={positions}
                      />
                    </div>

                    {/* PositionsTable - Active trades (full width) */}
                    <PositionsTable
                      positions={positions}
                    />
                  </div>
                ) : (
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
                    onBotTypeChange={handleBotTypeChange}
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
        onCreateNew={handleCreateNewBot}
        isCreatingNew={isCreatingNew}
        onRename={handleRenameBot}
        onDuplicate={handleDuplicateBot}
        onDelete={handleDeleteBot}
        isBotAction={isBotAction}
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