'use client'

export default function Demo() {
  return (
    <section id="demo" className="py-12 bg-charcoal-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Demo Container - Arcade Embed */}
        <div className="relative overflow-hidden">
          <div style={{position: 'relative', paddingBottom: 'calc(51.71875% + 41px)', height: 0, width: '100%'}}>
            <iframe
              src="https://demo.arcade.software/q0l4MM1QqmUJLDwDTJin?embed&embed_mobile=tab&embed_desktop=inline&show_copy_link=true"
              title="Set Up and Configure Automated Trading Bots"
              frameBorder="0"
              loading="lazy"
              allowFullScreen={true}
              allow="clipboard-write"
              style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', colorScheme: 'light'}}
            />
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