'use client'

import { useState, useMemo } from 'react'
import { Search } from 'lucide-react'
import { useBotStore } from '@/store/bot'
import { ExtractionConfig } from '@/types'
import { IndicatorCard } from './IndicatorCard'
import { INDICATORS, CATEGORY_LABELS, IndicatorCategory } from './constants'
import { cn } from '@/lib/utils/cn'

interface ExtractionConfigFormProps {
  activeTab: number
  config: ExtractionConfig | null
}

const commonSymbols = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
  'MATIC/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
]

export function ExtractionConfigForm({ activeTab, config }: ExtractionConfigFormProps) {
  const { updateAgentConfig, setError } = useBotStore()
  const [isSaving, setIsSaving] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<IndicatorCategory | 'all'>('all')
  
  // Parse existing config to new format
  const parseExistingConfig = (config: ExtractionConfig | null) => {
    if (!config) {
      return {
        symbols: [],
        indicators: INDICATORS.map(ind => ({
          name: ind.name,
          enabled: false,
          timeframes: []
        }))
      }
    }

    const existingIndicators = config.sources?.crypto_indicators_mcp?.indicators || []
    const indicatorMap = new Map<string, string[]>()
    
    // Parse old format (RSI_15m) to new format
    existingIndicators.forEach(indicator => {
      const parts = indicator.split('_')
      if (parts.length >= 2) {
        const timeframe = parts[parts.length - 1]
        const indicatorName = parts.slice(0, -1).join('_').toLowerCase()
        
        if (!indicatorMap.has(indicatorName)) {
          indicatorMap.set(indicatorName, [])
        }
        indicatorMap.get(indicatorName)!.push(timeframe)
      }
    })

    return {
      symbols: config.symbols || [],
      indicators: INDICATORS.map(ind => ({
        name: ind.name,
        enabled: indicatorMap.has(ind.name),
        timeframes: indicatorMap.get(ind.name) || []
      }))
    }
  }

  const [formData, setFormData] = useState(() => parseExistingConfig(config))

  // Filter indicators based on search and category
  const filteredIndicators = useMemo(() => {
    return INDICATORS.filter(indicator => {
      const matchesSearch = searchQuery === '' || 
        indicator.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        indicator.description.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesCategory = selectedCategory === 'all' || indicator.category === selectedCategory
      
      return matchesSearch && matchesCategory
    })
  }, [searchQuery, selectedCategory])

  const handleToggleIndicator = (indicatorName: string, enabled: boolean) => {
    setFormData(prev => ({
      ...prev,
      indicators: prev.indicators.map(ind => 
        ind.name === indicatorName
          ? { 
              ...ind, 
              enabled,
              // Set default timeframes when enabling
              timeframes: enabled && ind.timeframes.length === 0 
                ? INDICATORS.find(i => i.name === indicatorName)?.defaultTimeframes || []
                : ind.timeframes
            }
          : ind
      )
    }))
  }

  const handleTimeframeChange = (indicatorName: string, timeframes: string[]) => {
    setFormData(prev => ({
      ...prev,
      indicators: prev.indicators.map(ind => 
        ind.name === indicatorName
          ? { ...ind, timeframes }
          : ind
      )
    }))
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      setError(null)
      
      // Validate
      if (formData.symbols.length === 0) {
        throw new Error('Please select at least one symbol')
      }
      
      const enabledIndicators = formData.indicators.filter(ind => ind.enabled)
      if (enabledIndicators.length === 0) {
        throw new Error('Please select at least one indicator')
      }
      
      const hasTimeframes = enabledIndicators.every(ind => ind.timeframes.length > 0)
      if (!hasTimeframes) {
        throw new Error('Please select timeframes for all enabled indicators')
      }
      
      // Convert back to old format for compatibility
      const indicators: string[] = []
      formData.indicators.forEach(ind => {
        if (ind.enabled) {
          ind.timeframes.forEach(tf => {
            indicators.push(`${ind.name}_${tf}`)
          })
        }
      })
      
      const configToSave: ExtractionConfig = {
        symbols: formData.symbols,
        sources: {
          crypto_indicators_mcp: {
            enabled: true,
            indicators
          }
        }
      }
      
      await updateAgentConfig('extraction', configToSave)
      setJustSaved(true)
      setTimeout(() => setJustSaved(false), 2000)
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
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Trading Pairs</h3>
        <p className="text-sm text-bone-400 mb-4">
          Select the cryptocurrency pairs to analyze. You can choose from common pairs or add custom ones.
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {commonSymbols.map(symbol => (
            <button
              key={symbol}
              onClick={() => toggleSymbol(symbol)}
              className={cn(
                "p-3 text-sm font-medium rounded-lg border transition-all duration-200",
                formData.symbols.includes(symbol)
                  ? "bg-agents-extraction/20 border-agents-extraction text-bone-200 shadow-sm"
                  : "bg-charcoal-700/50 border-bone-200/40 text-bone-300 hover:border-bone-200/60"
              )}
            >
              {symbol}
            </button>
          ))}
        </div>
        
        <div className="mt-6">
          <label className="block text-sm font-medium mb-2">Add Custom Symbol</label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g., DOGE/USDT"
              className="flex-1 p-3 bg-charcoal-700 border border-bone-200/40 rounded-lg text-bone-200 placeholder-bone-500 focus:border-agents-extraction focus:outline-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const value = e.currentTarget.value.trim().toUpperCase()
                  if (value && !formData.symbols.includes(value)) {
                    toggleSymbol(value)
                    e.currentTarget.value = ''
                  }
                }
              }}
            />
            <button
              onClick={(e) => {
                const input = e.currentTarget.previousElementSibling as HTMLInputElement
                const value = input.value.trim().toUpperCase()
                if (value && !formData.symbols.includes(value)) {
                  toggleSymbol(value)
                  input.value = ''
                }
              }}
              className="px-4 py-3 bg-agents-extraction hover:bg-agents-extraction/80 text-charcoal-900 font-medium rounded-lg transition-colors"
            >
              Add
            </button>
          </div>
        </div>
        
        {formData.symbols.length > 0 && (
          <div className="mt-4 p-3 bg-bone-200/10 border border-bone-200/40 rounded-lg">
            <p className="text-sm text-bone-300">
              <strong>{formData.symbols.length}</strong> symbols selected
            </p>
          </div>
        )}
      </div>
    </div>
  )

  const renderIndicatorsTab = () => {
    const enabledCount = formData.indicators.filter(ind => ind.enabled).length
    const totalCombinations = formData.indicators.reduce((acc, ind) => 
      acc + (ind.enabled ? ind.timeframes.length : 0), 0
    )

    return (
      <div className="space-y-6">
        {/* Header & Search */}
        <div>
          <h3 className="text-lg font-medium mb-3">Technical Indicators</h3>
          <p className="text-sm text-bone-400 mb-4">
            Select indicators and their timeframes. Premium indicators provide AI-enhanced signals.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-bone-500" size={18} />
              <input
                type="text"
                placeholder="Search indicators..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-charcoal-700 border border-bone-200/40 rounded-lg text-bone-200 placeholder-bone-500 focus:border-agents-extraction focus:outline-none"
              />
            </div>
            
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setSelectedCategory('all')}
                className={cn(
                  "px-3 py-2 text-sm rounded-lg border transition-colors",
                  selectedCategory === 'all'
                    ? "bg-agents-extraction/20 border-agents-extraction text-bone-200"
                    : "bg-charcoal-700 border-bone-200/40 text-bone-400 hover:border-bone-200/60"
                )}
              >
                All
              </button>
              {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key as IndicatorCategory)}
                  className={cn(
                    "px-3 py-2 text-sm rounded-lg border transition-colors",
                    selectedCategory === key
                      ? "bg-agents-extraction/20 border-agents-extraction text-bone-200"
                      : "bg-charcoal-700 border-bone-200/40 text-bone-400 hover:border-bone-200/60"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Indicators Grid */}
        <div className="grid gap-4 md:grid-cols-2">
          {filteredIndicators.map(indicator => {
            const config = formData.indicators.find(ind => ind.name === indicator.name)!
            return (
              <IndicatorCard
                key={indicator.name}
                indicator={indicator}
                selected={config.enabled}
                selectedTimeframes={config.timeframes}
                onToggle={(enabled) => handleToggleIndicator(indicator.name, enabled)}
                onTimeframeChange={(timeframes) => handleTimeframeChange(indicator.name, timeframes)}
              />
            )
          })}
        </div>

        {/* Summary */}
        {enabledCount > 0 && (
          <div className="p-4 bg-bone-200/10 border border-bone-200/40 rounded-lg">
            <p className="text-sm text-bone-300">
              <strong>{enabledCount}</strong> indicators selected with{' '}
              <strong>{totalCombinations}</strong> total timeframe combinations
            </p>
          </div>
        )}
      </div>
    )
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 0: return renderSymbolsTab()
      case 1: return renderIndicatorsTab()
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      {renderTabContent()}
      
      {/* Save Button */}
      <div className="flex justify-end pt-4 border-t border-bone-200/40">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={cn(
            "px-6 py-3 font-medium rounded-lg transition-all duration-200",
            justSaved
              ? "bg-green-500 text-white"
              : isSaving
                ? "bg-agents-extraction/50 text-charcoal-900/70 cursor-not-allowed"
                : "bg-agents-extraction hover:bg-agents-extraction/80 text-charcoal-900"
          )}
        >
          {justSaved ? '✓ Saved Successfully!' : isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}