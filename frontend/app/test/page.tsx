'use client'

import { useState } from 'react'
import { PageWrapper } from '@/components/ui/PageWrapper'

interface TestResult {
  service: string
  status: 'pending' | 'success' | 'error'
  message: string
  responseTime?: number
  data?: Record<string, unknown>
}

export default function TestPage() {
  const [results, setResults] = useState<TestResult[]>([
    { service: 'Backend API', status: 'pending', message: 'Not tested' },
    { service: 'GGBot Postgres', status: 'pending', message: 'Not tested' },
    { service: 'Hummingbot Postgres', status: 'pending', message: 'Not tested' }
  ])
  const [testing, setTesting] = useState(false)

  const updateResult = (index: number, update: Partial<TestResult>) => {
    setResults(prev => prev.map((result, i) => 
      i === index ? { ...result, ...update } : result
    ))
  }

  const testConnections = async () => {
    setTesting(true)
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ggbots-api.nightingale.business'

    // Test 1: Backend API Health Check
    try {
      updateResult(0, { status: 'pending', message: 'Testing...' })
      const start = Date.now()
      const response = await fetch(`${baseUrl}/test/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      const responseTime = Date.now() - start
      const data = await response.json()
      
      if (response.ok) {
        updateResult(0, { 
          status: 'success', 
          message: 'Backend API connection successful',
          responseTime,
          data
        })
      } else {
        updateResult(0, { 
          status: 'error', 
          message: `HTTP ${response.status}: ${data.message || 'Unknown error'}`,
          responseTime
        })
      }
    } catch (error) {
      updateResult(0, { 
        status: 'error', 
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      })
    }

    // Test 2: GGBot Postgres
    try {
      updateResult(1, { status: 'pending', message: 'Testing...' })
      const start = Date.now()
      const response = await fetch(`${baseUrl}/test/ggbot-db`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      const responseTime = Date.now() - start
      const data = await response.json()
      
      if (response.ok) {
        updateResult(1, { 
          status: 'success', 
          message: 'GGBot Postgres connection successful',
          responseTime,
          data
        })
      } else {
        updateResult(1, { 
          status: 'error', 
          message: `HTTP ${response.status}: ${data.message || 'Unknown error'}`,
          responseTime
        })
      }
    } catch (error) {
      updateResult(1, { 
        status: 'error', 
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      })
    }

    // Test 3: Hummingbot Postgres
    try {
      updateResult(2, { status: 'pending', message: 'Testing...' })
      const start = Date.now()
      const response = await fetch(`${baseUrl}/test/hummingbot-db`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      const responseTime = Date.now() - start
      const data = await response.json()
      
      if (response.ok) {
        updateResult(2, { 
          status: 'success', 
          message: 'Hummingbot Postgres connection successful',
          responseTime,
          data
        })
      } else {
        updateResult(2, { 
          status: 'error', 
          message: `HTTP ${response.status}: ${data.message || 'Unknown error'}`,
          responseTime
        })
      }
    } catch (error) {
      updateResult(2, { 
        status: 'error', 
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      })
    }

    setTesting(false)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-400'
      case 'error': return 'text-red-400'
      case 'pending': return 'text-yellow-400'
      default: return 'text-bone-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✅'
      case 'error': return '❌'
      case 'pending': return '⏳'
      default: return '⚪'
    }
  }

  return (
    <PageWrapper>
      <div className="min-h-screen bg-charcoal-900 text-bone-200 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold mb-8 text-center">
            Connection Test
          </h1>
          
          <div className="mb-8 text-center">
            <p className="text-bone-200/80 mb-4">
              Testing connections from Vercel → Backend API → Databases
            </p>
            <p className="text-sm text-bone-200/60">
              API Base URL: {process.env.NEXT_PUBLIC_API_URL || 'https://ggbots-api.nightingale.business'}
            </p>
            <p className="text-xs text-bone-200/40 mt-2">
              Note: Frontend connects to HTTPS API, which then tests local database connections
            </p>
          </div>

          <div className="mb-8 text-center">
            <button
              onClick={testConnections}
              disabled={testing}
              className="bg-bone-200 text-charcoal-900 px-8 py-3 font-bold hover:bg-bone-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {testing ? 'Testing...' : 'Run Connection Tests'}
            </button>
          </div>

          <div className="space-y-6">
            {results.map((result) => (
              <div
                key={result.service}
                className="border-2 border-bone-200/20 p-6 bg-bone-200/5"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold">
                    {getStatusIcon(result.status)} {result.service}
                  </h3>
                  <span className={`font-mono ${getStatusColor(result.status)}`}>
                    {result.status.toUpperCase()}
                  </span>
                </div>
                
                <p className={`mb-2 ${getStatusColor(result.status)}`}>
                  {result.message}
                </p>
                
                {result.responseTime && (
                  <p className="text-sm text-bone-200/60 mb-2">
                    Response time: {result.responseTime}ms
                  </p>
                )}
                
                {result.data && (
                  <div className="mt-4">
                    <h4 className="text-sm font-bold mb-2 text-bone-200/80">Response Data:</h4>
                    <pre className="bg-charcoal-800 p-3 text-xs overflow-x-auto border border-bone-200/10">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}