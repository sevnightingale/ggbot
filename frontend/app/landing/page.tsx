import { Metadata } from 'next'
import Header from '@/components/new-landing/Header'
import Hero from '@/components/new-landing/Hero'
import SocialProof from '@/components/new-landing/SocialProof'
import Process from '@/components/new-landing/Process'
import PersonalStory from '@/components/new-landing/PersonalStory'
import Features from '@/components/new-landing/Features'
import FAQ from '@/components/new-landing/FAQ'
import Pricing from '@/components/new-landing/Pricing'
import Footer from '@/components/new-landing/Footer'

export const metadata: Metadata = {
  title: 'AI Trading Agents That Adapt Like You Do',
  description: 'Create autonomous AI trading bots that think, adapt, and execute your strategies 24/7. Built by traders, for traders. Start free, no credit card required.',
  keywords: ['AI trading', 'autonomous trading bots', 'cryptocurrency trading', 'algorithmic trading', 'adaptive bots', 'crypto trading bot', 'AI crypto', 'trading automation'],
  alternates: {
    canonical: 'https://ggbots.ai',
  },
  openGraph: {
    title: 'ggbots - AI Trading Agents That Adapt Like You Do',
    description: 'Create autonomous AI trading bots that think, adapt, and execute your strategies 24/7. Built by traders, for traders.',
    url: 'https://ggbots.ai',
    type: 'website',
  },
}

// JSON-LD Structured Data for rich search results
const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'ggbots',
  applicationCategory: 'FinanceApplication',
  operatingSystem: 'Web',
  description: 'Create autonomous AI trading bots that think, adapt, and execute your strategies 24/7. Built by traders, for traders.',
  url: 'https://ggbots.ai',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
    description: 'Free tier with 20 AI decisions per day',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.8',
    ratingCount: '47',
  },
  featureList: [
    'AI-powered trading decisions',
    'Multiple LLM providers (GPT-5, Claude, Grok, DeepSeek)',
    'Paper trading and live trading',
    'Real-time market data',
    'Customizable strategies',
  ],
}

export default function NewLandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <main className="min-h-screen bg-obsidian">
        <Header />
        <Hero />
        <SocialProof />
        <Process />
        <PersonalStory />
        <Features />
        <FAQ />
        <Pricing />
        <Footer />
      </main>
    </>
  )
}
