'use client'

import React from 'react'
import GGBot from '@/components/GGBot'

export default function DemoPage() {
  const [currentBotIndex, setCurrentBotIndex] = React.useState(0)
  
  const demoBots = [
    {
      name: "ggShot-Pro",
      status: "idle" as const,
      message: "🔒 Monitoring 140+ crypto pairs...",
      isLive: true
    },
    {
      name: "MyTrader", 
      status: "extracting" as const,
      message: "Fetching BTC market data...",
      showSpinner: true
    },
    {
      name: "TestBot",
      status: "deciding" as const, 
      message: "AI analyzing RSI signals...",
      showSpinner: true
    }
  ]

  const currentBot = demoBots[currentBotIndex]

  const handleBotClick = (botName: string) => {
    if (botName === 'Create New') {
      console.log('Opening configuration modal...')
      return
    }
    console.log(`Clicked ${botName}`)
  }

  const nextBot = () => {
    setCurrentBotIndex((prev) => (prev + 1) % demoBots.length)
  }

  const prevBot = () => {
    setCurrentBotIndex((prev) => (prev - 1 + demoBots.length) % demoBots.length)
  }

  return (
    <div className="min-h-screen bg-charcoal-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 text-bone-200">
          ggbot Live Demo
        </h1>


        {/* Main ggbot showcase */}
        <div className="mb-16">
          <div className="flex justify-center">
            <GGBot
              name={currentBot.name}
              status={currentBot.status}
              message={currentBot.message}
              showSpinner={currentBot.showSpinner}
              onClick={() => handleBotClick(currentBot.name)}
              disabled={currentBot.isLive}
            />
          </div>
          {currentBot.isLive && (
            <div className="text-center mt-4">
              <span className="text-bone-300 text-sm">🔒 LIVE - Production Bot</span>
            </div>
          )}
        </div>

        {/* Carousel controls */}
        <div className="flex justify-center items-center gap-8 mb-12">
          <button 
            className="text-bone-300 hover:text-bone-200 text-2xl transition-colors"
            onClick={prevBot}
          >
            ◀
          </button>
          <span className="text-bone-300 text-sm">
            {currentBotIndex + 1} of {demoBots.length}
          </span>
          <button 
            className="text-bone-300 hover:text-bone-200 text-2xl transition-colors"
            onClick={nextBot}
          >
            ▶
          </button>
        </div>

        {/* Create new ggbot button */}
        <div className="flex justify-center">
          <button 
            className="px-8 py-3 bg-charcoal-800 border border-bone-200/20 text-bone-200 hover:bg-charcoal-700 transition-colors"
            onClick={() => handleBotClick('Create New')}
          >
            + Create Your ggbot
          </button>
        </div>
      </div>
    </div>
  )
}