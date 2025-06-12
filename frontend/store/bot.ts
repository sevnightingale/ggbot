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
      // Mock data for now since backend is not available
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
      // Mock trades data
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
      set({ trades: mockTrades })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load trades' })
    }
  },

  loadPerformance: async (period = '7d') => {
    try {
      // Mock performance data
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
      set({ performance: mockPerformance })
    } catch (error) {
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
    try {
      // Mock scheduler status
      const mockStatus: SchedulerStatus = {
        is_running: false
      }
      set({ schedulerStatus: mockStatus })
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