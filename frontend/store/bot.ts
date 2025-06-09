import { create } from 'zustand'
import { 
  UserConfig, 
  Trade, 
  PerformanceData, 
  SchedulerStatus,
  AgentStatus,
  ExtractionConfig,
  DecisionConfig,
  TradingConfig
} from '@/types'
import { api } from '@/lib/api/client'

interface BotState {
  // Current bot configuration
  currentBot: Partial<UserConfig> | null
  
  // Agent configurations
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
  currentBot: null,
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

  loadConfigurations: async () => {
    set({ isLoading: true, error: null })
    try {
      const [extraction, decision, trading] = await Promise.all([
        api.getConfig('extraction'),
        api.getConfig('decision'),
        api.getConfig('trading'),
      ])
      
      set({
        extractionConfig: extraction.config,
        decisionConfig: decision.config,
        tradingConfig: trading.config,
        agentStatuses: {
          extraction: calculateAgentStatus(extraction.config),
          decision: calculateAgentStatus(decision.config),
          trading: calculateAgentStatus(trading.config),
        },
        isLoading: false,
      })
    } catch (error) {
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
    try {
      const response = await api.getTrades()
      set({ trades: response.trades })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load trades' })
    }
  },

  loadPerformance: async (period = '7d') => {
    try {
      const performance = await api.getPerformance(period)
      set({ performance })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load performance' })
    }
  },

  startScheduler: async () => {
    set({ isLoading: true, error: null })
    try {
      await api.startScheduler()
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
      await api.stopScheduler()
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
    try {
      const status = await api.getSchedulerStatus()
      set({ schedulerStatus: status })
    } catch (error) {
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