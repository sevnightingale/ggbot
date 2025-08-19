'use client'

import React from 'react'
import { Bot } from '@/store/botStore'

interface GGBotConfigProps {
  bot: Bot | null
  isOpen: boolean
  onClose: () => void
}

// Technical Indicators data (20 preprocessed indicators)
const technicalIndicators = {
  'Momentum Indicators': [
    { id: 'RSI', name: 'RSI', description: 'Relative Strength Index - Momentum oscillator (0-100)' },
    { id: 'Stochastic', name: 'Stochastic', description: 'Stochastic Oscillator - %K %D momentum indicator' },
    { id: 'Williams%R', name: 'Williams %R', description: 'Williams %R - Momentum oscillator (-100 to 0)' },
    { id: 'CCI', name: 'CCI', description: 'Commodity Channel Index - Momentum indicator' },
    { id: 'ROC', name: 'ROC', description: 'Rate of Change - Price momentum indicator' },
    { id: 'MFI', name: 'MFI', description: 'Money Flow Index - Volume-weighted RSI' }
  ],
  'Trend Indicators': [
    { id: 'MACD', name: 'MACD', description: 'Moving Average Convergence Divergence - Trend following' },
    { id: 'ADX', name: 'ADX', description: 'Average Directional Index - Trend strength indicator' },
    { id: 'Aroon', name: 'Aroon', description: 'Aroon Oscillator - Trending vs ranging market detector' },
    { id: 'Vortex', name: 'Vortex', description: 'Vortex Indicator - Trend momentum alignment' },
    { id: 'EMA', name: 'EMA', description: 'Exponential Moving Average - Trend following' },
    { id: 'TRIX', name: 'TRIX', description: 'Triple Exponential Average - Trend indicator' }
  ],
  'Volatility Indicators': [
    { id: 'BollingerBands', name: 'Bollinger Bands', description: 'Statistical volatility bands around price' },
    { id: 'BollingerBandsWidth', name: 'Bollinger Bands Width', description: 'Volatility/range detection indicator' },
    { id: 'ATR', name: 'ATR', description: 'Average True Range - Market volatility/choppiness' },
    { id: 'KeltnerChannel', name: 'Keltner Channel', description: 'Volatility-based channel indicator' }
  ],
  'Volume Indicators': [
    { id: 'VWAP', name: 'VWAP', description: 'Volume Weighted Average Price - Volume-price sentiment' },
    { id: 'OBV', name: 'OBV', description: 'On Balance Volume - Volume momentum indicator' }
  ],
  'Support/Resistance': [
    { id: 'DonchianChannel', name: 'Donchian Channel', description: 'Major liquidity zones and breakouts' },
    { id: 'ParabolicSAR', name: 'Parabolic SAR', description: 'Stop and Reverse - Trend reversal points' }
  ]
}

const GGBotConfig: React.FC<GGBotConfigProps> = ({ bot, isOpen, onClose }) => {
  const [isEditingName, setIsEditingName] = React.useState(false)
  const [botName, setBotName] = React.useState(bot?.name || '')
  const [hasChanges, setHasChanges] = React.useState(false)
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(new Set(['extraction']))
  const [isVisible, setIsVisible] = React.useState(false)
  const [isMounted, setIsMounted] = React.useState(false)
  
  // Extraction Agent states
  const [selectedDataSource, setSelectedDataSource] = React.useState('Technical Indicators')
  const [selectedIndicators, setSelectedIndicators] = React.useState<Set<string>>(new Set(['RSI', 'MACD', 'BollingerBands']))
  const [searchTerm, setSearchTerm] = React.useState('')

  // Helper functions for indicator management
  const toggleIndicator = (indicatorId: string) => {
    setSelectedIndicators(prev => {
      const newSet = new Set(prev)
      if (newSet.has(indicatorId)) {
        newSet.delete(indicatorId)
      } else {
        if (newSet.size < 12) { // Max 12 indicators
          newSet.add(indicatorId)
        }
      }
      setHasChanges(true)
      return newSet
    })
  }

  const filteredIndicators = React.useMemo(() => {
    const filtered: Record<string, typeof technicalIndicators['Momentum Indicators']> = {}
    
    Object.entries(technicalIndicators).forEach(([category, indicators]) => {
      const categoryFiltered = indicators.filter(indicator => 
        indicator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        indicator.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
      
      if (categoryFiltered.length > 0) {
        filtered[category] = categoryFiltered
      }
    })
    
    return filtered
  }, [searchTerm])

  React.useEffect(() => {
    if (bot) {
      setBotName(bot.name)
    }
  }, [bot])

  React.useEffect(() => {
    if (isOpen) {
      setIsMounted(true)
      // Small delay to ensure the component is mounted before animation
      setTimeout(() => setIsVisible(true), 50)
    } else {
      setIsVisible(false)
      // Keep component mounted during close animation
      setTimeout(() => setIsMounted(false), 500)
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

  if (!bot || !isMounted) return null

  return (
    <div className={`fixed inset-0 z-50 ${isOpen ? 'pointer-events-auto' : 'pointer-events-none'}`}>
      {/* Backdrop overlay */}
      <div 
        className={`fixed inset-0 bg-black transition-opacity duration-500 ${
          isVisible ? 'opacity-50' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Bottom sheet */}
      <div 
        className={`fixed bottom-0 left-0 right-0 transition-transform duration-500 ease-out ${
          isVisible ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ height: '85vh' }}
      >
        <div className="h-full bg-charcoal-900 relative flex flex-col">
          {/* Top sharp gradient border - matching dashboard style */}
          <div 
            className="absolute top-0 left-0 right-0 z-30"
            style={{
              height: '1px',
              background: 'linear-gradient(to right, transparent 0%, #e3e5e6 20%, #e3e5e6 80%, transparent 100%)',
              opacity: 0.6
            }}
          />

          {/* Sticky Top Bar */}
          <div className="flex-shrink-0 z-20 bg-charcoal-900" style={{
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

          {/* Content area - scrollable */}
          <div className="flex-1 overflow-y-auto">
            <div className="w-full max-w-none px-4 md:max-w-4xl md:mx-auto md:px-8 py-8">
              
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
                    <div className="p-6 space-y-6">
                      {/* Data Source Selection */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">DATA SOURCE</h4>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          <button
                            onClick={() => setSelectedDataSource('Technical Indicators')}
                            className={`px-3 py-1 text-xs rounded transition-colors ${
                              selectedDataSource === 'Technical Indicators'
                                ? 'bg-agent-extraction text-charcoal-900'
                                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                            }`}
                          >
                            Technical Indicators
                          </button>
                          <button
                            disabled
                            className="px-3 py-1 text-xs rounded bg-charcoal-800 text-gray-600 cursor-not-allowed"
                          >
                            Sentiment
                          </button>
                          <button
                            disabled
                            className="px-3 py-1 text-xs rounded bg-charcoal-800 text-gray-600 cursor-not-allowed"
                          >
                            News
                          </button>
                          <button
                            disabled
                            className="px-3 py-1 text-xs rounded bg-charcoal-800 text-gray-600 cursor-not-allowed"
                          >
                            On-chain
                          </button>
                        </div>
                      </div>

                      {/* Search and Filter */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">INDICATOR SELECTION</h4>
                          <span className="text-footnote text-gray-400">{selectedIndicators.size}/12 selected</span>
                        </div>
                        <div className="flex gap-4 mb-4">
                          <div className="flex-1 relative">
                            <input
                              type="text"
                              placeholder="Search indicators..."
                              value={searchTerm}
                              onChange={(e) => setSearchTerm(e.target.value)}
                              className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agent-extraction transition-colors"
                            />
                            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-gray-400">
                                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                              </svg>
                            </div>
                          </div>
                        </div>

                        {/* Selected Indicators */}
                        {selectedIndicators.size > 0 && (
                          <div className="mb-6">
                            <h5 className="text-xs text-gray-400 mb-2">Selected:</h5>
                            <div className="flex flex-wrap gap-2">
                              {Array.from(selectedIndicators).map(indicatorId => (
                                <span
                                  key={indicatorId}
                                  className="inline-flex items-center gap-1 px-2 py-1 bg-agent-extraction text-charcoal-900 text-xs rounded"
                                >
                                  {indicatorId}
                                  <button
                                    onClick={() => toggleIndicator(indicatorId)}
                                    className="hover:bg-black/20 rounded"
                                  >
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                                    </svg>
                                  </button>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Indicator Categories */}
                        <div className="space-y-6">
                          {Object.entries(filteredIndicators).map(([category, indicators]) => (
                            <div key={category}>
                              <h5 className="text-xs text-bone-200 font-medium mb-3 bg-charcoal-800 px-3 py-2 border-l-2 border-agent-extraction">
                                {category.toUpperCase()}
                              </h5>
                              <div className="space-y-2">
                                {indicators.map(indicator => {
                                  const isSelected = selectedIndicators.has(indicator.id)
                                  const isDisabled = !isSelected && selectedIndicators.size >= 12
                                  
                                  return (
                                    <button
                                      key={indicator.id}
                                      onClick={() => !isDisabled && toggleIndicator(indicator.id)}
                                      disabled={isDisabled}
                                      className={`w-full text-left p-3 border transition-colors ${
                                        isSelected
                                          ? 'bg-agent-extraction/10 border-agent-extraction text-bone-200'
                                          : isDisabled
                                          ? 'bg-charcoal-800/50 border-charcoal-700 text-gray-600 cursor-not-allowed'
                                          : 'bg-charcoal-800 border-charcoal-700 text-bone-200 hover:border-agent-extraction hover:bg-agent-extraction/5'
                                      }`}
                                    >
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                          <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                                            isSelected
                                              ? 'bg-agent-extraction border-agent-extraction'
                                              : 'border-gray-600'
                                          }`}>
                                            {isSelected && (
                                              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="text-charcoal-900">
                                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                                              </svg>
                                            )}
                                          </div>
                                          <div>
                                            <div className="text-footnote font-medium">{indicator.name}</div>
                                            <div className="text-xs text-gray-400 mt-1">{indicator.description}</div>
                                          </div>
                                        </div>
                                      </div>
                                    </button>
                                  )
                                })}
                              </div>
                            </div>
                          ))}
                        </div>
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
    </div>
  )
}

export default GGBotConfig