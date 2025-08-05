import { create } from 'zustand'
import { 
  Trade, 
  PerformanceData, 
  SchedulerStatus,
  AgentStatus,
  ExtractionConfig,
  DecisionConfig,
  TradingConfig,
  UnifiedConfig
} from '@/types'
import { api } from '@/lib/api/client'

interface BotState {
  // Bot management
  availableBots: UnifiedConfig[]
  currentBotId: string | null
  currentConfig: UnifiedConfig | null
  
  // Agent configurations (parsed from current config)
  extractionConfig: ExtractionConfig | null
  decisionConfig: DecisionConfig | null
  tradingConfig: TradingConfig | null
  
  // Agent statuses
  agentStatuses: {
    extraction: AgentStatus
    decision: AgentStatus
    trading: AgentStatus
  }
  
  // Trading data
  trades: Trade[]
  performance: PerformanceData | null
  
  // Scheduler
  schedulerStatus: SchedulerStatus
  
  // UI state
  isConfigModalOpen: boolean
  activeConfigAgent: 'extraction' | 'decision' | 'trading' | null
  isLoading: boolean
  error: string | null
  
  // Actions
  loadBots: () => Promise<void>
  createBot: (template: string, name?: string) => Promise<void>
  selectBot: (botId: string) => Promise<void>
  updateBotName: (botId: string, name: string) => Promise<void>
  deleteBot: (botId: string) => Promise<void>
  loadCurrentConfig: () => Promise<void>
  updateAgentConfig: (agent: 'extraction' | 'decision' | 'trading', config: any) => Promise<void>
  loadTrades: () => Promise<void>
  loadPerformance: (period?: string) => Promise<void>
  startScheduler: () => Promise<void>
  stopScheduler: () => Promise<void>
  checkSchedulerStatus: () => Promise<void>
  openConfigModal: (agent: 'extraction' | 'decision' | 'trading') => void
  closeConfigModal: () => void
  setError: (error: string | null) => void
}

const calculateAgentStatus = (config: any): AgentStatus => {
  if (!config) return 'unconfigured'
  
  // Add specific validation logic here based on required fields
  const hasRequiredFields = config && Object.keys(config).length > 0
  return hasRequiredFields ? 'configured' : 'partial'
}

// Demo config ID for rich mock data
const DEMO_CONFIG_ID = "demo-bot-00000000-1111-2222-3333-444444444444"
const GGSHOT_CONFIG_ID = "e249bb49-0455-4596-9657-09bf9e14ca14"

export const useBotStore = create<BotState>((set, get) => ({
  availableBots: [],
  currentBotId: null,
  currentConfig: null,
  extractionConfig: null,
  decisionConfig: null,
  tradingConfig: null,
  agentStatuses: {
    extraction: 'unconfigured',
    decision: 'unconfigured',
    trading: 'unconfigured',
  },
  trades: [],
  performance: null,
  schedulerStatus: { is_running: false },
  isConfigModalOpen: false,
  activeConfigAgent: null,
  isLoading: false,
  error: null,

  loadBots: async () => {
    console.log('Loading available bots...')
    const state = get()
    
    // Prevent multiple simultaneous loads
    if (state.isLoading && state.availableBots.length === 0) {
      console.log('Already loading bots, skipping...')
      return
    }
    
    try {
      set({ isLoading: true, error: null })
      
      // Test API connection first
      const isConnected = await api.testConnection()
      console.log('API connection test result:', isConnected)
      
      let configs: UnifiedConfig[] = []
      
      if (isConnected) {
        try {
          // Load all user configs from API
          configs = await api.getUserConfigs()
          console.log('Loaded configs from API:', configs.length)
        } catch (apiError) {
          console.warn('Failed to load configs from API, using demo fallback:', apiError)
          configs = []
        }
      } else {
        console.warn('API not available, using demo fallback')
      }
      
      // Default to ggShot flagship if available, otherwise first config, otherwise create demo
      let defaultConfigId = configs.find(c => c.config_id === GGSHOT_CONFIG_ID)?.config_id
      
      if (!defaultConfigId && configs.length > 0) {
        defaultConfigId = configs[0].config_id
      }
      
      // Always add demo bot as fallback
      const demoConfig: UnifiedConfig = {
        config_id: DEMO_CONFIG_ID,
        config_name: "Demo Bot - Showcase",
        config_type: "demo",
        user_id: api.currentUserId,
        config_data: {
          extraction: { symbols: ['BTC/USDT'], sources: { crypto_indicators_mcp: { enabled: true, indicators: [] } } },
          decision: { llm_provider: 'deepseek', system_prompt: '', strategy: '', additional_context: '' },
          trading: { exchange: 'demo', exchange_id: '', authentication: '', risk_rules: { max_leverage: 3, max_position_size_pct: 0.05, max_risk_per_trade_pct: 0.02, min_equity_protection: 0.8 } }
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        editable: true,
        is_flagship: false,
        paper_balance: 10000
      }
      configs.push(demoConfig)
      
      // Default to demo if no real configs available
      if (!defaultConfigId) {
        defaultConfigId = DEMO_CONFIG_ID
      }
      
      set({ 
        availableBots: configs,
        currentBotId: defaultConfigId || null,
        isLoading: false
      })
      
      // Load the default config
      if (defaultConfigId) {
        await get().selectBot(defaultConfigId)
      }
    } catch (error) {
      console.error('Error loading bots:', error)
      // Still show demo bot even if everything fails
      const demoConfig: UnifiedConfig = {
        config_id: DEMO_CONFIG_ID,
        config_name: "Demo Bot - Showcase",
        config_type: "demo",
        user_id: api.currentUserId,
        config_data: {
          extraction: { symbols: ['BTC/USDT'], sources: { crypto_indicators_mcp: { enabled: true, indicators: [] } } },
          decision: { llm_provider: 'deepseek', system_prompt: '', strategy: '', additional_context: '' },
          trading: { exchange: 'demo', exchange_id: '', authentication: '', risk_rules: { max_leverage: 3, max_position_size_pct: 0.05, max_risk_per_trade_pct: 0.02, min_equity_protection: 0.8 } }
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        editable: true,
        is_flagship: false,
        paper_balance: 10000
      }
      
      set({ 
        availableBots: [demoConfig],
        currentBotId: DEMO_CONFIG_ID,
        error: `API connection failed, showing demo mode. Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isLoading: false
      })
      
      // Load demo config
      await get().selectBot(DEMO_CONFIG_ID)
    }
  },

  createBot: async (template: string, name?: string) => {
    console.log('Creating new bot:', name, 'from template:', template)
    try {
      set({ isLoading: true, error: null })
      
      // Create config from template via API
      const newConfig = await api.createConfigFromTemplate(template, 'BTC/USDT', name)
      
      const state = get()
      const updatedBots = [...state.availableBots, newConfig]
      
      set({
        availableBots: updatedBots,
        currentBotId: newConfig.config_id,
        currentConfig: newConfig,
        isLoading: false
      })
      
      // Load the new config and switch to it
      await get().selectBot(newConfig.config_id)
    } catch (error) {
      console.error('Error creating bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to create bot', isLoading: false })
    }
  },

  selectBot: async (botId: string) => {
    console.log('Selecting bot:', botId)
    try {
      const state = get()
      
      // Prevent unnecessary re-selection of the same bot
      if (state.currentBotId === botId && state.currentConfig) {
        console.log('Bot already selected:', botId)
        return
      }
      
      set({ isLoading: true, error: null })
      
      // Check if it's the demo bot
      if (botId === DEMO_CONFIG_ID) {
        const demoBot = state.availableBots.find(bot => bot.config_id === DEMO_CONFIG_ID)
        if (demoBot) {
          set({
            currentBotId: botId,
            currentConfig: demoBot,
            extractionConfig: demoBot.config_data.extraction,
            decisionConfig: demoBot.config_data.decision,
            tradingConfig: demoBot.config_data.trading,
            agentStatuses: {
              extraction: calculateAgentStatus(demoBot.config_data.extraction),
              decision: calculateAgentStatus(demoBot.config_data.decision),
              trading: calculateAgentStatus(demoBot.config_data.trading),
            },
            isLoading: false
          })
          return
        }
      }
      
      // Load real config from API
      const config = await api.getUnifiedConfig(botId)
      
      // Parse complex config_data structure to simplified form structure
      const parseExtractionConfig = (configData: any, config: any): ExtractionConfig => {
        const extraction = configData.extraction || {}
        const cryptoMcp = extraction.sources?.crypto_indicators_mcp || {}
        
        return {
          symbols: ['BTC/USDT'], // Default symbol - would need to be stored in config
          sources: {
            crypto_indicators_mcp: {
              enabled: cryptoMcp.enabled || false,
              indicators: cryptoMcp.indicators || []
            },
            ggshot: {
              enabled: extraction.sources?.telegram?.enabled || config.config_type === 'ggshot'
            }
          }
        }
      }
      
      const parseDecisionConfig = (configData: any): DecisionConfig => {
        const decision = configData.decision || {}
        return {
          llm_provider: decision.llm_provider || 'deepseek',
          system_prompt: decision.system_prompt || '',
          strategy: decision.strategy || '',
          additional_context: decision.additional_context || ''
        }
      }
      
      const parseTradingConfig = (configData: any): TradingConfig => {
        const trading = configData.trading || {}
        return {
          exchange: trading.exchange || '',
          exchange_id: trading.exchange_id || '',
          authentication: trading.authentication || '',
          risk_rules: trading.risk_rules || {
            max_leverage: 3,
            max_position_size_pct: 0.05,
            max_risk_per_trade_pct: 0.02,
            min_equity_protection: 0.8
          }
        }
      }
      
      const extractionConfig = parseExtractionConfig(config.config_data, config)
      const decisionConfig = parseDecisionConfig(config.config_data)
      const tradingConfig = parseTradingConfig(config.config_data)
      
      set({
        currentBotId: botId,
        currentConfig: config,
        extractionConfig,
        decisionConfig,
        tradingConfig,
        agentStatuses: {
          extraction: calculateAgentStatus(extractionConfig),
          decision: calculateAgentStatus(decisionConfig),
          trading: calculateAgentStatus(tradingConfig),
        },
        isLoading: false
      })
    } catch (error) {
      console.error('Error selecting bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to select bot', isLoading: false })
    }
  },

  updateBotName: async (botId: string, name: string) => {
    console.log('Updating bot name:', botId, name)
    try {
      const state = get()
      const updatedBots = state.availableBots.map(bot =>
        bot.config_id === botId 
          ? { ...bot, config_name: name, updated_at: new Date().toISOString() }
          : bot
      )
      
      set({
        availableBots: updatedBots
      })
      
      // Update currentConfig if it's the current bot
      if (state.currentBotId === botId && state.currentConfig) {
        set({
          currentConfig: { ...state.currentConfig, config_name: name }
        })
      }
    } catch (error) {
      console.error('Error updating bot name:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to update bot name' })
    }
  },

  deleteBot: async (botId: string) => {
    console.log('Deleting bot:', botId)
    try {
      const state = get()
      const updatedBots = state.availableBots.filter(bot => bot.config_id !== botId)
      
      // If deleting current bot, switch to first available or create default
      let newCurrentBotId = state.currentBotId
      
      if (state.currentBotId === botId) {
        if (updatedBots.length > 0) {
          newCurrentBotId = updatedBots[0].config_id
        } else {
          newCurrentBotId = null
        }
      }
      
      set({
        availableBots: updatedBots,
        currentBotId: newCurrentBotId,
        currentConfig: null // Clear current config
      })
      
      // Load the new bot if we switched
      if (state.currentBotId === botId && newCurrentBotId) {
        await get().selectBot(newCurrentBotId)
      }
    } catch (error) {
      console.error('Error deleting bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to delete bot' })
    }
  },

  loadCurrentConfig: async () => {
    console.log('loadCurrentConfig called - this should be handled by selectBot')
    // This function is now redundant since selectBot handles config loading
    // Keep it for compatibility but make it a no-op
    const currentBotId = get().currentBotId
    if (currentBotId) {
      await get().selectBot(currentBotId)
    }
  },

  updateAgentConfig: async (agent, config) => {
    set({ isLoading: true, error: null })
    try {
      const currentBotId = get().currentBotId
      const currentConfig = get().currentConfig
      
      if (!currentBotId || !currentConfig) {
        throw new Error('No bot selected')
      }
      
      // Check if it's the demo bot - only update local state
      if (currentBotId === DEMO_CONFIG_ID) {
        console.log(`Updating demo bot ${agent} config locally only`)
        
        // Update local state only for demo bot
        if (agent === 'extraction') {
          set({ 
            extractionConfig: config,
            agentStatuses: { ...get().agentStatuses, extraction: calculateAgentStatus(config) }
          })
        } else if (agent === 'decision') {
          set({ 
            decisionConfig: config,
            agentStatuses: { ...get().agentStatuses, decision: calculateAgentStatus(config) }
          })
        } else if (agent === 'trading') {
          set({ 
            tradingConfig: config,
            agentStatuses: { ...get().agentStatuses, trading: calculateAgentStatus(config) }
          })
        }
        
        set({ isLoading: false, isConfigModalOpen: false })
        return
      }
      
      // For real bots, merge form data back into complex JSONB structure
      const mergeConfigData = (agent: string, formConfig: any, existingConfigData: any) => {
        const updatedData = { ...existingConfigData }
        
        if (agent === 'extraction') {
          // Merge extraction form data into complex structure
          updatedData.extraction = {
            ...updatedData.extraction,
            sources: {
              ...updatedData.extraction?.sources,
              crypto_indicators_mcp: {
                ...updatedData.extraction?.sources?.crypto_indicators_mcp,
                enabled: formConfig.sources.crypto_indicators_mcp.enabled,
                indicators: formConfig.sources.crypto_indicators_mcp.indicators
              },
              telegram: {
                ...updatedData.extraction?.sources?.telegram,
                enabled: formConfig.sources.ggshot?.enabled || false
              }
            }
          }
        } else if (agent === 'decision') {
          updatedData.decision = {
            ...updatedData.decision,
            llm_provider: formConfig.llm_provider,
            system_prompt: formConfig.system_prompt,
            strategy: formConfig.strategy,
            additional_context: formConfig.additional_context
          }
        } else if (agent === 'trading') {
          updatedData.trading = {
            ...updatedData.trading,
            exchange: formConfig.exchange,
            exchange_id: formConfig.exchange_id,
            authentication: formConfig.authentication,
            risk_rules: formConfig.risk_rules
          }
        }
        
        return updatedData
      }
      
      const updatedConfigData = mergeConfigData(agent, config, currentConfig.config_data)
      
      // Save to API using unified config endpoint
      await api.updateUnifiedConfig(currentBotId, { config_data: updatedConfigData })
      console.log(`Successfully saved ${agent} config to API for bot ${currentBotId}`)
      
      // Update local state
      const updatedConfig = {
        ...currentConfig,
        config_data: updatedConfigData,
        updated_at: new Date().toISOString()
      }
      
      if (agent === 'extraction') {
        set({ 
          currentConfig: updatedConfig,
          extractionConfig: config,
          agentStatuses: { ...get().agentStatuses, extraction: calculateAgentStatus(config) }
        })
      } else if (agent === 'decision') {
        set({ 
          currentConfig: updatedConfig,
          decisionConfig: config,
          agentStatuses: { ...get().agentStatuses, decision: calculateAgentStatus(config) }
        })
      } else if (agent === 'trading') {
        set({ 
          currentConfig: updatedConfig,
          tradingConfig: config,
          agentStatuses: { ...get().agentStatuses, trading: calculateAgentStatus(config) }
        })
      }
      
      set({ isLoading: false, isConfigModalOpen: false })
    } catch (error) {
      console.error(`Error updating ${agent} config:`, error)
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update configuration',
        isLoading: false 
      })
    }
  },

  loadTrades: async () => {
    console.log('Loading trades...')
    try {
      const currentBotId = get().currentBotId
      
      if (!currentBotId) {
        set({ trades: [] })
        return
      }
      
      // Try to load from API first
      try {
        const result = await api.getTrades(currentBotId)
        console.log('Trades loaded from API for config:', currentBotId)
        
        // Convert backend trade format to frontend format if needed
        const trades = result.trades || []
        set({ trades })
      } catch (apiError) {
        console.warn('API trades request failed, using fallback for demo:', apiError)
        
        // Only use mock data for demo bot when API fails
        if (currentBotId === DEMO_CONFIG_ID) {
          const mockTrades: Trade[] = [
            {
              id: '1',
              symbol: 'BTCUSD',
              side: 'long',
              entry_price: 94500,
              current_price: 96100,
              quantity: 0.05,
              pnl: 80,
              pnl_percentage: 1.69,
              status: 'open',
              created_at: new Date(Date.now() - 14400000).toISOString(),
              updated_at: new Date(Date.now() - 1800000).toISOString(),
              decision_reasoning: 'Strong bullish momentum with volume confirmation'
            },
            {
              id: '2', 
              symbol: 'ETHUSD',
              side: 'long',
              entry_price: 3420,
              current_price: 3489,
              quantity: 0.8,
              pnl: 55.2,
              pnl_percentage: 2.02,
              status: 'open',
              created_at: new Date(Date.now() - 7200000).toISOString(),
              updated_at: new Date(Date.now() - 900000).toISOString(),
              decision_reasoning: 'ETH breaking key resistance with strong volume'
            }
          ]
          console.log('Using demo bot mock trades data')
          set({ trades: mockTrades })
        } else {
          // Empty trades for real bots with API errors
          set({ trades: [] })
        }
      }
    } catch (error) {
      console.error('Error loading trades:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to load trades' })
    }
  },

  loadPerformance: async (period = '7d') => {
    console.log('Loading performance data for period:', period)
    try {
      const currentBotId = get().currentBotId
      
      if (!currentBotId) {
        set({ performance: null })
        return
      }
      
      // Try to load from API first
      try {
        const result = await api.getPerformance(period, currentBotId)
        console.log('Performance data loaded from API for config:', currentBotId)
        
        // Convert backend format to frontend format
        const performance: PerformanceData = {
          period,
          total_pnl: result.total_pnl || 0,
          total_pnl_percentage: (result as any).total_pnl_pct || 0,
          win_rate: result.win_rate || 0,
          total_trades: (result as any).trade_count || 0,
          daily_pnl: [] // Backend doesn't provide daily breakdown yet
        }
        
        set({ performance })
      } catch (apiError) {
        console.warn('API performance request failed, using fallback for demo:', apiError)
        
        // Only use mock data for demo bot when API fails
        if (currentBotId === DEMO_CONFIG_ID) {
          const generateDailyPnL = () => {
            const data = []
            const today = new Date()
            
            for (let i = 29; i >= 0; i--) {
              const date = new Date(today)
              date.setDate(date.getDate() - i)
              const dayPnL = Math.random() * 200 - 50 + (29 - i) * 5
              
              data.push({
                date: date.toISOString().split('T')[0],
                pnl: Math.round(dayPnL * 100) / 100
              })
            }
            return data
          }

          const mockPerformance: PerformanceData = {
            period,
            total_pnl: 3847.25,
            total_pnl_percentage: 38.47,
            win_rate: 0.75,
            total_trades: 42,
            daily_pnl: generateDailyPnL()
          }
          set({ performance: mockPerformance })
        } else {
          // Empty performance for real bots with API errors
          const emptyPerformance: PerformanceData = {
            period,
            total_pnl: 0,
            total_pnl_percentage: 0,
            win_rate: 0,
            total_trades: 0,
            daily_pnl: []
          }
          set({ performance: emptyPerformance })
        }
      }
    } catch (error) {
      console.error('Error loading performance:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to load performance' })
    }
  },

  startScheduler: async () => {
    set({ isLoading: true, error: null })
    try {
      // Mock start scheduler
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API delay
      set({ 
        schedulerStatus: { is_running: true },
        isLoading: false 
      })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to start scheduler',
        isLoading: false 
      })
    }
  },

  stopScheduler: async () => {
    set({ isLoading: true, error: null })
    try {
      // Mock stop scheduler
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API delay
      set({ 
        schedulerStatus: { is_running: false },
        isLoading: false 
      })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to stop scheduler',
        isLoading: false 
      })
    }
  },

  checkSchedulerStatus: async () => {
    console.log('Checking scheduler status...')
    try {
      // Try to get real status first, fall back to mock
      const isConnected = await api.testConnection()
      
      if (isConnected) {
        try {
          const result = await api.getSchedulerStatus()
          console.log('Scheduler status loaded from API:', result)
          set({ schedulerStatus: result })
          return
        } catch (apiError) {
          console.warn('API scheduler status request failed, using mock data:', apiError)
        }
      }

      // Mock scheduler status as fallback
      const mockStatus: SchedulerStatus = {
        is_running: false
      }
      console.log('Using mock scheduler status')
      set({ schedulerStatus: mockStatus })
    } catch (error) {
      console.error('Error checking scheduler status:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to check scheduler status' })
    }
  },

  openConfigModal: (agent) => {
    set({ isConfigModalOpen: true, activeConfigAgent: agent })
  },

  closeConfigModal: () => {
    set({ isConfigModalOpen: false, activeConfigAgent: null })
  },

  setError: (error) => {
    set({ error })
  },
}))