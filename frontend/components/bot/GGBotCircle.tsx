'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Plus, Play, Square, TestTube, Edit3, Check, X } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { SchedulerStatus } from '@/types'

interface GGBotCircleProps {
  status: SchedulerStatus
}

export function GGBotCircle({ status }: GGBotCircleProps) {
  const { 
    startScheduler, 
    stopScheduler, 
    agentStatuses,
    availableBots,
    currentBotId,
    currentBotName,
    createBot,
    selectBot,
    updateBotName,
    loadBots
  } = useBotStore()
  const [currentBotIndex, setCurrentBotIndex] = useState(0)
  const [isEditingName, setIsEditingName] = useState(false)
  const [editName, setEditName] = useState(currentBotName)
  
  const isRunning = status?.is_running || false
  
  // Load bots on component mount
  useEffect(() => {
    loadBots()
  }, [loadBots])
  
  // Update edit name when current bot name changes
  useEffect(() => {
    setEditName(currentBotName)
  }, [currentBotName])
  
  // Update current bot index when current bot changes
  useEffect(() => {
    if (currentBotId && availableBots.length > 0) {
      const index = availableBots.findIndex(bot => bot.config_id === currentBotId)
      if (index !== -1) {
        setCurrentBotIndex(index)
      }
    }
  }, [currentBotId, availableBots])
  
  const totalBots = availableBots.length
  const isLastBot = currentBotIndex === totalBots - 1
  
  // Check if all agents are configured
  const allConfigured = Object.values(agentStatuses).every(status => status === 'configured')
  const canStart = allConfigured && !isRunning

  const handleLeftNav = async () => {
    if (currentBotIndex > 0) {
      const newIndex = currentBotIndex - 1
      const targetBot = availableBots[newIndex]
      if (targetBot) {
        await selectBot(targetBot.config_id)
      }
    }
  }

  const handleRightNav = async () => {
    if (isLastBot) {
      // Create new bot
      const newBotName = `BOT-${String(availableBots.length + 1).padStart(2, '0')}`
      await createBot(newBotName)
    } else {
      const newIndex = currentBotIndex + 1
      const targetBot = availableBots[newIndex]
      if (targetBot) {
        await selectBot(targetBot.config_id)
      }
    }
  }

  const handleStartStop = async () => {
    if (isRunning) {
      await stopScheduler()
    } else if (canStart) {
      await startScheduler()
    }
  }

  const handleTestRun = async () => {
    // Trigger test run (future feature)
    console.log('Test run triggered')
  }

  const handleNameEdit = () => {
    setEditName(currentBotName)
    setIsEditingName(true)
  }

  const handleNameSave = async () => {
    if (currentBotId && editName.trim()) {
      await updateBotName(currentBotId, editName.trim())
      setIsEditingName(false)
    }
  }

  const handleNameCancel = () => {
    setEditName(currentBotName)
    setIsEditingName(false)
  }

  return (
    <div className="flex flex-col items-center space-y-8">
      {/* Floating GGBot Emblem */}
      <div className="p-6 w-full max-w-4xl">
        {/* Centered Bot Emblem Section */}
        <div className="relative flex flex-col items-center space-y-4">
          {/* Carousel Navigation */}
          <div className="flex items-center justify-between w-full max-w-sm">
            {/* Left Arrow */}
            <button
              onClick={handleLeftNav}
              disabled={currentBotIndex === 0}
              className={`p-2 transition-colors ${
                currentBotIndex === 0 
                  ? 'text-bone-500/30 cursor-not-allowed' 
                  : 'text-bone-200 hover:text-bone-100'
              }`}
            >
              <ChevronLeft size={32} />
            </button>

            {/* Bot Emblem */}
            <div className="flex flex-col items-center space-y-3">
              {/* Large Circle Emblem */}
              <div 
                className="w-24 h-24 rounded-full bg-bone-200/90 border-2 border-bone-200/90 relative"
                style={{
                  backgroundImage: `
                    radial-gradient(circle at 30% 30%, rgba(227, 229, 230, 0.95) 0%, rgba(227, 229, 230, 0.85) 100%),
                    url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23161618' fill-opacity='0.05'%3E%3Ccircle cx='7' cy='7' r='1'/%3E%3Ccircle cx='53' cy='53' r='1'/%3E%3Ccircle cx='23' cy='43' r='1'/%3E%3Ccircle cx='37' cy='17' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")
                  `,
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4), inset 0 2px 10px rgba(227, 229, 230, 0.1)'
                }}
              >
                {/* Status indicator ring */}
                {isRunning && (
                  <div className="absolute inset-1 rounded-full border-2 border-bone-200/90 animate-pulse" />
                )}
              </div>

              {/* Bot Name */}
              <div className="flex items-center space-x-2">
                {isEditingName ? (
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="bg-charcoal-700 border border-bone-200/70 px-2 py-1 text-bone-200 text-sm w-24"
                      autoFocus
                    />
                    <button
                      onClick={handleNameSave}
                      className="text-bone-200 hover:text-bone-100"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      onClick={handleNameCancel}
                      className="text-red-400 hover:text-red-300"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <span className="text-bone-200 font-display font-bold">{currentBotName}</span>
                    <button
                      onClick={handleNameEdit}
                      className="text-bone-400 hover:text-bone-200"
                    >
                      <Edit3 size={14} />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Right Arrow or Plus */}
            <button
              onClick={handleRightNav}
              className="p-2 text-bone-200 hover:text-bone-100 transition-colors"
            >
              {isLastBot ? <Plus size={32} /> : <ChevronRight size={32} />}
            </button>
          </div>

          {/* Pagination Dots */}
          <div className="flex justify-center space-x-2">
            {Array.from({ length: totalBots + 1 }).map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-colors ${
                  index === currentBotIndex 
                    ? 'bg-bone-200' 
                    : index === totalBots 
                      ? 'bg-bone-500/50'
                      : 'bg-bone-500'
                }`}
              />
            ))}
          </div>
        </div>
        
        {/* Floating Action Controls */}
        <div className="relative flex justify-center space-x-12 mt-8">
          {/* Start/Stop Icon */}
          <div className="relative group">
            <button
              onClick={handleStartStop}
              disabled={!canStart && !isRunning}
              className={`p-4 rounded-full transition-all duration-300 relative ${
                isRunning
                  ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400 hover:text-red-300'
                  : canStart
                    ? 'bg-bone-200/20 hover:bg-bone-200/30 text-bone-200 hover:text-bone-100'
                    : 'bg-charcoal-700/50 text-bone-500/50 cursor-not-allowed'
              }`}
            >
              {isRunning ? <Square size={24} /> : <Play size={24} />}
            </button>
            {/* Floating Label */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
              <div className="bg-charcoal-800 border border-bone-200/60 px-2 py-1 text-xs text-bone-200 whitespace-nowrap">
                {isRunning ? 'STOP' : canStart ? 'START' : 'Configure agents first'}
              </div>
            </div>
          </div>

          {/* Test Run Icon */}
          <div className="relative group">
            <button
              onClick={handleTestRun}
              className="p-4 rounded-full bg-bone-200/20 hover:bg-bone-200/30 text-bone-200 hover:text-bone-100 transition-all duration-300"
            >
              <TestTube size={24} />
            </button>
            {/* Floating Label */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
              <div className="bg-charcoal-800 border border-bone-200/60 px-2 py-1 text-xs text-bone-200 whitespace-nowrap">
                TEST RUN
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}