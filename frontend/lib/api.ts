/**
 * Authenticated API client for GGBot backend integration with Supabase auth
 */

import { createClient } from '@/lib/supabase'

export interface ConfigData {
  schema_version: string
  config_type?: string  // 'scheduled_trading' | 'signal_validation' | 'agent'
  selected_pair: string
  extraction?: {  // Optional for agent configs
    selected_data_sources: {
      technical_analysis?: {
        data_points: string[]  // Indicator names like ["RSI", "MACD"]
        timeframes: string[]   // Always all 7: ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
      }
      signals_group_chats?: {
        data_points: string[]  // e.g., ["ggShot"]
        timeframes: string[]   // e.g., ["1h"]
      }
      fundamental_analysis?: {
        data_points: string[]
        timeframes: string[]
      }
      sentiment_and_trends?: {
        data_points: string[]
        timeframes: string[]
      }
      influencer_kol?: {
        data_points: string[]
        timeframes: string[]
      }
      news_and_regulations?: {
        data_points: string[]
        timeframes: string[]
      }
      onchain_analytics?: {
        data_points: string[]
        timeframes: string[]
      }
    }
  }
  decision?: {  // Optional for agent and signal_validation configs
    analysis_frequency: string | null  // null for signal_validation mode
    system_prompt?: string
    user_prompt?: string
  }
  llm_config?: {  // Optional for agent and signal_validation configs
    provider: string  // 'default' | 'openai' | 'deepseek' | 'anthropic' | 'xai'
    model?: string    // Model name for the provider
    use_platform_keys: boolean
    use_own_key: boolean
    // API keys are NOT stored here - they go to user_llm_credentials table via Vault
    // We only store references to credentials when use_own_key is true
  }
  agent_strategy?: {  // Only for agent configs
    content: string
    autonomously_editable: boolean
    version: number
    last_updated_at: string
    last_updated_by: 'user' | 'agent'
    performance_log: Array<Record<string, unknown>>
  }
  trading: {
    execution_mode: string
    leverage: number
    position_sizing: {
      method: string
      fixed_amount_usd?: number
      account_percent?: number
      max_position_percent?: number
    }
    risk_management: {
      max_positions: number
      default_stop_loss_percent?: number
      default_take_profit_percent?: number
      max_daily_loss_usd?: number
    }
  }
  telegram_integration: {
    listener: {
      enabled: boolean
      api_id: string
      api_hash: string
      session_name: string
      source_channels: string[]
    }
    publisher: {
      enabled: boolean
      bot_token: string
      filter_channel: string
      confidence_threshold: number
      include_reasoning: boolean
      include_market_context: boolean
      message_template: string
    }
  }
}

export interface BotConfiguration {
  config_id: string
  user_id: string
  config_name: string
  config_type: string
  config_data: ConfigData
  state: 'active' | 'inactive'
  trading_mode?: 'paper' | 'live' | 'aster'
  symphony_agent_id?: string
  created_at: string
  updated_at: string
}

export interface DataSource {
  source_id: string
  name: string
  display_name: string
  description: string
  enabled: boolean
  requires_premium: boolean
  sort_order: number
  data_points: DataPoint[]
}

export interface DataPoint {
  data_point_id: string
  name: string
  display_name: string
  description: string
  config_values?: Record<string, unknown>
  requires_premium: boolean
  enabled: boolean
  sort_order: number
  has_access: boolean
  is_locked: boolean
}

export interface UserProfile {
  user_id: string
  subscription_tier: 'free' | 'ggbase'
  subscription_status: 'active' | 'cancelled' | 'past_due'
  can_use_premium_features: boolean
  requires_own_llm_keys: boolean
  can_publish_telegram_signals: boolean
  can_use_signal_validation: boolean
  can_use_live_trading: boolean
  paid_data_points: string[]
}

export class ApiClient {
  private supabase = createClient()
  private baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
  
  async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await this.supabase.auth.getSession()
    
    if (!session?.access_token) {
      throw new Error('Not authenticated')
    }
    
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  }

  async getCurrentUserId(): Promise<string> {
    const { data: { user } } = await this.supabase.auth.getUser()
    
    if (!user) {
      throw new Error('Not authenticated')
    }
    
    return user.id
  }

  /**
   * Retry logic with exponential backoff
   * Retries up to 3 times with delays: 1s, 2s, 4s
   */
  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries = 3,
    initialDelay = 1000
  ): Promise<T> {
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error as Error

        // Don't retry on auth errors (4xx)
        if (error instanceof Error && error.message.includes('Not authenticated')) {
          throw error
        }

        // Don't retry on the last attempt
        if (attempt === maxRetries) {
          break
        }

        // Calculate delay with exponential backoff
        const delay = initialDelay * Math.pow(2, attempt)
        console.log(`🔄 Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms...`)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }

    throw lastError || new Error('Max retries exceeded')
  }

  async authenticatedFetch(url: string, options: RequestInit = {}) {
    return this.retryWithBackoff(async () => {
      const headers = await this.getAuthHeaders()

      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers
        }
      })

      return response
    })
  }

  // Configuration Management
  async createConfig(configName: string, configData: Partial<ConfigData>): Promise<BotConfiguration> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/config`, {
      method: 'POST',
      body: JSON.stringify({
        config_name: configName,
        ...configData
      })
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to create config: ${error}`)
    }

    const result = await response.json()
    return result.config
  }

  async updateConfig(configId: string, configData: Partial<ConfigData>, configName?: string, configType?: string): Promise<BotConfiguration> {
    const updateData: Record<string, unknown> = { ...configData }
    if (configName) {
      updateData.config_name = configName
    }
    if (configType) {
      updateData.config_type = configType
    }

    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/config/${configId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to update config: ${error}`)
    }

    const result = await response.json()
    return result.config
  }

  async getConfig(configId: string): Promise<BotConfiguration> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/config/${configId}`)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to load config: ${error}`)
    }

    const result = await response.json()
    return result.config
  }

  async listConfigs(): Promise<BotConfiguration[]> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/config`)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to list configs: ${error}`)
    }

    const result = await response.json()
    return result.configs
  }

  async deleteConfig(configId: string): Promise<void> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/config/${configId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to delete config: ${error}`)
    }
  }

  async resetAccount(configId: string): Promise<{ status: string; positions_closed: number; new_balance: number; message: string }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/bot/${configId}/reset-account`, {
      method: 'POST'
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to reset account: ${error}`)
    }

    return await response.json()
  }

  async closePosition(configId: string, tradeId: string): Promise<{ status: string; trade_id: string; close_price: number; realized_pnl: number; message: string }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/bot/${configId}/positions/${tradeId}/close`, {
      method: 'POST'
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to close position: ${error}`)
    }

    return await response.json()
  }

  // Data Sources Management  
  async getDataSourcesWithPoints(): Promise<DataSource[]> {
    console.log('🔍 API Call: getDataSourcesWithPoints to', `${this.baseUrl}/api/v2/data-sources-with-points`)
    
    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/data-sources-with-points`)
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        throw new Error(`Failed to load data sources: ${error}`)
      }

      const result = await response.json()
      console.log('✅ Data sources loaded:', result)
      return result.data_sources
    } catch (err) {
      console.error('💥 Network error:', err)
      throw err
    }
  }

  // User Profile Management
  async getUserProfile(): Promise<UserProfile> {
    console.log('🔍 API Call: getUserProfile to', `${this.baseUrl}/api/v2/user/profile`)
    
    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/user/profile`)
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        throw new Error(`Failed to load user profile: ${error}`)
      }

      const result = await response.json()
      console.log('✅ User profile loaded:', result)
      return result.profile
    } catch (err) {
      console.error('💥 Network error:', err)
      throw err
    }
  }

  // Bot Status Management
  async getBotStatus(configId: string): Promise<{
    status: string
    config_id: string
    bot_status: 'active' | 'inactive'
    is_scheduled: boolean
    next_run?: string
    timeframe: string
    scheduler_job_exists: boolean
  }> {
    console.log('🔍 API Call: getBotStatus to', `${this.baseUrl}/api/v2/bot/${configId}/status`)
    
    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/bot/${configId}/status`)
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        throw new Error(`Failed to get bot status: ${error}`)
      }

      const result = await response.json()
      console.log('✅ Bot status loaded:', result)
      return result
    } catch (err) {
      console.error('💥 Network error:', err)
      throw err
    }
  }

  async triggerBotManually(configId: string): Promise<{ status: string, config_id: string, execution_id?: string }> {
    console.log('🔥 API Call: triggerBotManually to', `${this.baseUrl}/api/v2/orchestrate/${configId}`)

    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/orchestrate/${configId}`, {
        method: 'POST'
      })
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        throw new Error(`Failed to trigger bot orchestration: ${error}`)
      }

      const result = await response.json()
      console.log('✅ Manual trigger result:', result)
      return result
    } catch (err) {
      console.error('💥 Network error:', err)
      throw err
    }
  }

  // LLM Credential Management
  async storeCredential(provider: string, apiKey: string): Promise<void> {
    const credentialName = `${provider}_production`
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/user/llm-credentials`, {
      method: 'POST',
      body: JSON.stringify({
        credential_name: credentialName,
        provider: provider,
        api_key: apiKey
      })
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to store credential: ${error}`)
    }
  }

  async listCredentials(): Promise<{ credential_name: string; provider: string; created_at: string }[]> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/user/llm-credentials`)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to list credentials: ${error}`)
    }

    const result = await response.json()
    return result.credentials || []
  }

  async deleteCredential(credentialName: string): Promise<void> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/user/llm-credentials/${credentialName}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to delete credential: ${error}`)
    }
  }

  async hasCredential(provider: string): Promise<boolean> {
    try {
      const credentials = await this.listCredentials()
      return credentials.some(cred => cred.provider === provider)
    } catch (error) {
      console.warn('Failed to check credential existence:', error)
      return false
    }
  }

  // Utility function to check if user can access premium features
  async canAccessDataPoint(dataPointId: string): Promise<boolean> {
    try {
      const profile = await this.getUserProfile()
      return profile.can_use_premium_features || profile.paid_data_points.includes(dataPointId)
    } catch (error) {
      console.warn('Failed to check premium access, defaulting to false:', error)
      return false
    }
  }

  // Scheduler Management
  async getSchedulerStatus(): Promise<{
    status: string
    scheduler_running: boolean
    active_jobs: Array<{
      job_id: string
      config_id: string
      timeframe: string
      next_run: string | null
      misfire_grace_time: number
    }>
    job_count: number
  }> {
    console.log('🔍 API Call: getSchedulerStatus to', `${this.baseUrl}/api/v2/scheduler/status`)

    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/scheduler/status`)
      console.log('📡 Response status:', response.status, response.statusText)
      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        throw new Error(`Failed to get scheduler status: ${error}`)
      }
      const result = await response.json()
      console.log('✅ Scheduler status loaded:', result)
      return result
    } catch (err) {
      console.error('💥 Network error:', err)
      throw err
    }
  }

  // Stripe Subscription Management
  async createCheckoutSession(params: {
    plan: 'monthly' | 'annual'
    coupon?: string
  }): Promise<{ checkout_url: string }> {
    console.log('🔍 API Call: createCheckoutSession', params)

    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })

      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.json()
        console.error('❌ Stripe API Error:', error)
        throw new Error(error.detail || 'Failed to create checkout session')
      }

      const result = await response.json()
      console.log('✅ Checkout session created:', result)
      return result
    } catch (err) {
      console.error('💥 Checkout error:', err)
      throw err
    }
  }

  async createPortalSession(): Promise<{ portal_url: string }> {
    console.log('🔍 API Call: createPortalSession')

    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/create-portal-session`, {
        method: 'POST'
      })

      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.json()
        console.error('❌ Stripe API Error:', error)
        throw new Error(error.detail || 'Failed to create billing portal session')
      }

      const result = await response.json()
      console.log('✅ Portal session created:', result)
      return result
    } catch (err) {
      console.error('💥 Portal error:', err)
      throw err
    }
  }

  // Trade History with Decisions
  async getTradeHistoryWithDecisions(configId: string, limit: number = 50): Promise<{
    status: string
    config_id: string
    trades: Array<{
      trade_id: string
      symbol: string
      side: string
      entry_price: number
      size_usd: number
      leverage: number
      realized_pnl: number
      close_reason: string
      opened_at: string | null
      closed_at: string | null
      confidence_score: number | null
      decision_id: string | null
      action: string | null
      decision_confidence: number | null
      reasoning: string | null
    }>
    total_count: number
  }> {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/v2/bot/${configId}/trade-history-with-decisions?limit=${limit}`
    )

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to get trade history: ${error}`)
    }

    return await response.json()
  }

  // Live Trade History (from Symphony)
  async getLiveTradeHistory(configId: string, limit: number = 50): Promise<{
    trades: Array<{
      trade_id: string
      symbol: string
      side: string
      entry_price: number
      size_usd: number
      leverage: number
      realized_pnl: number
      close_reason: string
      opened_at: string | null
      closed_at: string | null
    }>
    count: number
  }> {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/v2/trades/live/${configId}?limit=${limit}`
    )

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to get live trade history: ${error}`)
    }

    return await response.json()
  }

  // Confidence Analysis
  async getConfidenceAnalysis(configId: string): Promise<{
    status: string
    config_id: string
    confidence_distribution: {
      '5-35': { wins: number; losses: number }
      '35-45': { wins: number; losses: number }
      '45-55': { wins: number; losses: number }
      '55-65': { wins: number; losses: number }
      '65-95': { wins: number; losses: number }
    }
    summary_stats: {
      avg_confidence_wins: number
      avg_confidence_losses: number
      total_wins: number
      total_losses: number
    }
  }> {
    const response = await this.authenticatedFetch(
      `${this.baseUrl}/api/v2/bot/${configId}/confidence-analysis`
    )

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to get confidence analysis: ${error}`)
    }

    return await response.json()
  }
}

export const apiClient = new ApiClient()

// Helper function to create default config data structure
export function createDefaultConfigData(): ConfigData {
  return {
    schema_version: "2.1",
    config_type: "scheduled_trading", // Default to scheduled trading for all users
    selected_pair: "BTC/USDT",
    extraction: {
      selected_data_sources: {
        technical_analysis: {
          data_points: ["RSI"], // Single indicator for minimal friction
          timeframes: ["5m", "15m", "30m", "1h", "4h", "1d", "1w"] // All 7 timeframes
        },
        signals_group_chats: {
          data_points: [], // Empty by default
          timeframes: ["15m"]
        },
        fundamental_analysis: {
          data_points: [],
          timeframes: ["1d"]
        },
        sentiment_and_trends: {
          data_points: [],
          timeframes: ["1h"]
        },
        influencer_kol: {
          data_points: [],
          timeframes: ["1h"]
        },
        news_and_regulations: {
          data_points: [],
          timeframes: ["1d"]
        },
        onchain_analytics: {
          data_points: [],
          timeframes: ["1h"]
        }
      }
    },
    decision: {
      analysis_frequency: "1h",
      system_prompt: "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.",
      user_prompt: "If 1h RSI is below 40, enter long. If 1h RSI is above 60, enter short. Otherwise, wait."
    },
    llm_config: {
      provider: "default",
      model: "default", // Backend resolves to current default model
      use_platform_keys: true, // Use platform-managed keys by default
      use_own_key: false
    },
    trading: {
      execution_mode: "paper",
      leverage: 1,
      position_sizing: {
        method: "fixed_usd", // Simple fixed amount for beginners
        fixed_amount_usd: 100,
        account_percent: 5.0,
        max_position_percent: 10.0
      },
      risk_management: {
        max_positions: 1, // Conservative default
        default_stop_loss_percent: 5.0, // Wider stops for demo
        default_take_profit_percent: 10.0,
        max_daily_loss_usd: 500
      }
    },
    telegram_integration: {
      listener: {
        enabled: false,
        api_id: "",
        api_hash: "",
        session_name: "ggbot_session",
        source_channels: []
      },
      publisher: {
        enabled: false,
        bot_token: "",
        filter_channel: "",
        confidence_threshold: 0.7,
        include_reasoning: true,
        include_market_context: true,
        message_template: "🔥 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\n{REASONING}"
      }
    }
  }
}