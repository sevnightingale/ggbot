'use client'

export default function Hero() {
  return (
    <section id="hero" className="relative overflow-hidden bg-obsidian py-20 md:py-32">
      {/* Subtle Background Textures - ceremonial brutalism */}
      <div className="absolute inset-0 opacity-[0.03]">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23edebe7%22%20fill-opacity%3D%220.4%22%3E%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%221%22/%3E%3Ccircle%20cx%3D%2225%22%20cy%3D%2225%22%20r%3D%221%22/%3E%3Ccircle%20cx%3D%2245%22%20cy%3D%2245%22%20r%3D%221%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] animate-pulse"></div>
      </div>

      {/* Directional lighting effect - subtle warmth */}
      <div className="absolute inset-0 opacity-[0.08] mix-blend-overlay">
        <div className="absolute inset-0 bg-gradient-to-br from-ivory/20 via-transparent to-brass/10"></div>
      </div>

      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          {/* Main Headline */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-ivory mb-8 font-display leading-tight">
            AI trading bots that{' '}
            <span className="inline-flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
              <span className="text-brass relative">
                think
                <span className="absolute inset-0 text-brass opacity-30 blur-sm">think</span>
              </span>
              <span className="text-brass relative">
                adapt
                <span className="absolute inset-0 text-brass opacity-30 blur-sm">adapt</span>
              </span>
              <span className="text-brass relative">
                execute
                <span className="absolute inset-0 text-brass opacity-30 blur-sm">execute</span>
              </span>
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-ivory/70 mb-12 max-w-3xl mx-auto leading-relaxed font-sans">
            Become a vibetrader. Our AI agents analyze market conditions, reason through decisions, and adapt your trading strategies in real-time — just like you would, but 24/7.
          </p>

          {/* Primary CTA */}
          <div className="flex justify-center">
            <a
              href="https://app.ggbots.ai"
              className="bg-brass hover:bg-brass-light text-obsidian px-8 py-4 rounded-sm font-medium transition-colors text-lg"
            >
              Create a ggbot now
            </a>
          </div>

        </div>
      </div>
    </section>
  )
}