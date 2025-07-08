'use client'

export default function AgentShowcase() {
  return (
    <section className="py-20 bg-charcoal-900 border-t-2 border-bone-200/20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-2xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            The Problem With Modern Trading
          </h2>
          <p className="text-base md:text-lg text-bone-200/70 max-w-xl mx-auto leading-relaxed">
            Traditional tools force you to choose between sleep and profits.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* Problem 1 */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-bone-200/40 flex items-center justify-center">
              <span className="text-2xl">😴</span>
            </div>
            <h3 className="text-lg font-bold text-bone-200 mb-2 font-display">Humans Need Sleep</h3>
            <p className="text-bone-200/70 text-sm">
              Manual trading means constant monitoring or missed opportunities.
            </p>
          </div>

          {/* Problem 2 */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-bone-200/40 flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="text-lg font-bold text-bone-200 mb-2 font-display">Rigid Bots Break</h3>
            <p className="text-bone-200/70 text-sm">
              Basic rule-based automation fails when market conditions change.
            </p>
          </div>

          {/* Problem 3 */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-bone-200/40 flex items-center justify-center">
              <span className="text-2xl">💸</span>
            </div>
            <h3 className="text-lg font-bold text-bone-200 mb-2 font-display">High Costs</h3>
            <p className="text-bone-200/70 text-sm">
              Advanced quant systems are inaccessible or extremely expensive.
            </p>
          </div>
        </div>

        {/* Solution */}
        <div className="border-t-2 border-bone-200/20 pt-16">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-4xl font-bold text-bone-200 mb-4 font-display">
              Why ggbots Works
            </h2>
            <p className="text-base md:text-lg text-bone-200/70 max-w-3xl mx-auto">
              AI has advanced significantly, while trading tools have not kept pace. Three breakthroughs make ggbots possible today.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-3 h-3 bg-agents-extraction mx-auto mb-4"></div>
              <h3 className="text-lg font-bold text-bone-200 mb-2">Reasoning AI</h3>
              <p className="text-bone-200/70 text-sm">
                Advanced LLMs offer adaptive, human-like thinking that understands complex market patterns.
              </p>
            </div>
            <div className="text-center">
              <div className="w-3 h-3 bg-agents-decision mx-auto mb-4"></div>
              <h3 className="text-lg font-bold text-bone-200 mb-2">Browser Automation</h3>
              <p className="text-bone-200/70 text-sm">
                Technology now mimics trader behavior on platforms like TradingView seamlessly.
              </p>
            </div>
            <div className="text-center">
              <div className="w-3 h-3 bg-agents-trading mx-auto mb-4"></div>
              <h3 className="text-lg font-bold text-bone-200 mb-2">24/7 Markets</h3>
              <p className="text-bone-200/70 text-sm">
                Crypto never sleeps. Your edge shouldn&apos;t either. AI provides continuous oversight.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}