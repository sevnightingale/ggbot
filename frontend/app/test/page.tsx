'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'

export default function TestPage() {
  const [user, setUser] = useState<{ id: string; email?: string } | null>(null)
  const [token, setToken] = useState<string>('')
  const [results, setResults] = useState<Record<string, { success: boolean; status?: number; data?: unknown; error?: string }>>({})
  const [loading, setLoading] = useState(false)
  const [sseConnected, setSseConnected] = useState(false)
  const [sseData, setSseData] = useState<Record<string, unknown> | null>(null)
  const [sseMessages, setSseMessages] = useState<string[]>([])

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
      selected_data_sources: {
        technical_analysis: {
          data_points: ["RSI", "MACD", "BB", "EMA", "SMA"],
          timeframes: ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        },
        signals_group_chats: {
          data_points: ["ggShot"],
          timeframes: ["1h"]
        }
      }
    },
    decision: {
      analysis_frequency: "15m",
      system_prompt: "You are an expert cryptocurrency trader analyzing {SYMBOL} at current price {CURRENT_PRICE}. Your analysis is based on the following market data:\n\n{MARKET_DATA}\n\nProvide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.",
      user_prompt: "My trading strategy:\nEnter when RSI is oversold below 30 and MACD shows bullish crossover. Avoid during high volatility periods.\n\nCurrent market analysis:\n{MARKET_DATA}\n\nDecision: Based on the above data, should I ENTER, WAIT, or EXIT this position?"
    },
    llm_config: {
      provider: "openai",
      use_platform_keys: true,
      openai_api_key: null,
      deepseek_api_key: null,
      anthropic_api_key: null
    },
    trading: {
      execution_mode: "paper",
      leverage: 1,
      position_sizing: {
        method: "confidence_based",
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
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    }

    if (body) {
      options.body = JSON.stringify(body)
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_V2_API_URL}${endpoint}`, options)
    const data = await response.json()
    return { status: response.status, data }
  }

  // Test functions
  const runTest = async (testName: string, testFn: () => Promise<{ status: number; data: unknown }>) => {
    setLoading(true)
    try {
      const result = await testFn()
      setResults(prev => ({
        ...prev,
        [testName]: { success: true, status: result.status, data: result.data }
      }))
    } catch (error) {
      setResults(prev => ({
        ...prev,
        [testName]: { success: false, error: (error as Error).message }
      }))
    }
    setLoading(false)
  }

  // Individual test functions
  const testListConfigs = () => apiCall('GET', '/api/v2/config')
  const testCreateConfig = () => apiCall('POST', '/api/v2/config', testConfigPayload)
  const testGetUserProfile = () => apiCall('GET', '/api/v2/user/profile')
  const testGetDataSources = () => apiCall('GET', '/api/v2/data-sources-with-points')
  
  // Signal publishing test with config selection
  const testSignalPublishing = () => {
    const configId = prompt('Enter Config ID to test signal publishing:')
    if (!configId) {
      alert('Config ID is required for signal publishing test')
      return Promise.reject(new Error('Config ID required'))
    }
    return apiCall('POST', `/api/v2/test/signal-publishing/${configId}`)
  }

  // SSE test functions
  const startSseTest = () => {
    if (sseConnected) {
      alert('SSE already connected!')
      return
    }

    setSseMessages(['🔌 Connecting to SSE dashboard stream...'])
    
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_V2_API_URL}/api/dashboard-stream?token=${encodeURIComponent(token)}`
    )

    eventSource.onopen = () => {
      setSseConnected(true)
      setSseMessages(prev => [...prev, '✅ SSE connection opened'])
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setSseData(data)
        setSseMessages(prev => [...prev, `📨 Dashboard update received: ${Object.keys(data).join(', ')}`])
      } catch {
        setSseMessages(prev => [...prev, `📨 Raw message: ${event.data}`])
      }
    }

    eventSource.addEventListener('dashboard', (event: Event) => {
      const messageEvent = event as MessageEvent
      try {
        const data = JSON.parse(messageEvent.data)
        setSseData(data)
        setSseMessages(prev => [...prev, `🏠 Dashboard event: ${(data.bots as unknown[])?.length || 0} bots, ${(data.positions as unknown[])?.length || 0} positions`])
      } catch {
        setSseMessages(prev => [...prev, `🏠 Dashboard event (raw): ${messageEvent.data}`])
      }
    })

    eventSource.addEventListener('error', (event: Event) => {
      setSseMessages(prev => [...prev, `❌ SSE error event: ${JSON.stringify(event)}`])
    })

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error)
      setSseMessages(prev => [...prev, `❌ SSE connection error occurred`])
      setSseConnected(false)
    }

    // Store reference for cleanup
    ;(window as unknown as Record<string, unknown>).testEventSource = eventSource
  }

  const stopSseTest = () => {
    const eventSource = (window as unknown as Record<string, unknown>).testEventSource as EventSource | undefined
    if (eventSource) {
      eventSource.close()
      delete (window as unknown as Record<string, unknown>).testEventSource
    }
    setSseConnected(false)
    setSseMessages(prev => [...prev, '🛑 SSE connection closed'])
  }

  const clearSseMessages = () => {
    setSseMessages([])
    setSseData(null)
  }
  
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
          <p>✅ Logged in as: {user.email || 'No email'}</p>
          <p>🔑 User ID: {user.id}</p>
          <p>📝 Token: {token ? 'Present' : 'Missing'}</p>
        </div>
      ) : (
        <p>❌ Not logged in</p>
      )}
    </div>
  )

  // Results display component
  const ResultDisplay = ({ testName, result }: { 
    testName: string; 
    result: { success: boolean; status?: number; data?: unknown; error?: string }
  }) => (
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
          
          <button 
            onClick={() => runTest('Signal Publishing', testSignalPublishing)}
            className="bg-pink-500 text-white px-4 py-2 rounded hover:bg-pink-600"
            disabled={loading}
          >
            🔔 Test Signal Publishing
          </button>
        </div>

        <div className="mb-8">
          <h3 className="text-xl font-bold mb-4">🔥 SSE Dashboard Stream Test</h3>
          <div className="space-x-4 mb-4">
            <button 
              onClick={startSseTest}
              className={`px-4 py-2 rounded ${sseConnected ? 'bg-gray-400' : 'bg-orange-500 hover:bg-orange-600'} text-white`}
              disabled={sseConnected}
            >
              {sseConnected ? '🔌 Connected' : '🚀 Start SSE Test'}
            </button>
            
            <button 
              onClick={stopSseTest}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              disabled={!sseConnected}
            >
              🛑 Stop SSE
            </button>
            
            <button 
              onClick={clearSseMessages}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              🧹 Clear Messages
            </button>
          </div>

          {sseMessages.length > 0 && (
            <div className="bg-black text-green-400 p-4 rounded mb-4 max-h-64 overflow-y-auto">
              <h4 className="font-bold mb-2">SSE Console:</h4>
              {sseMessages.map((msg, idx) => (
                <div key={idx} className="text-sm font-mono">{msg}</div>
              ))}
            </div>
          )}

          {sseData && (
            <div className="bg-blue-50 p-4 rounded">
              <h4 className="font-bold mb-2">Latest Dashboard Data:</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{(sseData.bots as unknown[])?.length || 0}</div>
                  <div className="text-sm text-gray-600">Bots</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{(sseData.positions as unknown[])?.length || 0}</div>
                  <div className="text-sm text-gray-600">Positions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{(sseData.decisions as unknown[])?.length || 0}</div>
                  <div className="text-sm text-gray-600">Decisions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{(sseData.accounts as unknown[])?.length || 0}</div>
                  <div className="text-sm text-gray-600">Accounts</div>
                </div>
              </div>
              <details>
                <summary className="cursor-pointer font-bold">View Raw Data</summary>
                <pre className="bg-gray-100 p-2 text-xs overflow-auto mt-2">
                  {JSON.stringify(sseData, null, 2)}
                </pre>
              </details>
            </div>
          )}
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