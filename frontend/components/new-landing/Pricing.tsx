'use client'

import { Check } from 'lucide-react'

export default function Pricing() {
  const plans = [
    {
      name: "Free Plan",
      price: "Free",
      description: "Perfect for learning and testing strategies",
      features: [
        "Paper Trading",
        "User API LLM",
        "Basic strategy templates",
        "Community support"
      ],
      cta: "Sign up",
      href: "https://app.ggbots.ai/signup",
      popular: false
    },
    {
      name: "Base Plan", 
      price: "$49/mo",
      description: "For serious traders ready to automate",
      features: [
        "No API LLM costs",
        "Telegram Signals",
        "Live trading execution",
        "Priority support"
      ],
      cta: "Coming Soon",
      href: "#",
      popular: true
    },
    {
      name: "Premium Plan",
      price: "$149/mo", 
      description: "Advanced features for professional traders",
      features: [
        "Full Automation",
        "Plus paper trading",
        "Advanced AI models",
        "Custom indicators",
        "Portfolio management",
        "White-glove setup"
      ],
      cta: "Coming Soon",
      href: "#",
      popular: false
    }
  ]

  return (
    <section id="pricing" className="py-20 bg-charcoal-800 border-t-2 border-bone-200/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-bone-200 mb-6 font-display">
            Simple, transparent pricing
          </h2>
          <p className="text-lg text-bone-200/70 max-w-2xl mx-auto">
            Start free and upgrade as your trading grows. No hidden fees, cancel anytime.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-charcoal-900 border-2 rounded-sm p-8 ${
                plan.popular 
                  ? 'border-agents-decision shadow-[0_0_25px_rgba(44,190,119,0.3)]' 
                  : 'border-bone-200/20'
              }`}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-agents-decision text-bone-200 px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </div>
                </div>
              )}

              {/* Plan Header */}
              <div className="text-center mb-8">
                <h3 className="text-xl font-bold text-bone-200 mb-2 font-display">
                  {plan.name}
                </h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-bone-200 blur-sm">
                    {plan.price}
                  </span>
                  {plan.price !== "Free" && (
                    <span className="text-bone-200/60 ml-1 blur-sm">/month</span>
                  )}
                </div>
                <p className="text-sm text-bone-200/70">
                  {plan.description}
                </p>
              </div>

              {/* Features List */}
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start gap-3">
                    <Check className="text-agents-decision flex-shrink-0 mt-0.5" size={16} />
                    <span className="text-bone-200/80 text-sm">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              {plan.cta === "Coming Soon" ? (
                <div className="block w-full text-center py-3 px-6 rounded-sm font-medium bg-charcoal-700 text-bone-200/60 border border-bone-200/20 cursor-not-allowed">
                  {plan.cta}
                </div>
              ) : (
                <a
                  href={plan.href}
                  className="block w-full text-center py-3 px-6 rounded-sm font-medium transition-all duration-200 bg-charcoal-700 hover:bg-charcoal-600 text-bone-200 border border-bone-200/20 hover:border-bone-200/40"
                >
                  {plan.cta}
                </a>
              )}

            </div>
          ))}
        </div>

        {/* Bottom Note */}
        <div className="text-center mt-12 p-6 bg-charcoal-900 border border-bone-200/20 rounded-sm">
          <p className="text-bone-200/70 mb-4">
            <strong className="text-bone-200">Early Access Pricing:</strong> Lock in these rates during our beta period.
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-bone-200/60">
            <span>• 7-day free trial on all plans</span>
            <span>• Cancel anytime</span>
            <span>• 30-day money-back guarantee</span>
          </div>
        </div>

        {/* Final CTA */}
        <div className="text-center mt-12">
          <p className="text-xl text-bone-200/80 mb-6">
            Ready to let AI trade like you do?
          </p>
          <a
            href="https://app.ggbots.ai"
            className="inline-flex items-center gap-2 bg-agents-extraction hover:bg-agents-extraction/90 text-bone-200 px-8 py-4 rounded-sm font-medium transition-all duration-200 text-lg shadow-[0_0_25px_rgba(56,161,199,0.3)] hover:shadow-[0_0_35px_rgba(56,161,199,0.4)]"
          >
            Start your free trial
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}