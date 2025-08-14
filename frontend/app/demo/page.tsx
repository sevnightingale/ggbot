'use client'

import { useState } from 'react'
import { PageWrapper } from '@/components/ui/PageWrapper'
import { CircularGGBot } from '@/components/ggbot/CircularGGBot'

export default function DemoPage() {
  const [selectedBot, setSelectedBot] = useState<string>('')

  const handleBotClick = (botName: string) => {
    setSelectedBot(botName)
    console.log(`Clicked ${botName} - would open config modal`)
  }

  return (
    <PageWrapper>
      <div className="min-h-screen bg-charcoal-900 text-bone-200">
        <div className="container mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold text-center mb-8">
            ggbot Live Demo
          </h1>
          
          {/* Test the circular ggbot components */}
          <div className="flex flex-wrap justify-center gap-8 mb-8">
            {/* Live ggShot bot */}
            <div className="text-center">
              <CircularGGBot
                botName="ggShot-Pro"
                status="idle"
                message="🔵 Monitoring 140+ crypto pairs..."
                onClick={() => handleBotClick('ggShot-Pro')}
                isClickable={false}
              />
              <div className="mt-2 text-sm text-bone-300">🔒 LIVE</div>
            </div>

            {/* Demo bot - different states for testing */}
            <div className="text-center">
              <CircularGGBot
                botName="MyTrader"
                status="extracting"
                message="🔵 Fetching BTC price data..."
                onClick={() => handleBotClick('MyTrader')}
              />
              <div className="mt-2 text-sm text-bone-300">DEMO</div>
            </div>

            {/* Another demo bot in different state */}
            <div className="text-center">
              <CircularGGBot
                botName="TestBot"
                status="deciding"
                message="🟢 AI analyzing RSI signals..."
                onClick={() => handleBotClick('TestBot')}
              />
              <div className="mt-2 text-sm text-bone-300">DEMO</div>
            </div>
          </div>

          {/* Status display */}
          {selectedBot && (
            <div className="text-center p-4 bg-charcoal-800 border border-bone-200/20">
              <p>Selected: <strong>{selectedBot}</strong></p>
              <p className="text-sm text-bone-300 mt-2">
                (Configuration modal would open here)
              </p>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}