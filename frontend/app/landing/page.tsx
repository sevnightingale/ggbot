import Header from '@/components/new-landing/Header'
import Hero from '@/components/new-landing/Hero'
import Demo from '@/components/new-landing/Demo'
import Process from '@/components/new-landing/Process'
import PersonalStory from '@/components/new-landing/PersonalStory'
import Features from '@/components/new-landing/Features'
import FAQ from '@/components/new-landing/FAQ'
import Pricing from '@/components/new-landing/Pricing'

export default function NewLandingPage() {
  return (
    <main className="min-h-screen bg-charcoal-900">
      <Header />
      <Hero />
      <Demo />
      <Process />
      <PersonalStory />
      <Features />
      <FAQ />
      <Pricing />
    </main>
  )
}

export const metadata = {
  title: 'ggbots - AI trading agents that adapt like you do',
  description: 'Create autonomous AI trading bots that think, adapt, and execute your strategies 24/7. Built by traders, for traders.',
  keywords: 'AI trading, autonomous trading bots, cryptocurrency trading, algorithmic trading, adaptive bots',
}