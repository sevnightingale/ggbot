'use client'

export default function Demo() {
  return (
    <section id="demo" className="py-20 bg-charcoal-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Interactive Demo
          </h2>
          <p className="text-lg text-bone-200/70 max-w-2xl mx-auto">
            See ggbots in action
          </p>
        </div>

        {/* Demo Container - Ready for Arcade Embed */}
        <div className="relative">
          {/* Placeholder for Arcade Demo */}
          <div className="bg-charcoal-900 border-2 border-bone-200/20 rounded-sm aspect-video flex items-center justify-center">
            <div className="text-center">
              <div className="w-24 h-24 mx-auto mb-6 bg-bone-200/10 rounded-full flex items-center justify-center">
                <div className="w-8 h-8 bg-agents-extraction rounded-full animate-pulse"></div>
              </div>
              <h3 className="text-xl font-medium text-bone-200 mb-2">Interactive Demo Space</h3>
              <p className="text-bone-200/60">
                Arcade demo will be embedded here showing:<br/>
                Bot creation → Configuration → Dashboard → Live trades
              </p>
            </div>
          </div>

          {/* Demo Features Overlay */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-charcoal-900/80 backdrop-blur-sm border border-bone-200/20 rounded-sm p-4">
              <div className="flex flex-wrap justify-center gap-4 text-sm text-bone-200/70">
                <span className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-agents-extraction rounded-full"></div>
                  Bot Creation Process
                </span>
                <span className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-agents-decision rounded-full"></div>
                  Strategy Configuration
                </span>
                <span className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-agents-trading rounded-full"></div>
                  Live Performance
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-12">
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-agents-decision hover:bg-agents-decision/90 text-bone-200 px-8 py-4 rounded-sm font-medium transition-all duration-200 shadow-[0_0_25px_rgba(44,190,119,0.3)] hover:shadow-[0_0_35px_rgba(44,190,119,0.4)]"
          >
            Try it yourself
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}