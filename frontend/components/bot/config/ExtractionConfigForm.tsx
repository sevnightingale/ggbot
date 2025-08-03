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

// ggShot 20 indicators with sophisticated pre-processing
const availableIndicators = [
  'RSI_15m', 'RSI_1h', 'MACD_15m', 'MACD_1h', 'BollingerBands_15m', 'BollingerBands_1h',
  'ATR_15m', 'ATR_1h', 'EMA_15m', 'EMA_1h', 'VWAP_15m', 'VWAP_1h',
  'Stochastic_15m', 'Stochastic_1h', 'Williams%R_15m', 'Williams%R_1h', 
  'OBV_15m', 'OBV_1h', 'CCI_15m', 'CCI_1h'
]


export function ExtractionConfigForm({ activeTab, config }: ExtractionConfigFormProps) {
  const { updateAgentConfig, setError } = useBotStore()
  const [isSaving, setIsSaving] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  
  const [formData, setFormData] = useState<ExtractionConfig>({
    symbols: config?.symbols || [],
    timeframes: [], // No longer used - integrated into indicators
    sources: {
      ggshot: {
        enabled: config?.sources?.ggshot?.enabled ?? false
      },
      crypto_indicators_mcp: {
        enabled: config?.sources?.crypto_indicators_mcp?.enabled ?? true,
        indicators: config?.sources?.crypto_indicators_mcp?.indicators || [],
        use_llm_selection: false, // Removed
        llm_interpretation: false, // Removed
        llm_model: '' // Removed
      },
      tradingview: {
        enabled: false, // Hidden for now
        strategy: ''
      },
      yfinance: {
        enabled: false // Hidden for now
      }
    }
  })

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

  const toggleIndicator = (indicator: string) => {
    setFormData(prev => ({
      ...prev,
      sources: {
        ...prev.sources,
        crypto_indicators_mcp: {
          ...prev.sources.crypto_indicators_mcp!,
          indicators: prev.sources.crypto_indicators_mcp!.indicators.includes(indicator)
            ? prev.sources.crypto_indicators_mcp!.indicators.filter(i => i !== indicator)
            : [...prev.sources.crypto_indicators_mcp!.indicators, indicator]
        }
      }
    }))
  }

  const toggleSource = (source: string) => {
    if (source === 'ggshot') {
      setFormData(prev => ({
        ...prev,
        sources: {
          ...prev.sources,
          ggshot: {
            ...prev.sources.ggshot!,
            enabled: !prev.sources.ggshot!.enabled
          }
        }
      }))
    }
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

      {/* ggShot Signals */}
      <div className="p-4 bg-charcoal-700/50 border border-bone-200/60">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-medium">ggShot Signals</h4>
            <p className="text-sm text-bone-400">High-confidence trading signals from ggShot Telegram channel</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.sources.ggshot?.enabled}
              onChange={() => toggleSource('ggshot')}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-charcoal-600 peer-focus:outline-none peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-5 after:w-5 after:transition-all peer-checked:bg-agents-extraction"></div>
          </label>
        </div>

        {formData.sources.ggshot?.enabled && (
          <div className="p-3 bg-blue-900/20 border border-blue-500/60">
            <p className="text-sm text-blue-200">
              ✅ ggShot signals will be processed for trading decisions. These are manually curated, high-confidence signals.
            </p>
          </div>
        )}
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
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Available Indicators (with timeframes)</label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                {availableIndicators.map(indicator => (
                  <button
                    key={indicator}
                    onClick={() => toggleIndicator(indicator)}
                    className={`p-2 text-xs border transition-colors ${
                      formData.sources.crypto_indicators_mcp!.indicators.includes(indicator)
                        ? 'bg-agents-extraction/20 border-agents-extraction text-bone-200'
                        : 'bg-charcoal-600 border-bone-200/80 text-bone-300 hover:border-bone-200/90'
                    }`}
                  >
                    {indicator}
                  </button>
                ))}
              </div>
            </div>

            <div className="p-3 bg-bone-200/10 border border-bone-200/60">
              <p className="text-sm text-bone-200">
                <strong>Note:</strong> All indicators include both 15-minute and 1-hour timeframes for comprehensive market analysis.
              </p>
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