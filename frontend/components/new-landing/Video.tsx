'use client'

export default function Video() {
  return (
    <section className="py-20 bg-charcoal-800 border-t-2 border-bone-200/10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            See the complete walkthrough
          </h2>
        </div>

        {/* Video Container - YouTube Ready */}
        <div className="relative mb-12">
          {/* Placeholder for YouTube Video */}
          <div className="bg-charcoal-900 border-2 border-bone-200/20 rounded-sm aspect-video flex items-center justify-center shadow-[8px_8px_16px_rgba(0,0,0,0.9),-8px_-8px_16px_rgba(255,255,255,0.08)]">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 bg-bone-200/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-bone-200/60" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
              <h3 className="text-xl font-medium text-bone-200 mb-3">
                Talking Head Style Video Walkthrough
              </h3>
              <p className="text-bone-200/60 max-w-md mx-auto">
                Personal explanation from Sev covering:<br/>
                • Why existing bots fail<br/>
                • How AI agents adapt<br/>
                • Real trading results<br/>
                • Getting started guide
              </p>
              <div className="mt-6">
                <div className="inline-block px-4 py-2 bg-bone-200/10 rounded-sm text-xs text-bone-200/50">
                  [YouTube Video ID Placeholder]
                </div>
              </div>
            </div>
          </div>

          {/* Video Overlay Info */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-charcoal-900/90 backdrop-blur-sm border border-bone-200/20 rounded-sm p-4">
              <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-bone-200/10 rounded-full flex items-center justify-center">
                    <div className="w-4 h-4 bg-agents-extraction rounded-full"></div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-bone-200">Deep Dive: AI Trading Explained</p>
                    <p className="text-xs text-bone-200/60">Duration: ~12 minutes</p>
                  </div>
                </div>
                <div className="text-xs text-bone-200/50">
                  🎯 Real examples • 📊 Live results • 🚀 Getting started
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* CTA */}
        <div className="text-center">
          <p className="text-bone-200/70 mb-6">
            Ready to create your AI trading agent?
          </p>
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-agents-trading hover:bg-agents-trading/90 text-bone-200 px-8 py-4 rounded-sm font-medium transition-all duration-200 shadow-[0_0_25px_rgba(190,106,71,0.3)] hover:shadow-[0_0_35px_rgba(190,106,71,0.4)]"
          >
            Try free today
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}