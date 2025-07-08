'use client'

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-charcoal-900">
      {/* Textural Background Layers */}
      <div className="absolute inset-0 opacity-[0.03]">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23e3e5e6" fill-opacity="0.4"%3E%3Ccircle cx="5" cy="5" r="1"/%3E%3Ccircle cx="25" cy="25" r="1"/%3E%3Ccircle cx="45" cy="45" r="1"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] animate-pulse"></div>
      </div>
      
      {/* Paper Grain Overlay */}
      <div className="absolute inset-0 opacity-[0.08] mix-blend-overlay">
        <div className="absolute inset-0 bg-gradient-to-br from-bone-200/20 via-transparent to-bone-200/10"></div>
      </div>
      
      {/* Subtle Scan Lines */}
      <div className="absolute inset-0 opacity-[0.02]">
        <div className="absolute inset-0 bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,#e3e5e6_2px,#e3e5e6_4px)]"></div>
      </div>
      
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="text-center">
          {/* Main Headline */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-bone-200 mb-8 font-display leading-tight relative">
            {/* Subtle text shadow for carved effect */}
            <span className="relative">
              AI Trading Agents<br />
              That <span className="text-bone-200 relative">
                <span className="absolute inset-0 text-bone-200/20 blur-sm">Trade Like You</span>
                <span className="relative">Trade Like You</span>
              </span>
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-bone-200/70 mb-16 max-w-2xl mx-auto leading-relaxed">
            Deploy autonomous AI trading agents that analyze markets, adapt to changing conditions, 
            and execute your proven strategies 24/7.
          </p>

          {/* Integrated Waitlist */}
          <div className="max-w-sm mx-auto">
            <p className="text-bone-200/80 font-medium mb-6 text-base">Join the waitlist for early access</p>
            <div className="relative">
              {/* Subtle container styling */}
              <div className="absolute inset-0 bg-bone-200/5 border border-bone-200/20 -z-10"></div>
              <div className="launchlist-widget" data-key-id="8390qp" data-height="160px"></div>
            </div>
            <p className="text-bone-200/50 text-xs mt-6 leading-relaxed">
              Refer friends to move up the waitlist.<br/>Share your unique link after signing up.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}