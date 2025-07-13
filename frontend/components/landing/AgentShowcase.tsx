'use client'

export default function AgentShowcase() {
  return (
    <section className="py-20 bg-charcoal-900 border-t-2 border-bone-200/20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-bone-200 mb-6 font-display">
            the problem with modern trading
          </h2>
          <p className="text-sm md:text-base lg:text-base text-bone-200/70 max-w-xl mx-auto leading-relaxed font-sans">
            traditional tools force you to choose between sleep and profits.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* Problem 1 */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-bone-200/40 flex items-center justify-center">
              <span className="text-2xl">😴</span>
            </div>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-bone-200 mb-2 font-display">humans need sleep</h3>
            <p className="text-sm md:text-base lg:text-base text-bone-200/70 font-sans">
              manual trading means constant monitoring or missed opportunities.
            </p>
          </div>

          {/* Problem 2 */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-bone-200/40 flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-bone-200 mb-2 font-display">rigid bots break</h3>
            <p className="text-sm md:text-base lg:text-base text-bone-200/70 font-sans">
              basic rule-based automation fails when market conditions change.
            </p>
          </div>

          {/* Problem 3 */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-bone-200/40 flex items-center justify-center">
              <span className="text-2xl">💸</span>
            </div>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-bone-200 mb-2 font-display">high costs</h3>
            <p className="text-sm md:text-base lg:text-base text-bone-200/70 font-sans">
              advanced quant systems are inaccessible or extremely expensive.
            </p>
          </div>
        </div>

      </div>
    </section>
  )
}