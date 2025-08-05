'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Plus, Play, Square, TestTube, Edit3, Check, X, Trash2, Crown } from 'lucide-react'
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
    currentConfig,
    createBot,
    selectBot,
    updateBotName,
    deleteBot,
    loadBots
  } = useBotStore()
  const [currentBotIndex, setCurrentBotIndex] = useState(0)
  const [isEditingName, setIsEditingName] = useState(false)
  const [editName, setEditName] = useState('')
  
  const currentBotName = currentConfig?.config_name || 'Loading...'
  const isRunning = status?.is_running || false
  
  // Remove the problematic loadBots useEffect - MainDashboard handles initial loading
  
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
      // Create new bot from RSI template
      const newBotName = `GGBOT-${String(availableBots.length + 1).padStart(2, '0')}`
      await createBot('rsi', newBotName)
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

  const handleDelete = async () => {
    if (currentBotId && availableBots.length > 1) {
      await deleteBot(currentBotId)
    }
  }

  return (
    <div className="flex flex-col items-center space-y-8">
      {/* Floating GGBot Emblem */}
      <div className="p-6 w-full max-w-4xl">
        {/* Centered Bot Emblem Section */}
        <div className="relative flex flex-col items-center space-y-4">
          {/* Carousel Navigation */}
          <div className="flex items-center justify-between w-full max-w-lg">
            {/* Left Arrow */}
            <div className="flex items-center justify-center w-16 h-32">
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
            </div>

            {/* Bot Emblem */}
            <div className="flex flex-col items-center">
              {/* Large Circle Emblem */}
              <div 
                className={`w-32 h-32 rounded-full bg-bone-200/90 border-2 border-bone-200/90 relative flex items-center justify-center transition-all duration-300 ${
                  isRunning ? 'animate-pulse' : ''
                }`}
                style={{
                  backgroundImage: `
                    radial-gradient(circle at 30% 30%, rgba(227, 229, 230, 0.95) 0%, rgba(227, 229, 230, 0.85) 100%),
                    url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23161618' fill-opacity='0.05'%3E%3Ccircle cx='7' cy='7' r='1'/%3E%3Ccircle cx='53' cy='53' r='1'/%3E%3Ccircle cx='23' cy='43' r='1'/%3E%3Ccircle cx='37' cy='17' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")
                  `,
                  boxShadow: isRunning 
                    ? '0 4px 20px rgba(0, 0, 0, 0.4), inset 0 2px 10px rgba(227, 229, 230, 0.1), 0 0 30px rgba(44, 190, 119, 0.6), 0 0 60px rgba(44, 190, 119, 0.3)'
                    : '0 4px 20px rgba(0, 0, 0, 0.4), inset 0 2px 10px rgba(227, 229, 230, 0.1)'
                }}
              >
                {/* Status indicator ring - enhanced when running */}
                {isRunning && (
                  <div className="absolute inset-1 rounded-full border-2 border-green-400 animate-pulse" 
                       style={{
                         boxShadow: '0 0 20px rgba(44, 190, 119, 0.8), inset 0 0 20px rgba(44, 190, 119, 0.2)'
                       }} />
                )}
                
                {/* Bot Name Inside Circle */}
                <div className="flex items-center space-x-1 z-10">
                  {isEditingName ? (
                    <div className="flex items-center space-x-1">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="bg-charcoal-800/90 border border-charcoal-700 px-2 py-1 text-charcoal-900 text-sm font-bold w-20 text-center"
                        autoFocus
                      />
                      <button
                        onClick={handleNameSave}
                        className="text-charcoal-700 hover:text-charcoal-900"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        onClick={handleNameCancel}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-1">
                      <span className="font-display font-bold text-sm text-charcoal-900">
                        {currentBotName}
                      </span>
                      <button
                        onClick={handleNameEdit}
                        className="text-charcoal-700 hover:text-charcoal-900"
                      >
                        <Edit3 size={12} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Arrow or Plus */}
            <div className="flex items-center justify-center w-16 h-32">
              <button
                onClick={handleRightNav}
                className="p-2 text-bone-200 hover:text-bone-100 transition-colors"
              >
                {isLastBot ? <Plus size={32} /> : <ChevronRight size={32} />}
              </button>
            </div>
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
          
          {/* Bot Status Badge */}
          <div className="flex justify-center mt-3">
            {currentConfig && (
              <div className="flex items-center space-x-1 bg-bone-200/20 border border-bone-200/60 px-3 py-1 rounded-full">
                <span className="text-bone-200 text-xs font-semibold uppercase">{currentConfig.config_type}</span>
              </div>
            )}
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

          {/* Delete Icon */}
          <div className="relative group">
            <button
              onClick={handleDelete}
              disabled={availableBots.length <= 1}
              className={`p-4 rounded-full transition-all duration-300 relative ${
                availableBots.length > 1
                  ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400 hover:text-red-300'
                  : 'bg-charcoal-700/50 text-bone-500/50 cursor-not-allowed'
              }`}
            >
              <Trash2 size={24} />
            </button>
            {/* Floating Label */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
              <div className="bg-charcoal-800 border border-bone-200/60 px-2 py-1 text-xs text-bone-200 whitespace-nowrap">
                {availableBots.length > 1 ? 'DELETE BOT' : 'Cannot delete last bot'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}