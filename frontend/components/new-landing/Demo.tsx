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

        {/* Demo Container - Arcade Embed */}
        <div className="relative">
          {/* Arcade Demo Embed */}
          <div className="bg-charcoal-900 border-2 border-bone-200/20 rounded-sm overflow-hidden">
            <div style={{position: 'relative', paddingBottom: 'calc(51.71875% + 41px)', height: 0, width: '100%'}}>
              <iframe
                src="https://demo.arcade.software/q0l4MM1QqmUJLDwDTJin?embed&embed_mobile=tab&embed_desktop=inline&show_copy_link=true"
                title="Set Up and Configure Automated Trading Bots"
                frameBorder="0"
                loading="lazy"
                webkitallowfullscreen="true"
                mozallowfullscreen="true"
                allowFullScreen={true}
                allow="clipboard-write"
                style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', colorScheme: 'light'}}
              />
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