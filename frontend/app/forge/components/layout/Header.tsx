'use client'

import React from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { ThemeToggle } from '../shared/ThemeToggle'
import { UserProfile } from './UserProfile'

// Social icons as inline SVGs for size control
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

interface HeaderProps {
  className?: string
}

export function Header({}: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Logo + Nav */}
        <div className="flex items-center gap-6">
          <div className="h-8 w-8 flex items-center justify-center">
            <Image
              src="/ggbots_logo.png"
              alt="ggbots logo"
              width={28}
              height={28}
              className="h-7 w-auto"
            />
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-4">
            <Link
              href="/arena"
              className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Arena
            </Link>
          </nav>
        </div>

        {/* Right: Social + Theme + Profile */}
        <div className="flex items-center gap-3">
          {/* Social Links */}
          <div className="hidden sm:flex items-center gap-2">
            <a
              href="https://x.com/ggbots_ai"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
              title="Follow @ggbots_ai on X"
            >
              <TwitterIcon className="h-4 w-4" />
            </a>
            <a
              href="https://t.me/+ndI762EkfcszZTUx"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
              title="Join Telegram community"
            >
              <TelegramIcon className="h-4 w-4" />
            </a>
          </div>

          <ThemeToggle />
          <UserProfile />
        </div>
      </div>
    </header>
  )
}