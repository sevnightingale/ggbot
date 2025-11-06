'use client'

export default function Video() {
  return (
    <section className="py-20 bg-carbon border-t-2 border-ivory/10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-ivory mb-6 font-display">
            See the complete walkthrough
          </h2>
        </div>

        {/* Video Container - YouTube Ready */}
        <div className="relative mb-12">
          {/* Placeholder for YouTube Video */}
          <div className="bg-obsidian border-2 border-ivory/20 rounded-sm aspect-video flex items-center justify-center">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 bg-ivory/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-ivory/60" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
              <h3 className="text-xl font-medium text-ivory mb-3">
                Talking Head Style Video Walkthrough
              </h3>
              <p className="text-ivory/60 max-w-md mx-auto">
                Personal explanation from Sev covering:<br/>
                • Why existing bots fail<br/>
                • How AI agents adapt<br/>
                • Real trading results<br/>
                • Getting started guide
              </p>
              <div className="mt-6">
                <div className="inline-block px-4 py-2 bg-ivory/10 rounded-sm text-xs text-ivory/50">
                  [YouTube Video ID Placeholder]
                </div>
              </div>
            </div>
          </div>

          {/* Video Overlay Info */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-obsidian/90 backdrop-blur-sm border border-ivory/20 rounded-sm p-4">
              <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-ivory/10 rounded-full flex items-center justify-center">
                    <div className="w-4 h-4 bg-brass rounded-full"></div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-ivory">Deep Dive: AI Trading Explained</p>
                    <p className="text-xs text-ivory/60">Duration: ~12 minutes</p>
                  </div>
                </div>
                <div className="text-xs text-ivory/50">
                  Real examples • Live results • Getting started
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* CTA */}
        <div className="text-center">
          <p className="text-ivory/70 mb-6">
            Ready to create your AI trading agent?
          </p>
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-brass hover:bg-brass-light text-obsidian px-8 py-4 rounded-sm font-medium transition-all duration-200 shadow-[0_0_25px_rgba(193,168,125,0.3)] hover:shadow-[0_0_35px_rgba(193,168,125,0.4)]"
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