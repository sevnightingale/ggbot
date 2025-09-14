'use client'

import React, { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'
import { apiClient, BotConfiguration } from '@/lib/api'
import { ThemeProvider } from '@/lib/theme'
import { Header } from './components/layout/Header'
import { BotRail } from './components/layout/BotRail'
import { TabNavigation } from './components/layout/TabNavigation'
import { MobileNav } from './components/layout/MobileNav'
import { EmptyState } from './components/shared/EmptyState'
import { ActivationBar } from './components/monitor/ActivationBar'
import { MetricsBar } from './components/monitor/MetricsBar'
import { DecisionFeed } from './components/monitor/DecisionFeed'
import { PositionsTable } from './components/monitor/PositionsTable'

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
}

interface Decision {
  decision_id: string
  symbol: string
  action: string
  confidence: number
  reasoning: string
  created_at: string
}

export default function ForgePage() {
  const [user, setUser] = useState<{ id: string } | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Core bot data - all local state with multi-bot support
  const [allBots, setAllBots] = useState<BotConfiguration[]>([])
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])
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

  // Get currently selected bot
  const selectedBot = selectedConfigId
    ? allBots.find(bot => bot.config_id === selectedConfigId) || null
    : null

  // Get account data for selected bot
  const selectedAccount = selectedBot
    ? accounts.find(account => account.config_id === selectedBot.config_id) || null
    : null

  // Debug MetricsBar data
  console.log('🔍 MetricsBar Debug:')
  console.log('  selectedBot?.config_id:', selectedBot?.config_id)
  console.log('  accounts array:', accounts)
  console.log('  selectedAccount:', selectedAccount)

  
  // Real-time status tracking
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'extraction' | 'decision' | 'trading'>('idle')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [nextRun, setNextRun] = useState<string | null>(null)
  const [countdown, setCountdown] = useState<string>('')

  // Tab navigation state
  const [activeTab, setActiveTab] = useState<'monitor' | 'configure'>('monitor')

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
      config_type: 'autonomous_trading',
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
        provider: 'deepseek',
        model: 'deepseek-r1',
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
    
    // No transformation needed - return directly
    return newConfig
  }

  // Load or create bot when user is ready
  useEffect(() => {
    if (!user) return

    const loadOrCreateBot = async () => {
      console.log('🔥 Loading bot for user:', user.id)
      
      try {
        // Get user's existing bots using proper API client
        const configs = await apiClient.listConfigs()
        console.log('📡 Loaded configs:', configs)
        
        if (configs.length > 0) {
          // Load all configs and select first one
          setAllBots(configs)
          setSelectedConfigId(configs[0].config_id)
        } else {
          // Create default bot
          console.log('🔨 No bots found, creating default bot')
          const newBot = await createDefaultBot()
          setAllBots([newBot])
          setSelectedConfigId(newBot.config_id)
        }
        
      } catch (error) {
        console.error('❌ Failed to load/create bot:', error)
      }
    }

    loadOrCreateBot()
  }, [user])

  // Real-time SSE connection for status updates
  useEffect(() => {
    if (!user || !selectedBot) return

    const connectSSE = async () => {
      try {
        const token = await getAuthToken()
        if (!token) return

        console.log('🔥 Connecting to forge SSE stream...')
        const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const stream = new EventSource(`${apiUrl}/api/dashboard-stream?token=${encodeURIComponent(token)}`)

        stream.onopen = () => {
          console.log('✅ Forge SSE connected')
        }

        stream.addEventListener('dashboard', (event) => {
          console.log('📨 Raw SSE message received:', event)
          try {
            const data = JSON.parse(event.data)
            console.log('📨 Parsed SSE data:', data)

            // Update bot execution status (extraction/decision/trading phases)
            if (data.bots) {
              const myBot = data.bots.find((b: { config_id: string }) => b.config_id === selectedBot.config_id)
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
              }
            }

            // Update live positions with P&L
            if (data.positions) {
              const myPositions = data.positions.filter((p: { config_id: string }) => p.config_id === selectedBot.config_id)
              setPositions(myPositions)
            }

            // Update recent decisions
            if (data.decisions) {
              const myDecisions = data.decisions.filter((d: { config_id: string }) => d.config_id === selectedBot.config_id)
              setDecisions(myDecisions.slice(0, 10)) // Keep last 10
            }

            // Update accounts data
            if (data.accounts) {
              console.log('📊 SSE received accounts:', data.accounts)
              setAccounts(data.accounts)
            } else {
              console.log('📊 SSE: no accounts in data')
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
  }, [user, selectedBot])

  // Countdown timer for next run
  useEffect(() => {
    if (!nextRun) return

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
      console.log('✅ Bot started:', result)
      
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

      const result = await response.json()
      console.log('✅ Bot stopped:', result)
      
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

  // Handler functions for ActivationBar
  const handleStart = () => {
    startBot()
  }

  const handleStop = () => {
    stopBot()
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
      <ThemeProvider>
        <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
          <div className="text-[var(--text-secondary)]">Please log in</div>
        </div>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Header />

        {/* 12-column grid container */}
        <div className="mx-auto grid max-w-7xl grid-cols-12 gap-4 px-4 py-4 min-h-[calc(100vh-64px)]">
          {/* Bot Rail */}
          <BotRail
            bots={allBots}
            selectedId={selectedConfigId}
            onSelect={setSelectedConfigId}
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
                account={selectedAccount}
                isStarting={isStarting}
                isStopping={isStopping}
                onStart={handleStart}
                onStop={handleStop}
              />
            )}

            <TabNavigation
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            <div className="flex-1 mt-4">
              {selectedBot ? (
                activeTab === 'monitor' ? (
                  <div className="space-y-4">
                    {/* MetricsBar - Professional KPI grid */}
                    <MetricsBar
                      account={selectedAccount}
                      positions={positions}
                    />

                    {/* DecisionFeed - Decision carousel */}
                    <DecisionFeed
                      decisions={decisions}
                    />

                    {/* PositionsTable - Active trades */}
                    <PositionsTable
                      positions={positions}
                    />

                    {/* Legacy MonitorContent - will be replaced progressively */}
                    <MonitorContent
                      selectedBot={selectedBot}
                      executionStatus={executionStatus}
                      statusMessage={statusMessage}
                      countdown={countdown}
                      positions={positions}
                      decisions={decisions}
                      isStarting={isStarting}
                      isStopping={isStopping}
                      onStart={handleStart}
                      onStop={handleStop}
                    />
                  </div>
                ) : (
                  <EmptyState
                    title="Configuration Editor"
                    description="Bot configuration interface coming soon"
                    icon="⚙️"
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

        <MobileNav className="md:hidden" />
      </div>
    </ThemeProvider>
  )
}

// Extract the monitor content into a separate component for cleaner code
interface MonitorContentProps {
  selectedBot: BotConfiguration
  executionStatus: 'idle' | 'extraction' | 'decision' | 'trading'
  statusMessage: string
  countdown: string
  positions: Position[]
  decisions: Decision[]
  isStarting: boolean
  isStopping: boolean
  onStart: () => void
  onStop: () => void
}

function MonitorContent({
  selectedBot,
  executionStatus,
  statusMessage,
  countdown,
  positions,
  decisions,
  isStarting,
  isStopping,
  onStart,
  onStop
}: MonitorContentProps) {
  return (
    <div className="space-y-6">
      {/* Bot Status Card */}
      <div className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl text-[var(--text-primary)]">{selectedBot.config_name}</h2>
          <div className={`px-3 py-1 rounded text-sm ${
            executionStatus === 'extraction' ? 'bg-green-500/20 text-green-400' :
            executionStatus === 'decision' ? 'bg-orange-500/20 text-orange-400' :
            executionStatus === 'trading' ? 'bg-red-500/20 text-red-400' :
            selectedBot.state === 'active' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'
          }`}>
            {executionStatus !== 'idle' ? executionStatus : (selectedBot.state === 'active' ? 'idle' : 'inactive')}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-[var(--text-muted)]">Trading Pair:</span>
            <div className="text-[var(--text-primary)]">{selectedBot.config_data.selected_pair}</div>
          </div>
          <div>
            <span className="text-[var(--text-muted)]">Status Message:</span>
            <div className="text-[var(--text-primary)]">{statusMessage || 'Ready'}</div>
          </div>
          <div>
            <span className="text-[var(--text-muted)]">Next Run:</span>
            <div className="text-[var(--text-primary)]">{countdown || 'Not scheduled'}</div>
          </div>
          <div>
            <span className="text-[var(--text-muted)]">Positions:</span>
            <div className="text-[var(--text-primary)]">{positions.length} open</div>
          </div>
        </div>

        {/* Start/Stop Controls */}
        <div className="mt-4 flex gap-3">
          {selectedBot.state === 'active' ? (
            <button
              onClick={onStop}
              disabled={isStopping}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
            >
              {isStopping ? 'Stopping...' : 'Stop Bot'}
            </button>
          ) : (
            <button
              onClick={onStart}
              disabled={isStarting}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {isStarting ? 'Starting...' : 'Start Bot'}
            </button>
          )}
        </div>
      </div>

      {/* Live Positions */}
      {positions.length > 0 && (
        <div className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
          <h3 className="text-lg text-[var(--text-primary)] mb-4">Live Positions</h3>
          <div className="space-y-2">
            {positions.map(position => (
              <div key={position.trade_id} className="flex justify-between items-center p-3 bg-[var(--bg-tertiary)] rounded">
                <div>
                  <span className="text-[var(--text-primary)]">{position.symbol}</span>
                  <span className={`ml-2 ${position.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                    {position.side.toUpperCase()}
                  </span>
                </div>
                <div className="text-right">
                  <div className={`${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl?.toFixed(2)}
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">${position.size_usd}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Decisions */}
      {decisions.length > 0 && (
        <div className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
          <h3 className="text-lg text-[var(--text-primary)] mb-4">Recent Decisions</h3>
          <div className="space-y-2">
            {decisions.slice(0, 5).map(decision => (
              <div key={decision.decision_id} className="p-3 bg-[var(--bg-tertiary)] rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className={`font-semibold ${
                    decision.action === 'enter' ? 'text-green-400' :
                    decision.action === 'exit' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {decision.action.toUpperCase()} {decision.symbol}
                  </span>
                  <span className="text-xs text-[var(--text-muted)]">
                    {Math.round(decision.confidence * 100)}% confidence
                  </span>
                </div>
                <p className="text-sm text-[var(--text-secondary)] line-clamp-2">
                  {decision.reasoning}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}