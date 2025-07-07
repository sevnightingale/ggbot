'use client'

export default function Features() {
  return (
    <section className="py-20 bg-charcoal-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-2xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Built Like a Trader, Not a Bot
          </h2>
          <p className="text-base md:text-lg text-bone-200/70 max-w-xl mx-auto leading-relaxed">
            Most algo bots are glorified calculators. ggbots is an intelligent agent system designed to think like a real trader.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Sees Everything */}
          <div className="border-2 border-bone-200/20 p-6 bg-bone-200/5">
            <div className="w-12 h-12 border-2 border-agents-extraction bg-agents-extraction/10 flex items-center justify-center mb-4">
              <span className="text-agents-extraction font-bold">👁</span>
            </div>
            <h3 className="text-xl font-bold text-bone-200 mb-3 font-display">Sees Everything</h3>
            <p className="text-bone-200/80">
              Charts. Custom indicators. Real-time prices. Even sentiment and news. The Extraction Agent watches it all.
            </p>
          </div>

          {/* Thinks Strategically */}
          <div className="border-2 border-bone-200/20 p-6 bg-bone-200/5">
            <div className="w-12 h-12 border-2 border-agents-decision bg-agents-decision/10 flex items-center justify-center mb-4">
              <span className="text-agents-decision font-bold">🧠</span>
            </div>
            <h3 className="text-xl font-bold text-bone-200 mb-3 font-display">Thinks Strategically</h3>
            <p className="text-bone-200/80">
              The Decision Agent analyzes the full picture, applies your strategy, and adjusts in real time. Just like you would if you didn&apos;t need sleep.
            </p>
          </div>

          {/* Executes with Discipline */}
          <div className="border-2 border-bone-200/20 p-6 bg-bone-200/5">
            <div className="w-12 h-12 border-2 border-agents-trading bg-agents-trading/10 flex items-center justify-center mb-4">
              <span className="text-agents-trading font-bold">⚡</span>
            </div>
            <h3 className="text-xl font-bold text-bone-200 mb-3 font-display">Executes with Discipline</h3>
            <p className="text-bone-200/80">
              The Trading Agent acts instantly, enforces your risk rules, and keeps you in the trade—or out—based on actual conditions, not old code.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}