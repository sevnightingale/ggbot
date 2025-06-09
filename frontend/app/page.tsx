import { PageWrapper } from '@/components/ui/PageWrapper'

export default function Home() {
  return (
    <PageWrapper>
      <div className="container mx-auto px-6 py-8">
        <h1 className="text-4xl font-display font-bold mb-8">ggbots</h1>
        <p className="text-xl text-bone-300 mb-8">Your Edge, Amplified.</p>
        
        <div className="grid gap-6 max-w-2xl">
          <a 
            href="/bot/default"
            className="block p-6 bg-charcoal-800 border border-bone-200/20 rounded-lg hover:border-bone-200/40 transition-colors"
          >
            <h2 className="text-2xl font-display font-bold mb-2">Default Bot</h2>
            <p className="text-bone-300">Click to view and configure your trading bot</p>
          </a>
        </div>
      </div>
    </PageWrapper>
  )
}