'use client'

import React, { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'

// Clean, focused types for forge
interface BotConfig {
  schema_version?: string
  config_type?: string
  selected_pair?: string
  extraction?: Record<string, unknown>
  decision?: Record<string, unknown>
  llm_config?: Record<string, unknown>
  trading?: Record<string, unknown>
}

interface Bot {
  config_id: string
  config_name: string
  config_data: BotConfig
  state: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

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
  
  // Core bot data - all local state
  const [bot, setBot] = useState<Bot | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  
  // Real-time status tracking
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'extraction' | 'decision' | 'trading'>('idle')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [nextRun, setNextRun] = useState<string | null>(null)
  const [countdown, setCountdown] = useState<string>('')

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

  // Create default bot with RSI strategy
  const createDefaultBot = async (): Promise<Bot> => {
    const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
    
    const defaultConfig = {
      config_name: 'Default ggbot',
      config_type: 'autonomous_trading',
      config_data: {
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
    }
    
    const response = await fetch(`${apiUrl}/api/v2/configurations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify(defaultConfig)
    })
    
    if (!response.ok) {
      throw new Error(`Failed to create bot: ${response.status}`)
    }
    
    const newBot = await response.json()
    console.log('🔨 Created default bot:', newBot)
    return newBot
  }

  // Load or create bot when user is ready
  useEffect(() => {
    if (!user) return

    const loadOrCreateBot = async () => {
      console.log('🔥 Loading bot for user:', user.id)
      
      try {
        // Get user's existing bots
        const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const response = await fetch(`${apiUrl}/api/v2/configurations`, {
          headers: {
            'Authorization': `Bearer ${await getAuthToken()}`
          }
        })
        
        if (!response.ok) {
          throw new Error(`Failed to load bots: ${response.status}`)
        }
        
        const bots = await response.json()
        console.log('📡 Loaded bots:', bots)
        
        if (bots.length > 0) {
          // Use first existing bot
          setBot(bots[0])
        } else {
          // Create default bot
          console.log('🔨 No bots found, creating default bot')
          const newBot = await createDefaultBot()
          setBot(newBot)
        }
        
      } catch (error) {
        console.error('❌ Failed to load/create bot:', error)
      }
    }

    loadOrCreateBot()
  }, [user])

  // Real-time SSE connection for status updates
  useEffect(() => {
    if (!user || !bot) return

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

        stream.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('📨 Forge SSE update:', data)

            // Update bot execution status (extraction/decision/trading phases)
            if (data.bots) {
              const myBot = data.bots.find((b: { config_id: string }) => b.config_id === bot.config_id)
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
              const myPositions = data.positions.filter((p: { config_id: string }) => p.config_id === bot.config_id)
              setPositions(myPositions)
            }

            // Update recent decisions
            if (data.decisions) {
              const myDecisions = data.decisions.filter((d: { config_id: string }) => d.config_id === bot.config_id)
              setDecisions(myDecisions.slice(0, 10)) // Keep last 10
            }

          } catch (error) {
            console.error('❌ Failed to parse SSE data:', error)
          }
        }

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
  }, [user, bot])

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

  // Start bot function
  const startBot = async () => {
    if (!bot) return
    setIsStarting(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      const response = await fetch(`${apiUrl}/api/v2/bot/${bot.config_id}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to start bot: ${response.status}`)
      }

      const result = await response.json()
      console.log('✅ Bot started:', result)
      
      // Update local bot state
      setBot(prev => prev ? { ...prev, state: 'active' } : null)

    } catch (error) {
      console.error('❌ Failed to start bot:', error)
    } finally {
      setIsStarting(false)
    }
  }

  // Stop bot function
  const stopBot = async () => {
    if (!bot) return
    setIsStopping(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      const response = await fetch(`${apiUrl}/api/v2/bot/${bot.config_id}/stop`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to stop bot: ${response.status}`)
      }

      const result = await response.json()
      console.log('✅ Bot stopped:', result)
      
      // Update local bot state
      setBot(prev => prev ? { ...prev, state: 'inactive' } : null)
      setExecutionStatus('idle')
      setStatusMessage('')

    } catch (error) {
      console.error('❌ Failed to stop bot:', error)
    } finally {
      setIsStopping(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-charcoal-700 flex items-center justify-center">
        <div className="text-bone-300">Loading forge...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-charcoal-700 flex items-center justify-center">
        <div className="text-bone-300">Please log in</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-700 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-bone-200 mb-8">🔥 ggbot Forge</h1>
        
        {bot ? (
          <div className="space-y-6">
            
            {/* Bot Status Card */}
            <div className="bg-charcoal-800 p-6 rounded-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl text-bone-300">{bot.config_name}</h2>
                <div className={`px-3 py-1 rounded text-sm ${
                  executionStatus === 'extraction' ? 'bg-green-500/20 text-green-400' :
                  executionStatus === 'decision' ? 'bg-orange-500/20 text-orange-400' :
                  executionStatus === 'trading' ? 'bg-red-500/20 text-red-400' :
                  bot.state === 'active' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {executionStatus !== 'idle' ? executionStatus : (bot.state === 'active' ? 'idle' : 'inactive')}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Trading Pair:</span>
                  <div className="text-bone-200">{bot.config_data?.selected_pair || 'BTC/USDT'}</div>
                </div>
                <div>
                  <span className="text-gray-400">Status Message:</span>
                  <div className="text-bone-200">{statusMessage || 'Ready'}</div>
                </div>
                <div>
                  <span className="text-gray-400">Next Run:</span>
                  <div className="text-bone-200">{countdown || 'Not scheduled'}</div>
                </div>
                <div>
                  <span className="text-gray-400">Positions:</span>
                  <div className="text-bone-200">{positions.length} open</div>
                </div>
              </div>
              
              {/* Start/Stop Controls */}
              <div className="mt-4 flex gap-3">
                {bot.state === 'active' ? (
                  <button
                    onClick={stopBot}
                    disabled={isStopping}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    {isStopping ? 'Stopping...' : 'Stop Bot'}
                  </button>
                ) : (
                  <button
                    onClick={startBot}
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
              <div className="bg-charcoal-800 p-6 rounded-lg">
                <h3 className="text-lg text-bone-300 mb-4">Live Positions</h3>
                <div className="space-y-2">
                  {positions.map(position => (
                    <div key={position.trade_id} className="flex justify-between items-center p-3 bg-charcoal-700 rounded">
                      <div>
                        <span className="text-bone-200">{position.symbol}</span>
                        <span className={`ml-2 ${position.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                          {position.side.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className={`${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl?.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-400">${position.size_usd}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Decisions */}
            {decisions.length > 0 && (
              <div className="bg-charcoal-800 p-6 rounded-lg">
                <h3 className="text-lg text-bone-300 mb-4">Recent Decisions</h3>
                <div className="space-y-2">
                  {decisions.slice(0, 5).map(decision => (
                    <div key={decision.decision_id} className="p-3 bg-charcoal-700 rounded">
                      <div className="flex justify-between items-center mb-2">
                        <span className={`font-semibold ${
                          decision.action === 'enter' ? 'text-green-400' :
                          decision.action === 'exit' ? 'text-red-400' : 'text-gray-400'
                        }`}>
                          {decision.action.toUpperCase()} {decision.symbol}
                        </span>
                        <span className="text-xs text-gray-400">
                          {Math.round(decision.confidence * 100)}% confidence
                        </span>
                      </div>
                      <p className="text-sm text-bone-400 line-clamp-2">
                        {decision.reasoning}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        ) : (
          <div className="bg-charcoal-800 p-6 rounded-lg">
            <div className="text-bone-400">Creating your ggbot...</div>
          </div>
        )}
      </div>
    </div>
  )
}