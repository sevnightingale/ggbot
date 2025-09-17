'use client'

import { useState } from 'react'
import { useBotStore } from '@/store/bot'
import { DecisionConfig } from '@/types'

interface DecisionConfigFormProps {
  activeTab: number
  config: DecisionConfig | null
}

const llmProviders = [
  { value: 'deepseek', label: 'DeepSeek (Recommended)', description: 'Cost-effective with strong reasoning' },
  { value: 'openai', label: 'OpenAI GPT-4', description: 'Premium quality, higher cost' },
  { value: 'anthropic', label: 'Anthropic Claude', description: 'Good balance of quality and cost' }
]

const strategyTemplates = [
  {
    name: 'Momentum Breakout',
    strategy: 'Trade momentum breakouts using RSI and MACD confluence. Enter long when RSI crosses above 50 with MACD bullish crossover. Enter short when RSI drops below 50 with MACD bearish crossover. Look for volume confirmation and strong directional moves.',
    risk: 'Max position size 3% of capital. Max leverage 5x. Stop trading after 2 consecutive losses.',
    context: 'I prefer catching strong directional moves over ranging markets. Focus on clear signals with multiple confirmations.'
  },
  {
    name: 'Mean Reversion',
    strategy: 'Trade oversold/overbought conditions using RSI and Bollinger Bands. Enter long when RSI < 30 and price touches lower BB. Enter short when RSI > 70 and price touches upper BB. Target middle BB for exits.',
    risk: 'Max position size 2% of capital. Max leverage 3x. Stop trading after 3 losses in 6 hours.',
    context: 'I prefer scalping quick reversals in ranging markets. Quick in and out trades work best for my style.'
  },
  {
    name: 'Trend Following',
    strategy: 'Follow established trends using EMA crossovers and MACD. Enter long when price is above 20 EMA and MACD is positive. Enter short when price is below 20 EMA and MACD is negative. Hold positions until trend reversal signals.',
    risk: 'Max position size 5% of capital. Max leverage 10x. Stop trading after 5% daily drawdown.',
    context: 'I prefer riding trends for bigger moves. Patient holding is more important than frequent trading.'
  }
]

export function DecisionConfigForm({ activeTab, config }: DecisionConfigFormProps) {
  const { updateAgentConfig, setError } = useBotStore()
  const [isSaving, setIsSaving] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  
  const [formData, setFormData] = useState<DecisionConfig>({
    llm_provider: config?.llm_provider || 'deepseek',
    system_prompt: config?.system_prompt || '',
    strategy: config?.strategy || '',
    additional_context: config?.additional_context || ''
  })

  const handleSave = async () => {
    try {
      setIsSaving(true)
      setError(null)
      
      // Validation
      if (!formData.strategy.trim()) {
        setError('Trading strategy is required')
        return
      }

      await updateAgentConfig('decision', formData)
      setJustSaved(true)
      setTimeout(() => setJustSaved(false), 2000)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save configuration')
    } finally {
      setIsSaving(false)
    }
  }

  const applyTemplate = (template: typeof strategyTemplates[0]) => {
    setFormData(prev => ({
      ...prev,
      strategy: template.strategy,
      additional_context: template.context
    }))
  }

  const renderStrategyTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">Trading Strategy</h3>
        <p className="text-sm text-bone-400 mb-4">
          Describe your trading strategy in natural language. The AI will interpret and execute this strategy autonomously.
        </p>

        {/* Strategy Input - Moved to top */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Your Trading Strategy</label>
          <textarea
            value={formData.strategy}
            onChange={(e) => setFormData(prev => ({ ...prev, strategy: e.target.value }))}
            placeholder="Describe how you want the AI to trade. For example: 'Trade momentum breakouts using RSI position relative to 50. If RSI is above 50, enter SHORT. If RSI is below 50, enter LONG. Use 15m timeframe for entries. Hold positions for at least 5 minutes, then exit on 2-point RSI move in opposite direction.'"
            rows={8}
            className="w-full p-4 bg-charcoal-700 border border-bone-200/80 text-bone-200 placeholder-bone-400 resize-none focus:border-agents-decision focus:outline-none"
          />
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-bone-400">
              Be specific about entry/exit conditions, timeframes, and decision logic.
            </p>
            <p className="text-xs text-bone-400">
              {formData.strategy.length} characters
            </p>
          </div>
        </div>

        {/* Strategy Templates - Moved below */}
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Quick Start Templates</h4>
          <div className="grid gap-3">
            {strategyTemplates.map((template, index) => (
              <div key={index} className="p-4 bg-charcoal-700/50 border border-bone-200/60">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className="font-medium text-bone-200 mb-1">{template.name}</h5>
                    <p className="text-sm text-bone-400 line-clamp-2">{template.strategy}</p>
                  </div>
                  <button
                    onClick={() => applyTemplate(template)}
                    className="ml-3 px-3 py-1 text-xs bg-agents-decision hover:bg-agents-decision/80 text-charcoal-900 font-medium transition-colors"
                  >
                    Use Template
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Output Format - New section */}
        <div className="p-4 bg-charcoal-700/50 border border-bone-200/60">
          <h4 className="text-sm font-medium mb-3">Required Output Format</h4>
          <div className="p-3 bg-charcoal-800/50 border border-bone-200/40 font-mono text-xs text-bone-300">
            <div className="text-bone-400 opacity-60">
              ACTION: [long/short/no_action]<br/>
              CONFIDENCE: [0.000-1.000, 3 decimal places]<br/>
              STOP_LOSS: [price level]<br/>
              TAKE_PROFIT: [price level]<br/>
              <br/>
              REASONING:<br/>
              [your detailed analysis]
            </div>
          </div>
          <p className="text-xs text-bone-400 mt-2">
            All decisions must follow this exact format for proper system integration.
          </p>
        </div>

        {/* Strategy Tips */}
        <div className="p-4 bg-blue-900/20 border border-blue-500/60">
          <h5 className="text-sm font-medium text-blue-300 mb-2">Strategy Writing Tips</h5>
          <ul className="text-sm text-blue-200 space-y-1">
            <li>• Specify clear entry and exit conditions</li>
            <li>• Mention preferred timeframes and indicators</li>
            <li>• Describe risk tolerance and position management</li>
            <li>• Include market conditions you prefer (trending vs ranging)</li>
          </ul>
        </div>
      </div>
    </div>
  )

  const renderLLMSettingsTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">LLM Provider</h3>
        <p className="text-sm text-bone-400 mb-4">
          Choose the AI model that will interpret your strategy and make trading decisions.
        </p>

        <div className="space-y-3">
          {llmProviders.map((provider) => (
            <label key={provider.value} className="flex items-start gap-3 p-4 bg-charcoal-700/50 border border-bone-200/60 cursor-pointer hover:border-bone-200/90 transition-colors">
              <input
                type="radio"
                name="llm_provider"
                value={provider.value}
                checked={formData.llm_provider === provider.value}
                onChange={(e) => setFormData(prev => ({ ...prev, llm_provider: e.target.value }))}
                className="mt-1 text-agents-decision focus:ring-agents-decision"
              />
              <div className="flex-1">
                <div className="font-medium text-bone-200">{provider.label}</div>
                <div className="text-sm text-bone-400">{provider.description}</div>
              </div>
            </label>
          ))}
        </div>

        {/* Provider-specific settings */}
        {formData.llm_provider === 'openai' && (
          <div className="mt-4 p-4 bg-yellow-900/20 border border-yellow-500/60">
            <p className="text-sm text-yellow-200">
              <strong>Note:</strong> OpenAI GPT-4 provides excellent reasoning but has higher API costs. 
              Make sure your OpenAI API key is configured in the environment.
            </p>
          </div>
        )}

        {formData.llm_provider === 'deepseek' && (
          <div className="mt-4 p-4 bg-bone-200/10 border border-bone-200/60">
            <p className="text-sm text-bone-200">
              <strong>Recommended:</strong> DeepSeek offers strong reasoning capabilities at a fraction 
              of the cost compared to other providers. Great for frequent trading decisions.
            </p>
          </div>
        )}
      </div>

      {/* Model Performance Notes */}
      <div className="p-4 bg-bone-200/10 border border-bone-200/60">
        <h4 className="text-sm font-medium mb-2">Model Performance</h4>
        <p className="text-sm text-bone-300">
          All models are configured to output structured decisions with confidence scoring and reasoning. 
          The system automatically includes market context from technical indicators and price data.
        </p>
      </div>
    </div>
  )


  const renderTabContent = () => {
    switch (activeTab) {
      case 0: return renderStrategyTab()
      case 1: return renderLLMSettingsTab()
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
                ? 'bg-agents-decision/50 text-charcoal-900/70 cursor-not-allowed'
                : 'bg-agents-decision hover:bg-agents-decision/80 text-charcoal-900'
          }`}
        >
          {justSaved ? '✓ Saved!' : isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}