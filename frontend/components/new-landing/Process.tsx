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
          <p className="text-lg text-bone-200/70 max-w-2xl mx-auto">
            From setup to execution in minutes. Our AI handles the complexity while you stay in control.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Step 1: Configure */}
          <div className="text-center">
            <div className="relative mb-8">
              {/* Step number */}
              <div className="absolute -top-4 -left-4 w-8 h-8 bg-agents-extraction text-bone-200 rounded-full flex items-center justify-center text-sm font-bold">
                1
              </div>
              
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
            <div className="relative mb-8">
              {/* Step number */}
              <div className="absolute -top-4 -left-4 w-8 h-8 bg-agents-decision text-bone-200 rounded-full flex items-center justify-center text-sm font-bold">
                2
              </div>
              
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
            <div className="relative mb-8">
              {/* Step number */}
              <div className="absolute -top-4 -left-4 w-8 h-8 bg-agents-trading text-bone-200 rounded-full flex items-center justify-center text-sm font-bold">
                3
              </div>
              
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

        {/* Process Flow Visualization */}
        <div className="mt-16 relative">
          <div className="flex justify-center items-center">
            {/* Flow arrows for desktop */}
            <div className="hidden md:flex items-center justify-between w-full max-w-4xl">
              <div className="flex-1"></div>
              <div className="flex items-center">
                <div className="w-16 h-0.5 bg-gradient-to-r from-agents-extraction to-agents-decision"></div>
                <div className="w-0 h-0 border-l-8 border-l-agents-decision border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
              </div>
              <div className="flex-1"></div>
              <div className="flex items-center">
                <div className="w-16 h-0.5 bg-gradient-to-r from-agents-decision to-agents-trading"></div>
                <div className="w-0 h-0 border-l-8 border-l-agents-trading border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
              </div>
              <div className="flex-1"></div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-16">
          <a
            href="https://app.ggbots.ai"
            className="bg-agents-trading hover:bg-agents-trading/90 text-bone-200 px-8 py-4 rounded-sm font-medium transition-all duration-200 shadow-[0_0_25px_rgba(190,106,71,0.3)] hover:shadow-[0_0_35px_rgba(190,106,71,0.4)]"
          >
            Launch App
          </a>
        </div>
      </div>
    </section>
  )
}