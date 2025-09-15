'use client'

import { Settings, Shield, Rocket } from 'lucide-react'

export default function Process() {
  return (
    <section id="process" className="py-20 bg-charcoal-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Automate your trading in 3 easy steps
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Step 1: Configure */}
          <div className="text-center">
            <div className="mb-8">
              {/* Icon container with neumorphic styling */}
              <div className="w-24 h-24 mx-auto bg-charcoal-800 rounded-sm flex items-center justify-center shadow-[8px_8px_16px_rgba(0,0,0,0.9),-8px_-8px_16px_rgba(255,255,255,0.08)]">
                <Settings className="text-agents-extraction" size={40} />
              </div>
            </div>
            
            <h3 className="text-xl font-bold text-bone-200 mb-4 font-display">
              Configure your agents
            </h3>
            <p className="text-bone-200/70">
              Set up your trading preferences, risk tolerance, and strategy parameters. Customize indicators, timeframes, and market conditions your AI should respond to.
            </p>
          </div>

          {/* Step 2: Guardrails */}
          <div className="text-center">
            <div className="mb-8">
              {/* Icon container */}
              <div className="w-24 h-24 mx-auto bg-charcoal-800 rounded-sm flex items-center justify-center shadow-[8px_8px_16px_rgba(0,0,0,0.9),-8px_-8px_16px_rgba(255,255,255,0.08)]">
                <Shield className="text-agents-decision" size={40} />
              </div>
            </div>
            
            <h3 className="text-xl font-bold text-bone-200 mb-4 font-display">
              Set your guardrails
            </h3>
            <p className="text-bone-200/70">
              Define position sizes, maximum drawdown, stop-loss levels, and portfolio limits. Your AI operates within these boundaries to protect your capital.
            </p>
          </div>

          {/* Step 3: Launch */}
          <div className="text-center">
            <div className="mb-8">
              {/* Icon container */}
              <div className="w-24 h-24 mx-auto bg-charcoal-800 rounded-sm flex items-center justify-center shadow-[8px_8px_16px_rgba(0,0,0,0.9),-8px_-8px_16px_rgba(255,255,255,0.08)]">
                <Rocket className="text-agents-trading" size={40} />
              </div>
            </div>
            
            <h3 className="text-xl font-bold text-bone-200 mb-4 font-display">
              Launch your AI bot
            </h3>
            <p className="text-bone-200/70">
              Deploy your configured agent to start trading. Monitor performance, adjust strategies, and watch your AI adapt to changing market conditions in real-time.
            </p>
          </div>
        </div>

      </div>
    </section>
  )
}