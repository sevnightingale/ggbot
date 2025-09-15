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
        <div className="h-6 w-6 flex items-center justify-center">
          <Image
            src="/ggbots_logo.svg"
            alt="ggbots logo"
            width={20}
            height={20}
            className="h-5 w-auto [filter:brightness(0)_saturate(100%)_invert(12%)_sepia(12%)_saturate(584%)_hue-rotate(200deg)_brightness(95%)_contrast(89%)] dark:[filter:brightness(0)_saturate(100%)_invert(89%)_sepia(13%)_saturate(282%)_hue-rotate(165deg)_brightness(106%)_contrast(90%)]"
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