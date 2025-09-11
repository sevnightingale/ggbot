'use client'

import React, { useState, useEffect } from 'react'
import { createBrowserClient } from '@/lib/supabase-client'
import { useBotStore } from '@/store/botStore'
import { useBotWebSocket } from '@/hooks/useBotWebSocket'
import { useBotStatus } from './hooks/useBotStatus'

// Local components
import GGBot from './components/GGBot'
import GGBotConfig from './components/GGBotConfig'
import FloatingActionButtons from './components/FloatingActionButtons'
import PerformancePanel from './components/PerformancePanel'
import ActivityPanel from './components/ActivityPanel'

export default function DashboardV2Page() {
  // Authentication
  const supabase = createBrowserClient()
  const [userId, setUserId] = useState<string | undefined>(undefined)

  // Bot store and state
  const { userBots, loadBots, startBot, stopBot, deleteBot, getBotById } = useBotStore()
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
  const [isConfigOpen, setIsConfigOpen] = useState(false)
  const [selectedBot, setSelectedBot] = useState<any | null>(null)

  // WebSocket connection
  const { isConnected: isWebSocketConnected } = useBotWebSocket(userId)

  // Get current bot data
  const currentBotConfig = selectedConfigId ? getBotById(selectedConfigId) : userBots[0] || null
  
  // Get unified bot status using our new hook
  const botStatus = useBotStatus(currentBotConfig)

  // Initialize user and load bots
  useEffect(() => {
    const initializeUser = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.user?.id) {
          setUserId(session.user.id)
          await loadBots(session.user.id)
        }
      } catch (error) {
        console.error('Failed to initialize user:', error)
      }
    }

    initializeUser()
  }, [supabase, loadBots])

  // Auto-select first bot when bots are loaded
  useEffect(() => {
    if (userBots.length > 0 && !selectedConfigId) {
      setSelectedConfigId(userBots[0].config_id)
    }
  }, [userBots.length, selectedConfigId])

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
  const handleBotClick = (bot: any) => {
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

  const handleAddBot = () => {
    setSelectedBot(null)
    setIsConfigOpen(true)
  }

  // Loading state
  if (!userId) {
    return (
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center">
        <div className="text-bone-200">Loading...</div>
      </div>
    )
  }

  // No bots state
  if (userBots.length === 0) {
    return (
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-bone-200 text-xl mb-4">No bots configured</div>
          <button
            onClick={handleAddBot}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded"
          >
            Create Your First Bot
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-900 p-6">
      {/* Three Column Grid Layout */}
      <div className="dashboard-grid h-full grid grid-cols-4 gap-6 max-w-7xl mx-auto">
        
        {/* Left Column - Performance Panel */}
        <div className="col-span-1">
          <React.Suspense fallback={<div>Loading performance...</div>}>
            <PerformancePanel 
              botId={selectedConfigId} 
              className="h-full"
            />
          </React.Suspense>
        </div>

        {/* Center Column - Bot Carousel */}
        <div className="col-span-2 flex flex-col items-center justify-center">
          
          {/* WebSocket Status Indicator */}
          <div className="mb-4">
            <div className={`text-sm ${isWebSocketConnected ? 'text-green-400' : 'text-red-400'}`}>
              WebSocket: {isWebSocketConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          {/* GGBot with navigation arrows */}
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
              name={currentBotConfig?.name || 'Bot'}
              status={botStatus.currentState}
              message={botStatus.message || ''}
              showSpinner={botStatus.showSpinner}
              onClick={() => currentBotConfig && handleBotClick(currentBotConfig)}
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

          {/* Dots Navigation */}
          <div className="flex justify-center mb-4">
            <div className="flex items-center gap-3">
              {userBots.map((bot) => (
                <button
                  key={bot.config_id}
                  className={`w-3 h-3 rounded-full transition-all duration-200 ${
                    bot.config_id === selectedConfigId
                      ? 'bg-bone-200'
                      : 'bg-bone-500 hover:bg-bone-300'
                  }`}
                  onClick={() => setSelectedConfigId(bot.config_id)}
                />
              ))}
            </div>
          </div>

          {/* Floating Action Buttons */}
          {currentBotConfig && (
            <FloatingActionButtons
              currentBot={currentBotConfig}
              onStart={handleFloatingStart}
              onDelete={handleDeleteBot}
              onAdd={handleAddBot}
            />
          )}
        </div>

        {/* Right Column - Activity Panel */}
        <div className="col-span-1">
          <React.Suspense fallback={<div>Loading activity...</div>}>
            <ActivityPanel 
              botId={selectedConfigId}
              className="h-full"
            />
          </React.Suspense>
        </div>
      </div>

      {/* Configuration Modal */}
      <GGBotConfig
        bot={selectedBot}
        isOpen={isConfigOpen}
        onClose={handleConfigClose}
        onConfigSaved={handleConfigSaved}
      />
    </div>
  )
}