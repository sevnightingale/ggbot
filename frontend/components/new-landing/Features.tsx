'use client'

import { TrendingUp, Brain, Zap, BarChart } from 'lucide-react'

export default function Features() {
  const features = [
    {
      icon: TrendingUp,
      title: "Customized Indicators",
      description: "AI-powered technical analysis with custom indicators that adapt to market conditions and your trading style."
    },
    {
      icon: Brain,
      title: "Intelligent Decision Making",
      description: "Advanced reasoning algorithms that analyze market sentiment, news, and patterns beyond traditional indicators."
    },
    {
      icon: Zap,
      title: "Real-time Execution",
      description: "Lightning-fast trade execution with dynamic position sizing and risk management that adjusts to volatility."
    },
    {
      icon: BarChart,
      title: "Performance Analytics",
      description: "Comprehensive tracking and analysis of your bot's performance with detailed insights and optimization suggestions."
    }
  ]

  return (
    <section id="features" className="py-20 bg-obsidian">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-ivory mb-6 font-display">
            Features that make the difference
          </h2>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {features.map((feature, index) => {
            const IconComponent = feature.icon

            return (
              <div
                key={index}
                className="relative border-2 border-brass/40 bg-carbon p-8 rounded-sm shadow-[0_0_25px_rgba(193,168,125,0.2)]"
              >
                {/* Icon */}
                <div className="mb-6">
                  <IconComponent className="text-brass" size={48} />
                </div>

                {/* Content */}
                <h3 className="text-xl font-bold text-ivory mb-4 font-display">
                  {feature.title}
                </h3>
                <p className="text-ivory/70 leading-relaxed">
                  {feature.description}
                </p>

                {/* Decorative corner bracket */}
                <div className="absolute top-0 left-0 w-6 h-6">
                  <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-brass to-transparent opacity-60"></div>
                  <div className="absolute top-0 left-0 w-0.5 h-full bg-gradient-to-b from-brass to-transparent opacity-60"></div>
                </div>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}