'use client'

export default function Features() {
  return (
    <section className="py-20 bg-charcoal-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-2xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            built like a trader, not a bot
          </h2>
          <p className="text-base md:text-lg text-bone-200/70 max-w-xl mx-auto leading-relaxed">
            traditional algo bots are rigid and rule-bound. ggbots is an intelligent agent system that adapts dynamically to changing conditions like a real trader.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Extraction Agent */}
          <div className="relative border-2 border-bone-200/20 p-6 bg-bone-200/5 group hover:border-agents-extraction/40 transition-all duration-500 hover:shadow-[0_0_25px_rgba(56,161,199,0.3)]">
            {/* Subtle weathered edge effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/5 via-transparent to-transparent opacity-50"></div>
            <div className="relative w-12 h-12 border-2 border-agents-extraction bg-agents-extraction/10 flex items-center justify-center mb-4 group-hover:bg-agents-extraction/20 transition-all duration-500">
              <span className="text-agents-extraction font-bold">👁</span>
            </div>
            <h4 className="text-sm font-medium text-agents-extraction mb-2 tracking-wide">EXTRACTION AGENT</h4>
            <h3 className="text-xl font-bold text-bone-200 mb-3 font-display">sees everything</h3>
            <p className="text-bone-200/80">
              charts. custom indicators. real-time prices. even sentiment and news. the extraction agent watches it all.
            </p>
          </div>

          {/* Decision Agent */}
          <div className="relative border-2 border-bone-200/20 p-6 bg-bone-200/5 group hover:border-agents-decision/40 transition-all duration-500 hover:shadow-[0_0_25px_rgba(44,190,119,0.3)]">
            {/* Subtle weathered edge effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/5 via-transparent to-transparent opacity-50"></div>
            <div className="relative w-12 h-12 border-2 border-agents-decision bg-agents-decision/10 flex items-center justify-center mb-4 group-hover:bg-agents-decision/20 transition-all duration-500">
              <span className="text-agents-decision font-bold">🧠</span>
            </div>
            <h4 className="text-sm font-medium text-agents-decision mb-2 tracking-wide">DECISION AGENT</h4>
            <h3 className="text-xl font-bold text-bone-200 mb-3 font-display">thinks strategically</h3>
            <p className="text-bone-200/80">
              the decision agent analyzes the full picture, applies your strategy, and adjusts in real time. just like you would if you never needed sleep.
            </p>
          </div>

          {/* Trading Agent */}
          <div className="relative border-2 border-bone-200/20 p-6 bg-bone-200/5 group hover:border-agents-trading/40 transition-all duration-500 hover:shadow-[0_0_25px_rgba(190,106,71,0.3)]">
            {/* Subtle weathered edge effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/5 via-transparent to-transparent opacity-50"></div>
            <div className="relative w-12 h-12 border-2 border-agents-trading bg-agents-trading/10 flex items-center justify-center mb-4 group-hover:bg-agents-trading/20 transition-all duration-500">
              <span className="text-agents-trading font-bold">⚡</span>
            </div>
            <h4 className="text-sm font-medium text-agents-trading mb-2 tracking-wide">TRADING AGENT</h4>
            <h3 className="text-xl font-bold text-bone-200 mb-3 font-display">executes with discipline</h3>
            <p className="text-bone-200/80">
              the trading agent executes with precision, enforces your risk rules, and reacts to market conditions without human emotions or hesitation.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}