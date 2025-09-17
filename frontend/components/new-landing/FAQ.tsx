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
    <section className="py-20 bg-charcoal-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Frequently asked questions
          </h2>
        </div>

        <div className="space-y-4">
          {faqItems.map((item, index) => {
            const isOpen = openItems.includes(index)
            
            return (
              <div
                key={index}
                className="bg-charcoal-800 border border-bone-200/20 rounded-sm overflow-hidden"
              >
                {/* Question Button */}
                <button
                  onClick={() => toggleItem(index)}
                  className="w-full p-6 text-left flex items-center justify-between hover:bg-charcoal-700 transition-colors group"
                >
                  <h3 className="text-lg font-medium text-bone-200 pr-4 group-hover:text-bone-100 transition-colors">
                    {item.question}
                  </h3>
                  <div className="flex-shrink-0">
                    {isOpen ? (
                      <ChevronUp className="text-bone-200/60 group-hover:text-bone-200 transition-colors" size={20} />
                    ) : (
                      <ChevronDown className="text-bone-200/60 group-hover:text-bone-200 transition-colors" size={20} />
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
                    <div className="border-t border-bone-200/10 pt-4">
                      <p className="text-bone-200/70 leading-relaxed">
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
        <div className="text-center mt-12 p-8 bg-charcoal-800 border border-bone-200/20 rounded-sm">
          <p className="text-bone-200/70 mb-6">
            Still have questions? Reach out to me through email. Your feedback is quintessential to the future of ggbots.
          </p>
          <a
            href="mailto:sevnightingale@gmail.com"
            className="text-agents-extraction hover:text-agents-extraction/80 transition-colors font-medium"
          >
            Contact sev →
          </a>
        </div>
      </div>
    </section>
  )
}