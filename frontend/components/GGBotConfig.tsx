'use client'

import React from 'react'
import { Bot } from '@/store/botStore'

interface GGBotConfigProps {
  bot: Bot | null
  isOpen: boolean
  onClose: () => void
}

// Trading pairs data
const tradingPairs = {
  popular: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT'],
  all: [
    'AAVE/USDT', 'ADA/USDT', 'ALGO/USDT', 'APT/USDT', 'ARB/USDT', 'ATOM/USDT', 'AVAX/USDT',
    'AXS/USDT', 'BAL/USDT', 'BCH/USDT', 'BNB/USDT', 'BTC/USDT', 'CAKE/USDT', 'CHZ/USDT',
    'COMP/USDT', 'CRV/USDT', 'DOT/USDT', 'DYDX/USDT', 'EGLD/USDT', 'ENJ/USDT', 'EOS/USDT',
    'ETC/USDT', 'ETH/USDT', 'FIL/USDT', 'FLOW/USDT', 'FTM/USDT', 'GALA/USDT', 'GMT/USDT',
    'GRT/USDT', 'HBAR/USDT', 'ICP/USDT', 'IMX/USDT', 'INJ/USDT', 'JUP/USDT', 'KSM/USDT',
    'LINK/USDT', 'LRC/USDT', 'LTC/USDT', 'MANA/USDT', 'MATIC/USDT', 'MINA/USDT', 'MKR/USDT',
    'NEAR/USDT', 'NEO/USDT', 'OP/USDT', 'PYTH/USDT', 'QNT/USDT', 'RNDR/USDT', 'ROSE/USDT',
    'RUNE/USDT', 'SAND/USDT', 'SEI/USDT', 'SHIB/USDT', 'SNX/USDT', 'SOL/USDT', 'STX/USDT',
    'SUI/USDT', 'SUSHI/USDT', 'TIA/USDT', 'TRX/USDT', 'UNI/USDT', 'VET/USDT', 'WLD/USDT',
    'WOO/USDT', 'XLM/USDT', 'XRP/USDT', 'XTZ/USDT', 'ZIL/USDT', 'ZRX/USDT'
  ].sort()
}

// Analysis frequency options
const frequencyOptions = [
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '1d', label: '1 day' },
  { value: '1w', label: '1 week' }
]

// Signal providers data
const signalProviders = [
  { id: 'ggshot', name: 'GG-Shot', description: 'Breakout and momentum signals from ggShot indicator' }
]

// Decision modes
const decisionModes = [
  { value: 'autonomous', label: 'Autonomous Trading', description: 'Generate and execute trades independently' },
  { value: 'validation', label: 'Signal Validation', description: 'Validate external signals before execution' }
]

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

// Technical Indicators Section Component
interface TechnicalIndicatorsSectionProps {
  selectedIndicators: Set<string>
  onToggleIndicator: (indicatorId: string) => void
}

const TechnicalIndicatorsSection: React.FC<TechnicalIndicatorsSectionProps> = ({
  selectedIndicators,
  onToggleIndicator
}) => {
  const [searchTerm, setSearchTerm] = React.useState('')

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

  return (
    <div>
      {/* Header and Search */}
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
            className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agent-extraction focus:outline-none transition-colors"
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-gray-400">
              <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Indicators Content */}
      <div className="space-y-6 max-h-96 overflow-y-auto">
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
                    onClick={() => !isDisabled && onToggleIndicator(indicator.id)}
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
  )
}

// Signal Providers Section Component
interface SignalProvidersSectionProps {
  selectedSignals: Set<string>
  onToggleSignal: (signalId: string) => void
}

const SignalProvidersSection: React.FC<SignalProvidersSectionProps> = ({
  selectedSignals,
  onToggleSignal
}) => {
  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-footnote text-bone-200 font-medium">SIGNAL PROVIDER SELECTION</h4>
      </div>

      {/* Providers Content */}
      <div className="space-y-4">
        {signalProviders.map(provider => {
          const isSelected = selectedSignals.has(provider.id)
          
          return (
            <button
              key={provider.id}
              onClick={() => onToggleSignal(provider.id)}
              className={`w-full text-left p-4 border transition-colors ${
                isSelected
                  ? 'bg-agents-extraction/10 border-agents-extraction text-bone-200'
                  : 'bg-charcoal-800 border-charcoal-700 text-bone-200 hover:border-agents-extraction hover:bg-agents-extraction/5'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                    isSelected
                      ? 'bg-agents-extraction border-agents-extraction'
                      : 'border-gray-600'
                  }`}>
                    {isSelected && (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="text-charcoal-900">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                      </svg>
                    )}
                  </div>
                  <div>
                    <div className="text-footnote font-medium">{provider.name}</div>
                    <div className="text-xs text-gray-400 mt-1">{provider.description}</div>
                  </div>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// Risk Management Section Component
interface RiskManagementSectionProps {
  positionSizeType: string
  onPositionSizeTypeChange: (type: string) => void
  fixedAmount: number
  onFixedAmountChange: (amount: number) => void
  accountPercentage: number
  onAccountPercentageChange: (percentage: number) => void
  maxRiskPerTrade: number
  onMaxRiskPerTradeChange: (risk: number) => void
  maxTotalExposure: number
  onMaxTotalExposureChange: (exposure: number) => void
  maxPositions: number
  onMaxPositionsChange: (positions: number) => void
  dailyLossLimit: number
  onDailyLossLimitChange: (limit: number) => void
  stopTradingOnLimit: boolean
  onStopTradingOnLimitChange: (enabled: boolean) => void
  defaultStopLoss: number
  onDefaultStopLossChange: (sl: number) => void
  defaultTpRatio: string
  onDefaultTpRatioChange: (ratio: string) => void
  trailingStopsEnabled: boolean
  onTrailingStopsEnabledChange: (enabled: boolean) => void
  trailingDistance: number
  onTrailingDistanceChange: (distance: number) => void
}

const RiskManagementSection: React.FC<RiskManagementSectionProps> = ({
  positionSizeType,
  onPositionSizeTypeChange,
  fixedAmount,
  onFixedAmountChange,
  accountPercentage,
  onAccountPercentageChange,
  maxRiskPerTrade,
  onMaxRiskPerTradeChange,
  maxTotalExposure,
  onMaxTotalExposureChange,
  maxPositions,
  onMaxPositionsChange,
  dailyLossLimit,
  onDailyLossLimitChange,
  stopTradingOnLimit,
  onStopTradingOnLimitChange,
  defaultStopLoss,
  onDefaultStopLossChange,
  defaultTpRatio,
  onDefaultTpRatioChange,
  trailingStopsEnabled,
  onTrailingStopsEnabledChange,
  trailingDistance,
  onTrailingDistanceChange
}) => {
  const tpRatioOptions = ['1:1', '2:1', '3:1', '4:1', '5:1']

  return (
    <div className="space-y-6">
      {/* Position Sizing Strategy */}
      <div className="bg-charcoal-800 border border-charcoal-600 p-4">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-footnote text-bone-200 font-medium">POSITION SIZING STRATEGY</h4>
        </div>
        <div className="flex gap-2 flex-wrap mb-4">
          <button
            onClick={() => onPositionSizeTypeChange('fixed')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              positionSizeType === 'fixed'
                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
            }`}
          >
            Fixed Amount
          </button>
          <button
            onClick={() => onPositionSizeTypeChange('percentage')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              positionSizeType === 'percentage'
                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
            }`}
          >
            Account Percentage
          </button>
          <button
            onClick={() => onPositionSizeTypeChange('risk-based')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              positionSizeType === 'risk-based'
                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
            }`}
          >
            Risk-Based
          </button>
        </div>
        
        <div className="bg-charcoal-900 border border-charcoal-700 p-3 rounded">
          {positionSizeType === 'fixed' && (
            <div className="grid grid-cols-2 gap-4 items-center">
              <span className="text-xs text-gray-400">Amount per trade:</span>
              <div className="flex items-center">
                <span className="text-bone-200 text-xs mr-2">$</span>
                <input
                  type="number"
                  value={fixedAmount}
                  onChange={(e) => onFixedAmountChange(Number(e.target.value))}
                  min="1"
                  step="1"
                  className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-20 focus:border-[#be6a47] focus:outline-none transition-colors"
                />
              </div>
            </div>
          )}
          {positionSizeType === 'percentage' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 items-center">
                <span className="text-xs text-gray-400">Percentage of account:</span>
                <div className="flex items-center">
                  <input
                    type="number"
                    value={accountPercentage}
                    onChange={(e) => onAccountPercentageChange(Number(e.target.value))}
                    min="0.1"
                    max="100"
                    step="0.1"
                    className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                  />
                  <span className="text-bone-200 text-xs ml-2">%</span>
                </div>
              </div>
              <div>
                <input
                  type="range"
                  min="0.1"
                  max="25"
                  step="0.1"
                  value={accountPercentage}
                  onChange={(e) => onAccountPercentageChange(Number(e.target.value))}
                  className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer slider-thumb"
                  style={{
                    background: `linear-gradient(to right, #be6a47 0%, #be6a47 ${(accountPercentage / 25) * 100}%, #374151 ${(accountPercentage / 25) * 100}%, #374151 100%)`
                  }}
                />
              </div>
            </div>
          )}
          {positionSizeType === 'risk-based' && (
            <div className="text-center">
              <span className="text-xs text-gray-400">Position size calculated dynamically based on stop loss distance and maximum risk per trade</span>
            </div>
          )}
        </div>
      </div>

      {/* Risk Limits */}
      <div className="bg-charcoal-800 border border-charcoal-600 p-4">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-footnote text-bone-200 font-medium">RISK LIMITS</h4>
        </div>
        <div className="space-y-4">
          <div>
            <div className="grid grid-cols-2 gap-4 items-center mb-2">
              <span className="text-xs text-gray-400">Max risk per trade:</span>
              <div className="flex items-center">
                <input
                  type="number"
                  value={maxRiskPerTrade}
                  onChange={(e) => onMaxRiskPerTradeChange(Number(e.target.value))}
                  min="0.1"
                  max="50"
                  step="0.1"
                  className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                />
                <span className="text-bone-200 text-xs ml-2">% of balance</span>
              </div>
            </div>
            <input
              type="range"
              min="0.1"
              max="15"
              step="0.1"
              value={maxRiskPerTrade}
              onChange={(e) => onMaxRiskPerTradeChange(Number(e.target.value))}
              className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #be6a47 0%, #be6a47 ${(maxRiskPerTrade / 15) * 100}%, #374151 ${(maxRiskPerTrade / 15) * 100}%, #374151 100%)`
              }}
            />
          </div>
          
          <div>
            <div className="grid grid-cols-2 gap-4 items-center mb-2">
              <span className="text-xs text-gray-400">Max total exposure:</span>
              <div className="flex items-center">
                <input
                  type="number"
                  value={maxTotalExposure}
                  onChange={(e) => onMaxTotalExposureChange(Number(e.target.value))}
                  min="1"
                  max="100"
                  step="1"
                  className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                />
                <span className="text-bone-200 text-xs ml-2">% across positions</span>
              </div>
            </div>
            <input
              type="range"
              min="5"
              max="100"
              step="5"
              value={maxTotalExposure}
              onChange={(e) => onMaxTotalExposureChange(Number(e.target.value))}
              className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #be6a47 0%, #be6a47 ${((maxTotalExposure - 5) / 95) * 100}%, #374151 ${((maxTotalExposure - 5) / 95) * 100}%, #374151 100%)`
              }}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4 items-center">
            <span className="text-xs text-gray-400">Max active positions:</span>
            <div className="flex gap-2">
              {[1,2,3,4,5].map(num => (
                <button
                  key={num}
                  onClick={() => onMaxPositionsChange(num)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    maxPositions === num
                      ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                      : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 items-center">
            <span className="text-xs text-gray-400">Daily loss limit:</span>
            <div className="flex items-center gap-3">
              <div className="flex items-center">
                <span className="text-bone-200 text-xs mr-1">$</span>
                <input
                  type="number"
                  value={dailyLossLimit}
                  onChange={(e) => onDailyLossLimitChange(Number(e.target.value))}
                  min="1"
                  step="1"
                  className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-20 focus:border-[#be6a47] focus:outline-none transition-colors"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={stopTradingOnLimit}
                  onChange={(e) => onStopTradingOnLimitChange(e.target.checked)}
                  className="w-3 h-3 accent-[#be6a47]"
                />
                <span className="text-xs text-gray-400">Stop trading</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Stop Loss & Take Profit */}
      <div className="bg-charcoal-800 border border-charcoal-600 p-4">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-footnote text-bone-200 font-medium">STOP LOSS & TAKE PROFIT</h4>
        </div>
        <div className="space-y-4">
          <div>
            <div className="grid grid-cols-2 gap-4 items-center mb-2">
              <span className="text-xs text-gray-400">Default stop loss:</span>
              <div className="flex items-center">
                <input
                  type="number"
                  value={defaultStopLoss}
                  onChange={(e) => onDefaultStopLossChange(Number(e.target.value))}
                  min="0.1"
                  max="50"
                  step="0.1"
                  className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                />
                <span className="text-bone-200 text-xs ml-2">% from entry</span>
              </div>
            </div>
            <input
              type="range"
              min="0.5"
              max="10"
              step="0.1"
              value={defaultStopLoss}
              onChange={(e) => onDefaultStopLossChange(Number(e.target.value))}
              className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #be6a47 0%, #be6a47 ${((defaultStopLoss - 0.5) / 9.5) * 100}%, #374151 ${((defaultStopLoss - 0.5) / 9.5) * 100}%, #374151 100%)`
              }}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4 items-center">
            <span className="text-xs text-gray-400">Default take profit:</span>
            <div className="flex gap-2">
              {tpRatioOptions.map(ratio => (
                <button
                  key={ratio}
                  onClick={() => onDefaultTpRatioChange(ratio)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    defaultTpRatio === ratio
                      ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                      : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                  }`}
                >
                  {ratio}
                </button>
              ))}
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={trailingStopsEnabled}
                  onChange={(e) => onTrailingStopsEnabledChange(e.target.checked)}
                  className="w-4 h-4 accent-[#be6a47]"
                />
                <span className="text-xs text-bone-200">Enable trailing stops</span>
              </label>
            </div>
            {trailingStopsEnabled && (
              <div>
                <div className="grid grid-cols-2 gap-4 items-center mb-2">
                  <span className="text-xs text-gray-400 ml-6">Trailing distance:</span>
                  <div className="flex items-center">
                    <input
                      type="number"
                      value={trailingDistance}
                      onChange={(e) => onTrailingDistanceChange(Number(e.target.value))}
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                    />
                    <span className="text-bone-200 text-xs ml-2">%</span>
                  </div>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="5"
                  step="0.1"
                  value={trailingDistance}
                  onChange={(e) => onTrailingDistanceChange(Number(e.target.value))}
                  className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer ml-6"
                  style={{
                    background: `linear-gradient(to right, #be6a47 0%, #be6a47 ${((trailingDistance - 0.1) / 4.9) * 100}%, #374151 ${((trailingDistance - 0.1) / 4.9) * 100}%, #374151 100%)`
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Exchange Connection Section Component
interface ExchangeConnectionSectionProps {
  exchangeType: string
  onExchangeTypeChange: (type: string) => void
  selectedExchange: string
  onSelectedExchangeChange: (exchange: string) => void
  apiKey: string
  onApiKeyChange: (key: string) => void
  secretKey: string
  onSecretKeyChange: (key: string) => void
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  onTestConnection: () => void
  onClearCredentials: () => void
  selectedNetwork: string
  onSelectedNetworkChange: (network: string) => void
  walletConnected: boolean
  onConnectWallet: () => void
  slippageTolerance: number
  onSlippageToleranceChange: (slippage: number) => void
}

const ExchangeConnectionSection: React.FC<ExchangeConnectionSectionProps> = ({
  exchangeType,
  onExchangeTypeChange,
  selectedExchange,
  onSelectedExchangeChange,
  apiKey,
  onApiKeyChange,
  secretKey,
  onSecretKeyChange,
  connectionStatus,
  onTestConnection,
  onClearCredentials,
  selectedNetwork,
  onSelectedNetworkChange,
  walletConnected,
  onConnectWallet,
  slippageTolerance,
  onSlippageToleranceChange
}) => {
  const cexOptions = ['binance', 'coinbase', 'kraken', 'bybit']
  const networkOptions = ['ethereum', 'bsc', 'polygon', 'arbitrum']

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-400'
      case 'connecting': return 'text-yellow-400'
      case 'error': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected'
      case 'connecting': return 'Connecting...'
      case 'error': return 'Connection failed'
      default: return exchangeType === 'cex' ? 'Not connected' : 'No wallet connected'
    }
  }

  return (
    <div className="space-y-6">
      {/* Exchange Type Selection */}
      <div className="bg-charcoal-800 border border-charcoal-600 p-4">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-footnote text-bone-200 font-medium">SELECT EXCHANGE TYPE</h4>
        </div>
        <div className="flex gap-2 flex-wrap mb-4">
          <button
            onClick={() => onExchangeTypeChange('cex')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              exchangeType === 'cex'
                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
            }`}
          >
            Centralized (CEX)
          </button>
          <button
            onClick={() => onExchangeTypeChange('dex')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              exchangeType === 'dex'
                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
            }`}
          >
            Decentralized (DEX)
          </button>
        </div>
        
        {/* Warning */}
        <div className="bg-orange-900/20 border border-orange-700/50 p-3 rounded">
          <div className="flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-orange-400">
              <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
            </svg>
            <span className="text-xs text-orange-400">Only one exchange can be connected per bot</span>
          </div>
        </div>
      </div>

      {/* CEX Configuration */}
      {exchangeType === 'cex' && (
        <div className="bg-charcoal-800 border border-charcoal-600 p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-footnote text-bone-200 font-medium">CENTRALIZED EXCHANGE SETUP</h4>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 items-center">
              <span className="text-xs text-gray-400">Exchange:</span>
              <div className="flex gap-2">
                {cexOptions.map(exchange => (
                  <button
                    key={exchange}
                    onClick={() => onSelectedExchangeChange(exchange)}
                    className={`px-2 py-1 text-xs rounded transition-colors capitalize ${
                      selectedExchange === exchange
                        ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                        : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                    }`}
                  >
                    {exchange}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-2">API Key:</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => onApiKeyChange(e.target.value)}
                  placeholder="Enter API key..."
                  className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-[#be6a47] focus:outline-none transition-colors rounded"
                />
              </div>
              
              <div>
                <label className="block text-xs text-gray-400 mb-2">Secret Key:</label>
                <input
                  type="password"
                  value={secretKey}
                  onChange={(e) => onSecretKeyChange(e.target.value)}
                  placeholder="Enter secret key..."
                  className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-[#be6a47] focus:outline-none transition-colors rounded"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={onTestConnection}
                disabled={!apiKey || !secretKey || connectionStatus === 'connecting'}
                className={`px-4 py-2 text-xs rounded transition-colors font-medium ${
                  !apiKey || !secretKey || connectionStatus === 'connecting'
                    ? 'bg-charcoal-700 text-gray-500 cursor-not-allowed'
                    : 'bg-[#be6a47] text-charcoal-900 hover:bg-[#be6a47]/80'
                }`}
              >
                {connectionStatus === 'connecting' ? '⏳ Testing...' : '🔍 Test Connection'}
              </button>
              <button
                onClick={onClearCredentials}
                className="px-3 py-2 text-xs rounded transition-colors bg-charcoal-700 text-gray-400 hover:text-bone-200 hover:bg-charcoal-600"
              >
                Clear
              </button>
            </div>
            
            <div className="bg-charcoal-900 border border-charcoal-700 p-3 rounded">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-green-400' :
                  connectionStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' :
                  connectionStatus === 'error' ? 'bg-red-400' : 'bg-gray-400'
                }`} />
                <span className={`text-xs font-medium ${getStatusColor()}`}>
                  {getStatusText()}
                </span>
                {connectionStatus === 'connected' && (
                  <span className="text-xs text-gray-400">• Ready for trading</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DEX Configuration */}
      {exchangeType === 'dex' && (
        <div className="bg-charcoal-800 border border-charcoal-600 p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-footnote text-bone-200 font-medium">DECENTRALIZED EXCHANGE SETUP</h4>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 items-center">
              <span className="text-xs text-gray-400">Blockchain Network:</span>
              <div className="flex gap-2">
                {networkOptions.map(network => (
                  <button
                    key={network}
                    onClick={() => onSelectedNetworkChange(network)}
                    className={`px-2 py-1 text-xs rounded transition-colors capitalize ${
                      selectedNetwork === network
                        ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                        : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                    }`}
                  >
                    {network}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 items-center">
              <span className="text-xs text-gray-400">Wallet Connection:</span>
              <div>
                <button
                  onClick={onConnectWallet}
                  className={`px-4 py-2 text-xs rounded transition-colors font-medium ${
                    walletConnected
                      ? 'bg-green-600 text-white'
                      : 'bg-[#be6a47] text-charcoal-900 hover:bg-[#be6a47]/80'
                  }`}
                >
                  {walletConnected ? '🔗 Wallet Connected' : '🔌 Connect Wallet'}
                </button>
              </div>
            </div>
            
            <div>
              <div className="grid grid-cols-2 gap-4 items-center mb-2">
                <span className="text-xs text-gray-400">Slippage tolerance:</span>
                <div className="flex items-center">
                  <input
                    type="number"
                    value={slippageTolerance}
                    onChange={(e) => onSlippageToleranceChange(Number(e.target.value))}
                    min="0.1"
                    max="50"
                    step="0.1"
                    className="bg-charcoal-900 border border-charcoal-700 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors rounded"
                  />
                  <span className="text-bone-200 text-xs ml-2">%</span>
                </div>
              </div>
              <input
                type="range"
                min="0.1"
                max="5"
                step="0.1"
                value={slippageTolerance}
                onChange={(e) => onSlippageToleranceChange(Number(e.target.value))}
                className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #be6a47 0%, #be6a47 ${((slippageTolerance - 0.1) / 4.9) * 100}%, #374151 ${((slippageTolerance - 0.1) / 4.9) * 100}%, #374151 100%)`
                }}
              />
            </div>
            
            <div className="bg-charcoal-900 border border-charcoal-700 p-3 rounded">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${walletConnected ? 'bg-green-400' : 'bg-gray-400'}`} />
                <span className={`text-xs font-medium ${walletConnected ? 'text-green-400' : 'text-gray-400'}`}>
                  {walletConnected ? 'Wallet Connected' : 'No Wallet Connected'}
                </span>
                {walletConnected && (
                  <span className="text-xs text-gray-400">• Ready for DEX trading</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const GGBotConfig: React.FC<GGBotConfigProps> = ({ bot, isOpen, onClose }) => {
  const [isEditingName, setIsEditingName] = React.useState(false)
  const [botName, setBotName] = React.useState(bot?.name || '')
  const [hasChanges, setHasChanges] = React.useState(false)
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(new Set(['extraction']))
  const [isVisible, setIsVisible] = React.useState(false)
  const [isMounted, setIsMounted] = React.useState(false)
  
  // Extraction Agent states
  const [selectedPair, setSelectedPair] = React.useState('BTC/USDT')
  const [pairSearchTerm, setPairSearchTerm] = React.useState('')
  const [showPairDropdown, setShowPairDropdown] = React.useState(false)
  const [selectedDataSource, setSelectedDataSource] = React.useState('Technical Indicators')
  const [selectedIndicators, setSelectedIndicators] = React.useState<Set<string>>(new Set(['RSI', 'MACD', 'BollingerBands']))

  // Decision Agent states
  const [decisionMode, setDecisionMode] = React.useState('autonomous')
  const [analysisFrequency, setAnalysisFrequency] = React.useState('1h')
  const [tradingStrategy, setTradingStrategy] = React.useState('Enter when RSI is oversold below 30 and MACD shows bullish crossover. Avoid during high volatility periods or when multiple indicators conflict.')
  const [marketAnalysis, setMarketAnalysis] = React.useState('Look for confluence between momentum and trend indicators. Pay special attention to volume confirmation and support/resistance levels.')
  const [validationCriteria, setValidationCriteria] = React.useState('Accept signals that align with overall trend and have strong volume confirmation. Avoid signals during major news events or extreme market conditions.')
  const [riskAssessment, setRiskAssessment] = React.useState('Evaluate market volatility and position sizing based on signal confidence. Consider correlation with other active positions.')
  const [customPrompt, setCustomPrompt] = React.useState('')
  const [useCustomPrompt, setUseCustomPrompt] = React.useState(false)
  const [showPromptPreview, setShowPromptPreview] = React.useState(false)
  
  // Additional data sources
  const [selectedSignals, setSelectedSignals] = React.useState<Set<string>>(new Set())

  // Trading Agent states - with defaults
  const [tradingAgentTab, setTradingAgentTab] = React.useState('risk-management')
  
  // Risk Management defaults
  const [positionSizeType, setPositionSizeType] = React.useState('fixed')
  const [fixedAmount, setFixedAmount] = React.useState(100)
  const [accountPercentage, setAccountPercentage] = React.useState(5.0)
  const [maxRiskPerTrade, setMaxRiskPerTrade] = React.useState(5.0)
  const [maxTotalExposure, setMaxTotalExposure] = React.useState(20.0)
  const [maxPositions, setMaxPositions] = React.useState(3)
  const [dailyLossLimit, setDailyLossLimit] = React.useState(500)
  const [stopTradingOnLimit, setStopTradingOnLimit] = React.useState(true)
  const [defaultStopLoss, setDefaultStopLoss] = React.useState(2.0)
  const [defaultTpRatio, setDefaultTpRatio] = React.useState('3:1')
  const [trailingStopsEnabled, setTrailingStopsEnabled] = React.useState(true)
  const [trailingDistance, setTrailingDistance] = React.useState(1.0)
  
  // Exchange Connection defaults
  const [exchangeType, setExchangeType] = React.useState('cex')
  const [selectedExchange, setSelectedExchange] = React.useState('binance')
  const [apiKey, setApiKey] = React.useState('')
  const [secretKey, setSecretKey] = React.useState('')
  const [connectionStatus, setConnectionStatus] = React.useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [selectedNetwork, setSelectedNetwork] = React.useState('ethereum')
  const [walletConnected, setWalletConnected] = React.useState(false)
  const [slippageTolerance, setSlippageTolerance] = React.useState(0.5)

  // Helper functions for selection management
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

  const toggleSignal = (signalId: string) => {
    setSelectedSignals(prev => {
      const newSet = new Set(prev)
      if (newSet.has(signalId)) {
        newSet.delete(signalId)
      } else {
        newSet.add(signalId)
      }
      setHasChanges(true)
      return newSet
    })
  }

  // Trading Agent helper functions
  const handleTestConnection = async () => {
    setConnectionStatus('connecting')
    // TODO: Implement actual API testing
    setTimeout(() => {
      setConnectionStatus(Math.random() > 0.5 ? 'connected' : 'error')
    }, 2000)
  }

  const handleClearCredentials = () => {
    setApiKey('')
    setSecretKey('')
    setConnectionStatus('disconnected')
    setHasChanges(true)
  }

  const handleConnectWallet = async () => {
    // TODO: Implement actual wallet connection
    setWalletConnected(!walletConnected)
    setHasChanges(true)
  }

  // Helper to update Trading Agent fields and trigger change detection
  const updateTradingField = <T,>(setter: (value: T) => void) => (value: T) => {
    setter(value)
    setHasChanges(true)
  }

  // Filter trading pairs based on search
  const filteredPairs = React.useMemo(() => {
    if (!pairSearchTerm) return tradingPairs
    
    const searchLower = pairSearchTerm.toLowerCase()
    return {
      popular: tradingPairs.popular.filter(pair => 
        pair.toLowerCase().includes(searchLower)
      ),
      all: tradingPairs.all.filter(pair => 
        pair.toLowerCase().includes(searchLower)
      )
    }
  }, [pairSearchTerm])

  React.useEffect(() => {
    if (bot) {
      setBotName(bot.name)
    }
  }, [bot])

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (showPairDropdown && !(e.target as HTMLElement).closest('.pair-dropdown-container')) {
        setShowPairDropdown(false)
        setPairSearchTerm('')
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showPairDropdown])

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
        style={{ height: '90vh' }}
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
                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-subheader focus:border-agent-extraction focus:outline-none transition-colors"
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
                      {/* Trading Pair Selection */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">TRADING PAIR</h4>
                        </div>
                        <div className="relative pair-dropdown-container">
                          <div 
                            className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs cursor-pointer hover:border-agent-extraction transition-colors flex items-center justify-between"
                            onClick={() => setShowPairDropdown(!showPairDropdown)}
                          >
                            <span>{selectedPair}</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className={`text-gray-400 transition-transform ${showPairDropdown ? 'rotate-180' : ''}`}>
                              <path d="M7 10l5 5 5-5z"/>
                            </svg>
                          </div>
                          
                          {showPairDropdown && (
                            <div className="absolute top-full mt-1 w-full bg-charcoal-800 border border-charcoal-600 z-10">
                              {/* Search input */}
                              <div className="p-2 border-b border-charcoal-600">
                                <input
                                  type="text"
                                  placeholder="Search pairs..."
                                  value={pairSearchTerm}
                                  onChange={(e) => setPairSearchTerm(e.target.value)}
                                  onClick={(e) => e.stopPropagation()}
                                  className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-2 py-1 text-xs focus:border-agent-extraction focus:outline-none transition-colors"
                                  autoFocus
                                />
                              </div>
                              
                              {/* Scrollable list */}
                              <div className="max-h-64 overflow-y-auto">
                                {filteredPairs.popular.length > 0 && (
                                  <div>
                                    <div className="px-2 py-1 text-xs text-gray-500 bg-charcoal-900">Popular Pairs</div>
                                    {filteredPairs.popular.map(pair => (
                                      <button
                                        key={pair}
                                        onClick={() => {
                                          setSelectedPair(pair)
                                          setShowPairDropdown(false)
                                          setPairSearchTerm('')
                                          setHasChanges(true)
                                        }}
                                        className={`w-full text-left px-3 py-2 text-xs hover:bg-agent-extraction/10 transition-colors ${
                                          selectedPair === pair ? 'bg-agent-extraction/20 text-bone-200' : 'text-bone-200'
                                        }`}
                                      >
                                        {pair}
                                      </button>
                                    ))}
                                  </div>
                                )}
                                
                                {filteredPairs.all.length > 0 && (
                                  <div>
                                    <div className="px-2 py-1 text-xs text-gray-500 bg-charcoal-900">All Pairs</div>
                                    {filteredPairs.all.map(pair => (
                                      <button
                                        key={pair}
                                        onClick={() => {
                                          setSelectedPair(pair)
                                          setShowPairDropdown(false)
                                          setPairSearchTerm('')
                                          setHasChanges(true)
                                        }}
                                        className={`w-full text-left px-3 py-2 text-xs hover:bg-agent-extraction/10 transition-colors ${
                                          selectedPair === pair ? 'bg-agent-extraction/20 text-bone-200' : 'text-bone-200'
                                        }`}
                                      >
                                        {pair}
                                      </button>
                                    ))}
                                  </div>
                                )}
                                
                                {filteredPairs.popular.length === 0 && filteredPairs.all.length === 0 && (
                                  <div className="px-3 py-4 text-xs text-gray-500 text-center">
                                    No pairs found
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Selected Data Points Summary */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">SELECTED DATA POINTS</h4>
                        </div>
                        <div className="bg-charcoal-800 border border-charcoal-600 p-3">
                          {selectedIndicators.size > 0 && (
                            <div className="mb-3">
                              <h5 className="text-xs text-gray-400 mb-2">Indicators:</h5>
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
                          {selectedSignals.size > 0 && (
                            <div className="mb-3">
                              <h5 className="text-xs text-gray-400 mb-2">Signals:</h5>
                              <div className="flex flex-wrap gap-2">
                                {Array.from(selectedSignals).map(signalId => (
                                  <span
                                    key={signalId}
                                    className="inline-flex items-center gap-1 px-2 py-1 bg-agent-extraction text-charcoal-900 text-xs rounded"
                                  >
                                    {signalId}
                                    <button
                                      onClick={() => {
                                        setSelectedSignals(prev => {
                                          const newSet = new Set(prev)
                                          newSet.delete(signalId)
                                          setHasChanges(true)
                                          return newSet
                                        })
                                      }}
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
                          {selectedIndicators.size === 0 && selectedSignals.size === 0 && (
                            <div className="text-gray-500 text-xs">No data sources selected</div>
                          )}
                        </div>
                      </div>

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
                                ? 'bg-agents-extraction text-charcoal-900'
                                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                            }`}
                          >
                            Technical Indicators
                          </button>
                          <button
                            onClick={() => setSelectedDataSource('Signals')}
                            className={`px-3 py-1 text-xs rounded transition-colors ${
                              selectedDataSource === 'Signals'
                                ? 'bg-agents-extraction text-charcoal-900'
                                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                            }`}
                          >
                            Signals
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

                      {/* Data Source Content */}
                      <div>
                        {selectedDataSource === 'Technical Indicators' && (
                          <TechnicalIndicatorsSection 
                            selectedIndicators={selectedIndicators}
                            onToggleIndicator={toggleIndicator}
                          />
                        )}
                        {selectedDataSource === 'Signals' && (
                          <SignalProvidersSection 
                            selectedSignals={selectedSignals}
                            onToggleSignal={toggleSignal}
                          />
                        )}
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
                    <div className="p-6 space-y-6">
                      {/* Decision Mode Selection */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">DECISION MODE</h4>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          {decisionModes.map(mode => (
                            <button
                              key={mode.value}
                              onClick={() => {
                                setDecisionMode(mode.value)
                                setHasChanges(true)
                              }}
                              className={`px-3 py-1 text-xs rounded transition-colors ${
                                decisionMode === mode.value
                                  ? 'bg-agents-decision text-charcoal-900 font-medium'
                                  : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                              }`}
                            >
                              {mode.label}
                            </button>
                          ))}
                        </div>
                        <div className="mt-2 text-xs text-gray-400">
                          {decisionModes.find(m => m.value === decisionMode)?.description}
                        </div>
                      </div>

                      {/* Analysis Frequency */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">ANALYSIS FREQUENCY</h4>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          {frequencyOptions.map(freq => (
                            <button
                              key={freq.value}
                              onClick={() => {
                                setAnalysisFrequency(freq.value)
                                setHasChanges(true)
                              }}
                              className={`px-3 py-1 text-xs rounded transition-colors ${
                                analysisFrequency === freq.value
                                  ? 'bg-agents-decision text-charcoal-900 font-medium'
                                  : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                              }`}
                            >
                              {freq.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Context Display */}
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-footnote text-bone-200 font-medium">MARKET CONTEXT</h4>
                        </div>
                        <div className="bg-charcoal-800 border border-charcoal-600 p-3 text-xs text-gray-300">
                          <div>Analyzing: <span className="text-bone-200">{selectedPair}</span></div>
                          <div className="mt-1">Using indicators: <span className="text-bone-200">{Array.from(selectedIndicators).join(', ')}</span></div>
                          <div className="mt-1">Review frequency: <span className="text-bone-200">Every {frequencyOptions.find(f => f.value === analysisFrequency)?.label.toLowerCase()}</span></div>
                        </div>
                      </div>

                      {/* Strategy Configuration */}
                      {!useCustomPrompt ? (
                        <div>
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-footnote text-bone-200 font-medium">
                              {decisionMode === 'autonomous' ? 'TRADING STRATEGY' : 'VALIDATION CRITERIA'}
                            </h4>
                            <button
                              onClick={() => setUseCustomPrompt(true)}
                              className="text-xs text-gray-400 hover:text-agent-decision transition-colors"
                            >
                              Custom Prompt ↗
                            </button>
                          </div>

                          {decisionMode === 'autonomous' ? (
                            <div className="space-y-4">
                              <div>
                                <label className="block text-xs text-gray-400 mb-2">Your trading strategy:</label>
                                <textarea
                                  value={tradingStrategy}
                                  onChange={(e) => {
                                    setTradingStrategy(e.target.value)
                                    setHasChanges(true)
                                  }}
                                  placeholder="Enter when conditions are met and avoid when..."
                                  rows={3}
                                  className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors resize-none"
                                />
                              </div>

                              <div>
                                <label className="block text-xs text-gray-400 mb-2">Market analysis approach:</label>
                                <textarea
                                  value={marketAnalysis}
                                  onChange={(e) => {
                                    setMarketAnalysis(e.target.value)
                                    setHasChanges(true)
                                  }}
                                  placeholder="Look for patterns and pay attention to..."
                                  rows={3}
                                  className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors resize-none"
                                />
                              </div>
                            </div>
                          ) : (
                            <div className="space-y-4">
                              <div>
                                <label className="block text-xs text-gray-400 mb-2">Signal acceptance criteria:</label>
                                <textarea
                                  value={validationCriteria}
                                  onChange={(e) => {
                                    setValidationCriteria(e.target.value)
                                    setHasChanges(true)
                                  }}
                                  placeholder="What makes a signal worth taking?"
                                  rows={3}
                                  className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors resize-none"
                                />
                              </div>

                              <div>
                                <label className="block text-xs text-gray-400 mb-2">Risk assessment approach:</label>
                                <textarea
                                  value={riskAssessment}
                                  onChange={(e) => {
                                    setRiskAssessment(e.target.value)
                                    setHasChanges(true)
                                  }}
                                  placeholder="How to evaluate signal risks?"
                                  rows={3}
                                  className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors resize-none"
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-footnote text-bone-200 font-medium">CUSTOM PROMPT</h4>
                            <button
                              onClick={() => setUseCustomPrompt(false)}
                              className="text-xs text-gray-400 hover:text-agent-decision transition-colors"
                            >
                              ← Guided Mode
                            </button>
                          </div>

                          <div>
                            <label className="block text-xs text-gray-400 mb-2">Full decision prompt (advanced):</label>
                            <textarea
                              value={customPrompt}
                              onChange={(e) => {
                                setCustomPrompt(e.target.value)
                                setHasChanges(true)
                              }}
                              placeholder="You are analyzing {SYMBOL} using {INDICATORS}. Your complete trading strategy and decision framework..."
                              rows={6}
                              className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision transition-colors resize-none"
                            />
                          </div>
                        </div>
                      )}

                      {/* Prompt Preview */}
                      <div>
                        <button
                          onClick={() => setShowPromptPreview(!showPromptPreview)}
                          className="flex items-center justify-between w-full p-3 bg-charcoal-800 border border-charcoal-700 text-xs text-gray-400 hover:text-bone-200 transition-colors"
                        >
                          <span>View Full Prompt</span>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className={`transition-transform ${showPromptPreview ? 'rotate-180' : ''}`}>
                            <path d="M7 10l5 5 5-5z"/>
                          </svg>
                        </button>
                        
                        {showPromptPreview && (
                          <div className="mt-2 bg-charcoal-900 border border-charcoal-700 p-3 text-xs max-h-64 overflow-y-auto">
                            <div className="space-y-3">
                              <div>
                                <div className="text-gray-500 mb-1">System Prompt (read-only):</div>
                                <div className="text-gray-400 italic">
                                  You are an expert cryptocurrency {decisionMode === 'autonomous' ? 'trader' : 'signal validator'} analyzing market data...
                                </div>
                              </div>
                              
                              <div>
                                <div className="text-gray-500 mb-1">Market Context (auto-generated):</div>
                                <div className="text-gray-400">
                                  Analyzing {selectedPair} using: {Array.from(selectedIndicators).concat(Array.from(selectedSignals)).join(', ') || 'No data sources selected'}
                                </div>
                              </div>
                              
                              <div>
                                <div className="text-gray-500 mb-1">User Strategy (editable):</div>
                                <div className="text-bone-200">
                                  {useCustomPrompt ? customPrompt || '[Custom prompt...]' : 
                                   decisionMode === 'autonomous' ? tradingStrategy : validationCriteria}
                                </div>
                              </div>
                              
                              <div>
                                <div className="text-gray-500 mb-1">Output Format (read-only):</div>
                                <div className="text-gray-400 font-mono">
                                  {decisionMode === 'autonomous' ? 
                                    'ACTION: ENTER|WAIT|EXIT' : 
                                    'ACTION: APPROVE|REJECT'
                                  }<br />
                                  CONFIDENCE: 0.000-1.000<br />
                                  REASONING: [Detailed analysis...]
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Output Format Info */}
                      <div>
                        <div className="bg-charcoal-800 border border-charcoal-700 p-3 text-xs">
                          <div className="text-gray-500 mb-2">Expected output format:</div>
                          <div className="text-gray-400 font-mono">
                            {decisionMode === 'autonomous' ? (
                              <>
                                ACTION: ENTER|WAIT|EXIT<br />
                                CONFIDENCE: 0.000-1.000<br />
                                REASONING: [Detailed analysis...]
                              </>
                            ) : (
                              <>
                                ACTION: APPROVE|REJECT<br />
                                CONFIDENCE: 0.000-1.000<br />
                                REASONING: [Detailed analysis...]
                              </>
                            )}
                          </div>
                        </div>
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
                    <div className="p-6 space-y-6">
                      {/* Tab Navigation */}
                      <div>
                        <div className="flex gap-2 flex-wrap">
                          <button
                            onClick={() => setTradingAgentTab('risk-management')}
                            className={`px-3 py-1 text-xs rounded transition-colors ${
                              tradingAgentTab === 'risk-management'
                                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                            }`}
                          >
                            Risk Management
                          </button>
                          <button
                            onClick={() => setTradingAgentTab('exchange-connection')}
                            className={`px-3 py-1 text-xs rounded transition-colors ${
                              tradingAgentTab === 'exchange-connection'
                                ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                            }`}
                          >
                            Exchange Connection
                          </button>
                        </div>
                        <div className="mt-2 text-xs text-gray-400">
                          {tradingAgentTab === 'risk-management' 
                            ? 'Configure position sizing, risk limits, and stop loss settings'
                            : 'Connect to centralized or decentralized exchanges'
                          }
                        </div>
                      </div>

                      {/* Tab Content */}
                      <div>
                        {tradingAgentTab === 'risk-management' && (
                          <RiskManagementSection
                            positionSizeType={positionSizeType}
                            onPositionSizeTypeChange={updateTradingField(setPositionSizeType)}
                            fixedAmount={fixedAmount}
                            onFixedAmountChange={updateTradingField(setFixedAmount)}
                            accountPercentage={accountPercentage}
                            onAccountPercentageChange={updateTradingField(setAccountPercentage)}
                            maxRiskPerTrade={maxRiskPerTrade}
                            onMaxRiskPerTradeChange={updateTradingField(setMaxRiskPerTrade)}
                            maxTotalExposure={maxTotalExposure}
                            onMaxTotalExposureChange={updateTradingField(setMaxTotalExposure)}
                            maxPositions={maxPositions}
                            onMaxPositionsChange={updateTradingField(setMaxPositions)}
                            dailyLossLimit={dailyLossLimit}
                            onDailyLossLimitChange={updateTradingField(setDailyLossLimit)}
                            stopTradingOnLimit={stopTradingOnLimit}
                            onStopTradingOnLimitChange={updateTradingField(setStopTradingOnLimit)}
                            defaultStopLoss={defaultStopLoss}
                            onDefaultStopLossChange={updateTradingField(setDefaultStopLoss)}
                            defaultTpRatio={defaultTpRatio}
                            onDefaultTpRatioChange={updateTradingField(setDefaultTpRatio)}
                            trailingStopsEnabled={trailingStopsEnabled}
                            onTrailingStopsEnabledChange={updateTradingField(setTrailingStopsEnabled)}
                            trailingDistance={trailingDistance}
                            onTrailingDistanceChange={updateTradingField(setTrailingDistance)}
                          />
                        )}
                        {tradingAgentTab === 'exchange-connection' && (
                          <ExchangeConnectionSection
                            exchangeType={exchangeType}
                            onExchangeTypeChange={updateTradingField(setExchangeType)}
                            selectedExchange={selectedExchange}
                            onSelectedExchangeChange={updateTradingField(setSelectedExchange)}
                            apiKey={apiKey}
                            onApiKeyChange={updateTradingField(setApiKey)}
                            secretKey={secretKey}
                            onSecretKeyChange={updateTradingField(setSecretKey)}
                            connectionStatus={connectionStatus}
                            onTestConnection={handleTestConnection}
                            onClearCredentials={handleClearCredentials}
                            selectedNetwork={selectedNetwork}
                            onSelectedNetworkChange={updateTradingField(setSelectedNetwork)}
                            walletConnected={walletConnected}
                            onConnectWallet={handleConnectWallet}
                            slippageTolerance={slippageTolerance}
                            onSlippageToleranceChange={updateTradingField(setSlippageTolerance)}
                          />
                        )}
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