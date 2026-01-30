import Link from 'next/link'
import { Metadata } from 'next'

export const metadata: Metadata = {
  robots: {
    index: true,
    follow: true,
  },
}

export default function LegalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <header className="border-b border-[var(--border)] bg-[var(--bg-secondary)]">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-[var(--text-primary)] hover:text-[var(--accent)] font-bold text-xl">
            ggbots
          </Link>
          <div className="flex gap-6 text-sm">
            <Link href="/terms" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
              Terms
            </Link>
            <Link href="/privacy" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
              Privacy
            </Link>
          </div>
        </div>
      </header>
      {children}
    </div>
  )
}
