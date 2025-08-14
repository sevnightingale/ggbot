'use client'

import React, { useEffect } from 'react'
import GGBot from '@/components/GGBot'
import BotControlModal from '@/components/BotControlModal'
import { useBotStore, Bot } from '@/store/botStore'

// Demo user ID constant
const DEMO_USER_ID = "demo-user-123"

export default function DemoPage() {
  const [currentBotIndex, setCurrentBotIndex] = React.useState(0)
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [selectedBot, setSelectedBot] = React.useState<Bot | null>(null)
  
  // Zustand store hooks
  const { 
    getBotsByUser, 
    addBot, 
    updateBot,
    startBot,
    deleteBot,
    createBot
  } = useBotStore()
  
  const demoBots = getBotsByUser(DEMO_USER_ID)

  // Initialize demo bots on component mount
  useEffect(() => {
    // Only initialize if no bots exist for this user
    if (demoBots.length === 0) {
      const initialBots: Bot[] = [
        {
          config_id: "e249bb49-0455-4596-9657-09bf9e14ca14", // Real ggShot config_id from CONTEXT.md
          instance_name: "ggshot-pro-1",
          name: "ggShot-Pro",
          config_type: "ggshot",
          strategy: "ai",
          crypto: "BTC",
          riskLevel: "medium",
          userId: DEMO_USER_ID,
          isActive: true,
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
          status: {
            phase: "idle",
            color: "blue",
            message: "Monitoring 140+ crypto pairs...",
            timestamp: new Date().toISOString()
          }
        },
        {
          config_id: "demo-config-001", // Demo config from CONTEXT.md
          instance_name: "mytrader-1", 
          name: "MyTrader",
          config_type: "demo",
          strategy: "meanrev",
          crypto: "BTC",
          riskLevel: "medium",
          userId: DEMO_USER_ID,
          isActive: true,
          createdAt: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
          status: {
            phase: "extraction",
            color: "blue",
            message: "Fetching BTC market data...",
            timestamp: new Date().toISOString(),
            showSpinner: true
          }
        },
        {
          config_id: "demo-config-002",
          instance_name: "testbot-1",
          name: "TestBot", 
          config_type: "demo",
          strategy: "momentum",
          crypto: "ETH",
          riskLevel: "high",
          userId: DEMO_USER_ID,
          isActive: true,
          createdAt: new Date(Date.now() - 10 * 60 * 1000), // 10 minutes ago
          status: {
            phase: "decision",
            color: "green",
            message: "AI analyzing RSI signals...",
            timestamp: new Date().toISOString(),
            showSpinner: true
          }
        }
      ]

      // Add all initial bots to store
      initialBots.forEach(bot => addBot(bot))
    }
  }, [demoBots.length, addBot])

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
      await startBot(config_id)
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to start bot:', error)
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

  return (
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
      <div className="flex flex-col items-center">
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