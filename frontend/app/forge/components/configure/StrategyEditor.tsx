'use client'

import React, { useState, useEffect, useRef } from 'react'
import Image from 'next/image'
import { Crown } from 'lucide-react'
import { usePermissions } from '@/lib/permissions'
import { ConfigData, apiClient } from '@/lib/api'
import { UpgradeModal } from '@/components/UpgradeModal'

interface LLMModel {
  model_id: string
  display_name: string
  provider: string
  context_display: string
  supports_thinking: boolean
  enabled: boolean
  cost_per_decision: {
    standard: number
    thinking: number
  }
}

// Logo mapping for LLM models
const MODEL_LOGOS: Record<string, string> = {
  'grok': '/Grok_logo.png',
  'claude': '/Claude_logo.png',
  'gemini': '/Gemini_logo.png',
  'deepseek': '/deepseek_logo.png',
  'gpt': '/GPT_logo.png',
  'kimi': '/kimi-color.png',
  'qwen': '/qwen_logo.png',
}

// Background colors for model logos
const MODEL_COLORS: Record<string, string> = {
  'qwen': '#8760ec',
  'deepseek': '#617aef',
  'claude': '#ff6938',
  'grok': '#030303',
  'gemini': '#458dfb',
  'gpt': '#1d967b',
  'kimi': '#080808',
}

interface StrategyEditorProps {
  configData?: ConfigData
  configType?: string
  onUpdate?: (updates: Partial<ConfigData>) => void
  className?: string
}

export function StrategyEditor({
  configData,
  configType,
  onUpdate,
  className = ''
}: StrategyEditorProps) {
  const { canAccess } = usePermissions()
  const currentStrategy = configData?.decision?.user_prompt || ''
  const analysisFrequency = configData?.decision?.analysis_frequency || '1h'
  const llmModel = configData?.llm_config?.model || 'grok'
  const thinkingMode = configData?.llm_config?.thinking_mode || false
  const currentConfigType = configType || configData?.config_type || 'scheduled_trading'

  // Check premium access once to avoid repeated permission checks
  const hasPremiumAccess = canAccess('premium_llms')

  // State for LLM models
  const [llmModels, setLLMModels] = useState<LLMModel[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)

  // State for collapsible sections
  const [showSystemSections, setShowSystemSections] = useState(false)
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

  // Ref for textarea auto-resize
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Fetch available LLM models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setModelsLoading(true)
        const models = await apiClient.getLLMModels()
        setLLMModels(models.filter(m => m.enabled))
      } catch (error) {
        console.error('Failed to fetch LLM models:', error)
        // Fallback to empty array on error
        setLLMModels([])
      } finally {
        setModelsLoading(false)
      }
    }

    fetchModels()
  }, [])

  // Auto-resize textarea when content changes or component mounts
  useEffect(() => {
    const resizeTextarea = () => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
      }
    }

    // Resize immediately when content changes
    resizeTextarea()
  }, [currentStrategy])

  // Handle frequency selection
  const handleFrequencyChange = (freq: string) => {
    // Check permissions for high-frequency options
    if ((freq === '5m' || freq === '15m') && !hasPremiumAccess) {
      setUpgradeModalOpen(true)
      return
    }

    onUpdate?.({
      decision: {
        ...(configData?.decision || {}),  // Guard: fallback to empty object
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
        ...(configData?.decision || {}),  // Guard: fallback to empty object
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

  // Handle model selection (OpenRouter only)
  const handleModelChange = (modelId: string) => {
    // Check if user has access to premium LLMs
    if (!hasPremiumAccess) {
      setUpgradeModalOpen(true)
      return
    }

    onUpdate?.({
      llm_config: {
        ...(configData?.llm_config || { use_platform_keys: true, use_own_key: false, thinking_mode: false }),
        provider: 'openrouter',
        model: modelId,
        thinking_mode: configData?.llm_config?.thinking_mode || false,
        use_platform_keys: true,
        use_own_key: false
      }
    })
  }

  // Handle thinking mode toggle
  const handleThinkingModeChange = (enabled: boolean) => {
    onUpdate?.({
      llm_config: {
        ...(configData?.llm_config || { use_platform_keys: true, use_own_key: false, provider: 'openrouter', model: 'grok' }),
        thinking_mode: enabled
      }
    })
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Analysis Frequency - Hide for signal_validation configs */}
      {currentConfigType !== 'signal_validation' && (
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
              const hasAccess = !isPremium || hasPremiumAccess
              const isLocked = isPremium && !hasAccess

              return (
                <button
                  key={freq}
                  onClick={() => handleFrequencyChange(freq)}
                  className={`px-4 py-3 text-sm rounded-xl border transition-all relative ${
                    analysisFrequency === freq
                      ? 'bg-[var(--accent)] text-[#edebe7] dark:text-[#1a1816] border-[var(--accent)] hover:bg-[var(--accent-hover)]'
                      : isLocked
                        ? 'bg-[var(--bg-primary)] text-[var(--text-muted)] border-[var(--border)] opacity-60 hover:opacity-80'
                        : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span>Every {freq}</span>
                    {isLocked && <Crown className="h-3 w-3" />}
                  </div>
                </button>
              )
            })}
          </div>

          <div className="mt-4 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="text-sm text-[var(--text-muted)] flex items-center gap-2">
              Current: <span className="text-[var(--text-primary)] font-medium">Every {analysisFrequency}</span>
              {(analysisFrequency === '5m' || analysisFrequency === '15m') && (
                <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                  <Crown className="h-3 w-3" />
                  <span>Pro</span>
                </div>
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
              ref={textareaRef}
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

      {/* LLM Model Selection */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          AI Decision Engine
        </h3>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Choose which AI model analyzes your strategy and makes trading decisions
        </p>

        <div className="space-y-4">
          {modelsLoading ? (
            <div className="p-4 text-center text-[var(--text-muted)]">Loading models...</div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {/* All OpenRouter Models */}
              {!hasPremiumAccess ? (
                <button
                  onClick={() => setUpgradeModalOpen(true)}
                  className="p-4 rounded-xl border text-left transition-all bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-muted)] opacity-60 hover:opacity-80"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium flex items-center gap-2">
                      7 AI Models
                      <Crown className="h-3 w-3" />
                    </div>
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">
                    Grok, Claude, Gemini, DeepSeek, GPT, Kimi, Qwen
                  </div>
                </button>
              ) : (
                llmModels.map((model) => {
                  const logoPath = MODEL_LOGOS[model.model_id]
                  return (
                    <button
                      key={model.model_id}
                      onClick={() => handleModelChange(model.model_id)}
                      className={`p-4 rounded-xl border text-left transition-all ${
                        llmModel === model.model_id
                          ? 'bg-[var(--agent-decision)]/20 border-[var(--agent-decision)] text-[var(--text-primary)]'
                          : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium flex items-center gap-2">
                          {logoPath && (
                            <div
                              className="flex items-center justify-center rounded-full"
                              style={{
                                backgroundColor: MODEL_COLORS[model.model_id] || '#333',
                                width: '28px',
                                height: '28px',
                                padding: '4px'
                              }}
                            >
                              <Image
                                src={logoPath}
                                alt={`${model.display_name} logo`}
                                width={20}
                                height={20}
                                className="object-contain"
                              />
                            </div>
                          )}
                          {model.display_name}
                          <Crown className="h-3 w-3 text-amber-500" />
                        </div>
                        <span className="text-xs text-[var(--text-muted)]">
                          {model.context_display || 'N/A'}
                        </span>
                      </div>
                      <div className="text-xs text-[var(--text-muted)]">
                        {(() => {
                          const cost = thinkingMode ? model.cost_per_decision?.thinking : model.cost_per_decision?.standard
                          return cost != null ? `$${cost.toFixed(3)}/decision` : 'Pricing unavailable'
                        })()}
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          )}

          {/* Thinking Mode Toggle - Below model selection */}
          {hasPremiumAccess && (
            <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="text-sm font-medium text-[var(--text-primary)] mb-1">
                    Extended Reasoning Mode
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">
                    Enables deeper analysis with longer thinking time (higher cost, better quality)
                  </div>
                </div>
                <button
                  onClick={() => handleThinkingModeChange(!thinkingMode)}
                  className={`ml-4 relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    thinkingMode ? 'bg-[var(--accent)]' : 'bg-[var(--border)]'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      thinkingMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          )}

          {/* Current Selection Display */}
          <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="text-sm text-[var(--text-muted)]">
              Current: <span className="text-[var(--text-primary)] font-medium">
                {llmModels.find(m => m.model_id === llmModel)?.display_name || llmModel}
                {thinkingMode && <span className="text-[var(--text-muted)]"> (Thinking Mode)</span>}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </div>
  )
}