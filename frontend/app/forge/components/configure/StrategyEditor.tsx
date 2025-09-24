'use client'

import React, { useState } from 'react'
import { usePermissions } from '@/lib/permissions'
import { ConfigData } from '@/lib/api'

interface StrategyEditorProps {
  configData?: ConfigData
  onUpdate?: (updates: Partial<ConfigData>) => void
  className?: string
}

export function StrategyEditor({
  configData,
  onUpdate,
  className = ''
}: StrategyEditorProps) {
  const { canAccess } = usePermissions()
  const currentStrategy = configData?.decision?.user_prompt || ''
  const analysisFrequency = configData?.decision?.analysis_frequency || '1h'
  const llmProvider = configData?.llm_config?.provider || 'default'
  const configType = configData?.config_type || 'autonomous_trading'

  // State for collapsible sections
  const [showSystemSections, setShowSystemSections] = useState(false)

  // Handle frequency selection
  const handleFrequencyChange = (freq: string) => {
    // Check permissions for high-frequency options
    if ((freq === '5m' || freq === '15m') && !canAccess('premium_llms')) {
      alert('High-frequency analysis requires a premium subscription. Upgrade to access 5m and 15m frequencies!')
      return
    }

    onUpdate?.({
      decision: {
        analysis_frequency: freq,
        system_prompt: configData?.decision?.system_prompt,
        user_prompt: configData?.decision?.user_prompt
      }
    })
  }

  // Handle strategy text change
  const handleStrategyChange = (value: string) => {
    // Limit to 10,000 characters
    if (value.length > 10000) {
      value = value.substring(0, 10000)
    }

    onUpdate?.({
      decision: {
        analysis_frequency: configData?.decision?.analysis_frequency ?? null,
        system_prompt: configData?.decision?.system_prompt,
        user_prompt: value
      }
    })
  }

  // Auto-resize textarea
  const handleTextareaResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
    handleStrategyChange(textarea.value)
  }

  // Handle LLM provider change
  const handleProviderChange = (provider: string) => {
    // Check if user has access to premium LLMs
    if (provider === 'openai' && !canAccess('premium_llms')) {
      alert('Premium AI models require a ggbase subscription. Upgrade to access OpenAI GPT-5!')
      return
    }

    // Set appropriate model for each provider
    let model
    if (provider === 'openai') {
      model = 'gpt-5'
    } else if (provider === 'default') {
      model = 'default'
    } else if (provider === 'deepseek') {
      model = 'deepseek-reasoner'
    } else if (provider === 'anthropic') {
      model = 'claude-opus-4-1-20250805'
    } else if (provider === 'xai') {
      model = 'grok-4-fast-non-reasoning'
    } else {
      model = 'deepseek-reasoner' // fallback
    }

    onUpdate?.({
      llm_config: {
        provider,
        model,
        use_platform_keys: true,
        use_own_key: false,
        ...configData?.llm_config
      }
    })
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Analysis Frequency - Hide for signal_validation configs */}
      {configType !== 'signal_validation' && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
            Analysis Frequency
          </h3>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            How often your bot analyzes the market and makes decisions
          </p>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {['5m', '15m', '1h', '4h'].map((freq) => {
              const isPremium = freq === '5m' || freq === '15m'
              const hasAccess = !isPremium || canAccess('premium_llms')
              const isLocked = isPremium && !hasAccess

              return (
                <button
                  key={freq}
                  onClick={() => handleFrequencyChange(freq)}
                  disabled={isLocked}
                  className={`px-4 py-3 text-sm rounded-xl border transition-colors relative ${
                    analysisFrequency === freq
                      ? 'bg-[var(--agent-decision)] text-white border-[var(--agent-decision)]'
                      : isLocked
                        ? 'bg-[var(--bg-primary)] text-[var(--text-muted)] border-[var(--border)] opacity-60 cursor-not-allowed'
                        : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span>Every {freq}</span>
                    {isPremium && (
                      <div className="flex items-center gap-1">
                        {isLocked && (
                          <svg className="h-3 w-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 0h12m-6 0V9a6 6 0 012.121-4.586M12 15v2m-6 0h12m-6 0V9a6 6 0 00-2.121-4.586" />
                          </svg>
                        )}
                        <span className={`text-xs px-1 py-0.5 rounded-full ${
                          isLocked
                            ? 'bg-amber-500/20 text-amber-500/70'
                            : 'bg-amber-500/20 text-amber-500'
                        }`}>
                          Pro
                        </span>
                      </div>
                    )}
                  </div>
                </button>
              )
            })}
          </div>

          <div className="mt-4 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="text-sm text-[var(--text-muted)]">
              Current: <span className="text-[var(--text-primary)] font-medium">Every {analysisFrequency}</span>
              {(analysisFrequency === '5m' || analysisFrequency === '15m') && (
                <span className="ml-2 text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-500">
                  Pro Feature
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Trading Strategy - Main Section */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Your Trading Strategy
        </h3>
        <p className="text-sm text-[var(--text-muted)] mb-6">
          Define your trading logic. The AI will use market data from your selected indicators to execute this strategy.
        </p>

        {/* User Strategy Input - The Main Focus */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Strategy Logic
            </label>
            <textarea
              value={currentStrategy}
              onChange={handleTextareaResize}
              rows={6}
              maxLength={10000}
              className="w-full p-4 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--agent-decision)]/30 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-[var(--agent-decision)] resize-none overflow-hidden"
              placeholder="Example: if RSI 1h below 30 and volume > 1.5x average enter long, if RSI 1h above 70 exit position"
              style={{minHeight: '6rem'}}
            />
            <div className="mt-2 flex justify-between items-center">
              <div className="text-xs text-[var(--text-muted)]">
                Write clear conditions for when to enter long/short positions, when to exit, and any risk rules.
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                {currentStrategy.length}/10,000
              </div>
            </div>
          </div>

          {/* Default Strategy Example */}
          <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="text-xs font-medium text-[var(--text-muted)] mb-2">DEFAULT STRATEGY:</div>
            <div className="text-sm text-[var(--text-secondary)] font-mono">
              if RSI 1h below 50 enter long, if above 50 enter short
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-2">
              This simple strategy will always enter a trade, giving you immediate results to see your bot in action.
            </div>
          </div>
        </div>
      </div>

      {/* System Template Context - Collapsible */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Complete Prompt Template
          </h3>
          <button
            onClick={() => setShowSystemSections(!showSystemSections)}
            className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            {showSystemSections ? 'Hide Details' : 'View Full Context'}
          </button>
        </div>

        <p className="text-sm text-[var(--text-muted)] mb-4">
          See the complete prompt structure that gets sent to the AI (your strategy + system context)
        </p>

        {showSystemSections && (
          <div className="space-y-4">
            {/* Market Data Section */}
            <div>
              <div className="text-sm font-medium text-[var(--text-muted)] mb-2">1. MARKET DATA ANALYSIS</div>
              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] opacity-70">
                <div className="text-sm text-[var(--text-secondary)]">
                  All technical indicators from your Market Data configuration across 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w)
                </div>
              </div>
            </div>

            {/* Volume Analysis Section */}
            <div>
              <div className="text-sm font-medium text-[var(--text-muted)] mb-2">2. VOLUME CONFIRMATION ANALYSIS</div>
              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] opacity-70">
                <div className="text-sm text-[var(--text-secondary)]">
                  Current volume vs average volume analysis for trade confirmation
                </div>
              </div>
            </div>

            {/* User Strategy Section */}
            <div>
              <div className="text-sm font-medium text-[var(--agent-decision)] mb-2">3. YOUR TRADING STRATEGY ← YOU CONTROL THIS</div>
              <div className="p-4 rounded-xl bg-[var(--agent-decision)]/10 border border-[var(--agent-decision)]/30">
                <div className="text-sm text-[var(--text-primary)] font-mono">
                  {currentStrategy || 'Your strategy will appear here...'}
                </div>
              </div>
            </div>

            {/* Task Instructions */}
            <div>
              <div className="text-sm font-medium text-[var(--text-muted)] mb-2">4. TASK INSTRUCTIONS</div>
              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] opacity-70">
                <div className="text-sm text-[var(--text-secondary)]">
                  Instructions to strictly follow your strategy, not invent additional rules, and use only provided data.
                </div>
              </div>
            </div>

            {/* Output Format */}
            <div>
              <div className="text-sm font-medium text-[var(--text-muted)] mb-2">5. OUTPUT FORMAT</div>
              <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] opacity-70">
                <div className="text-sm text-[var(--text-secondary)] font-mono">
                  ACTION: [long/short/hold/wait]<br/>
                  CONFIDENCE: [0.000-1.000]<br/>
                  REASONING: [explanation]<br/>
                  STOP_LOSS: [price or null]<br/>
                  TAKE_PROFIT: [price or null]
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* LLM Provider */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          AI Decision Engine
        </h3>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Choose which AI model analyzes your strategy and makes trading decisions
        </p>

        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {(configData?.llm_config?.use_own_key ? [
              // Show all providers when using personal keys
              {
                id: 'default',
                name: 'Default LLM',
                description: 'Platform recommended model (Grok 4 Fast)',
                recommended: true
              },
              {
                id: 'openai',
                name: 'OpenAI GPT-5',
                description: 'Latest OpenAI model with advanced reasoning',
                premium: false // Available with personal keys
              },
              {
                id: 'deepseek',
                name: 'DeepSeek R1',
                description: 'Advanced reasoning model for complex strategies',
                premium: false
              },
              {
                id: 'anthropic',
                name: 'Claude Opus',
                description: 'Anthropic\'s most capable model',
                premium: false
              },
              {
                id: 'xai',
                name: 'Grok 4 Fast',
                description: 'XAI\'s fast reasoning model',
                premium: false
              }
            ] : [
              // Show limited options when using platform keys
              {
                id: 'default',
                name: 'Default LLM',
                description: 'Our recommended AI model optimized for trading performance',
                recommended: true
              },
              {
                id: 'openai',
                name: 'OpenAI GPT-5',
                description: 'Premium model for advanced analysis',
                premium: true
              }
            ]).map((provider) => {
              const isPremium = provider.premium
              const hasAccess = !isPremium || canAccess('premium_llms')
              const isLocked = isPremium && !hasAccess

              return (
                <button
                  key={provider.id}
                  onClick={() => handleProviderChange(provider.id)}
                  disabled={isLocked}
                  className={`p-4 rounded-xl border text-left transition-colors relative ${
                    llmProvider === provider.id
                      ? 'bg-[var(--agent-decision)]/20 border-[var(--agent-decision)] text-[var(--text-primary)]'
                      : isLocked
                        ? 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-muted)] opacity-60 cursor-not-allowed'
                        : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
                  }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">{provider.name}</div>
                  {provider.recommended && (
                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-500">
                      Recommended
                    </span>
                  )}
                  {isPremium && (
                    <div className="flex items-center gap-1">
                      {isLocked && (
                        <svg className="h-3 w-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 0h12m-6 0V9a6 6 0 012.121-4.586M12 15v2m-6 0h12m-6 0V9a6 6 0 00-2.121-4.586" />
                        </svg>
                      )}
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        isLocked
                          ? 'bg-amber-500/20 text-amber-500/70'
                          : 'bg-amber-500/20 text-amber-500'
                      }`}>
                        Premium
                      </span>
                    </div>
                  )}
                </div>
                <div className="text-xs text-[var(--text-muted)]">
                  {provider.description}
                </div>
              </button>
              )
            })}
          </div>

          {/* API Key Configuration */}
          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div className="text-sm text-[var(--text-muted)]">
                Current: <span className="text-[var(--text-primary)] font-medium">
                  {llmProvider === 'default' ? 'Default LLM' :
                 llmProvider === 'openai' ? 'OpenAI GPT-5' :
                 llmProvider === 'deepseek' ? 'DeepSeek R1' :
                 llmProvider === 'anthropic' ? 'Claude Opus' :
                 llmProvider === 'xai' ? 'Grok 4 Fast' : 'Default LLM'}
                </span> • {configData?.llm_config?.use_own_key ? 'Using personal API keys' : 'Using platform keys'}
              </div>
            </div>

            {/* API Key Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
              <div>
                <div className="text-sm font-medium text-[var(--text-primary)]">
                  Use Personal API Keys
                </div>
                <div className="text-xs text-[var(--text-muted)]">
                  Use your own API keys instead of platform keys
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={configData?.llm_config?.use_own_key || false}
                  onChange={(e) => {
                    onUpdate?.({
                      llm_config: {
                        provider: 'default',
                        model: 'default',
                        ...configData?.llm_config,
                        use_own_key: e.target.checked,
                        use_platform_keys: !e.target.checked
                      }
                    })
                  }}
                  className="sr-only"
                />
                <div className={`w-11 h-6 rounded-full transition-colors ${
                  configData?.llm_config?.use_own_key
                    ? 'bg-[var(--agent-decision)]'
                    : 'bg-[var(--border)]'
                }`}>
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform duration-200 ease-in-out ${
                    configData?.llm_config?.use_own_key ? 'translate-x-5' : 'translate-x-0'
                  } mt-0.5 ml-0.5`}></div>
                </div>
              </label>
            </div>

            {/* Show API Key Manager if using personal keys */}
            {configData?.llm_config?.use_own_key && (
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                <div className="text-sm text-[var(--text-primary)] mb-3">
                  Personal API Keys Required
                </div>
                <div className="text-xs text-[var(--text-muted)] mb-3">
                  Add your API keys in Settings → API Keys to use personal credentials.
                </div>
                <button
                  onClick={() => window.open('/settings/api-keys', '_blank')}
                  className="text-xs text-[var(--agent-decision)] hover:underline"
                >
                  Manage API Keys →
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}