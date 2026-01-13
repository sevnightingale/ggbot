'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
    setIsMenuOpen(false)
  }

  return (
    <header className="sticky top-0 z-50 bg-obsidian/95 backdrop-blur-sm border-b border-ivory/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Legal Links */}
          <div className="flex items-center gap-6">
            <Image
              src="/ggbots_logo.png"
              alt="ggbots.ai"
              width={120}
              height={40}
              className="h-8 w-auto"
            />
            <div className="hidden sm:flex items-center gap-3 text-xs text-ivory/40">
              <Link href="/privacy" className="hover:text-ivory/70 transition-colors">
                Privacy
              </Link>
              <span>·</span>
              <Link href="/terms" className="hover:text-ivory/70 transition-colors">
                Terms
              </Link>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:block">
            <div className="flex items-center space-x-8">
              <button
                onClick={() => scrollToSection('demo')}
                className="text-ivory/80 hover:text-ivory transition-colors text-sm font-medium"
              >
                Demo
              </button>
              <button
                onClick={() => scrollToSection('process')}
                className="text-ivory/80 hover:text-ivory transition-colors text-sm font-medium"
              >
                How It Works
              </button>
              <button
                onClick={() => scrollToSection('features')}
                className="text-ivory/80 hover:text-ivory transition-colors text-sm font-medium"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                className="text-ivory/80 hover:text-ivory transition-colors text-sm font-medium"
              >
                Pricing
              </button>
            </div>
          </nav>

          {/* CTA Button & Mobile Menu */}
          <div className="flex items-center space-x-4">
            {/* Launch App CTA */}
            <a
              href="https://app.ggbots.ai"
              className="bg-brass hover:bg-brass-light text-obsidian px-6 py-2 rounded-sm font-medium transition-colors text-sm"
            >
              Launch App
            </a>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 text-ivory/80 hover:text-ivory"
            >
              {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-ivory/10">
            <div className="py-4 space-y-3">
              <button
                onClick={() => scrollToSection('demo')}
                className="block w-full text-left px-4 py-2 text-ivory/80 hover:text-ivory hover:bg-ivory/5 rounded-sm transition-colors"
              >
                Demo
              </button>
              <button
                onClick={() => scrollToSection('process')}
                className="block w-full text-left px-4 py-2 text-ivory/80 hover:text-ivory hover:bg-ivory/5 rounded-sm transition-colors"
              >
                How It Works
              </button>
              <button
                onClick={() => scrollToSection('features')}
                className="block w-full text-left px-4 py-2 text-ivory/80 hover:text-ivory hover:bg-ivory/5 rounded-sm transition-colors"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                className="block w-full text-left px-4 py-2 text-ivory/80 hover:text-ivory hover:bg-ivory/5 rounded-sm transition-colors"
              >
                Pricing
              </button>
              {/* Legal Links (Mobile) */}
              <div className="flex items-center gap-4 px-4 pt-3 mt-2 border-t border-ivory/10">
                <Link
                  href="/privacy"
                  className="text-ivory/50 hover:text-ivory text-sm transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Privacy
                </Link>
                <Link
                  href="/terms"
                  className="text-ivory/50 hover:text-ivory text-sm transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Terms
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}