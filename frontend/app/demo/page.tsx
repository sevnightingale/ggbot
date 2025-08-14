'use client'

import React from 'react'
import GGBot from '@/components/GGBot'

export default function DemoPage() {
  const handleBotClick = (botName: string) => {
    console.log(`Clicked ${botName}`)
  }

  return (
    <div className="min-h-screen bg-charcoal-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 text-bone-200">
          ggbot Visual Test
        </h1>


        {/* With messages */}
        <div className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-bone-300">With Messages</h2>
          <div className="flex gap-12 justify-center">
            <GGBot
              name="ggShot-Pro"
              status="idle"
              message="Monitoring 140+ crypto pairs..."
              onClick={() => handleBotClick('ggShot-Pro')}
            />
            <GGBot
              name="MyTrader"
              status="extracting"
              message="Analyzing market conditions for high-confidence setups"
              showSpinner={true}
              onClick={() => handleBotClick('MyTrader')}
            />
          </div>
        </div>

        {/* Status variations */}
        <div className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-bone-300">Status Colors</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 justify-items-center">
            <GGBot
              name="Inactive"
              status="inactive"
              message="Bot stopped"
              onClick={() => handleBotClick('Inactive')}
            />
            <GGBot
              name="Idle"
              status="idle"
              message="Waiting for signals"
              onClick={() => handleBotClick('Idle')}
            />
            <GGBot
              name="Extracting"
              status="extracting"
              message="Fetching market data..."
              showSpinner={true}
              onClick={() => handleBotClick('Extracting')}
            />
            <GGBot
              name="Deciding"
              status="deciding"
              message="AI analyzing patterns..."
              showSpinner={true}
              onClick={() => handleBotClick('Deciding')}
            />
            <GGBot
              name="Trading"
              status="trading"
              message="Executing trade..."
              showSpinner={true}
              onClick={() => handleBotClick('Trading')}
            />
          </div>
        </div>

        {/* Interactive states */}
        <div className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-bone-300">Interactive States</h2>
          <div className="flex gap-12 justify-center">
            <GGBot
              name="Clickable"
              message="Click me!"
              onClick={() => handleBotClick('Clickable')}
            />
            <GGBot
              name="Disabled"
              message="Not interactive"
              disabled={true}
            />
          </div>
        </div>

        {/* Layout test */}
        <div className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-bone-300">Layout & Spacing</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <GGBot
              name="Bot 1"
              message="Testing grid layout"
              onClick={() => handleBotClick('Bot 1')}
            />
            <GGBot
              name="Bot 2"
              message="Responsive design"
              onClick={() => handleBotClick('Bot 2')}
            />
            <GGBot
              name="Bot 3"
              message="Proper spacing"
              onClick={() => handleBotClick('Bot 3')}
            />
            <GGBot
              name="Bot 4"
              message="Clean alignment"
              onClick={() => handleBotClick('Bot 4')}
            />
            <GGBot
              name="Bot 5"
              message="Visual hierarchy"
              onClick={() => handleBotClick('Bot 5')}
            />
            <GGBot
              name="Bot 6"
              message="Consistent style"
              onClick={() => handleBotClick('Bot 6')}
            />
          </div>
        </div>
      </div>
    </div>
  )
}