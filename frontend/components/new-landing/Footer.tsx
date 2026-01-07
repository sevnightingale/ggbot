import Link from 'next/link'
import Image from 'next/image'

// Social icons
function TwitterIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  )
}

function TelegramIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
    </svg>
  )
}

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-obsidian border-t border-ivory/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-8">
          {/* Logo & Copyright */}
          <div className="flex flex-col gap-4">
            <Image
              src="/ggbots_logo.png"
              alt="ggbots.ai"
              width={100}
              height={32}
              className="h-6 w-auto"
            />
            <p className="text-ivory/50 text-sm">
              © {currentYear} ggbots.ai. All rights reserved.
            </p>
          </div>

          {/* Links */}
          <div className="flex flex-col sm:flex-row gap-6 sm:gap-12">
            {/* Legal Links */}
            <div className="flex flex-col gap-3">
              <h4 className="text-ivory/70 text-xs font-semibold uppercase tracking-wider">Legal</h4>
              <div className="flex flex-col gap-2">
                <Link
                  href="/terms"
                  className="text-ivory/50 hover:text-ivory text-sm transition-colors"
                >
                  Terms of Service
                </Link>
                <Link
                  href="/privacy"
                  className="text-ivory/50 hover:text-ivory text-sm transition-colors"
                >
                  Privacy Policy
                </Link>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex flex-col gap-3">
              <h4 className="text-ivory/70 text-xs font-semibold uppercase tracking-wider">Community</h4>
              <div className="flex items-center gap-4">
                <a
                  href="https://x.com/ggbots_ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-ivory/50 hover:text-ivory transition-colors"
                  title="Follow @ggbots_ai on X"
                >
                  <TwitterIcon className="h-5 w-5" />
                </a>
                <a
                  href="https://t.me/+ndI762EkfcszZTUx"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-ivory/50 hover:text-ivory transition-colors"
                  title="Join Telegram community"
                >
                  <TelegramIcon className="h-5 w-5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
