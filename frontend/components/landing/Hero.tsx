'use client'

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-charcoal-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center">
          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl font-bold text-bone-200 mb-6 font-display">
            AI Trading Agents<br />
            That <span className="text-agents-extraction">Trade Like You</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl md:text-2xl text-bone-200/80 mb-12 max-w-4xl mx-auto">
            Deploy autonomous AI trading agents that analyze markets, adapt to changing conditions, 
            and execute your proven strategies 24/7 across cryptocurrency exchanges.
          </p>

          {/* Integrated Waitlist */}
          <div className="max-w-md mx-auto">
            <p className="text-bone-200/80 font-medium mb-4">Join the waitlist for early access</p>
            <div className="launchlist-widget" data-key-id="8390qp" data-height="180px"></div>
            <p className="text-bone-200/60 text-sm mt-4">
              💡 Refer friends to move up the waitlist. Share your unique link after signing up!
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}