'use client'

import { Settings, Shield, Rocket } from 'lucide-react'

export default function Process() {
  return (
    <section id="process" className="py-20 bg-obsidian">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-ivory mb-6 font-display">
            Automate your trading in 3 easy steps
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Step 1: Configure */}
          <div className="text-center">
            <div className="mb-8">
              {/* Icon container with border-based styling */}
              <div className="w-24 h-24 mx-auto bg-carbon rounded-sm flex items-center justify-center border-2 border-brass/40">
                <Settings className="text-brass" size={40} />
              </div>
            </div>

            <h3 className="text-xl font-bold text-ivory mb-4 font-display">
              Configure your agents
            </h3>
            <p className="text-ivory/70">
              Set up your trading preferences, risk tolerance, and strategy parameters. Customize indicators, timeframes, and market conditions your AI should respond to.
            </p>
          </div>

          {/* Step 2: Guardrails */}
          <div className="text-center">
            <div className="mb-8">
              {/* Icon container */}
              <div className="w-24 h-24 mx-auto bg-carbon rounded-sm flex items-center justify-center border-2 border-brass/40">
                <Shield className="text-brass" size={40} />
              </div>
            </div>

            <h3 className="text-xl font-bold text-ivory mb-4 font-display">
              Set your guardrails
            </h3>
            <p className="text-ivory/70">
              Define position sizes, maximum drawdown, stop-loss levels, and portfolio limits. Your AI operates within these boundaries to protect your capital.
            </p>
          </div>

          {/* Step 3: Launch */}
          <div className="text-center">
            <div className="mb-8">
              {/* Icon container */}
              <div className="w-24 h-24 mx-auto bg-carbon rounded-sm flex items-center justify-center border-2 border-brass/40">
                <Rocket className="text-brass" size={40} />
              </div>
            </div>

            <h3 className="text-xl font-bold text-ivory mb-4 font-display">
              Launch your AI bot
            </h3>
            <p className="text-ivory/70">
              Deploy your configured agent to start trading. Monitor performance, adjust strategies, and watch your AI adapt to changing market conditions in real-time.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-16">
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-brass hover:bg-brass-light text-obsidian px-8 py-4 rounded-sm font-medium transition-colors"
          >
            Build your first bot in 2 minutes
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>

      </div>
    </section>
  )
}