'use client'

import React, { useState, useEffect } from 'react'

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

  // Simple auth check
  useEffect(() => {
    // Simulate auth for now - replace with actual auth
    setTimeout(() => {
      setUser({ id: 'user-123' })
      setLoading(false)
    }, 1000)
  }, [])

  // Load or create bot when user is ready
  useEffect(() => {
    if (!user) return

    const loadOrCreateBot = async () => {
      console.log('🔥 Loading bot for user:', user.id)
      
      // TODO: Real API call to get user's bots
      // const bots = await fetch('/api/bots').then(r => r.json())
      
      // For now, simulate auto-creation
      const defaultBot: Bot = {
        config_id: `bot-${Date.now()}`,
        name: 'Default ggbot',
        isActive: false,
        selectedPair: 'BTC/USDT',
        createdAt: new Date().toISOString()
      }
      
      console.log('🔨 Created default bot:', defaultBot)
      setBot(defaultBot)
    }

    loadOrCreateBot()
  }, [user])

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