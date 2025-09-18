'use client'

import React from 'react'
import Image from 'next/image'
import { ThemeToggle } from '../shared/ThemeToggle'
import { UserProfile } from './UserProfile'

interface HeaderProps {
  className?: string
}

export function Header({}: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="h-8 w-8 flex items-center justify-center">
          <Image
            src="/ggbots_logo.svg"
            alt="ggbots logo"
            width={28}
            height={28}
            className="h-7 w-auto text-[var(--text-primary)]"
            style={{
              filter: 'brightness(0) saturate(100%) invert(var(--logo-invert, 12%)) sepia(12%) saturate(584%) hue-rotate(200deg) brightness(95%) contrast(89%)'
            }}
          />
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <UserProfile />
        </div>
      </div>
    </header>
  )
}