'use client'

import React from 'react'
import { Bot } from '@/store/botStore'

interface GGBotConfigProps {
  bot: Bot | null
  isOpen: boolean
  onClose: () => void
}

const GGBotConfig: React.FC<GGBotConfigProps> = ({ bot, isOpen, onClose }) => {
  if (!isOpen || !bot) return null

  return (
    <>
      {/* Backdrop overlay */}
      <div 
        className={`fixed inset-0 bg-black transition-opacity duration-300 z-40 ${
          isOpen ? 'bg-opacity-50' : 'bg-opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />

      {/* Bottom sheet */}
      <div 
        className={`fixed bottom-0 left-0 right-0 z-50 transition-transform duration-500 ease-out ${
          isOpen ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ height: '85vh' }}
      >
        <div className="h-full bg-charcoal-900 relative">
          {/* Top gradient border - matching open trades styling */}
          <div 
            className="absolute top-0 left-0 right-0 h-px"
            style={{
              background: 'linear-gradient(to right, transparent 0%, #e3e5e6 30%, #e3e5e6 70%, transparent 100%)',
              opacity: 0.6
            }}
          />

          {/* Content area */}
          <div className="h-full p-8 overflow-y-auto">
            {/* Blank content area for now */}
          </div>
        </div>
      </div>
    </>
  )
}

export default GGBotConfig