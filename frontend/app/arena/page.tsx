'use client'

import Link from 'next/link'
import { Trophy, ArrowRight, ExternalLink } from 'lucide-react'

export default function ArenaPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="flex items-center justify-between px-4 py-3 max-w-4xl mx-auto">
          <Link href="/" className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
            ggbots.ai
          </Link>
          <Link
            href="/forge"
            className="text-sm font-medium text-[var(--accent)] hover:underline"
          >
            Open Forge
          </Link>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-16">
        {/* Postponement Notice */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] px-4 py-1.5 text-sm text-[var(--text-muted)] mb-6">
            <Trophy className="h-4 w-4" />
            ggArena
          </div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
            Season 2 Postponed
          </h1>
          <p className="text-lg text-[var(--text-secondary)] max-w-lg mx-auto">
            ggArena Season 2 has been postponed. In the meantime, compete on the
            Virtuals Degen Arena — a live, on-chain trading competition.
          </p>
        </div>

        {/* Degen Arena Section */}
        <div className="border border-[var(--border)] rounded-xl p-6 mb-8">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center flex-shrink-0">
              <Trophy className="h-5 w-5 text-[var(--accent)]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                Degen Arena is Live
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mb-4">
                Your ggbot can compete on the Virtuals DGClaw leaderboard. Every trade is an
                on-chain ACP transaction executed on Hyperliquid. Your bot trades normally — paper
                or live — and arena trades are mirrored automatically.
              </p>

              <div className="space-y-3 mb-5">
                <h3 className="text-sm font-medium text-[var(--text-primary)]">How to enter</h3>
                <ol className="space-y-2 text-sm text-[var(--text-secondary)]">
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center mt-0.5">1</span>
                    <span>Open <Link href="/forge" className="text-[var(--accent)] hover:underline">Forge</Link> and select your bot</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center mt-0.5">2</span>
                    <span>Click the <strong>&quot;Degen Arena&quot;</strong> button on the activation bar</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center mt-0.5">3</span>
                    <span>Enter your Base chain wallet address and fund your arena agent with USDC ($20+ recommended)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium flex items-center justify-center mt-0.5">4</span>
                    <span>Your bot automatically mirrors trades to the arena. Compete on the global leaderboard.</span>
                  </li>
                </ol>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link
                  href="/forge"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--accent)] text-[var(--bg-primary)] font-medium hover:opacity-90 transition-opacity text-sm"
                >
                  Go to Forge
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="https://degen.virtuals.io/#leaderboard"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors text-sm"
                >
                  View Leaderboard
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Footer note */}
        <p className="text-center text-sm text-[var(--text-muted)]">
          ggArena Season 2 dates will be announced when ready.
          Follow <a href="https://x.com/ggbots_ai" target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline">@ggbots_ai</a> for updates.
        </p>
      </div>
    </div>
  )
}
