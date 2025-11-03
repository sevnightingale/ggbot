// Bot management types
export interface Bot {
  config_id: string
  config_name: string
  created_at: string
  updated_at?: string
}

// Agent configuration types
export interface ExtractionConfig {
  symbols: string[]
  sources: {
    crypto_indicators_mcp: {
      enabled: boolean
      indicators: string[]
    }
    ggshot?: {
      enabled: boolean
    }
  }
}

export interface DecisionConfig {
  llm_provider: string
  system_prompt: string
  strategy: string
  additional_context: string
}

export interface TradingConfig {
  exchange: string
  exchange_id: string
  authentication: string
  risk_rules: {
    max_leverage: number
    max_position_size_pct: number
    max_risk_per_trade_pct: number
    min_equity_protection: number
  }
}

export interface ExecutionConfig {
  exchange: string
  exchange_id: string
  authentication: string
}

// Config type discriminator
export type ConfigType = 'scheduled_trading' | 'signal_validation' | 'agent'

// Agent strategy configuration
export interface AgentStrategy {
  content: string
  autonomously_editable: boolean
  version: number
  last_updated_at: string
  last_updated_by: 'user' | 'agent'
  performance_log: Array<Record<string, unknown>>
}

// Unified config interface matching backend response
export interface UnifiedConfig {
  config_id: string
  config_name: string
  config_type: string
  user_id: string
  config_data: {
    extraction?: ExtractionConfig       // Optional for agent configs
    decision?: DecisionConfig           // Optional for agent configs
    trading: TradingConfig
    agent_strategy?: AgentStrategy      // Only for agent configs
  }
  state: 'active' | 'inactive'  // New database field for scheduler state
  created_at: string
  updated_at: string
  editable: boolean
  is_flagship: boolean
  instance_name?: string
  hummingbot_account?: string
  paper_balance: number
}

// Trade types
export interface Trade {
  id: string
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  current_price: number
  quantity: number
  pnl: number
  pnl_percentage: number
  status: 'open' | 'closed' | 'pending'
  created_at: string
  updated_at: string
  decision_reasoning?: string
}

// Performance types
export interface PerformanceData {
  period: string
  total_pnl: number
  total_pnl_percentage: number
  win_rate: number
  total_trades: number
  daily_pnl: Array<{
    date: string
    pnl: number
  }>
}

// Scheduler types
export interface SchedulerStatus {
  is_running: boolean
  current_phase?: 'extracting' | 'deciding' | 'trading' | null  // Current execution phase
  last_run?: string
  next_run?: string
  error?: string
}

// Agent status types
export type AgentStatus = 'configured' | 'partial' | 'unconfigured'

export interface AgentInfo {
  name: string
  status: AgentStatus
  lastActivity?: string
}

// API response types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}