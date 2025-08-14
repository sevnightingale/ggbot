'use client'

import React from 'react'
import GGBot from '@/components/GGBot'

export default function DemoPage() {
  const [currentBotIndex, setCurrentBotIndex] = React.useState(0)
  
  const demoBots = [
    {
      name: "ggShot-Pro",
      status: "idle" as const,
      message: "Monitoring 140+ crypto pairs..."
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


        {/* Integrated Control Hub */}
        <div className="flex flex-col items-center max-w-md mx-auto">
          {/* ggbot with flanking arrows */}
          <div className="flex items-center gap-12 mb-8">
            <button 
              className={`text-3xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                currentBotIndex === 0 
                  ? 'text-bone-500 cursor-not-allowed opacity-50' 
                  : 'text-bone-300 hover:text-bone-200 hover:scale-110'
              }`}
              onClick={prevBot}
              disabled={currentBotIndex === 0}
            >
              ◀
            </button>
            
            <GGBot
              name={currentBot.name}
              status={currentBot.status}
              message={currentBot.message}
              showSpinner={currentBot.showSpinner}
              onClick={() => handleBotClick(currentBot.name)}
            />
            
            <button 
              className={`text-3xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                currentBotIndex === demoBots.length - 1 
                  ? 'text-bone-500 cursor-not-allowed opacity-50' 
                  : 'text-bone-300 hover:text-bone-200 hover:scale-110'
              }`}
              onClick={nextBot}
              disabled={currentBotIndex === demoBots.length - 1}
            >
              ▶
            </button>
          </div>

          {/* Create button */}
          <button 
            className="w-full max-w-sm px-8 py-3 bg-charcoal-800 border border-bone-200/20 text-bone-200 hover:bg-charcoal-700 hover:border-bone-200/30 transition-all duration-200"
            onClick={() => handleBotClick('Create New')}
          >
            + Create Your ggbot
          </button>
        </div>
      </div>
    </div>
  )
}