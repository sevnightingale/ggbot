'use client'

import { useState } from 'react'
import { Menu, X } from 'lucide-react'

export function TopNav() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <nav className="relative z-50">
      <div className="flex items-center justify-between px-6 py-4 border-b border-bone-200/60">
        <div className="flex items-center gap-8">
          <h1 className="text-2xl font-display font-bold">ggbots.ai</h1>
        </div>
        
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="p-2 hover:bg-charcoal-800 transition-colors"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Menu overlay */}
      {isMenuOpen && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsMenuOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 mr-6 bg-charcoal-800 border border-bone-200/80 p-4 min-w-[200px] z-50">
            <ul className="space-y-2">
              <li>
                <a 
                  href="/app" 
                  className="block px-4 py-2 hover:bg-charcoal-700 transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  My Bots
                </a>
              </li>
              <li>
                <a 
                  href="/settings" 
                  className="block px-4 py-2 hover:bg-charcoal-700 transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Settings
                </a>
              </li>
              <li>
                <a 
                  href="/docs" 
                  className="block px-4 py-2 hover:bg-charcoal-700 transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Docs
                </a>
              </li>
              <li>
                <a 
                  href="/profile" 
                  className="block px-4 py-2 hover:bg-charcoal-700 transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Profile
                </a>
              </li>
            </ul>
          </div>
        </>
      )}
    </nav>
  )
}