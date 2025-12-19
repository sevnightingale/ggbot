'use client'

import { Check, Zap, BarChart3, Brain } from 'lucide-react'

export default function Pricing() {
  const includedFeatures = [
    "Unlimited active ggbots",
    "All 7 frontier AI models",
    "5-minute to weekly analysis",
    "Paper & live trading modes",
    "Telegram signal publishing",
    "Real-time performance tracking"
  ]

  const costExamples = [
    {
      icon: Zap,
      scenario: "Budget Setup",
      config: "1-2 bots • Hourly checks • Economy reasoning",
      cost: "<$2/month",
      color: "text-[#10b981]"
    },
    {
      icon: BarChart3,
      scenario: "Active Trader",
      config: "3-5 bots • 15-30min frequency • Standard reasoning",
      cost: "$10-35/month",
      color: "text-brass"
    },
    {
      icon: Brain,
      scenario: "Power User",
      config: "5-10 bots • 5-15min frequency • Premium reasoning",
      cost: "$50-150/month",
      color: "text-[#8b5cf6]"
    }
  ]

  return (
    <section id="pricing" className="py-20 bg-carbon border-t-2 border-ivory/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-ivory mb-6 font-display">
            Pay only for what you use
          </h2>
          <p className="text-lg text-ivory/70 max-w-2xl mx-auto">
            No monthly fees. Free to build and test. Card required to activate.
          </p>
        </div>

        {/* Main Pricing Card */}
        <div className="max-w-4xl mx-auto mb-16">
          <div className="relative bg-obsidian border-2 border-brass rounded-sm p-8 md:p-12 shadow-[0_0_25px_rgba(193,168,125,0.3)]">
            {/* Badge */}
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <div className="bg-brass text-obsidian px-4 py-1 rounded-full text-sm font-medium">
                Usage-Based Pricing
              </div>
            </div>

            {/* Pricing Header */}
            <div className="text-center mb-8">
              <div className="mb-4">
                <span className="text-5xl font-bold text-ivory">$0</span>
                <span className="text-ivory/60 text-xl ml-2">base fee</span>
              </div>
              <p className="text-lg text-ivory/80 mb-2">
                Pay per AI decision • ~$0.003-0.09 each
              </p>
              <p className="text-sm text-ivory/60">
                Cost varies 30× between economy and premium reasoning tiers
              </p>
            </div>

            {/* Cost Range Examples */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              {costExamples.map((example, index) => {
                const Icon = example.icon
                return (
                  <div key={index} className="bg-carbon border border-ivory/10 rounded-sm p-4 text-center">
                    <Icon className={`${example.color} mx-auto mb-2`} size={24} />
                    <h4 className="font-semibold text-ivory text-sm mb-1">
                      {example.scenario}
                    </h4>
                    <p className="text-xs text-ivory/60 mb-3">
                      {example.config}
                    </p>
                    <div className={`${example.color} font-bold text-lg`}>
                      {example.cost}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Features List - 2 columns */}
            <div className="grid md:grid-cols-2 gap-3 mb-8">
              {includedFeatures.map((feature, index) => (
                <div key={index} className="flex items-start gap-3">
                  <Check className="text-brass flex-shrink-0 mt-0.5" size={16} />
                  <span className="text-ivory/80 text-sm">
                    {feature}
                  </span>
                </div>
              ))}
            </div>

            {/* CTA Button */}
            <a
              href="https://app.ggbots.ai/signup"
              className="block w-full text-center py-3 px-6 rounded-sm font-medium transition-all duration-200 bg-brass hover:bg-brass-light text-obsidian shadow-[0_0_15px_rgba(193,168,125,0.3)]"
            >
              Start Building for Free
            </a>
          </div>
        </div>

        {/* How It Works */}
        <div className="max-w-4xl mx-auto mb-12">
          <h3 className="text-2xl font-bold text-ivory mb-6 text-center font-display">
            You control the costs
          </h3>
          <div className="bg-obsidian border border-ivory/20 rounded-sm p-6 space-y-4">
            <div className="flex items-start gap-4">
              <div className="bg-brass/20 rounded-full p-2 flex-shrink-0">
                <Check className="text-brass" size={16} />
              </div>
              <div>
                <h4 className="text-ivory font-medium mb-1">Choose your reasoning tier</h4>
                <p className="text-sm text-ivory/70">
                  Economy (<span className="text-brass">~$0.003</span>), Standard (<span className="text-brass">~$0.01</span>), or Premium (<span className="text-brass">~$0.04-0.09</span>) per decision
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="bg-brass/20 rounded-full p-2 flex-shrink-0">
                <Check className="text-brass" size={16} />
              </div>
              <div>
                <h4 className="text-ivory font-medium mb-1">Set your frequency</h4>
                <p className="text-sm text-ivory/70">
                  Hourly checks (minimal cost) to 5-minute analysis (high activity)
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="bg-brass/20 rounded-full p-2 flex-shrink-0">
                <Check className="text-brass" size={16} />
              </div>
              <div>
                <h4 className="text-ivory font-medium mb-1">Scale your fleet</h4>
                <p className="text-sm text-ivory/70">
                  Run 1 bot for testing or 100 for diversification—costs scale linearly
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom guarantees */}
        <div className="text-center p-6 bg-obsidian border border-ivory/20 rounded-sm">
          <div className="flex flex-wrap justify-center gap-6 text-sm text-ivory/60">
            <span>• Free to build and test</span>
            <span>• Cancel anytime</span>
            <span>• Usage caps available</span>
            <span>• Full cost transparency</span>
          </div>
        </div>

        {/* Final CTA */}
        <div className="text-center mt-12">
          <p className="text-xl text-ivory/80 mb-6">
            Ready to let AI trade like you do?
          </p>
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-brass hover:bg-brass-light text-obsidian px-8 py-4 rounded-sm font-medium transition-all duration-200 text-lg shadow-[0_0_25px_rgba(193,168,125,0.3)] hover:shadow-[0_0_35px_rgba(193,168,125,0.4)]"
          >
            Start for free
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}