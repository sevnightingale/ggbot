'use client'

import { Bot, TrendingUp, Brain, Trophy } from 'lucide-react'

export default function SocialProof() {
  // Stats - these could be fetched dynamically in the future
  const stats = [
    {
      icon: Bot,
      value: "470+",
      label: "Bots Created",
      subtext: "by traders worldwide"
    },
    {
      icon: TrendingUp,
      value: "5,900+",
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

        {/* ggArena Banner */}
        <div className="mb-12">
          <a
            href="https://app.ggbots.ai/arena"
            className="block relative overflow-hidden rounded-sm border-2 border-brass bg-gradient-to-r from-brass/10 via-brass/5 to-brass/10 p-6 md:p-8 hover:border-brass-light transition-colors group"
          >
            {/* Trophy icon */}
            <div className="absolute top-4 right-4 opacity-20 group-hover:opacity-30 transition-opacity">
              <Trophy size={80} className="text-brass" />
            </div>

            <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-flex items-center gap-1.5 bg-brass/20 text-brass px-2 py-0.5 rounded-full text-xs font-medium">
                    <span className="w-1.5 h-1.5 bg-brass rounded-full animate-pulse"></span>
                    LIVE NOW
                  </span>
                </div>
                <h3 className="text-2xl md:text-3xl font-bold text-ivory font-display mb-2">
                  ggArena Season 1
                </h3>
                <p className="text-ivory/70">
                  <span className="text-brass font-semibold">$2,500 prize pool</span> • 33 bots competing • Top 3 get funded live trading
                </p>
              </div>

              <div className="flex-shrink-0">
                <span className="inline-flex items-center gap-2 bg-brass hover:bg-brass-light text-obsidian px-6 py-3 rounded-sm font-medium transition-colors">
                  Watch the competition
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </span>
              </div>
            </div>
          </a>
        </div>

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
          Join 300+ traders building AI agents that trade while they sleep
        </p>
      </div>
    </section>
  )
}
