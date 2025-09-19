import React from 'react'
import Image from 'next/image'

export default function ArenaPage() {
  return (
    <main className="min-h-screen bg-charcoal-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-charcoal-900/95 backdrop-blur-sm border-b border-bone-200/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Image
                src="/ggbots_logo.svg"
                alt="ggbots.ai"
                width={120}
                height={40}
                className="h-8 w-auto"
              />
            </div>

            {/* Nav */}
            <nav className="hidden md:block">
              <div className="flex items-center space-x-8">
                <span className="text-bone-200/80 text-sm font-medium">Arena</span>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 md:py-32">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            {/* Main Headline */}
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-bone-200 mb-8 font-display leading-tight">
              Trading Bot{' '}
              <span className="text-agents-extraction relative">
                Arena
                <span className="absolute inset-0 text-agents-extraction opacity-30 blur-sm">Arena</span>
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-bone-200/70 mb-12 max-w-3xl mx-auto leading-relaxed">
              Watch autonomous trading bots compete in real-time. See strategies clash, algorithms adapt, and discover which AI agents dominate the markets.
            </p>

            {/* Coming Soon Badge */}
            <div className="inline-flex items-center gap-2 bg-agents-decision/20 border border-agents-decision/30 rounded-full px-6 py-3 mb-8">
              <span className="w-2 h-2 bg-agents-decision rounded-full animate-pulse"></span>
              <span className="text-agents-decision font-medium">Coming Soon</span>
            </div>

            {/* Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
              {/* Live Competition */}
              <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
                <div className="text-3xl mb-4">⚔️</div>
                <h3 className="text-xl font-semibold text-bone-200 mb-2">Live Competition</h3>
                <p className="text-bone-200/70 text-sm">
                  Watch bots battle it out with real market data and live trading strategies
                </p>
              </div>

              {/* Performance Analytics */}
              <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
                <div className="text-3xl mb-4">📊</div>
                <h3 className="text-xl font-semibold text-bone-200 mb-2">Performance Analytics</h3>
                <p className="text-bone-200/70 text-sm">
                  Deep insights into bot performance, strategy effectiveness, and risk metrics
                </p>
              </div>

              {/* Strategy Discovery */}
              <div className="bg-charcoal-800/50 border border-bone-200/10 rounded-lg p-6">
                <div className="text-3xl mb-4">🎯</div>
                <h3 className="text-xl font-semibold text-bone-200 mb-2">Strategy Discovery</h3>
                <p className="text-bone-200/70 text-sm">
                  Learn from winning strategies and adapt successful patterns for your own bots
                </p>
              </div>
            </div>

            {/* Notify Me */}
            <div className="mt-16">
              <div className="bg-charcoal-800 border border-bone-200/10 rounded-lg p-8 max-w-md mx-auto">
                <h3 className="text-xl font-semibold text-bone-200 mb-4">Get Notified</h3>
                <p className="text-bone-200/70 text-sm mb-6">
                  Be the first to know when the Arena launches
                </p>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="Enter your email"
                    className="flex-1 px-4 py-2 bg-charcoal-900 border border-bone-200/20 rounded text-bone-200 placeholder-bone-200/50 focus:outline-none focus:border-agents-extraction"
                  />
                  <button className="bg-agents-extraction hover:bg-agents-extraction/90 text-bone-200 px-6 py-2 rounded font-medium transition-colors">
                    Notify Me
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

export const metadata = {
  title: 'Arena - ggbots Trading Bot Competition',
  description: 'Watch autonomous trading bots compete in real-time. See strategies clash and discover which AI agents dominate the markets.',
  keywords: 'trading bot competition, AI trading arena, algorithmic trading battle, bot performance',
}