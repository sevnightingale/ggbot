import { create } from 'zustand'
import { 
  Trade, 
  PerformanceData, 
  SchedulerStatus,
  AgentStatus,
  ExtractionConfig,
  DecisionConfig,
  TradingConfig,
  Bot
} from '@/types'
import { api } from '@/lib/api/client'

interface BotState {
  // Bot management
  availableBots: Bot[]
  currentBotId: string | null
  currentBotName: string
  
  // Agent configurations (for current bot)
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
  createBot: (name: string) => Promise<void>
  selectBot: (botId: string) => Promise<void>
  updateBotName: (botId: string, name: string) => Promise<void>
  deleteBot: (botId: string) => Promise<void>
  loadConfigurations: () => Promise<void>
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

export const useBotStore = create<BotState>((set, get) => ({
  availableBots: [],
  currentBotId: null,
  currentBotName: 'GGBOT-01',
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
    try {
      // For now, create a default bot if none exist
      const state = get()
      if (state.availableBots.length === 0) {
        const defaultBot: Bot = {
          config_id: 'default-bot-id',
          config_name: 'GGBOT-01',
          created_at: new Date().toISOString()
        }
        set({ 
          availableBots: [defaultBot],
          currentBotId: defaultBot.config_id,
          currentBotName: defaultBot.config_name
        })
      }
    } catch (error) {
      console.error('Error loading bots:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to load bots' })
    }
  },

  createBot: async (name: string) => {
    console.log('Creating new bot:', name)
    try {
      // Generate a new bot ID (in real implementation, this would come from backend)
      const newBot: Bot = {
        config_id: `bot-${Date.now()}`,
        config_name: name,
        created_at: new Date().toISOString()
      }
      
      const state = get()
      set({
        availableBots: [...state.availableBots, newBot],
        currentBotId: newBot.config_id,
        currentBotName: newBot.config_name,
        // Reset configurations for new bot
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
        schedulerStatus: { is_running: false }
      })
    } catch (error) {
      console.error('Error creating bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to create bot' })
    }
  },

  selectBot: async (botId: string) => {
    console.log('Selecting bot:', botId)
    try {
      const state = get()
      const selectedBot = state.availableBots.find(bot => bot.config_id === botId)
      if (!selectedBot) {
        throw new Error('Bot not found')
      }
      
      set({
        currentBotId: botId,
        currentBotName: selectedBot.config_name,
        // Reset data for new bot
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
        schedulerStatus: { is_running: false }
      })
      
      // Load configurations for the selected bot
      await get().loadConfigurations()
    } catch (error) {
      console.error('Error selecting bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to select bot' })
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
        availableBots: updatedBots,
        currentBotName: state.currentBotId === botId ? name : state.currentBotName
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
      
      // If deleting current bot, switch to first available or create default
      let newCurrentBotId = state.currentBotId
      let newCurrentBotName = state.currentBotName
      
      if (state.currentBotId === botId) {
        if (updatedBots.length > 0) {
          newCurrentBotId = updatedBots[0].config_id
          newCurrentBotName = updatedBots[0].config_name
        } else {
          // Create a new default bot
          const defaultBot: Bot = {
            config_id: `bot-${Date.now()}`,
            config_name: 'GGBOT-01',
            created_at: new Date().toISOString()
          }
          updatedBots.push(defaultBot)
          newCurrentBotId = defaultBot.config_id
          newCurrentBotName = defaultBot.config_name
        }
      }
      
      set({
        availableBots: updatedBots,
        currentBotId: newCurrentBotId,
        currentBotName: newCurrentBotName
      })
      
      // Reload configurations if we switched bots
      if (state.currentBotId === botId) {
        await get().loadConfigurations()
      }
    } catch (error) {
      console.error('Error deleting bot:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to delete bot' })
    }
  },

  loadConfigurations: async () => {
    set({ isLoading: true, error: null })
    console.log('Starting loadConfigurations...')
    
    try {
      // First test API connection
      const isConnected = await api.testConnection()
      console.log('API connection test result:', isConnected)
      
      if (!isConnected) {
        console.log('API not available, using mock data')
        // Use mock data if API is not available
        const mockExtraction: ExtractionConfig = {
          symbols: ['BTCUSD', 'ETHUSD'],
          timeframes: ['15m', '1h'],
          sources: {
            tradingview: {
              enabled: true,
              strategy: 'momentum'
            },
            yfinance: {
              enabled: true
            }
          }
        }
        const mockDecision: DecisionConfig = {
          llm_provider: 'deepseek',
          strategy: 'momentum',
          risk_guidelines: 'Conservative risk management',
          additional_context: 'Focus on crypto trends'
        }
        const mockTrading: TradingConfig = {
          risk_rules: {
            max_leverage: 3,
            max_position_size_pct: 10,
            max_risk_per_trade_pct: 2,
            min_equity_protection: 1000,
            max_contracts_per_trade: 100
          }
        }
        
        set({
          extractionConfig: mockExtraction,
          decisionConfig: mockDecision,
          tradingConfig: mockTrading,
          agentStatuses: {
            extraction: calculateAgentStatus(mockExtraction),
            decision: calculateAgentStatus(mockDecision),
            trading: calculateAgentStatus(mockTrading),
          },
          isLoading: false,
          error: 'Backend API not available - using demo data'
        })
        return
      }

      // Try to load real configurations if API is available
      console.log('API available, attempting to load real configurations...')
      const [extractionResult, decisionResult, tradingResult] = await Promise.allSettled([
        api.getConfig('extraction'),
        api.getConfig('decision'),
        api.getConfig('trading')
      ])

      const extractionConfig = extractionResult.status === 'fulfilled' ? extractionResult.value.config as ExtractionConfig : null
      const decisionConfig = decisionResult.status === 'fulfilled' ? decisionResult.value.config as DecisionConfig : null
      const tradingConfig = tradingResult.status === 'fulfilled' ? tradingResult.value.config as TradingConfig : null

      console.log('Configuration loading results:', {
        extraction: extractionResult.status,
        decision: decisionResult.status,
        trading: tradingResult.status
      })

      set({
        extractionConfig,
        decisionConfig,
        tradingConfig,
        agentStatuses: {
          extraction: calculateAgentStatus(extractionConfig),
          decision: calculateAgentStatus(decisionConfig),
          trading: calculateAgentStatus(tradingConfig),
        },
        isLoading: false,
      })
    } catch (error) {
      console.error('Error in loadConfigurations:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Failed to load configurations',
        isLoading: false 
      })
    }
  },

  updateAgentConfig: async (agent, config) => {
    set({ isLoading: true, error: null })
    try {
      await api.updateConfig(agent, config)
      
      // Update local state
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
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update configuration',
        isLoading: false 
      })
    }
  },

  loadTrades: async () => {
    console.log('Loading trades...')
    try {
      // Try to load from API first, fall back to mock data
      const isConnected = await api.testConnection()
      
      if (isConnected) {
        try {
          const result = await api.getTrades()
          console.log('Trades loaded from API:', result.trades.length)
          set({ trades: result.trades })
          return
        } catch (apiError) {
          console.warn('API trades request failed, using mock data:', apiError)
        }
      }

      // Use mock trades data as fallback
      const mockTrades: Trade[] = [
        {
          id: '1',
          symbol: 'BTCUSD',
          side: 'long',
          entry_price: 45000,
          current_price: 45150,
          quantity: 0.1,
          pnl: 150,
          pnl_percentage: 0.33,
          status: 'closed',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          decision_reasoning: 'Strong momentum indicators'
        },
        {
          id: '2', 
          symbol: 'ETHUSD',
          side: 'short',
          entry_price: 3200,
          current_price: 3150,
          quantity: 1.0,
          pnl: 50,
          pnl_percentage: 1.56,
          status: 'open',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          updated_at: new Date(Date.now() - 1800000).toISOString(),
          decision_reasoning: 'Bearish trend detected'
        }
      ]
      console.log('Using mock trades data')
      set({ trades: mockTrades })
    } catch (error) {
      console.error('Error loading trades:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to load trades' })
    }
  },

  loadPerformance: async (period = '7d') => {
    console.log('Loading performance data for period:', period)
    try {
      // Try to load from API first, fall back to mock data
      const isConnected = await api.testConnection()
      
      if (isConnected) {
        try {
          const result = await api.getPerformance(period)
          console.log('Performance data loaded from API')
          set({ performance: result })
          return
        } catch (apiError) {
          console.warn('API performance request failed, using mock data:', apiError)
        }
      }

      // Mock performance data as fallback
      const mockPerformance: PerformanceData = {
        period,
        total_pnl: 1250.50,
        total_pnl_percentage: 12.5,
        win_rate: 0.68,
        total_trades: 15,
        daily_pnl: [
          { date: '2024-01-01', pnl: 100 },
          { date: '2024-01-02', pnl: 250 },
          { date: '2024-01-03', pnl: -50 },
          { date: '2024-01-04', pnl: 300 },
          { date: '2024-01-05', pnl: 150 },
          { date: '2024-01-06', pnl: 200 },
          { date: '2024-01-07', pnl: 300 }
        ]
      }
      console.log('Using mock performance data')
      set({ performance: mockPerformance })
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