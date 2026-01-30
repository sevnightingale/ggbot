'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function FAQ() {
  const [openItems, setOpenItems] = useState<number[]>([])

  const toggleItem = (index: number) => {
    setOpenItems(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    )
  }

  const faqItems = [
    {
      question: "How is ggbots different from traditional trading bots?",
      answer: "Traditional bots follow rigid, pre-programmed rules that break when market conditions change. ggbots uses AI agents that can reason, adapt, and make decisions based on real-time market analysis - just like a human trader, but without emotions or fatigue."
    },
    {
      question: "Do I need coding or technical analysis experience?",
      answer: "No coding required. While basic trading knowledge helps, ggbots is designed for traders of all experience levels. Our AI handles the complex analysis and decision-making, while you set your preferences and risk parameters through our intuitive interface."
    },
    {
      question: "What exchanges and trading pairs are supported?",
      answer: "Currently we support major cryptocurrency exchanges including BitMEX, with plans to expand to additional exchanges. We focus on the most liquid trading pairs to ensure optimal execution and minimal slippage for your strategies."
    },
    {
      question: "How does the AI learn and adapt my trading style?",
      answer: "Our AI agents analyze your trading preferences, risk tolerance, and historical decisions to understand your style. They continuously learn from market conditions and adapt their strategies while staying within your defined guardrails and risk parameters."
    },
    {
      question: "What happens if the market conditions change dramatically?",
      answer: "Unlike rigid bots that break during market volatility, our AI agents are designed to recognize and adapt to changing conditions. They can adjust position sizes, modify strategies, and even pause trading if conditions become too uncertain - protecting your capital first."
    }
  ]

  return (
    <section className="py-20 bg-obsidian">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-ivory mb-6 font-display">
            Frequently asked questions
          </h2>
        </div>

        <div className="space-y-4">
          {faqItems.map((item, index) => {
            const isOpen = openItems.includes(index)

            return (
              <div
                key={index}
                className="bg-carbon border border-ivory/20 rounded-sm overflow-hidden"
              >
                {/* Question Button */}
                <button
                  onClick={() => toggleItem(index)}
                  className="w-full p-6 text-left flex items-center justify-between hover:bg-[#1a1a1c] transition-colors group"
                >
                  <h3 className="text-lg font-medium text-ivory pr-4 group-hover:text-ivory/90 transition-colors">
                    {item.question}
                  </h3>
                  <div className="flex-shrink-0">
                    {isOpen ? (
                      <ChevronUp className="text-ivory/60 group-hover:text-ivory transition-colors" size={20} />
                    ) : (
                      <ChevronDown className="text-ivory/60 group-hover:text-ivory transition-colors" size={20} />
                    )}
                  </div>
                </button>

                {/* Answer Content */}
                <div className={`transition-all duration-300 ease-in-out ${
                  isOpen
                    ? 'max-h-96 opacity-100'
                    : 'max-h-0 opacity-0'
                } overflow-hidden`}>
                  <div className="px-6 pb-6">
                    <div className="border-t border-ivory/10 pt-4">
                      <p className="text-ivory/70 leading-relaxed">
                        {item.answer}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Still have questions CTA */}
        <div className="text-center mt-12 p-8 bg-carbon border border-ivory/20 rounded-sm">
          <p className="text-ivory/70 mb-6">
            Still have questions? Join our community and chat with other traders building AI bots.
          </p>
          <a
            href="https://t.me/ggbotsai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-brass hover:text-brass-light transition-colors font-medium"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
            </svg>
            Join the Telegram community →
          </a>
        </div>
      </div>
    </section>
  )
}