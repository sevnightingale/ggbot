'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'

export default function TestPage() {
  const [user, setUser] = useState<any>(null)
  const [token, setToken] = useState<string>('')
  const [results, setResults] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)

  const supabase = createClient()

  // Get current auth state
  useEffect(() => {
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        setUser(session.user)
        setToken(session.access_token)
      }
    }
    getSession()
  }, [supabase.auth])

  // Test configuration payloads based on template_v1.json
  const testConfigPayload = {
    config_name: "Test Bot - API Validation",
    selected_pair: "BTC/USDT",
    extraction: {
      data_sources: {
        technical_indicators: [
          "RSI_15m", "MACD_15m", "BB_15m", "EMA_1h", "SMA_4h"
        ],
        fundamental_analysis: [],
        sentiment_and_trends: [],
        influencer_kol: [],
        news_and_regulations: [],
        onchain_analytics: []
      }
    },
    decision: {
      analysis_frequency: "15m",
      system_prompt: "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.",
      user_prompt: "My trading strategy:\nEnter when RSI is oversold below 30 and MACD shows bullish crossover. Avoid during high volatility periods.\n\nCurrent market analysis:\n{MARKET_DATA}\n\nDecision: Based on the above data, should I ENTER, WAIT, or EXIT this position?"
    },
    trading: {
      execution_mode: "paper",
      leverage: 1,
      position_sizing: {
        method: "fixed_amount_usd",
        fixed_amount_usd: 50,
        account_percent: 5.0,
        max_position_percent: 10.0
      },
      risk_management: {
        max_positions: 3,
        default_stop_loss_percent: 2.0,
        default_take_profit_percent: 4.0,
        max_daily_loss_usd: 200
      },
      exchange_config: {
        exchange_type: "cex",
        selected_exchange: "binance",
        api_key: "",
        secret_key: ""
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
        message_template: "🔥 {ACTION} {SYMBOL} - Confidence: {CONFIDENCE}\\n{REASONING}"
      }
    }
  }

  // API call helper with auth
  const apiCall = async (method: string, endpoint: string, body?: unknown) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      ...(body && { body: JSON.stringify(body) })
    })

    const data = await response.json()
    return { status: response.status, data }
  }

  // Test functions
  const runTest = async (testName: string, testFn: () => Promise<unknown>) => {
    setLoading(true)
    try {
      const result = await testFn()
      setResults(prev => ({
        ...prev,
        [testName]: { success: true, ...result }
      }))
    } catch (error) {
      setResults(prev => ({
        ...prev,
        [testName]: { success: false, error: error.message }
      }))
    }
    setLoading(false)
  }

  // Individual test functions
  const testListConfigs = () => apiCall('GET', '/api/v2/config')
  const testCreateConfig = () => apiCall('POST', '/api/v2/config', testConfigPayload)
  const testGetUserProfile = () => apiCall('GET', '/api/v2/user/profile')
  const testGetDataSources = () => apiCall('GET', '/api/v2/data-sources-with-points')
  
  // Advanced tests with config ID (to be used later)
  // const testWithConfigId = async (configId: string) => ({
  //   getConfig: await apiCall('GET', `/api/v2/config/${configId}`),
  //   orchestrate: await apiCall('POST', `/api/v2/orchestrate/${configId}`),
  //   metrics: await apiCall('GET', `/api/v2/bot/${configId}/metrics`),
  //   positions: await apiCall('GET', `/api/v2/bot/${configId}/positions`),
  //   trades: await apiCall('GET', `/api/v2/bot/${configId}/trades`),
  //   startBot: await apiCall('POST', `/api/v2/bot/${configId}/start`),
  //   stopBot: await apiCall('POST', `/api/v2/bot/${configId}/stop`),
  //   status: await apiCall('GET', `/api/v2/bot/${configId}/status`)
  // })

  // Auth status component
  const AuthStatus = () => (
    <div className="bg-gray-50 p-4 rounded">
      <h3 className="font-bold">Auth Status</h3>
      {user ? (
        <div>
          <p>✅ Logged in as: {user.email}</p>
          <p>🔑 User ID: {user.id}</p>
          <p>📝 Token: {token ? 'Present' : 'Missing'}</p>
        </div>
      ) : (
        <p>❌ Not logged in</p>
      )}
    </div>
  )

  // Results display component
  const ResultDisplay = ({ testName, result }: { testName: string; result: any }) => (
    <div className="border p-4 rounded mb-4">
      <h4 className="font-bold">{testName}</h4>
      {result.success ? (
        <div>
          <p className="text-green-600">✅ Status: {result.status}</p>
          <details>
            <summary>View Response</summary>
            <pre className="bg-gray-100 p-2 text-xs overflow-auto">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </details>
        </div>
      ) : (
        <p className="text-red-600">❌ Error: {result.error}</p>
      )}
    </div>
  )

  if (!user || !token) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-4">API Test Page</h1>
        <AuthStatus />
        <p className="mt-4">Please log in to continue testing...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">🧪 GGBot V2 API Test Suite</h1>
      
      <AuthStatus />

      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Quick Tests</h2>
        
        <div className="space-x-4 mb-8">
          <button 
            onClick={() => runTest('List Configs', testListConfigs)}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            disabled={loading}
          >
            List Configs
          </button>
          
          <button 
            onClick={() => runTest('Create Config', testCreateConfig)}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            disabled={loading}
          >
            Create Test Config
          </button>
          
          <button 
            onClick={() => runTest('User Profile', testGetUserProfile)}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
            disabled={loading}
          >
            Get Profile
          </button>
          
          <button 
            onClick={() => runTest('Data Sources', testGetDataSources)}
            className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
            disabled={loading}
          >
            Get Data Sources
          </button>
        </div>

        {Object.keys(results).length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Test Results</h2>
            {Object.entries(results).map(([testName, result]) => (
              <ResultDisplay key={testName} testName={testName} result={result} />
            ))}
          </div>
        )}

        {loading && <p>🔄 Running test...</p>}
      </div>
    </div>
  )
}