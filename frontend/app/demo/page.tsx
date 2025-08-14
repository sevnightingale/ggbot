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
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
      <div className="flex flex-col items-center">
        {/* ggbot with flanking arrows */}
        <div className="flex items-center gap-16 mb-6">
          <button 
            className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
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
            className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
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

        {/* Dots navigation with + */}
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
          <button
            className="w-6 h-6 rounded-full border-2 border-bone-300 flex items-center justify-center text-bone-300 hover:text-bone-200 hover:border-bone-200 transition-all duration-200 ml-2"
            onClick={() => handleBotClick('Create New')}
          >
            <span className="text-sm font-bold">+</span>
          </button>
        </div>
      </div>
    </div>
  )
}