'use client'

import { TrendingUp, Brain, Zap, BarChart } from 'lucide-react'

export default function Features() {
  const features = [
    {
      icon: TrendingUp,
      title: "Customized Indicators",
      description: "AI-powered technical analysis with custom indicators that adapt to market conditions and your trading style.",
      color: "agents-extraction"
    },
    {
      icon: Brain,
      title: "Intelligent Decision Making", 
      description: "Advanced reasoning algorithms that analyze market sentiment, news, and patterns beyond traditional indicators.",
      color: "agents-decision"
    },
    {
      icon: Zap,
      title: "Real-time Execution",
      description: "Lightning-fast trade execution with dynamic position sizing and risk management that adjusts to volatility.",
      color: "agents-trading"
    },
    {
      icon: BarChart,
      title: "Performance Analytics",
      description: "Comprehensive tracking and analysis of your bot's performance with detailed insights and optimization suggestions.",
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
                <p className="text-bone-200/70 leading-relaxed">
                  {feature.description}
                </p>

                {/* Decorative corner bracket */}
                <div className="absolute top-0 left-0 w-6 h-6">
                  <div className={`absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-${colorClass} to-transparent opacity-60`}></div>
                  <div className={`absolute top-0 left-0 w-0.5 h-full bg-gradient-to-b from-${colorClass} to-transparent opacity-60`}></div>
                </div>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}