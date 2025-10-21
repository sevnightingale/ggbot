'use client'

import { X } from 'lucide-react'
import Image from 'next/image'

export default function PersonalStory() {
  return (
    <section className="py-20 bg-charcoal-800 border-t-2 border-bone-200/10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative">
          {/* Letter styling container */}
          <div className="bg-charcoal-900 border border-bone-200/20 rounded-sm p-8 md:p-12 shadow-[8px_8px_16px_rgba(0,0,0,0.9),-8px_-8px_16px_rgba(255,255,255,0.08)]">
            
            {/* Letter header with photo on right */}
            <div className="flex flex-col md:flex-row items-start gap-8 mb-8">
              {/* Letter greeting */}
              <div className="flex-grow">
                <h3 className="text-2xl font-bold text-bone-200 font-display mb-2">
                  Dear trader,
                </h3>
                <p className="text-lg text-bone-200/80">
                  I&apos;m sev
                </p>
              </div>

              {/* Profile photo on right */}
              <div className="flex-shrink-0 flex flex-col items-center">
                <div className="w-24 h-24 rounded-full border-2 border-bone-200/20 overflow-hidden">
                  <Image
                    src="/pfp.jpg"
                    alt="Sev - Founder of ggbots"
                    width={96}
                    height={96}
                    className="w-full h-full object-cover"
                  />
                </div>
                <a
                  href="https://x.com/SevNightingale"
                  className="text-bone-200/60 hover:text-bone-200 transition-colors mt-2"
                  title="Follow Sev on X"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <X size={18} />
                </a>
              </div>
            </div>

            {/* Letter content */}
            <div className="space-y-6 text-bone-200/80 leading-relaxed">
              <p>
                I&apos;ve been a crypto day trader for the last 5 years. I&apos;ve tried many bots, lost $1,500 in 
                experimenting with them, and ultimately found they created more work for me.
              </p>

              <div>
                <p className="mb-3">
                  <strong className="text-bone-200">The problem with bots are:</strong>
                </p>
                <ol className="list-decimal list-inside space-y-2 ml-4">
                  <li>They don&apos;t adapt to changing market conditions</li>
                  <li>They follow rigid rules with zero reasoning</li>
                  <li>They can&apos;t think beyond the data you hardcode in</li>
                </ol>
              </div>

              <p>
                This is what drove me to build ggbots, an AI first trading bot that...
              </p>

              <ol className="list-decimal list-inside space-y-2 ml-4 text-bone-200">
                <li className="flex items-start gap-2">
                  <span className="text-agents-extraction font-medium">Can predict and adapt</span>
                  <span className="text-bone-200/80">to market changes in real-time</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-agents-decision font-medium">Follows trading strategies</span>
                  <span className="text-bone-200/80">without being stuck to rigid rules</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-agents-trading font-medium">Can think and rationalize</span>
                  <span className="text-bone-200/80">like I would, but never sleeps</span>
                </li>
              </ol>

              <div className="pt-6 border-t border-bone-200/20">
                <p className="text-bone-200/70 italic">
                  I&apos;m building this with input from experienced traders who understand the frustrations of existing solutions. 
                  <strong className="text-bone-200 not-italic"> Come join our journey</strong> as we create AI that trades like humans think.
                </p>
              </div>

              {/* Signature */}
              <div className="pt-4">
                <p className="text-bone-200 font-medium">
                  – sev
                </p>
                <p className="text-sm text-bone-200/60">
                  Founder, ggbots.ai
                </p>
              </div>
            </div>
          </div>

          {/* Decorative corner brackets */}
          <div className="absolute top-0 left-0 w-8 h-8">
            <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-bone-200/60 to-transparent"></div>
            <div className="absolute top-0 left-0 w-0.5 h-full bg-gradient-to-b from-bone-200/60 to-transparent"></div>
          </div>
          <div className="absolute bottom-0 right-0 w-8 h-8">
            <div className="absolute bottom-0 right-0 w-full h-0.5 bg-gradient-to-l from-bone-200/60 to-transparent"></div>
            <div className="absolute bottom-0 right-0 w-0.5 h-full bg-gradient-to-t from-bone-200/60 to-transparent"></div>
          </div>
        </div>

        {/* CTA after story */}
        <div className="text-center mt-12">
          <p className="text-bone-200/70 mb-6">
            Ready to try AI trading that actually adapts to markets?
          </p>
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-agents-extraction hover:bg-agents-extraction/90 text-bone-200 px-8 py-4 rounded-sm font-medium transition-all duration-200 shadow-[0_0_25px_rgba(56,161,199,0.3)] hover:shadow-[0_0_35px_rgba(56,161,199,0.4)]"
          >
            Start building your ggbot
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}