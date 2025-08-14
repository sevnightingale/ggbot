'use client'

import React from 'react'
import GGBot from '@/components/GGBot'
import BotControlModal from '@/components/BotControlModal'
import { useBotStore, Bot } from '@/store/botStore'
import { useBotWebSocket } from '@/hooks/useBotWebSocket'

// Production user ID from backend
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

export default function DemoPage() {
  const [currentBotIndex, setCurrentBotIndex] = React.useState(0)
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [selectedBot, setSelectedBot] = React.useState<Bot | null>(null)
  
  // Zustand store hooks
  const { 
    getBotsByUser, 
    updateBot,
    startBot,
    deleteBot,
    createBot,
    stopBot
  } = useBotStore()
  
  // WebSocket connection for real-time updates
  const { isConnected, isLoadingBots } = useBotWebSocket(DEMO_USER_ID)
  
  const demoBots = getBotsByUser(DEMO_USER_ID)

  // Note: Bots are now loaded automatically via useBotWebSocket hook
  // Real backend data will be fetched on component mount

  // Add virtual "create bot" state
  const isCreatingBot = currentBotIndex >= demoBots.length
  const currentBot = isCreatingBot 
    ? { 
        config_id: "create-new",
        instance_name: "new-bot",
        name: "Create New", 
        config_type: "demo" as const,
        strategy: "meanrev",
        crypto: "BTC",
        riskLevel: "medium",
        userId: DEMO_USER_ID,
        isActive: false,
        createdAt: new Date(),
        status: {
          phase: "idle" as const,
          color: "gray" as const,
          message: "Click to configure your ggbot",
          timestamp: new Date().toISOString()
        }
      }
    : demoBots[currentBotIndex]

  const handleBotClick = (bot: Bot) => {
    if (bot.name === 'Create New' || isCreatingBot) {
      // Handle creating new bot
      setSelectedBot(bot)
      setIsModalOpen(true)
      return
    }
    
    // Handle clicking existing bot - open configuration
    setSelectedBot(bot)
    setIsModalOpen(true)
  }

  const handleModalSave = async (updatedBot: Bot) => {
    try {
      if (updatedBot.config_id === 'create-new') {
        // Create new bot using Zustand action
        await createBot({
          instance_name: `${updatedBot.name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`,
          name: updatedBot.name,
          config_type: 'demo',
          strategy: updatedBot.strategy,
          crypto: updatedBot.crypto,
          riskLevel: updatedBot.riskLevel,
          userId: DEMO_USER_ID,
          isActive: false
        })
        
        // Navigate to new bot
        setCurrentBotIndex(demoBots.length)
      } else {
        // Update existing bot using Zustand action
        updateBot(updatedBot.config_id, {
          name: updatedBot.name,
          strategy: updatedBot.strategy,
          crypto: updatedBot.crypto,
          riskLevel: updatedBot.riskLevel
        })
      }
      
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to save bot:', error)
      // Error handling - could show toast notification
    }
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setSelectedBot(null)
  }

  const handleStartBot = async (config_id: string) => {
    try {
      const bot = demoBots.find(b => b.config_id === config_id)
      if (bot?.isActive) {
        await stopBot(config_id)
      } else {
        await startBot(config_id)
      }
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to toggle bot:', error)
    }
  }

  const handleDeleteBot = async (config_id: string) => {
    try {
      await deleteBot(config_id)
      
      // Adjust current index if we deleted a bot before current position
      if (currentBotIndex >= demoBots.length - 1) {
        setCurrentBotIndex(Math.max(0, demoBots.length - 2))
      }
      
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to delete bot:', error)
    }
  }

  const nextBot = () => {
    setCurrentBotIndex((prev) => prev + 1)
  }

  const prevBot = () => {
    setCurrentBotIndex((prev) => Math.max(0, prev - 1))
  }

  // Show loading state while fetching bots
  if (isLoadingBots) {
    return (
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-bone-300">Loading bots...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-900 relative">
      {/* Connection Status */}
      <div className="absolute top-4 right-4 flex items-center gap-2 z-50">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
        <span className="text-footnote text-gray-400">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* 3-Column Desktop Layout */}
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="flex w-full max-w-7xl mx-auto gap-8 items-center">
          
          {/* Left Panel - Performance */}
          <div className="hidden lg:block w-80 h-96">
            <div className="bg-charcoal-900/90 backdrop-blur-sm border border-charcoal-700/80 h-full p-6 shadow-2xl paper-texture-subtle">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-2 h-2 bg-agent-extraction rounded-full"></div>
                <h3 className="text-subheader text-bone">Performance</h3>
              </div>
              
              {/* Chart Placeholder */}
              <div className="bg-charcoal-800 border border-charcoal-600 h-48 mb-4 p-4 flex items-center justify-center">
                <div className="text-gray-500 text-footnote">📊 Chart Coming Soon</div>
              </div>
              
              {/* Key Metrics */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-footnote text-gray-400">Accuracy</span>
                  <span className="text-body text-agent-extraction font-medium">95.2%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-footnote text-gray-400">Stop Loss Rate</span>
                  <span className="text-body text-green-400 font-medium">4.8%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-footnote text-gray-400">Signals</span>
                  <span className="text-body text-bone font-medium">227</span>
                </div>
              </div>
            </div>
          </div>

          {/* Center Column - ggbot Component */}
          <div className="flex-1 flex flex-col items-center max-w-md">
            {/* ggbot with flanking arrows/plus */}
            <div className="flex items-center gap-16 mb-6">
              <button 
                className={`text-3xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  currentBotIndex === 0 
                    ? 'text-bone-500 cursor-not-allowed opacity-50' 
                    : 'text-bone-300 hover:text-bone-200 hover:scale-110'
                }`}
                onClick={prevBot}
                disabled={currentBotIndex === 0}
              >
                ‹
              </button>
              
              <GGBot
                name={currentBot.name}
                status={currentBot.status.phase}
                message={currentBot.status.message}
                showSpinner={currentBot.status.showSpinner}
                onClick={() => handleBotClick(currentBot)}
              />
              
              <button 
                className="text-3xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center text-bone-300 hover:text-bone-200 hover:scale-110"
                onClick={isCreatingBot ? () => handleBotClick(currentBot) : nextBot}
              >
                {isCreatingBot ? '○' : (currentBotIndex === demoBots.length - 1 ? '+' : '›')}
              </button>
            </div>

            {/* Dots navigation */}
            <div className="flex justify-center">
              <div className="flex items-center gap-3">
                {demoBots.map((_, index) => (
                  <button
                    key={index}
                    className={`w-3 h-3 rounded-full transition-all duration-200 ${
                      index === currentBotIndex
                        ? 'bg-bone-200'
                        : 'bg-bone-500 hover:bg-bone-300'
                    }`}
                    onClick={() => setCurrentBotIndex(index)}
                  />
                ))}
                {isCreatingBot && (
                  <button
                    className="w-3 h-3 rounded-full bg-bone-200 transition-all duration-200"
                    onClick={() => setCurrentBotIndex(demoBots.length)}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Right Panel - Open Trades */}
          <div className="hidden lg:block w-80 h-96">
            <div className="bg-charcoal-900/90 backdrop-blur-sm border border-charcoal-700/80 h-full p-6 shadow-2xl paper-texture-subtle">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-2 h-2 bg-agent-trading rounded-full"></div>
                <h3 className="text-subheader text-bone">Open Trades</h3>
              </div>
              
              {/* Trades List */}
              <div className="space-y-4">
                <div className="bg-charcoal-800 border border-charcoal-600 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span className="text-body text-bone font-medium">APE/USDT</span>
                    <span className="text-footnote text-gray-400">SHORT</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">52% confidence</span>
                    <span className="text-body text-red-400 font-medium">-$45.32</span>
                  </div>
                </div>
                
                <div className="bg-charcoal-800 border border-charcoal-600 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                    <span className="text-body text-bone font-medium">BTC/USDT</span>
                    <span className="text-footnote text-gray-400">LONG</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">67% confidence</span>
                    <span className="text-body text-green-400 font-medium">+$12.08</span>
                  </div>
                </div>
              </div>
              
              {/* Total P&L */}
              <div className="mt-6 pt-4 border-t border-charcoal-600">
                <div className="flex justify-between items-center">
                  <span className="text-footnote text-gray-400">Total P&L</span>
                  <span className="text-body text-red-400 font-medium">-$33.24</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bot Count Info */}
      {demoBots.length > 0 && (
        <div className="absolute bottom-4 left-4 text-footnote text-gray-400">
          Showing {demoBots.length} bot{demoBots.length !== 1 ? 's' : ''}
        </div>
      )}

      {/* Control Modal */}
      {selectedBot && (
        <BotControlModal
          bot={selectedBot}
          isOpen={isModalOpen}
          onClose={handleModalClose}
          onSave={handleModalSave}
          onStart={handleStartBot}
          onDelete={handleDeleteBot}
          mode="demo"
        />
      )}
    </div>
  )
}