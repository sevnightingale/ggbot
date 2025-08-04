'use client'

import { useState } from 'react'
import { useBotStore } from '@/store/bot'
import { ExtractionConfig } from '@/types'

interface ExtractionConfigFormProps {
  activeTab: number
  config: ExtractionConfig | null
}

const commonSymbols = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
  'MATIC/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
]

// Technical indicators without timeframes
const baseIndicators = [
  { name: 'RSI', label: 'RSI (Relative Strength Index)', description: 'Momentum oscillator (0-100)' },
  { name: 'MACD', label: 'MACD', description: 'Moving Average Convergence Divergence' },
  { name: 'BollingerBands', label: 'Bollinger Bands', description: 'Volatility bands around moving average' },
  { name: 'ATR', label: 'ATR (Average True Range)', description: 'Volatility measurement' },
  { name: 'EMA', label: 'EMA (Exponential Moving Average)', description: 'Trend-following indicator' },
  { name: 'VWAP', label: 'VWAP (Volume Weighted Average Price)', description: 'Volume-based price average' },
  { name: 'Stochastic', label: 'Stochastic Oscillator', description: 'Momentum indicator (0-100)' },
  { name: 'Williams%R', label: 'Williams %R', description: 'Momentum indicator (-100 to 0)' },
  { name: 'OBV', label: 'OBV (On-Balance Volume)', description: 'Volume-based momentum' },
  { name: 'CCI', label: 'CCI (Commodity Channel Index)', description: 'Momentum oscillator' }
]

const availableTimeframes = [
  { value: '15m', label: '15 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' }
]

// Premium indicator
const premiumIndicators = [
  { name: 'ggshot', label: 'ggShot Signals', description: 'Premium AI-powered trading signals', premium: true }
]


export function ExtractionConfigForm({ activeTab, config }: ExtractionConfigFormProps) {
  const { updateAgentConfig, setError } = useBotStore()
  const [isSaving, setIsSaving] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  
  // Parse existing indicators to get selected indicators and timeframes
  const parseExistingIndicators = (indicators: string[]) => {
    const selectedIndicators = new Set<string>()
    const indicatorTimeframes: Record<string, string[]> = {}
    
    indicators.forEach(indicator => {
      const parts = indicator.split('_')
      if (parts.length >= 2) {
        const timeframe = parts[parts.length - 1]
        const indicatorName = parts.slice(0, -1).join('_')
        selectedIndicators.add(indicatorName)
        if (!indicatorTimeframes[indicatorName]) {
          indicatorTimeframes[indicatorName] = []
        }
        if (!indicatorTimeframes[indicatorName].includes(timeframe)) {
          indicatorTimeframes[indicatorName].push(timeframe)
        }
      }
    })
    
    return { selectedIndicators, indicatorTimeframes }
  }
  
  const existingIndicators = config?.sources?.crypto_indicators_mcp?.indicators || []
  const { selectedIndicators: initialSelected, indicatorTimeframes: initialTimeframes } = parseExistingIndicators(existingIndicators)
  
  const [formData, setFormData] = useState<ExtractionConfig>({
    symbols: config?.symbols || [],
    sources: {
      crypto_indicators_mcp: {
        enabled: config?.sources?.crypto_indicators_mcp?.enabled ?? true,
        indicators: existingIndicators
      }
    }
  })
  
  const [selectedIndicators, setSelectedIndicators] = useState<Set<string>>(initialSelected)
  const [indicatorTimeframes, setIndicatorTimeframes] = useState<Record<string, string[]>>(initialTimeframes)
  const [ggShotEnabled, setGgShotEnabled] = useState(false)

  // Helper function to rebuild indicator list with timeframes
  const rebuildIndicatorList = (currentSelected: Set<string>, currentTimeframes: Record<string, string[]>) => {
    const indicators: string[] = []
    
    currentSelected.forEach(indicator => {
      const timeframes = currentTimeframes[indicator] || []
      timeframes.forEach(timeframe => {
        indicators.push(`${indicator}_${timeframe}`)
      })
    })
    
    return indicators
  }

  const toggleIndicator = (indicatorName: string) => {
    const newSelected = new Set(selectedIndicators)
    let newTimeframes = { ...indicatorTimeframes }
    
    if (newSelected.has(indicatorName)) {
      newSelected.delete(indicatorName)
      // Remove timeframes for this indicator
      delete newTimeframes[indicatorName]
    } else {
      newSelected.add(indicatorName)
      // Add default timeframes (15m and 1h)
      newTimeframes = { ...newTimeframes, [indicatorName]: ['15m', '1h'] }
    }
    
    setSelectedIndicators(newSelected)
    setIndicatorTimeframes(newTimeframes)
    
    // Update form data
    const newIndicators = rebuildIndicatorList(newSelected, newTimeframes)
    setFormData(prev => ({
      ...prev,
      sources: {
        ...prev.sources,
        crypto_indicators_mcp: {
          ...prev.sources.crypto_indicators_mcp,
          indicators: newIndicators
        }
      }
    }))
  }

  const toggleTimeframe = (indicatorName: string, timeframe: string) => {
    const currentTimeframes = indicatorTimeframes[indicatorName] || []
    const newTimeframeList = currentTimeframes.includes(timeframe)
      ? currentTimeframes.filter(tf => tf !== timeframe)
      : [...currentTimeframes, timeframe]
    
    const newTimeframes = {
      ...indicatorTimeframes,
      [indicatorName]: newTimeframeList
    }
    
    setIndicatorTimeframes(newTimeframes)
    
    // Update form data
    const newIndicators = rebuildIndicatorList(selectedIndicators, newTimeframes)
    setFormData(prev => ({
      ...prev,
      sources: {
        ...prev.sources,
        crypto_indicators_mcp: {
          ...prev.sources.crypto_indicators_mcp,
          indicators: newIndicators
        }
      }
    }))
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      setError(null)
      await updateAgentConfig('extraction', formData)
      setJustSaved(true)
      setTimeout(() => setJustSaved(false), 2000) // Clear feedback after 2 seconds
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save configuration')
    } finally {
      setIsSaving(false)
    }
  }

  const toggleSymbol = (symbol: string) => {
    setFormData(prev => ({
      ...prev,
      symbols: prev.symbols.includes(symbol)
        ? prev.symbols.filter(s => s !== symbol)
        : [...prev.symbols, symbol]
    }))
  }



  const renderSymbolsTab = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium mb-3">Trading Symbols</h3>
        <p className="text-sm text-bone-400 mb-4">
          Select the cryptocurrency pairs you want to analyze. Common pairs are shown below.
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {commonSymbols.map(symbol => (
            <button
              key={symbol}
              onClick={() => toggleSymbol(symbol)}
              className={`p-3 text-sm border transition-colors ${
                formData.symbols.includes(symbol)
                  ? 'bg-agents-extraction/20 border-agents-extraction text-bone-200'
                  : 'bg-charcoal-700 border-bone-200/80 text-bone-300 hover:border-bone-200/90'
              }`}
            >
              {symbol}
            </button>
          ))}
        </div>
        
        <div className="mt-4">
          <label className="block text-sm font-medium mb-2">Custom Symbol</label>
          <input
            type="text"
            placeholder="e.g., DOGE/USDT"
            className="w-full p-3 bg-charcoal-700 border border-bone-200/80 text-bone-200 placeholder-bone-400"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const value = e.currentTarget.value.trim()
                if (value && !formData.symbols.includes(value)) {
                  toggleSymbol(value)
                  e.currentTarget.value = ''
                }
              }
            }}
          />
        </div>
      </div>
    </div>
  )


  const renderDataSourcesTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Data Sources</h3>
        <p className="text-sm text-bone-400 mb-4">
          Configure data sources for market analysis. ggShot provides high-confidence signals, while Technical Indicators offer detailed market analysis.
        </p>
      </div>


      {/* Technical Indicators */}
      <div className="p-4 bg-charcoal-700/50 border border-bone-200/60">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-medium">Technical Indicators</h4>
            <p className="text-sm text-bone-400">20 pre-processed indicators with timeframe integration (15m & 1h)</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.sources.crypto_indicators_mcp?.enabled}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                sources: {
                  ...prev.sources,
                  crypto_indicators_mcp: {
                    ...prev.sources.crypto_indicators_mcp!,
                    enabled: e.target.checked
                  }
                }
              }))}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-charcoal-600 peer-focus:outline-none peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-5 after:w-5 after:transition-all peer-checked:bg-agents-extraction"></div>
          </label>
        </div>

        {formData.sources.crypto_indicators_mcp?.enabled && (
          <div className="space-y-6">
            {/* Premium ggShot Indicator */}
            <div>
              <h4 className="text-sm font-medium text-bone-300 mb-3 flex items-center gap-2">
                Premium Signals
                <span className="text-xs bg-yellow-400/20 text-yellow-400 px-2 py-1 rounded">PREMIUM</span>
              </h4>
              {premiumIndicators.map(indicator => (
                <div key={indicator.name} className="p-4 bg-gradient-to-r from-yellow-400/10 to-orange-400/10 border border-yellow-400/40 rounded">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="text-yellow-400">⭐</div>
                      <div>
                        <h5 className="font-medium text-yellow-400">{indicator.label}</h5>
                        <p className="text-sm text-bone-300">{indicator.description}</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={ggShotEnabled}
                        onChange={(e) => setGgShotEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-charcoal-600 peer-focus:outline-none peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-5 after:w-5 after:transition-all peer-checked:bg-yellow-500"></div>
                    </label>
                  </div>
                </div>
              ))}
            </div>

            {/* Technical Indicators */}
            <div>
              <h4 className="text-sm font-medium text-bone-300 mb-3">Technical Indicators</h4>
              <div className="space-y-4">
                {baseIndicators.map(indicator => (
                  <div key={indicator.name} className="p-4 bg-charcoal-600/50 border border-bone-200/40 rounded">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={selectedIndicators.has(indicator.name)}
                          onChange={() => toggleIndicator(indicator.name)}
                          className="w-5 h-5 text-agents-extraction bg-charcoal-700 border-bone-200/60 rounded focus:ring-agents-extraction"
                        />
                        <div>
                          <h5 className="font-medium text-bone-200">{indicator.label}</h5>
                          <p className="text-sm text-bone-400">{indicator.description}</p>
                        </div>
                      </div>
                    </div>
                    
                    {selectedIndicators.has(indicator.name) && (
                      <div className="ml-8 pl-4 border-l border-bone-200/30">
                        <p className="text-sm text-bone-300 mb-2">Select timeframes:</p>
                        <div className="flex flex-wrap gap-2">
                          {availableTimeframes.map(timeframe => (
                            <button
                              key={timeframe.value}
                              onClick={() => toggleTimeframe(indicator.name, timeframe.value)}
                              className={`px-3 py-1 text-sm border rounded transition-colors ${
                                (indicatorTimeframes[indicator.name] || []).includes(timeframe.value)
                                  ? 'bg-agents-extraction/20 border-agents-extraction text-bone-200'
                                  : 'bg-charcoal-700 border-bone-200/60 text-bone-300 hover:border-bone-200/80'
                              }`}
                            >
                              {timeframe.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {/* Selection summary */}
              <div className="mt-4 p-3 bg-bone-200/10 border border-bone-200/60 rounded">
                <p className="text-sm text-bone-300">
                  <strong>{selectedIndicators.size}</strong> indicators selected with{' '}
                  <strong>{formData.sources.crypto_indicators_mcp!.indicators.length}</strong> total timeframe combinations
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 0: return renderSymbolsTab()
      case 1: return renderDataSourcesTab()
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      {renderTabContent()}
      
      {/* Save Button */}
      <div className="flex justify-end pt-4 border-t border-bone-200/60">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={`px-6 py-3 font-medium transition-colors ${
            justSaved
              ? 'bg-green-500 text-white'
              : isSaving
                ? 'bg-agents-extraction/50 text-charcoal-900/70 cursor-not-allowed'
                : 'bg-agents-extraction hover:bg-agents-extraction/80 text-charcoal-900'
          }`}
        >
          {justSaved ? '✓ Saved!' : isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}