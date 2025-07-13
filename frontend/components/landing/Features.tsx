'use client'

import { Eye, Brain, Zap } from 'lucide-react'

export default function Features() {
  return (
    <section className="py-20 bg-charcoal-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-bone-200 mb-6 font-display">
            built like a trader, not a bot
          </h2>
          <p className="text-sm md:text-base lg:text-base text-bone-200/70 max-w-xl mx-auto leading-relaxed font-sans">
            traditional algo bots are rigid and rule-bound. ggbots is an intelligent agent system that adapts dynamically to changing conditions like a real trader.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Extraction Agent */}
          <div className="relative border-2 border-agents-extraction/40 p-6 bg-bone-200/5 shadow-[0_0_25px_rgba(56,161,199,0.3)]">
            {/* Subtle weathered edge effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/5 via-transparent to-transparent opacity-50"></div>
            <div className="relative w-12 h-12 bg-agents-extraction/20 flex items-center justify-center mb-4">
              <Eye className="text-agents-extraction" size={24} />
            </div>
            <h4 className="text-xs md:text-xs lg:text-xs font-medium text-agents-extraction mb-2 tracking-wide">EXTRACTION AGENT</h4>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-bone-200 mb-3 font-display">sees everything</h3>
            <p className="text-sm md:text-base lg:text-base text-bone-200/80 font-sans">
              charts. custom indicators. real-time prices. even sentiment and news. the extraction agent watches it all.
            </p>
          </div>

          {/* Decision Agent */}
          <div className="relative border-2 border-agents-decision/40 p-6 bg-bone-200/5 shadow-[0_0_25px_rgba(44,190,119,0.3)]">
            {/* Subtle weathered edge effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/5 via-transparent to-transparent opacity-50"></div>
            <div className="relative w-12 h-12 bg-agents-decision/20 flex items-center justify-center mb-4">
              <Brain className="text-agents-decision" size={24} />
            </div>
            <h4 className="text-xs md:text-xs lg:text-xs font-medium text-agents-decision mb-2 tracking-wide">DECISION AGENT</h4>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-bone-200 mb-3 font-display">thinks strategically</h3>
            <p className="text-sm md:text-base lg:text-base text-bone-200/80 font-sans">
              the decision agent analyzes the full picture, applies your strategy, and adjusts in real time. just like you would if you never needed sleep.
            </p>
          </div>

          {/* Trading Agent */}
          <div className="relative border-2 border-agents-trading/40 p-6 bg-bone-200/5 shadow-[0_0_25px_rgba(190,106,71,0.3)]">
            {/* Subtle weathered edge effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/5 via-transparent to-transparent opacity-50"></div>
            <div className="relative w-12 h-12 bg-agents-trading/20 flex items-center justify-center mb-4">
              <Zap className="text-agents-trading" size={24} />
            </div>
            <h4 className="text-xs md:text-xs lg:text-xs font-medium text-agents-trading mb-2 tracking-wide">TRADING AGENT</h4>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-bone-200 mb-3 font-display">executes with discipline</h3>
            <p className="text-sm md:text-base lg:text-base text-bone-200/80 font-sans">
              the trading agent executes with precision, enforces your risk rules, and reacts to market conditions without human emotions or hesitation.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}