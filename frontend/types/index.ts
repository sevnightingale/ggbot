// Agent configuration types
export interface ExtractionConfig {
  symbols: string[]
  timeframes: string[]
  sources: {
    crypto_indicators_mcp?: {
      enabled: boolean
      indicators: string[]
      use_llm_selection: boolean
      llm_interpretation: boolean
      llm_model: string
    }
    tradingview?: {
      enabled: boolean
      strategy: string
    }
    yfinance?: {
      enabled: boolean
    }
    telegram?: {
      enabled: boolean
      channels: string[]
    }
    news_feed?: {
      enabled: boolean
      sources: string[]
    }
  }
}

export interface DecisionConfig {
  llm_provider: string
  strategy: string
  risk_guidelines: string
  additional_context: string
}

export interface TradingConfig {
  risk_rules: {
    max_leverage: number
    max_position_size_pct: number
    max_risk_per_trade_pct: number
    min_equity_protection: number
    max_contracts_per_trade: number
  }
}

export interface ExecutionConfig {
  exchange: string
  exchange_id: string
  authentication: string
}

export interface UserConfig {
  user_id: string
  mcp: {
    ccxt: {
      enabled: boolean
      config_path: string
      default_exchange: string
    }
    indicators: {
      enabled: boolean
      script_path: string
      exchange_name: string
    }
  }
  extraction: ExtractionConfig
  decision: DecisionConfig
  execution: ExecutionConfig
  trading: TradingConfig
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