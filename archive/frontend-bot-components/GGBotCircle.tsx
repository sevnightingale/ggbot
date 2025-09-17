'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Plus, Play, Square, TestTube, Edit3, Check, X, Trash2 } from 'lucide-react'
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
    deleteBot
  } = useBotStore()
  const [currentBotIndex, setCurrentBotIndex] = useState(0)
  const [isEditingName, setIsEditingName] = useState(false)
  const [editName, setEditName] = useState('')
  
  const currentBotName = currentConfig?.config_name || 'Loading...'
  const botState = currentConfig?.state || 'inactive' // Database state: 'active' or 'inactive'
  
  // Execution status from WebSocket (only when botState is 'active')
  const executionStatus = botState === 'active' ? status?.current_phase || null : null // 'extracting', 'deciding', 'trading'
  
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
  const canStart = allConfigured && botState === 'inactive'
  const canStop = botState === 'active'

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
    if (canStop) {
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
                className={`ggbot-circle ${
                  executionStatus === 'extracting' ? 'ggbot-extracting' :
                  executionStatus === 'deciding' ? 'ggbot-deciding' :
                  executionStatus === 'trading' ? 'ggbot-trading' :
                  botState === 'active' ? 'ggbot-idle' :
                  'ggbot-inactive'
                }`}
              >
                <div className="ggbot-inner">
                  <div className="ggbot-name">{currentBotName}</div>
                  <div className="ggbot-status-label">
                    <span className={`ggbot-status-indicator ${
                      executionStatus === 'extracting' ? 'ggbot-status-extracting' :
                      executionStatus === 'deciding' ? 'ggbot-status-deciding' :
                      executionStatus === 'trading' ? 'ggbot-status-trading' :
                      botState === 'active' ? 'ggbot-status-active' :
                      'ggbot-status-inactive'
                    }`}>
                      {botState === 'active' ? '●' : botState === 'inactive' ? '○' : '●'}
                    </span>
                    <span className="ggbot-status-text">
                      {executionStatus || (botState === 'active' ? 'active' : botState)}
                    </span>
                  </div>
                </div>
                
                {/* Edit functionality - positioned over the name */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-30">
                  {isEditingName && (
                    <div className="flex items-center space-x-1 bg-charcoal-800/90 p-2 rounded">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="bg-charcoal-700 border border-charcoal-600 px-2 py-1 text-bone-200 text-sm font-bold w-24 text-center rounded"
                        autoFocus
                      />
                      <button
                        onClick={handleNameSave}
                        className="text-green-400 hover:text-green-300"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        onClick={handleNameCancel}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  )}
                </div>
                
                {/* Edit button - positioned in corner */}
                {!isEditingName && (
                  <button
                    onClick={handleNameEdit}
                    className="absolute top-2 right-2 text-bone-300 hover:text-bone-200 z-30"
                  >
                    <Edit3 size={14} />
                  </button>
                )}
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
              disabled={!canStart && !canStop}
              className={`p-4 rounded-full transition-all duration-300 relative ${
                canStop
                  ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400 hover:text-red-300'
                  : canStart
                    ? 'bg-bone-200/20 hover:bg-bone-200/30 text-bone-200 hover:text-bone-100'
                    : 'bg-charcoal-700/50 text-bone-500/50 cursor-not-allowed'
              }`}
            >
              {canStop ? <Square size={24} /> : <Play size={24} />}
            </button>
            {/* Floating Label */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
              <div className="bg-charcoal-800 border border-bone-200/60 px-2 py-1 text-xs text-bone-200 whitespace-nowrap">
                {canStop ? 'STOP' : canStart ? 'START' : 'Configure agents first'}
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