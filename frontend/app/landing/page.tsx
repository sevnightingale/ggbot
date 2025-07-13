import Hero from '@/components/landing/Hero'
import Features from '@/components/landing/Features'
import AgentShowcase from '@/components/landing/AgentShowcase'
import Footer from '@/components/landing/Footer'

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-charcoal-900">
      <Hero />
      <AgentShowcase />
      <Features />
      <Footer />
    </main>
  )
}

export const metadata = {
  title: 'ggbots - AI trading agents that trade like you',
  description: 'deploy autonomous AI trading agents that analyze markets, adapt to conditions, and execute your strategies 24/7.',
  keywords: 'AI trading, autonomous trading bots, cryptocurrency trading, algorithmic trading',
}