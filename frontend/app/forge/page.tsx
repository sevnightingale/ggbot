'use client'

import React, { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'

// Simple bot type for now
interface Bot {
  config_id: string
  name: string
  isActive: boolean
  selectedPair: string
  createdAt: string
}

export default function ForgePage() {
  const [user, setUser] = useState<{ id: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [bot, setBot] = useState<Bot | null>(null)

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

  // Get auth token for API calls
  const getAuthToken = async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token
  }

  // Create default bot with RSI strategy (matches template_v1.json structure)
  const createDefaultBot = async () => {
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
          <div className="bg-charcoal-800 p-6 rounded-lg">
            <h2 className="text-xl text-bone-300 mb-4">Your ggbot</h2>
            <div className="space-y-3">
              <div>
                <span className="text-gray-400">Name: </span>
                <span className="text-bone-200">{bot.name}</span>
              </div>
              <div>
                <span className="text-gray-400">Trading Pair: </span>
                <span className="text-bone-200">{bot.selectedPair}</span>
              </div>
              <div>
                <span className="text-gray-400">Status: </span>
                <span className={bot.isActive ? 'text-green-400' : 'text-gray-400'}>
                  {bot.isActive ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Config ID: </span>
                <span className="text-bone-200 font-mono text-sm">{bot.config_id}</span>
              </div>
            </div>
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