'use client'

import { Bot, TrendingUp, Brain } from 'lucide-react'

export default function SocialProof() {
  const stats = [
    {
      icon: Bot,
      value: "322+",
      label: "Active Users",
      subtext: "building AI agents"
    },
    {
      icon: TrendingUp,
      value: "7,500+",
      label: "Trades Executed",
      subtext: "paper & live"
    },
    {
      icon: Brain,
      value: "86K+",
      label: "AI Decisions",
      subtext: "and learning"
    }
  ]

  return (
    <section className="py-16 bg-obsidian border-y border-ivory/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {stats.map((stat, index) => {
            const IconComponent = stat.icon
            return (
              <div
                key={index}
                className="text-center p-6 rounded-sm border border-ivory/10 bg-carbon"
              >
                <IconComponent className="mx-auto mb-4 text-brass" size={32} />
                <div className="text-3xl md:text-4xl font-bold text-ivory mb-1 font-display">
                  {stat.value}
                </div>
                <div className="text-ivory/80 font-medium">
                  {stat.label}
                </div>
                <div className="text-ivory/50 text-sm">
                  {stat.subtext}
                </div>
              </div>
            )
          })}
        </div>

        {/* Trust line */}
        <p className="text-center text-ivory/50 text-sm mt-8">
          Join 322+ traders building AI agents that trade while they sleep
        </p>
      </div>
    </section>
  )
}
