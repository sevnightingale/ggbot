import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg-secondary)] mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-[var(--text-secondary)]">
          <div className="flex items-center gap-2">
            <span>© 2025 ggbots.ai</span>
          </div>

          <div className="flex items-center gap-6">
            <Link
              href="/terms"
              className="hover:text-[var(--text-primary)] transition-colors"
              target="_blank"
            >
              Terms of Service
            </Link>
            <Link
              href="/privacy"
              className="hover:text-[var(--text-primary)] transition-colors"
              target="_blank"
            >
              Privacy Policy
            </Link>
            <a
              href="https://t.me/+ndI762EkfcszZTUx"
              className="hover:text-[var(--text-primary)] transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Telegram Community
            </a>
            <a
              href="mailto:support@ggbots.ai"
              className="hover:text-[var(--text-primary)] transition-colors"
            >
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
