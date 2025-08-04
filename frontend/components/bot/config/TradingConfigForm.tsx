'use client'

import { useState } from 'react'
import { useBotStore } from '@/store/bot'
import { TradingConfig } from '@/types'
import { AlertTriangle, DollarSign, Shield, Settings } from 'lucide-react'

interface TradingConfigFormProps {
  activeTab: number
  config: TradingConfig | null
}

const exchanges = [
  { value: 'bitmex', label: 'BitMEX', description: 'Crypto derivatives, high leverage available' },
  { value: 'binance', label: 'Binance', description: 'Spot and futures, largest volume' },
  { value: 'coinbase', label: 'Coinbase Pro', description: 'US regulated, spot trading' }
]

const orderTypes = [
  { value: 'market', label: 'Market Orders', description: 'Immediate execution at current price' },
  { value: 'limit', label: 'Limit Orders', description: 'Execute at specified price or better' },
  { value: 'stop', label: 'Stop Orders', description: 'Trigger when price reaches stop level' }
]

export function TradingConfigForm({ activeTab, config }: TradingConfigFormProps) {
  const { updateAgentConfig, setError } = useBotStore()
  const [isSaving, setIsSaving] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  
  const [formData, setFormData] = useState<TradingConfig>({
    risk_rules: {
      max_leverage: config?.risk_rules?.max_leverage || 10,
      max_position_size_pct: config?.risk_rules?.max_position_size_pct || 0.05,
      max_risk_per_trade_pct: config?.risk_rules?.max_risk_per_trade_pct || 0.02,
      min_equity_protection: config?.risk_rules?.min_equity_protection || 0.80,
      max_contracts_per_trade: config?.risk_rules?.max_contracts_per_trade || 1000000
    }
  })

  const [selectedExchange, setSelectedExchange] = useState('bitmex')
  const [selectedOrderTypes, setSelectedOrderTypes] = useState(['market', 'limit', 'stop'])

  const handleSave = async () => {
    try {
      setIsSaving(true)
      setError(null)
      await updateAgentConfig('trading', formData)
      setJustSaved(true)
      setTimeout(() => setJustSaved(false), 2000)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save configuration')
    } finally {
      setIsSaving(false)
    }
  }

  const calculateMaxPositionValue = (equity: number = 10000) => {
    return equity * formData.risk_rules.max_position_size_pct * formData.risk_rules.max_leverage
  }

  const calculateMaxRiskValue = (equity: number = 10000) => {
    return equity * formData.risk_rules.max_risk_per_trade_pct
  }

  const renderExchangeTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Exchange Selection</h3>
        <p className="text-sm text-bone-400 mb-4">
          Choose the cryptocurrency exchange where trades will be executed.
        </p>

        <div className="space-y-3">
          {exchanges.map((exchange) => (
            <label key={exchange.value} className="flex items-start gap-3 p-4 bg-charcoal-700/50 border border-bone-200/60 cursor-pointer hover:border-bone-200/90 transition-colors">
              <input
                type="radio"
                name="exchange"
                value={exchange.value}
                checked={selectedExchange === exchange.value}
                onChange={(e) => setSelectedExchange(e.target.value)}
                className="mt-1 text-agents-trading focus:ring-agents-trading"
              />
              <div className="flex-1">
                <div className="font-medium text-bone-200">{exchange.label}</div>
                <div className="text-sm text-bone-400">{exchange.description}</div>
              </div>
            </label>
          ))}
        </div>

        {/* Connection Status */}
        <div className="mt-6 p-4 bg-charcoal-700/50 border border-bone-200/60">
          <h4 className="text-sm font-medium mb-3">API Connection</h4>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-2">API Key Status</label>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-status-success"></div>
                <span className="text-sm text-bone-300">Connected (Environment Variable)</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Environment</label>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-status-warning"></div>
                <span className="text-sm text-bone-300">Testnet Mode (Safe for Testing)</span>
              </div>
              <p className="text-xs text-bone-400 mt-1">
                Switch to production in environment variables when ready for live trading
              </p>
            </div>

            <button className="px-4 py-2 bg-charcoal-600 hover:bg-charcoal-500 border border-bone-200/80 text-bone-200 text-sm transition-colors">
              Test Connection
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderRiskManagementTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Risk Management</h3>
        <p className="text-sm text-bone-400 mb-6">
          Configure position sizing, leverage limits, and safety rules. These are hard limits that cannot be overridden.
        </p>

        {/* Position Sizing */}
        <div className="space-y-6">
          <div className="p-4 bg-charcoal-700/50 border border-bone-200/60">
            <div className="flex items-center gap-2 mb-4">
              <DollarSign size={16} className="text-agents-trading" />
              <h4 className="font-medium">Position Sizing</h4>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Position Size (% of capital)
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="0.01"
                    max="0.20"
                    step="0.01"
                    value={formData.risk_rules.max_position_size_pct}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      risk_rules: { ...prev.risk_rules, max_position_size_pct: parseFloat(e.target.value) }
                    }))}
                    className="w-full h-2 bg-charcoal-600 appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-bone-400">
                    <span>1%</span>
                    <span className="font-medium text-bone-200">
                      {(formData.risk_rules.max_position_size_pct * 100).toFixed(1)}%
                    </span>
                    <span>20%</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Leverage
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="1"
                    max="100"
                    step="1"
                    value={formData.risk_rules.max_leverage}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      risk_rules: { ...prev.risk_rules, max_leverage: parseInt(e.target.value) }
                    }))}
                    className="w-full h-2 bg-charcoal-600 appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-bone-400">
                    <span>1x</span>
                    <span className="font-medium text-bone-200">
                      {formData.risk_rules.max_leverage}x
                    </span>
                    <span>100x</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Position Calculator */}
            <div className="mt-4 p-3 bg-charcoal-600/50">
              <h5 className="text-sm font-medium mb-2">Position Calculator</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-bone-400">Max Position Value:</span>
                  <span className="ml-2 font-medium text-bone-200">
                    ${calculateMaxPositionValue().toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-bone-400">Based on $10k equity</span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Limits */}
          <div className="p-4 bg-charcoal-700/50 border border-bone-200/60">
            <div className="flex items-center gap-2 mb-4">
              <Shield size={16} className="text-agents-trading" />
              <h4 className="font-medium">Risk Limits</h4>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Risk Per Trade (% of capital)
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="0.005"
                    max="0.10"
                    step="0.005"
                    value={formData.risk_rules.max_risk_per_trade_pct}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      risk_rules: { ...prev.risk_rules, max_risk_per_trade_pct: parseFloat(e.target.value) }
                    }))}
                    className="w-full h-2 bg-charcoal-600 appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-bone-400">
                    <span>0.5%</span>
                    <span className="font-medium text-bone-200">
                      {(formData.risk_rules.max_risk_per_trade_pct * 100).toFixed(1)}%
                    </span>
                    <span>10%</span>
                  </div>
                  <p className="text-xs text-bone-400">
                    Max risk: ${calculateMaxRiskValue().toFixed(0)} per trade
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Minimum Equity Protection
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="0.50"
                    max="0.95"
                    step="0.05"
                    value={formData.risk_rules.min_equity_protection}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      risk_rules: { ...prev.risk_rules, min_equity_protection: parseFloat(e.target.value) }
                    }))}
                    className="w-full h-2 bg-charcoal-600 appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-bone-400">
                    <span>50%</span>
                    <span className="font-medium text-bone-200">
                      {(formData.risk_rules.min_equity_protection * 100).toFixed(0)}%
                    </span>
                    <span>95%</span>
                  </div>
                  <p className="text-xs text-bone-400">
                    Stop trading if equity drops below this level
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Emergency Limits */}
          <div className="p-4 bg-red-900/20 border border-red-500/60">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={16} className="text-red-400" />
              <h4 className="font-medium text-red-300">Emergency Limits</h4>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Max Contracts Per Trade
              </label>
              <input
                type="number"
                value={formData.risk_rules.max_contracts_per_trade}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  risk_rules: { ...prev.risk_rules, max_contracts_per_trade: parseInt(e.target.value) || 0 }
                }))}
                className="w-full p-3 bg-charcoal-700 border border-bone-200/80 text-bone-200"
                placeholder="1000000"
              />
              <p className="text-xs text-red-300 mt-1">
                Hard limit to prevent runaway position sizes
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderExecutionRulesTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Execution Rules</h3>
        <p className="text-sm text-bone-400 mb-6">
          Configure how trades are executed and managed.
        </p>

        {/* Order Types */}
        <div className="p-4 bg-charcoal-700/50 border border-bone-200/10 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <Settings size={16} className="text-agents-trading" />
            <h4 className="font-medium">Allowed Order Types</h4>
          </div>

          <div className="space-y-3">
            {orderTypes.map((orderType) => (
              <label key={orderType.value} className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedOrderTypes.includes(orderType.value)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedOrderTypes(prev => [...prev, orderType.value])
                    } else {
                      setSelectedOrderTypes(prev => prev.filter(t => t !== orderType.value))
                    }
                  }}
                  className="mt-1 border-bone-200/80 text-agents-trading focus:ring-agents-trading"
                />
                <div className="flex-1">
                  <div className="font-medium text-bone-200">{orderType.label}</div>
                  <div className="text-sm text-bone-400">{orderType.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Execution Settings */}
        <div className="p-4 bg-charcoal-700/50 border border-bone-200/10 rounded-lg">
          <h4 className="font-medium mb-4">Execution Preferences</h4>
          
          <div className="space-y-4">
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  defaultChecked
                  className="border-bone-200/80 text-agents-trading focus:ring-agents-trading"
                />
                <span className="text-sm">Auto-place stop loss orders</span>
              </label>
              <p className="text-xs text-bone-400 ml-6">
                Automatically place stop loss orders when opening positions
              </p>
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  defaultChecked
                  className="border-bone-200/80 text-agents-trading focus:ring-agents-trading"
                />
                <span className="text-sm">Auto-place take profit orders</span>
              </label>
              <p className="text-xs text-bone-400 ml-6">
                Automatically place take profit orders when opening positions
              </p>
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="border-bone-200/80 text-agents-trading focus:ring-agents-trading"
                />
                <span className="text-sm">Enable position scaling</span>
              </label>
              <p className="text-xs text-bone-400 ml-6">
                Allow adding to winning positions (pyramid trading)
              </p>
            </div>
          </div>
        </div>

        {/* Slippage and Timing */}
        <div className="p-4 bg-charcoal-700/50 border border-bone-200/10 rounded-lg">
          <h4 className="font-medium mb-4">Slippage & Timing</h4>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Max Slippage Tolerance
              </label>
              <select className="w-full p-3 bg-charcoal-600 border border-bone-200/80 text-bone-200">
                <option value="0.1">0.1% (Conservative)</option>
                <option value="0.25" selected>0.25% (Balanced)</option>
                <option value="0.5">0.5% (Aggressive)</option>
                <option value="1.0">1.0% (High Volatility)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Order Timeout (seconds)
              </label>
              <select className="w-full p-3 bg-charcoal-600 border border-bone-200/80 text-bone-200">
                <option value="30">30 seconds</option>
                <option value="60" selected>60 seconds</option>
                <option value="120">2 minutes</option>
                <option value="300">5 minutes</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 0: return renderExchangeTab()
      case 1: return renderRiskManagementTab()
      case 2: return renderExecutionRulesTab()
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
                ? 'bg-agents-trading/50 text-charcoal-900/70 cursor-not-allowed'
                : 'bg-agents-trading hover:bg-agents-trading/80 text-charcoal-900'
          }`}
        >
          {justSaved ? '✓ Saved!' : isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}