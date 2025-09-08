'use client'

import { TrendingUp, Brain, Zap, BarChart } from 'lucide-react'

export default function Features() {
  const features = [
    {
      icon: TrendingUp,
      title: "Customized Indicators",
      description: "AI-powered technical analysis with custom indicators that adapt to market conditions and your trading style.",
      demoLink: "#",
      color: "agents-extraction"
    },
    {
      icon: Brain,
      title: "Intelligent Decision Making", 
      description: "Advanced reasoning algorithms that analyze market sentiment, news, and patterns beyond traditional indicators.",
      demoLink: "#",
      color: "agents-decision"
    },
    {
      icon: Zap,
      title: "Real-time Execution",
      description: "Lightning-fast trade execution with dynamic position sizing and risk management that adjusts to volatility.",
      demoLink: "#",
      color: "agents-trading"
    },
    {
      icon: BarChart,
      title: "Performance Analytics",
      description: "Comprehensive tracking and analysis of your bot's performance with detailed insights and optimization suggestions.",
      demoLink: "#",
      color: "agents-extraction"
    }
  ]

  return (
    <section id="features" className="py-20 bg-charcoal-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Features that make the difference
          </h2>
          <p className="text-lg text-bone-200/70 max-w-2xl mx-auto">
            Advanced AI capabilities that go beyond basic automation - giving you the edge in dynamic crypto markets.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {features.map((feature, index) => {
            const IconComponent = feature.icon
            const colorClass = feature.color as keyof typeof colorMap
            
            // Color mapping for dynamic classes
            const colorMap = {
              'agents-extraction': {
                icon: 'text-agents-extraction',
                border: 'border-agents-extraction/40',
                shadow: 'shadow-[0_0_25px_rgba(56,161,199,0.3)]',
                button: 'bg-agents-extraction/20 text-agents-extraction border-agents-extraction/40'
              },
              'agents-decision': {
                icon: 'text-agents-decision', 
                border: 'border-agents-decision/40',
                shadow: 'shadow-[0_0_25px_rgba(44,190,119,0.3)]',
                button: 'bg-agents-decision/20 text-agents-decision border-agents-decision/40'
              },
              'agents-trading': {
                icon: 'text-agents-trading',
                border: 'border-agents-trading/40', 
                shadow: 'shadow-[0_0_25px_rgba(190,106,71,0.3)]',
                button: 'bg-agents-trading/20 text-agents-trading border-agents-trading/40'
              }
            }
            
            return (
              <div
                key={index}
                className={`relative border-2 ${colorMap[colorClass].border} bg-charcoal-800 p-8 rounded-sm ${colorMap[colorClass].shadow}`}
              >
                {/* Icon */}
                <div className="mb-6">
                  <IconComponent className={`${colorMap[colorClass].icon}`} size={48} />
                </div>

                {/* Content */}
                <h3 className="text-xl font-bold text-bone-200 mb-4 font-display">
                  {feature.title}
                </h3>
                <p className="text-bone-200/70 mb-6 leading-relaxed">
                  {feature.description}
                </p>

                {/* Demo/Link Section */}
                <div className="space-y-4">
                  <a
                    href={feature.demoLink}
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-sm border transition-colors ${colorMap[colorClass].button} hover:bg-opacity-30`}
                  >
                    View live demo
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>

                  {/* Video walkthrough placeholder */}
                  <div className="bg-charcoal-900 border border-bone-200/20 rounded-sm aspect-video flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-3 bg-bone-200/10 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6 text-bone-200/60" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z"/>
                        </svg>
                      </div>
                      <p className="text-sm text-bone-200/60">
                        Video walkthrough of {feature.title.toLowerCase()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Decorative corner bracket */}
                <div className="absolute top-0 left-0 w-6 h-6">
                  <div className={`absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-${colorClass} to-transparent opacity-60`}></div>
                  <div className={`absolute top-0 left-0 w-0.5 h-full bg-gradient-to-b from-${colorClass} to-transparent opacity-60`}></div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <p className="text-bone-200/70 mb-6">
            Ready to experience next-generation AI trading?
          </p>
          <a
            href="https://app.ggbots.ai"
            className="bg-agents-decision hover:bg-agents-decision/90 text-bone-200 px-8 py-4 rounded-sm font-medium transition-all duration-200 shadow-[0_0_25px_rgba(44,190,119,0.3)] hover:shadow-[0_0_35px_rgba(44,190,119,0.4)]"
          >
            Launch App
          </a>
        </div>
      </div>
    </section>
  )
}