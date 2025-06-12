'use client'

import { useState } from 'react'
import { ChevronLeft, ChevronRight, Plus, Play, Square, TestTube, Edit3, Check, X } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { SchedulerStatus } from '@/types'

interface GGBotCircleProps {
  status: SchedulerStatus
}

export function GGBotCircle({ status }: GGBotCircleProps) {
  const { startScheduler, stopScheduler, agentStatuses } = useBotStore()
  const [currentBotIndex, setCurrentBotIndex] = useState(0)
  const [isEditingName, setIsEditingName] = useState(false)
  const [botName, setBotName] = useState('BOT-01')
  const [editName, setEditName] = useState(botName)
  
  const isRunning = status?.is_running || false
  
  // Mock data for multiple bots (future feature)
  const bots = [{ id: 1, name: botName }] // Single bot for now
  const totalBots = bots.length
  const isLastBot = currentBotIndex === totalBots - 1
  
  // Check if all agents are configured
  const allConfigured = Object.values(agentStatuses).every(status => status === 'configured')
  const canStart = allConfigured && !isRunning

  const handleLeftNav = () => {
    if (currentBotIndex > 0) {
      setCurrentBotIndex(currentBotIndex - 1)
    }
  }

  const handleRightNav = () => {
    if (isLastBot) {
      // Add new bot (future feature)
      console.log('Create new bot')
    } else {
      setCurrentBotIndex(currentBotIndex + 1)
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
    setEditName(botName)
    setIsEditingName(true)
  }

  const handleNameSave = () => {
    setBotName(editName)
    setIsEditingName(false)
  }

  const handleNameCancel = () => {
    setEditName(botName)
    setIsEditingName(false)
  }

  return (
    <div className="flex flex-col items-center space-y-8">
      {/* Bot Emblem Card */}
      <div className="bg-charcoal-800/50 border-2 border-bone-200/80 p-8 w-full max-w-md">
        {/* Carousel Navigation */}
        <div className="flex items-center justify-between mb-8">
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
            <ChevronLeft size={24} />
          </button>

          {/* Bot Emblem */}
          <div className="flex flex-col items-center space-y-4">
            {/* Large Circle Emblem */}
            <div 
              className="w-32 h-32 rounded-full bg-bone-200/90 border-2 border-bone-200/90 relative"
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
                <div className="absolute inset-1 rounded-full border-2 border-green-400/90 animate-pulse" />
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
                    className="text-green-400 hover:text-green-300"
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
                  <span className="text-bone-200 font-display font-bold">{botName}</span>
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
            {isLastBot ? <Plus size={24} /> : <ChevronRight size={24} />}
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
                    ? 'bg-bone-500/50' // Placeholder for new bot
                    : 'bg-bone-500'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-charcoal-800/50 border-2 border-bone-200/80 p-6 flex items-center space-x-6">
        {/* Start/Stop Button */}
        <button
          onClick={handleStartStop}
          disabled={!canStart && !isRunning}
          className={`
            flex items-center space-x-3 px-6 py-3 border-2 font-medium transition-all duration-300
            ${isRunning
              ? 'bg-red-600 hover:bg-red-700 text-white border-red-500'
              : canStart
                ? 'bg-green-600 hover:bg-green-700 text-white border-green-500'
                : 'bg-charcoal-700 text-bone-500 border-bone-500/20 cursor-not-allowed'
            }
          `}
        >
          {isRunning ? (
            <>
              <Square size={18} />
              <span>STOP</span>
            </>
          ) : (
            <>
              <Play size={18} />
              <span>START</span>
            </>
          )}
        </button>

        {/* Test Run Button */}
        <button
          onClick={handleTestRun}
          className="flex items-center space-x-3 px-6 py-3 border-2 border-bone-200/60 bg-charcoal-700 hover:bg-charcoal-600 text-bone-200 hover:text-bone-100 font-medium transition-all duration-300"
        >
          <TestTube size={18} />
          <span>TEST RUN</span>
        </button>
      </div>
    </div>
  )
}