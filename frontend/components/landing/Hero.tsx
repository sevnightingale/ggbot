'use client'

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-charcoal-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="text-center">
          {/* Main Headline */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-bone-200 mb-8 font-display leading-tight">
            AI Trading Agents<br />
            That <span className="text-agents-extraction">Trade Like You</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-bone-200/70 mb-16 max-w-2xl mx-auto leading-relaxed">
            Deploy autonomous AI trading agents that analyze markets, adapt to changing conditions, 
            and execute your proven strategies 24/7.
          </p>

          {/* Integrated Waitlist */}
          <div className="max-w-sm mx-auto">
            <p className="text-bone-200/80 font-medium mb-6 text-base">Join the waitlist for early access</p>
            <div className="launchlist-widget" data-key-id="8390qp" data-height="160px"></div>
            <p className="text-bone-200/50 text-xs mt-6 leading-relaxed">
              Refer friends to move up the waitlist.<br/>Share your unique link after signing up.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}