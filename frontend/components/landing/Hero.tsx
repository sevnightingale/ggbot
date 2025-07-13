'use client'

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-charcoal-900">
      {/* Textural Background Layers */}
      <div className="absolute inset-0 opacity-[0.03]">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23e3e5e6%22%20fill-opacity%3D%220.4%22%3E%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%221%22/%3E%3Ccircle%20cx%3D%2225%22%20cy%3D%2225%22%20r%3D%221%22/%3E%3Ccircle%20cx%3D%2245%22%20cy%3D%2245%22%20r%3D%221%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] animate-pulse"></div>
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
            AI trading agents<br />
            that <span className="inline-flex space-x-2 md:space-x-4">
              <span className="text-agents-extraction relative">
                trade
                <span className="absolute inset-0 text-agents-extraction opacity-30 blur-sm">trade</span>
              </span>
              <span className="text-agents-decision relative">
                like
                <span className="absolute inset-0 text-agents-decision opacity-30 blur-sm">like</span>
              </span>
              <span className="text-agents-trading relative">
                you
                <span className="absolute inset-0 text-agents-trading opacity-30 blur-sm">you</span>
              </span>
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-sm md:text-base lg:text-base text-bone-200/70 mb-16 max-w-2xl mx-auto leading-relaxed font-sans">
            Deploy autonomous AI trading agents that analyze markets, adapt to changing conditions, 
            and execute your proven strategies 24/7.
          </p>

          {/* Integrated Waitlist */}
          <div className="max-w-sm mx-auto">
            <p className="text-lg md:text-xl lg:text-2xl text-bone-200/80 font-medium mb-6 font-display">join the waitlist for early access</p>
            <div className="relative">
              {/* Subtle container styling */}
              <div className="absolute inset-0 bg-bone-200/5 border border-bone-200/20 -z-10"></div>
              <div className="launchlist-widget" data-key-id="8390qp" data-height="160px"></div>
            </div>
            <p className="text-xs md:text-xs lg:text-xs text-bone-200/50 mt-6 leading-relaxed font-sans">
              refer friends to move up the waitlist.<br/>share your unique link after signing up.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}