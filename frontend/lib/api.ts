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
    provider: string  // 'default' | 'openai' | 'deepseek' | 'anthropic' | 'xai' | 'openrouter'
    model?: string    // Model name for the provider
    reasoning_tier?: 'economy' | 'standard' | 'premium'  // Reasoning level (economy=fast/cheap, standard=balanced, premium=best)
    thinking_mode?: boolean  // DEPRECATED: Use reasoning_tier instead. Kept for backward compatibility.
    use_platform_keys: boolean
    use_own_key: boolean
    // API keys are NOT stored here - they go to user_llm_credentials table via Vault
    // We only store references to credentials when use_own_key is true
  }
  agent_strategy?: {  // Only for agent configs
    content: string
    autonomously_editable?: boolean
    version?: number
    last_updated_at?: string
    last_updated_by?: 'user' | 'agent'
    performance_log?: Array<Record<string, unknown>>
  }
  trading: {
    leverage: number
    position_sizing: {
      max_margin_percent: number
    }
    risk_management: {
      default_stop_loss_percent?: number
      default_take_profit_percent?: number
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
  trading_mode?: 'paper' | 'symphony' | 'aster' | 'hyperliquid'
  symphony_agent_id?: string
  profile_image_url?: string | null
  is_public_performance?: boolean
  first_run_used?: boolean  // Tracks if free first run has been used
  free_runs_remaining?: number  // Number of free manual "Run Once" clicks remaining (default 3)
  pause_reason?: string | null  // Reason bot was paused by system (e.g., 'prepaid_credits_exhausted')
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
  subscription_tier: 'free' | 'prepaid' | 'usage_based' | 'pro'
  subscription_status: 'active' | 'cancelled' | 'past_due'
  can_use_premium_features: boolean
  requires_own_llm_keys: boolean
  can_publish_telegram_signals: boolean
  can_use_signal_validation: boolean
  can_use_live_trading: boolean
  can_activate_bots: boolean
  can_use_agents: boolean
  paid_data_points: string[]
  // Credit-related fields
  credit_balance_usd: number | null
  has_available_credits: boolean
  // Live trading connection status
  hyperliquid_connected: boolean
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
  async createConfig(
    configName: string,
    configData: Partial<ConfigData>,
    options?: { config_type?: string; trading_mode?: string; symphony_agent_id?: string }
  ): Promise<BotConfiguration> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/config`, {
      method: 'POST',
      body: JSON.stringify({
        config_name: configName,
        ...configData,
        ...(options?.config_type && { config_type: options.config_type }),
        ...(options?.trading_mode && { trading_mode: options.trading_mode }),
        ...(options?.symphony_agent_id && { symphony_agent_id: options.symphony_agent_id })
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

  async promoteToLive(configId: string): Promise<{ status: string; live_config_id: string; version: number; message: string }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/bot/${configId}/promote-to-live`, {
      method: 'POST'
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to promote to live' }))
      throw new Error(error.detail || 'Failed to promote to live')
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

  // LLM Models Management
  async getLLMModels(): Promise<Array<{
    model_id: string
    display_name: string
    provider: string
    openrouter_model_id: string
    supports_thinking: boolean
    enabled: boolean
    max_context_tokens: number
    context_display: string
    pricing: {
      input_per_1m: number
      output_per_1m: number
    }
    cost_per_decision: {
      standard: number
      thinking: number
    }
    description: string
    sort_order: number
  }>> {
    console.log('🔍 API Call: getLLMModels to', `${this.baseUrl}/api/v2/llm-models`)

    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/llm-models`)
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        throw new Error(`Failed to load LLM models: ${error}`)
      }

      const result = await response.json()
      console.log('✅ LLM models loaded:', result)
      return result.models
    } catch (err) {
      console.error('💥 Network error:', err)
      throw err
    }
  }

  // Strategy Generation (one-shot from description)
  async generateStrategy(
    description: string,
    symbol: string = 'BTC/USDT',
    timeframe: string = '1h'
  ): Promise<{ success: boolean; user_prompt: string; error?: string }> {
    console.log('🔍 API Call: generateStrategy to', `${this.baseUrl}/api/v2/assistant/generate-strategy`)

    try {
      const response = await this.authenticatedFetch(
        `${this.baseUrl}/api/v2/assistant/generate-strategy`,
        {
          method: 'POST',
          body: JSON.stringify({ description, symbol, timeframe })
        }
      )
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        return { success: false, user_prompt: '', error: `Failed to generate strategy: ${error}` }
      }

      const result = await response.json()
      console.log('✅ Strategy generated:', result.success)
      return result
    } catch (err) {
      console.error('💥 Network error:', err)
      return { success: false, user_prompt: '', error: String(err) }
    }
  }

  // Config Creation (one-shot with extraction config)
  async createBotConfig(
    description: string,
    symbol: string = 'BTC/USDT',
    timeframe: string = '1h'
  ): Promise<{
    success: boolean
    user_prompt: string
    extraction: {
      selected_data_sources: {
        technical_analysis?: { data_points: string[]; timeframes: string[] }
        sentiment_social?: { data_points: string[]; timeframes: string[] }
        derivatives_leverage?: { data_points: string[]; timeframes: string[] }
        macro_economics?: { data_points: string[]; timeframes: string[] }
        onchain_analytics?: { data_points: string[]; timeframes: string[] }
        news_regulatory?: { data_points: string[]; timeframes: string[] }
      }
    }
    error?: string
  }> {
    console.log('🔍 API Call: createBotConfig to', `${this.baseUrl}/api/v2/assistant/create-config`)

    try {
      const response = await this.authenticatedFetch(
        `${this.baseUrl}/api/v2/assistant/create-config`,
        {
          method: 'POST',
          body: JSON.stringify({ description, symbol, timeframe })
        }
      )
      console.log('📡 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const error = await response.text()
        console.error('❌ API Error:', error)
        return { success: false, user_prompt: '', extraction: { selected_data_sources: {} }, error }
      }

      const result = await response.json()
      console.log('✅ Config created:', result.success, 'indicators:',
        result.extraction?.selected_data_sources?.technical_analysis?.data_points?.length || 0)
      return result
    } catch (err) {
      console.error('💥 Network error:', err)
      return { success: false, user_prompt: '', extraction: { selected_data_sources: {} }, error: String(err) }
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
      return result  // API now returns profile directly, not wrapped
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
    plan: 'usage' | 'monthly' | 'annual'
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

  // Credit Balance
  async getCreditBalance(): Promise<{ available_usd: number; ledger_usd: number }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/credits/balance`)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to get credit balance')
    }

    return await response.json()
  }

  // Usage Summary (for UserProfile display)
  async getUsageSummary(): Promise<{
    period: string
    usage_usd: number
    credits_usd: number | null
    net_balance_usd: number | null
    updated_at: string
    cached: boolean
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/usage/me`)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to get usage summary')
    }

    return await response.json()
  }

  // Per-Bot Usage (for ActivationBar display)
  async getConfigUsage(configId: string): Promise<{
    config_id: string
    config_name: string
    period: string
    period_usage_usd: number
    today_usage_usd: number
    total_usage_usd: number
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/usage/config/${configId}`)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to get config usage')
    }

    return await response.json()
  }

  // Purchase Credits via Stripe
  async purchaseCredits(amountCents: number): Promise<{ checkout_url: string }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/credits/purchase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: amountCents })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create credit checkout')
    }

    return await response.json()
  }

  // Purchase Credits via Crypto (NOWPayments)
  async purchaseCreditsCrypto(amountCents: number): Promise<{ invoice_url: string }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/credits/crypto-checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: amountCents })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create crypto checkout')
    }

    return await response.json()
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

  // =============================================================================
  // Arena Pledges (USX Staking on Bot Competition)
  // =============================================================================

  async recordArenaPledge(data: {
    wallet_address: string
    config_id: string
    usx_amount: string
    susx_amount?: string
    tx_hash: string
  }): Promise<{
    status: string
    pledge_id?: string
    bot_name?: string
    usx_amount?: string
    message: string
  }> {
    const response = await fetch(`${this.baseUrl}/api/v2/arena/pledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to record pledge')
    }

    return await response.json()
  }

  async getArenaPledges(): Promise<{
    status: string
    pledges: Array<{
      id: string
      config_id: string
      bot_name: string
      profile_image_url: string | null
      usx_amount: number
      susx_amount: number | null
      tx_hash: string
      pledged_at: string | null
      unstaked: boolean
    }>
    total_pledged: number
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/arena/pledges`)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to get pledges')
    }

    return await response.json()
  }

  // =============================================================================
  // Hyperliquid Live Trading Setup
  // =============================================================================

  async setupHyperliquid(apiWalletKey: string, walletAddress: string): Promise<{
    status: string
    message: string
    account_value?: number
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/hyperliquid/setup`, {
      method: 'POST',
      body: JSON.stringify({
        api_wallet_key: apiWalletKey,
        wallet_address: walletAddress,
      })
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to setup Hyperliquid')
    }

    return await response.json()
  }

  async getHyperliquidStatus(): Promise<{
    connected: boolean
    wallet_address: string | null
    account_value: number | null
    margin_used: number | null
    open_notional: number | null
    withdrawable: number | null
    positions_count: number | null
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/hyperliquid/status`)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to get Hyperliquid status')
    }

    return await response.json()
  }

  async disconnectHyperliquid(): Promise<{
    status: string
    message: string
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/hyperliquid/disconnect`, {
      method: 'POST',
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to disconnect Hyperliquid')
    }

    return await response.json()
  }

  async testHyperliquidTrade(): Promise<{
    status: string
    entry_price?: number
    close_status?: string
    error?: string
  }> {
    const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/hyperliquid/test-trade`, {
      method: 'POST',
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to execute test trade')
    }

    return await response.json()
  }
}

export const apiClient = new ApiClient()

// Helper function to create default config data structure
export function createDefaultConfigData(): ConfigData {
  return {
    schema_version: "2.2",
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
      thinking_mode: false, // Standard mode by default
      use_platform_keys: true, // Use platform-managed keys by default
      use_own_key: false
    },
    trading: {
      leverage: 5,
      position_sizing: {
        max_margin_percent: 20.0
      },
      risk_management: {
        default_stop_loss_percent: 5.0,
        default_take_profit_percent: 10.0
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