'use client'

import { useState, useEffect } from 'react'
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

const timeframeOptions = [
  { value: '1m', label: '1 minute' },
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '1d', label: '1 day' }
]

const availableIndicators = [
  'RSI', 'MACD', 'BollingerBands', 'ATR', 'Stochastic', 'Williams%R',
  'OBV', 'CCI', 'MFI', 'SMA', 'EMA', 'VWAP', 'ParabolicSAR', 'Ichimoku'
]

export function ExtractionConfigForm({ activeTab, config }: ExtractionConfigFormProps) {
  const { updateAgentConfig, setError } = useBotStore()
  
  const [formData, setFormData] = useState<ExtractionConfig>({
    symbols: config?.symbols || [],
    timeframes: config?.timeframes || [],
    sources: {
      crypto_indicators_mcp: {
        enabled: config?.sources?.crypto_indicators_mcp?.enabled ?? true,
        indicators: config?.sources?.crypto_indicators_mcp?.indicators || [],
        use_llm_selection: config?.sources?.crypto_indicators_mcp?.use_llm_selection ?? false,
        llm_interpretation: config?.sources?.crypto_indicators_mcp?.llm_interpretation ?? true,
        llm_model: config?.sources?.crypto_indicators_mcp?.llm_model || 'gpt-4o-mini'
      },
      tradingview: {
        enabled: config?.sources?.tradingview?.enabled ?? false,
        strategy: config?.sources?.tradingview?.strategy || ''
      },
      yfinance: {
        enabled: config?.sources?.yfinance?.enabled ?? false
      }
    }
  })

  const handleSave = async () => {
    try {
      setError(null)
      await updateAgentConfig('extraction', formData)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save configuration')
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

  const toggleTimeframe = (timeframe: string) => {
    setFormData(prev => ({
      ...prev,
      timeframes: prev.timeframes.includes(timeframe)
        ? prev.timeframes.filter(t => t !== timeframe)
        : [...prev.timeframes, timeframe]
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
              className={`p-3 text-sm rounded-lg border transition-colors ${
                formData.symbols.includes(symbol)
                  ? 'bg-agents-extraction/20 border-agents-extraction text-bone-200'
                  : 'bg-charcoal-700 border-bone-200/20 text-bone-300 hover:border-bone-200/40'
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
            className="w-full p-3 bg-charcoal-700 border border-bone-200/20 rounded-lg text-bone-200 placeholder-bone-400"
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

  const renderTimeframesTab = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium mb-3">Timeframes</h3>
        <p className="text-sm text-bone-400 mb-4">
          Choose the timeframes for technical analysis. Multiple timeframes provide better market perspective.
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {timeframeOptions.map(option => (
            <button
              key={option.value}
              onClick={() => toggleTimeframe(option.value)}
              className={`p-3 text-sm rounded-lg border transition-colors ${
                formData.timeframes.includes(option.value)
                  ? 'bg-agents-extraction/20 border-agents-extraction text-bone-200'
                  : 'bg-charcoal-700 border-bone-200/20 text-bone-300 hover:border-bone-200/40'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )

  const renderDataSourcesTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Data Sources</h3>
        <p className="text-sm text-bone-400 mb-4">
          Configure data sources and technical indicators for market analysis.
        </p>
      </div>

      {/* Crypto Indicators MCP */}
      <div className="p-4 bg-charcoal-700/50 border border-bone-200/10 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-medium">Crypto Indicators MCP</h4>
            <p className="text-sm text-bone-400">78 technical indicators via MCP server</p>
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
            <div className="w-11 h-6 bg-charcoal-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-agents-extraction"></div>
          </label>
        </div>

        {formData.sources.crypto_indicators_mcp?.enabled && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Technical Indicators</label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                {availableIndicators.map(indicator => (
                  <button
                    key={indicator}
                    onClick={() => toggleIndicator(indicator)}
                    className={`p-2 text-xs rounded border transition-colors ${
                      formData.sources.crypto_indicators_mcp!.indicators.includes(indicator)
                        ? 'bg-agents-extraction/20 border-agents-extraction text-bone-200'
                        : 'bg-charcoal-600 border-bone-200/20 text-bone-300 hover:border-bone-200/40'
                    }`}
                  >
                    {indicator}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.sources.crypto_indicators_mcp?.llm_interpretation}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      sources: {
                        ...prev.sources,
                        crypto_indicators_mcp: {
                          ...prev.sources.crypto_indicators_mcp!,
                          llm_interpretation: e.target.checked
                        }
                      }
                    }))}
                    className="rounded border-bone-200/20"
                  />
                  <span className="text-sm">LLM Interpretation</span>
                </label>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">LLM Model</label>
                <select
                  value={formData.sources.crypto_indicators_mcp?.llm_model}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    sources: {
                      ...prev.sources,
                      crypto_indicators_mcp: {
                        ...prev.sources.crypto_indicators_mcp!,
                        llm_model: e.target.value
                      }
                    }
                  }))}
                  className="w-full p-2 text-sm bg-charcoal-600 border border-bone-200/20 rounded text-bone-200"
                >
                  <option value="gpt-4o-mini">GPT-4O Mini</option>
                  <option value="gpt-4o">GPT-4O</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Future data sources can be added here */}
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 0: return renderSymbolsTab()
      case 1: return renderTimeframesTab()
      case 2: return renderDataSourcesTab()
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      {renderTabContent()}
      
      {/* Save Button */}
      <div className="flex justify-end pt-4 border-t border-bone-200/10">
        <button
          onClick={handleSave}
          className="px-6 py-3 bg-agents-extraction hover:bg-agents-extraction/80 text-charcoal-900 font-medium rounded-lg transition-colors"
        >
          Save Configuration
        </button>
      </div>
    </div>
  )
}