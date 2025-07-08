'use client'

export default function AgentShowcase() {
  return (
    <section className="py-20 bg-charcoal-900 border-t-2 border-bone-200/20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-2xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Why It Matters
          </h2>
          <p className="text-base md:text-lg text-bone-200/70 max-w-xl mx-auto leading-relaxed">
            Markets move fast. Static bots break. ggbots adapts.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h3 className="text-2xl font-bold text-bone-200 mb-4 font-display">
              Trade While You Sleep—Your Way
            </h3>
            <p className="text-bone-200/80 mb-6">
              Your ggbot doesn&apos;t guess. It trades the way you would, with your data, your indicators, and your risk limits.
            </p>
            <ul className="space-y-3 text-bone-200/80">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-agents-extraction mr-3"></span>
                Responds to volatility spikes instantly
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-agents-decision mr-3"></span>
                Adapts to breaking news and sentiment shifts
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-agents-trading mr-3"></span>
                Executes with your exact risk parameters
              </li>
            </ul>
          </div>

          <div className="relative border-2 border-bone-200/20 p-8 bg-bone-200/5">
            {/* Subtle concrete texture */}
            <div className="absolute inset-0 bg-gradient-to-br from-bone-200/10 via-transparent to-bone-200/5 opacity-30"></div>
            <div className="relative">
              <h4 className="text-xl font-bold text-bone-200 mb-4 font-display">
                Customizable. Scalable. Built to Win.
              </h4>
              <p className="text-bone-200/80">
                From niche indicators to dynamic strategies, ggbots gives you full control. Configure once. Improve over time. Let your edge scale without burnout.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}