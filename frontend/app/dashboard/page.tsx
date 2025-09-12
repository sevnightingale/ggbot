'use client'

import React, { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'
import { useBotStore, Bot } from '@/store/botStore'
import { useDashboardSSE } from '@/hooks/useDashboardSSE'
import { useBotStatus } from './hooks/useBotStatus'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api'
import type { User } from '@supabase/supabase-js'

// Local components
import GGBot from './components/GGBot'
import GGBotConfig from './components/GGBotConfig'
import FloatingActionButtons from './components/FloatingActionButtons'
import PerformancePanel from './components/PerformancePanel'
import ActivityPanel from './components/ActivityPanel'

export default function DashboardV2Page() {
  // Authentication (matching old dashboard)
  const supabase = createClient()
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isLoadingAuth, setIsLoadingAuth] = useState(true)

  // Bot store and state
  const { 
    getBotsByUser,
    getBotById,
    startBot,
    stopBot,
    deleteBot,
    loadBots
  } = useBotStore()
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
  const [isConfigOpen, setIsConfigOpen] = useState(false)
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null)

  // Get current user from Supabase (matching old dashboard)
  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
      setIsLoadingAuth(false)
    }
    getUser()
  }, [supabase.auth])

  const userId = user?.id

  // Load bots from V2 API on mount (matching old dashboard pattern)
  useEffect(() => {
    if (userId) {
      console.log('📡 Dashboard V2 loading bots for userId:', userId)
      loadBots(userId)
    }
  }, [userId, loadBots])

  // Get user's bots directly from store (reactive to store changes)
  const userBots = userId ? getBotsByUser(userId) : []

  // 🔥 SSE connection for real-time updates (replaces WebSocket!)
  const { isConnected: isSSEConnected, isLoading: isLoadingBots } = useDashboardSSE(userId)

  // Auto-select first bot if none selected and bots exist
  useEffect(() => {
    if (!selectedConfigId && userBots.length > 0) {
      setSelectedConfigId(userBots[0].config_id)
    }
  }, [selectedConfigId, userBots])

  // Get current bot data
  const currentBot = selectedConfigId ? getBotById(selectedConfigId) : userBots[0] || null
  
  // Get unified bot status using our corrected hook
  const botStatus = useBotStatus(currentBot || null)

  // Logout handler
  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/login')
    } catch (error) {
      console.error('Error logging out:', error)
    }
  }

  // Bot navigation functions
  const nextBot = () => {
    if (userBots.length === 0) return
    const currentIndex = selectedConfigId ? userBots.findIndex(b => b.config_id === selectedConfigId) : -1
    const nextIndex = currentIndex < userBots.length - 1 ? currentIndex + 1 : 0
    setSelectedConfigId(userBots[nextIndex].config_id)
  }

  const prevBot = () => {
    if (userBots.length === 0) return
    const currentIndex = selectedConfigId ? userBots.findIndex(b => b.config_id === selectedConfigId) : -1
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : userBots.length - 1
    setSelectedConfigId(userBots[prevIndex].config_id)
  }

  // Bot action handlers
  const handleBotClick = (bot: Bot) => {
    setSelectedBot(bot)
    setIsConfigOpen(true)
  }

  const handleConfigClose = () => {
    setIsConfigOpen(false)
    setSelectedBot(null)
  }

  const handleConfigSaved = (configId: string) => {
    if (userId) {
      loadBots(userId)
    }
    setSelectedConfigId(configId)
  }

  const handleFloatingStart = async (config_id: string) => {
    try {
      const bot = userBots.find(b => b.config_id === config_id)
      if (!bot) return

      if (bot.isActive) {
        await stopBot(config_id)
      } else {
        await startBot(config_id)
      }
    } catch (error) {
      console.error('Failed to toggle bot:', error)
    }
  }

  const handleDeleteBot = async (config_id: string) => {
    try {
      await deleteBot(config_id)
      
      // If we deleted the selected bot, select another one
      if (selectedConfigId === config_id) {
        const remainingBots = userBots.filter(b => b.config_id !== config_id)
        if (remainingBots.length > 0) {
          setSelectedConfigId(remainingBots[0].config_id)
        } else {
          setSelectedConfigId(null)
        }
      }
    } catch (error) {
      console.error('Failed to delete bot:', error)
    }
  }

  const handleManualTrigger = async (config_id: string) => {
    try {
      console.log('🔥 Manual trigger started for bot:', config_id)
      console.log('🔌 SSE connected:', isSSEConnected)
      console.log('👤 User ID for SSE:', userId)
      
      // Use same authentication method as startBot/stopBot
      const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      console.log(`📡 POST ${apiUrl}/api/v2/orchestrate/${config_id}`)
      
      const response = await apiClient.authenticatedFetch(`${apiUrl}/api/v2/orchestrate/${config_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      console.log(`📡 Manual trigger response:`, response.status, response.statusText)
      
      if (response.ok) {
        const result = await response.json()
        console.log('⚡ Manual trigger result:', result)
        console.log('⚡ Execution time:', result.execution_time_ms, 'ms')
      } else {
        const error = await response.text()
        console.error('❌ Manual trigger failed:', error)
      }
    } catch (error) {
      console.error('❌ Manual trigger error:', error)
    }
  }

  const handleAddBot = () => {
    setSelectedBot(null)
    setIsConfigOpen(true)
  }

  // Authentication guard (matching old dashboard)
  if (isLoadingAuth) {
    return (
      <div className="min-h-screen bg-charcoal-700 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-bone-300">Loading...</p>
        </div>
      </div>
    )
  }
  
  if (!user) {
    router.push('/login')
    return null
  }

  // Show loading state while fetching bots
  if (isLoadingBots) {
    return (
      <div className="min-h-screen bg-charcoal-700 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-bone-300">Loading bots...</p>
        </div>
      </div>
    )
  }

  // Show empty state if no bots (matching old dashboard)
  if (userBots.length === 0) {
    return (
      <div className="min-h-screen bg-charcoal-700 relative">
        <div className="flex items-center justify-center p-8 min-h-screen">
          <div className="flex flex-col items-center gap-4 max-w-md text-center">
            <div className="text-6xl mb-4">🤖</div>
            <h2 className="text-xl text-bone-200 mb-2">Welcome to GGBot Dashboard V2</h2>
            <p className="text-gray-400 mb-6">You don&apos;t have any bots configured yet. Create your first bot to get started with AI-powered trading.</p>
            <div className="flex gap-4 flex-col sm:flex-row">
              <button
                onClick={handleAddBot}
                className="px-6 py-3 bg-charcoal-700 text-charcoal-900 rounded-lg hover:bg-bone-300 transition-colors"
              >
                Create Your First Bot
              </button>
              <button
                onClick={handleLogout}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Sheet Config */}
        <GGBotConfig 
          bot={selectedBot}
          isOpen={isConfigOpen}
          onClose={handleConfigClose}
          onConfigSaved={handleConfigSaved}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-700 relative">
      {/* 3-Column Layout with Sharp Dividers (matching old dashboard) */}
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="w-full max-w-[1500px] mx-auto grid grid-cols-[550px_400px_550px] gap-4 relative">
          
          {/* Left Column - Performance Panel */}
          <div className="hidden lg:block">
            <PerformancePanel 
              botId={selectedConfigId} 
              className="min-h-[500px]"
            />
          </div>

          {/* Center Column - Bot Carousel (matching old dashboard layout) */}
          <div className="flex flex-col items-center justify-center">
            

            {/* GGBot with flanking arrows (matching old dashboard) */}
            <div className="flex items-center gap-10 mb-6 px-4">
              <button 
                className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  userBots.length <= 1
                    ? 'text-bone-500 cursor-not-allowed opacity-50' 
                    : 'text-bone-300 hover:text-bone-200 hover:scale-110'
                }`}
                onClick={prevBot}
                disabled={userBots.length <= 1}
              >
                ‹
              </button>
              
              <GGBot
                name={currentBot?.name || 'Bot'}
                status={botStatus.currentState}
                message={botStatus.message || ''}
                showSpinner={botStatus.showSpinner}
                onClick={() => currentBot && handleBotClick(currentBot)}
              />
              
              <button 
                className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  userBots.length <= 1
                    ? 'text-bone-500 cursor-not-allowed opacity-50' 
                    : 'text-bone-300 hover:text-bone-200 hover:scale-110'
                }`}
                onClick={nextBot}
                disabled={userBots.length <= 1}
              >
                ›
              </button>
            </div>

            {/* Dots navigation (matching old dashboard) */}
            <div className="flex justify-center mb-4">
              <div className="flex items-center gap-3">
                {userBots.map((bot) => (
                  <button
                    key={bot.config_id}
                    className={`w-3 h-3 rounded-full transition-all duration-200 ${
                      bot.config_id === selectedConfigId
                        ? 'bg-bone-200'
                        : 'bg-bone-600 hover:bg-bone-400'
                    }`}
                    onClick={() => setSelectedConfigId(bot.config_id)}
                  />
                ))}
              </div>
            </div>

            {/* Floating Action Buttons - positioned below dots */}
            <div>
              {currentBot && (
                <FloatingActionButtons 
                  currentBot={currentBot}
                  onStart={handleFloatingStart}
                  onDelete={handleDeleteBot}
                  onManualTrigger={handleManualTrigger}
                  onAdd={handleAddBot}
                />
              )}
            </div>
          </div>

          {/* Right Column - Activity Panel */}
          <div className="hidden lg:block">
            <ActivityPanel 
              botId={selectedConfigId}
              className="min-h-[500px]"
            />
          </div>
        </div>
      </div>

      {/* Bot Count Info (matching old dashboard) */}
      {userBots.length > 0 && currentBot && (
        <div className="absolute bottom-4 left-4 text-footnote text-gray-400">
          Showing {userBots.length} bot{userBots.length !== 1 ? 's' : ''} • Selected: {currentBot.name}
        </div>
      )}

      {/* Bottom Sheet Config */}
      <GGBotConfig 
        bot={selectedBot}
        isOpen={isConfigOpen}
        onClose={handleConfigClose}
        onConfigSaved={handleConfigSaved}
      />
    </div>
  )
}