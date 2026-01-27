'use client'

import dynamic from 'next/dynamic'
import { RefreshCw } from 'lucide-react'

/**
 * Arena Loading Skeleton
 * Shown while the Web3-enabled ArenaWithStaking component loads
 */
function ArenaLoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header skeleton */}
      <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="flex items-center justify-between px-4 py-3 max-w-7xl mx-auto">
          <div className="w-7 h-7 rounded bg-[var(--bg-secondary)] animate-pulse" />
          <div className="w-40 h-9 rounded-xl bg-[var(--bg-secondary)] animate-pulse" />
        </div>
      </header>

      {/* Hero skeleton */}
      <div className="border-b border-[var(--border)]">
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          <div className="w-32 h-8 mx-auto mb-6 rounded-full bg-[var(--bg-secondary)] animate-pulse" />
          <div className="w-64 h-12 mx-auto mb-4 rounded bg-[var(--bg-secondary)] animate-pulse" />
          <div className="w-48 h-8 mx-auto mb-4 rounded bg-[var(--bg-secondary)] animate-pulse" />
          <div className="w-80 h-6 mx-auto mb-8 rounded bg-[var(--bg-secondary)] animate-pulse" />
          <div className="w-40 h-12 mx-auto rounded-xl bg-[var(--bg-secondary)] animate-pulse" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <RefreshCw className="h-8 w-8 animate-spin text-[var(--accent)]" />
          <span className="text-[var(--text-muted)]">Loading arena...</span>
        </div>
      </div>
    </div>
  )
}

/**
 * Lazy-load ArenaWithStaking (includes wagmi/RainbowKit providers)
 *
 * SSR is disabled because Web3 libraries need client-side rendering.
 * This keeps the main app bundle lean - Web3 code (~65KB) only loads
 * when users visit /arena.
 */
const ArenaWithStaking = dynamic(
  () => import('@/components/arena/ArenaWithStaking'),
  {
    ssr: false,
    loading: () => <ArenaLoadingSkeleton />
  }
)

export default function ArenaPage() {
  return <ArenaWithStaking />
}
