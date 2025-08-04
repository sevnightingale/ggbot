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
    console.log('Loading available bots - MOCK MODE ONLY...')
    set({ isLoading: true, error: null })
    
    // PURE MOCK MODE - NO API CALLS
    const demoConfig: UnifiedConfig = {
      config_id: DEMO_CONFIG_ID,
      config_name: "Demo Bot - Showcase",
      config_type: "demo",
      user_id: api.currentUserId,
      config_data: {
        extraction: { symbols: ['BTC/USDT'], sources: { crypto_indicators_mcp: { enabled: true, indicators: [] } } },
        decision: { llm_provider: 'deepseek', system_prompt: 'Conservative trading approach with risk management', strategy: 'RSI momentum with volume confirmation', additional_context: 'Focus on major crypto pairs during high volume periods' },
        trading: { exchange: 'demo', exchange_id: '', authentication: '', risk_rules: { max_leverage: 3, max_position_size_pct: 0.05, max_risk_per_trade_pct: 0.02, min_equity_protection: 0.8 } }
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      editable: true,
      is_flagship: false,
      paper_balance: 10000
    }
    
    // Create ggShot flagship demo
    const ggShotConfig: UnifiedConfig = {
      config_id: GGSHOT_CONFIG_ID,
      config_name: "ggShot Flagship",
      config_type: "ggshot",
      user_id: api.currentUserId,
      config_data: {
        extraction: { symbols: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'], sources: { crypto_indicators_mcp: { enabled: true, indicators: ['RSI_15m', 'MACD_1h', 'BollingerBands_4h'] } } },
        decision: { llm_provider: 'gpt-4', system_prompt: 'Premium ggShot AI trading strategy with advanced risk management', strategy: 'AI-powered momentum trading with multi-timeframe analysis', additional_context: 'High-confidence signals only, institutional-grade execution' },
        trading: { exchange: 'uniswap_scroll', exchange_id: '', authentication: '', risk_rules: { max_leverage: 5, max_position_size_pct: 0.08, max_risk_per_trade_pct: 0.03, min_equity_protection: 0.75 } }
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      editable: false,
      is_flagship: true,
      paper_balance: 15000
    }
    
    const configs = [ggShotConfig, demoConfig]
    console.log('Using PURE MOCK MODE with flagship and demo bots')
    
    set({ 
      availableBots: configs,
      currentBotId: GGSHOT_CONFIG_ID,
      isLoading: false
    })
    
    // Load the ggShot config immediately
    await get().selectBot(GGSHOT_CONFIG_ID)
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
    console.log('Selecting bot - MOCK MODE:', botId)
    
    // PURE MOCK MODE - NO API CALLS
    const state = get()
    const selectedBot = state.availableBots.find(bot => bot.config_id === botId)
    
    if (selectedBot) {
      set({
        currentBotId: botId,
        currentConfig: selectedBot,
        extractionConfig: selectedBot.config_data.extraction,
        decisionConfig: selectedBot.config_data.decision,
        tradingConfig: selectedBot.config_data.trading,
        agentStatuses: {
          extraction: calculateAgentStatus(selectedBot.config_data.extraction),
          decision: calculateAgentStatus(selectedBot.config_data.decision),
          trading: calculateAgentStatus(selectedBot.config_data.trading),
        },
        isLoading: false
      })
      console.log('Bot selected instantly:', selectedBot.config_name)
    } else {
      console.error('Bot not found:', botId)
      set({ isLoading: false })
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
      
      // If deleting current bot, switch to first available  
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
        currentBotId: newCurrentBotId
      })
      
      // If we switched bots, load the new config
      if (state.currentBotId === botId && newCurrentBotId) {
        await get().selectBot(newCurrentBotId)
      }
    } catch (error) {
      console.error('Error deleting bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to delete bot' })
    }
  },

  loadCurrentConfig: async () => {
    // This method is no longer needed since selectBot handles config loading
    // Keeping for backward compatibility but making it a no-op
    console.log('loadCurrentConfig called - delegating to selectBot')
    
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
      
      // For real bots, merge with existing config and save to API
      const updatedConfigData = {
        ...currentConfig.config_data,
        [agent]: config
      }
      
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
      
      // Check if it's the demo bot - use mock data
      if (currentBotId === DEMO_CONFIG_ID) {
        console.log('Loading demo bot trading history')
        
        // Use rich mock data for demo bot
        const mockTrades: Trade[] = [
          // Active profitable trades
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
            created_at: new Date(Date.now() - 14400000).toISOString(), // 4 hours ago
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
            created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
            updated_at: new Date(Date.now() - 900000).toISOString(),
            decision_reasoning: 'ETH breaking key resistance with strong volume'
          },
          {
            id: '3',
            symbol: 'SOLUSD',
            side: 'long',
            entry_price: 185.50,
            current_price: 192.30,
            quantity: 2.5,
            pnl: 17,
            pnl_percentage: 3.67,
            status: 'open',
            created_at: new Date(Date.now() - 5400000).toISOString(), // 1.5 hours ago
            updated_at: new Date(Date.now() - 600000).toISOString(),
            decision_reasoning: 'SOL ecosystem momentum building'
          },
          // Recent closed profitable trades
          {
            id: '4',
            symbol: 'AVAXUSD',
            side: 'long',
            entry_price: 42.80,
            current_price: 44.95,
            quantity: 8.0,
            pnl: 172,
            pnl_percentage: 5.02,
            status: 'closed',
            created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
            updated_at: new Date(Date.now() - 21600000).toISOString(), // 6 hours ago
            decision_reasoning: 'AVAX subnet activity increasing significantly'
          }
        ]
        console.log('Using demo bot mock trades data')
        set({ trades: mockTrades })
      } else {
        // New bots have no trading history
        console.log('Using empty trades for new bot')
        set({ trades: [] })
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
      
      // Check if it's the demo bot - use mock data
      if (currentBotId === DEMO_CONFIG_ID) {
        console.log('Loading demo bot performance data')
        
        // Generate 30-day performance data showing steady growth
        const generateDailyPnL = () => {
          const data = []
          const today = new Date()
          
          for (let i = 29; i >= 0; i--) {
            const date = new Date(today)
            date.setDate(date.getDate() - i)
            
            // Generate realistic daily P&L with some volatility but overall upward trend
            const dayPnL = Math.random() * 200 - 50 + (29 - i) * 5 // Slight upward bias over time
            
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
        console.log('Using demo bot mock performance data')
        set({ performance: mockPerformance })
        return
      }
      
      // For real bots, load from API
      try {
        const result = await api.getPerformance(period, currentBotId)
        console.log('Performance data loaded from API for config:', currentBotId)
        set({ performance: result })
      } catch (apiError) {
        console.warn('API performance request failed:', apiError)
        // Empty performance for real bots with no data
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
    console.log('Checking scheduler status - MOCK MODE...')
    // Pure mock - no API calls
    const mockStatus: SchedulerStatus = {
      is_running: true // Show as running for demo
    }
    console.log('Using mock scheduler status (running)')
    set({ schedulerStatus: mockStatus })
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