'use client'

import React, { useState } from 'react'
import { HelpCircle, X, MessageCircle } from 'lucide-react'

export function HelpWidget() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      {/* Floating Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-[var(--agent-decision)] hover:bg-[var(--agent-decision)]/90 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center group"
        aria-label="Help"
      >
        <HelpCircle className="w-6 h-6 text-white" />
      </button>

      {/* Modal Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsOpen(false)
          }}
        >
          {/* Modal Content */}
          <div className="relative w-full max-w-md mx-4 p-6 bg-[var(--bg-secondary)] rounded-2xl border border-[var(--border)] shadow-2xl">
            {/* Close Button */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Content */}
            <div className="pr-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-[var(--agent-decision)]/20 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-5 h-5 text-[var(--agent-decision)]" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  Need Help?
                </h3>
              </div>

              <p className="text-[var(--text-secondary)] mb-6 leading-relaxed">
                Have questions or feedback? Join our Telegram community to get help from other traders and the ggbots team!
              </p>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <a
                  href="https://t.me/+ndI762EkfcszZTUx"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 bg-[var(--agent-decision)] hover:bg-[var(--agent-decision)]/90 text-white px-4 py-3 rounded-xl font-medium transition-colors text-center"
                  onClick={() => setIsOpen(false)}
                >
                  Join Telegram Group
                </a>
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-3 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}