import { redirect } from 'next/navigation'

export default function LandingPage() {
  // Temporary redirect to new-landing until we replace routing
  redirect('/new-landing')
}

export const metadata = {
  title: 'ggbots - AI trading agents that trade like you',
  description: 'deploy autonomous AI trading agents that analyze markets, adapt to conditions, and execute your strategies 24/7.',
  keywords: 'AI trading, autonomous trading bots, cryptocurrency trading, algorithmic trading',
}