import { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { ThemeProvider } from '@/lib/theme'

export const metadata: Metadata = {
  title: {
    default: 'Blog',
    template: '%s | ggbots Blog',
  },
  description: 'Learn about vibe trading, AI-autonomous trading, and building trading bots. Educational content for traders exploring AI.',
  keywords: ['vibe trading', 'AI trading', 'trading bots', 'autonomous trading', 'crypto trading'],
  alternates: {
    types: {
      'application/rss+xml': '/feed.xml',
    },
  },
}

export default function BlogLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ThemeProvider>
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--bg-secondary)]">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="font-semibold">ggbots</span>
          </Link>
          <nav className="flex gap-6 text-sm">
            <Link
              href="/blog"
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              All Posts
            </Link>
            <Link
              href="/arena"
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Arena
            </Link>
            <Link
              href="/signup"
              className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors font-medium"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      {/* Content */}
      <main>{children}</main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] bg-[var(--bg-secondary)] mt-16">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-[var(--text-muted)]">
            <p>&copy; {new Date().getFullYear()} ggbots. All rights reserved.</p>
            <div className="flex gap-6">
              <Link href="/terms" className="hover:text-[var(--text-primary)] transition-colors">
                Terms
              </Link>
              <Link href="/privacy" className="hover:text-[var(--text-primary)] transition-colors">
                Privacy
              </Link>
              <Link href="/feed.xml" className="hover:text-[var(--text-primary)] transition-colors">
                RSS
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
    </ThemeProvider>
  )
}
