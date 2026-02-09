'use client'

import dynamic from 'next/dynamic'
import { Loader2 } from 'lucide-react'

/**
 * Loading skeleton shown while Web3 component loads.
 */
function HyperliquidLoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <header className="border-b border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="flex items-center justify-between px-4 py-3 max-w-3xl mx-auto">
          <div className="w-7 h-7 rounded bg-[var(--bg-secondary)] animate-pulse" />
          <div className="w-24 h-5 rounded bg-[var(--bg-secondary)] animate-pulse" />
        </div>
      </header>
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="w-64 h-9 rounded bg-[var(--bg-secondary)] animate-pulse mb-2" />
        <div className="w-80 h-5 rounded bg-[var(--bg-secondary)] animate-pulse mb-8" />
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
          <span className="text-[var(--text-muted)]">Loading...</span>
        </div>
      </div>
    </div>
  )
}

/**
 * Lazy-load HyperliquidSetup (includes wagmi/RainbowKit for Arbitrum).
 * SSR disabled — Web3 libraries need client-side rendering.
 */
const HyperliquidSetup = dynamic(
  () => import('@/components/hyperliquid/HyperliquidSetup'),
  {
    ssr: false,
    loading: () => <HyperliquidLoadingSkeleton />
  }
)

export default function HyperliquidPage() {
  return <HyperliquidSetup />
}
