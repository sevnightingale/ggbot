'use client'

import React from 'react'
import { Bot } from '@/store/botStore'

interface GGBotConfigProps {
  bot: Bot | null
  isOpen: boolean
  onClose: () => void
}

const GGBotConfig: React.FC<GGBotConfigProps> = ({ bot, isOpen, onClose }) => {
  const [isEditingName, setIsEditingName] = React.useState(false)
  const [botName, setBotName] = React.useState(bot?.name || '')
  const [hasChanges, setHasChanges] = React.useState(false)
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(new Set(['extraction']))
  const [isVisible, setIsVisible] = React.useState(false)

  React.useEffect(() => {
    if (bot) {
      setBotName(bot.name)
    }
  }, [bot])

  React.useEffect(() => {
    if (isOpen) {
      // Small delay to ensure the component is mounted before animation
      setTimeout(() => setIsVisible(true), 50)
    } else {
      setIsVisible(false)
    }
  }, [isOpen])

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }

  const handleNameChange = (newName: string) => {
    setBotName(newName)
    setHasChanges(true)
  }

  const handleReset = () => {
    setBotName(bot?.name || '')
    setHasChanges(false)
  }

  const handleSave = () => {
    // TODO: Implement save functionality
    console.log('Saving bot config:', { name: botName })
    setHasChanges(false)
  }

  if (!bot) return null

  return (
    <div className={`fixed inset-0 z-50 ${isOpen ? 'pointer-events-auto' : 'pointer-events-none'}`}>
      {/* Backdrop overlay */}
      <div 
        className={`fixed inset-0 bg-black transition-opacity duration-[2000ms] ${
          isVisible ? 'opacity-50' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Bottom sheet */}
      <div 
        className={`fixed bottom-0 left-0 right-0 transition-transform duration-[2000ms] ease-out ${
          isVisible ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ height: '85vh' }}
      >
        <div className="h-full bg-charcoal-900 relative">
          {/* Top sharp gradient border - matching dashboard style */}
          <div 
            className="absolute top-0 left-0 right-0 z-30"
            style={{
              height: '3px',
              background: 'linear-gradient(to right, transparent 0%, #e3e5e6 20%, #e3e5e6 80%, transparent 100%)'
            }}
          />

          {/* Sticky Top Bar */}
          <div className="sticky top-0 z-20 bg-charcoal-900" style={{
            boxShadow: '0 8px 16px -8px rgba(22, 22, 24, 1)'
          }}>
            <div className="w-full max-w-none px-4 md:max-w-4xl md:mx-auto md:px-8 py-8">
              <div className="flex items-center justify-between">
                {/* Left side - Bot name */}
                <div className="flex items-center gap-2">
                  {isEditingName ? (
                    <input
                      type="text"
                      value={botName}
                      onChange={(e) => handleNameChange(e.target.value)}
                      onBlur={() => setIsEditingName(false)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') setIsEditingName(false)
                      }}
                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-subheader focus:border-agent-extraction transition-colors"
                      autoFocus
                    />
                  ) : (
                    <>
                      <h2 
                        className="text-subheader text-bone-200 font-medium cursor-pointer hover:text-bone-100 transition-colors"
                        onClick={() => setIsEditingName(true)}
                        title="Click to edit name"
                      >
                        {botName}
                      </h2>
                      <button
                        onClick={() => setIsEditingName(true)}
                        className="text-gray-400 hover:text-bone-200 transition-colors"
                        title="Edit name"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                        </svg>
                      </button>
                    </>
                  )}
                  {hasChanges && (
                    <>
                      <span className="text-gray-500">•</span>
                      <span className="text-footnote text-orange-400">unsaved changes</span>
                    </>
                  )}
                </div>

                {/* Right side - Action buttons */}
                <div className="flex items-center gap-6">
                  {/* Reset button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleReset}
                      disabled={!hasChanges}
                      className={`floating-action-btn ${hasChanges ? 'floating-action-enabled' : 'floating-action-disabled'}`}
                      title="Reset changes"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8c-.45-.83-.7-1.79-.7-2.8 0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z"/>
                      </svg>
                    </button>
                    <span className={`text-footnote ${hasChanges ? 'text-bone-300' : 'text-gray-500'}`}>reset</span>
                  </div>

                  {/* Save button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSave}
                      disabled={!hasChanges}
                      className={`floating-action-btn ${hasChanges ? 'floating-action-enabled' : 'floating-action-disabled'}`}
                      title="Save changes"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                      </svg>
                    </button>
                    <span className={`text-footnote ${hasChanges ? 'text-bone-300' : 'text-gray-500'}`}>save</span>
                  </div>

                  {/* Exit button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={onClose}
                      className="floating-action-btn floating-action-enabled"
                      title="Close config"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                      </svg>
                    </button>
                    <span className="text-footnote text-bone-300">exit</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Content area */}
          <div className="h-full overflow-y-auto">
            <div className="w-full max-w-none px-4 md:max-w-4xl md:mx-auto md:px-8 pb-8">
              
              {/* Extraction Agent Section */}
              <div className="mb-8">
                {!expandedSections.has('extraction') ? (
                  <button
                    onClick={() => toggleSection('extraction')}
                    className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                  >
                    <h3 className="text-subheader text-bone-200 font-medium">Extraction Agent</h3>
                    <span className="text-xl transition-transform duration-200" style={{ color: '#38a1c7' }}>
                      ▶
                    </span>
                  </button>
                ) : (
                  <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                    <div 
                      onClick={() => toggleSection('extraction')}
                      className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                    >
                      <h3 className="text-subheader text-bone-200 font-medium">Extraction Agent</h3>
                      <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#38a1c7' }}>
                        ▶
                      </span>
                    </div>
                    <div className="p-6">
                      <p className="text-footnote text-gray-400 mb-4">Market data extraction and indicator configuration</p>
                      {/* Minimal content structure - to be expanded later */}
                      <div className="space-y-4">
                        <div className="text-footnote text-gray-500">Indicator configuration will go here...</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Decision Agent Section */}
              <div className="mb-8">
                {!expandedSections.has('decision') ? (
                  <button
                    onClick={() => toggleSection('decision')}
                    className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                  >
                    <h3 className="text-subheader text-bone-200 font-medium">Decision Agent</h3>
                    <span className="text-xl transition-transform duration-200" style={{ color: '#2cbe77' }}>
                      ▶
                    </span>
                  </button>
                ) : (
                  <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                    <div 
                      onClick={() => toggleSection('decision')}
                      className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                    >
                      <h3 className="text-subheader text-bone-200 font-medium">Decision Agent</h3>
                      <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#2cbe77' }}>
                        ▶
                      </span>
                    </div>
                    <div className="p-6">
                      <p className="text-footnote text-gray-400 mb-4">AI decision making and strategy configuration</p>
                      {/* Minimal content structure - to be expanded later */}
                      <div className="space-y-4">
                        <div className="text-footnote text-gray-500">Strategy configuration will go here...</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Trading Agent Section */}
              <div className="mb-8">
                {!expandedSections.has('trading') ? (
                  <button
                    onClick={() => toggleSection('trading')}
                    className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                  >
                    <h3 className="text-subheader text-bone-200 font-medium">Trading Agent</h3>
                    <span className="text-xl transition-transform duration-200" style={{ color: '#be6a47' }}>
                      ▶
                    </span>
                  </button>
                ) : (
                  <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                    <div 
                      onClick={() => toggleSection('trading')}
                      className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                    >
                      <h3 className="text-subheader text-bone-200 font-medium">Trading Agent</h3>
                      <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#be6a47' }}>
                        ▶
                      </span>
                    </div>
                    <div className="p-6">
                      <p className="text-footnote text-gray-400 mb-4">Exchange connections and risk management</p>
                      {/* Minimal content structure - to be expanded later */}
                      <div className="space-y-4">
                        <div className="text-footnote text-gray-500">Trading configuration will go here...</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default GGBotConfig