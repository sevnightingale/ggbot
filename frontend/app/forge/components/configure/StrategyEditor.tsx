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
  // configId, configName, configType - unused, batched save handled by parent
  configData?: ConfigData
  onUpdate?: (updates: Partial<ConfigData>) => void
  className?: string
}

/**
 * StrategyEditor - Controlled component for strategy configuration
 *
 * This component is now fully controlled - all changes are passed to parent
 * via onUpdate(), and parent handles batched saving.
 *
 * Local state is only used for:
 * 1. UI responsiveness (optimistic updates)
 * 2. Syncing from configData prop when external updates arrive
 */
export function StrategyEditor({
  configData,
  onUpdate,
  className = ''
}: StrategyEditorProps) {
  const { canAccess } = usePermissions()
  const currentConfigType = configData?.config_type || 'scheduled_trading'

  // Check premium access once to avoid repeated permission checks
  const hasPremiumAccess = canAccess('premium_llms')

  // Local state for form fields - syncs with configData prop
  const [currentStrategy, setCurrentStrategy] = useState(configData?.decision?.user_prompt || '')
  const [analysisFrequency, setAnalysisFrequency] = useState(configData?.decision?.analysis_frequency || '1h')
  const [llmModel, setLlmModel] = useState(configData?.llm_config?.model || 'grok')
  // Reasoning tier: 'economy' | 'standard' | 'premium'
  // Backward compatible with thinking_mode: false -> 'standard', true -> 'premium'
  const [reasoningTier, setReasoningTier] = useState<'economy' | 'standard' | 'premium'>(() => {
    const tier = configData?.llm_config?.reasoning_tier
    if (tier) return tier as 'economy' | 'standard' | 'premium'
    // Legacy fallback
    return configData?.llm_config?.thinking_mode ? 'premium' : 'standard'
  })

  // State for LLM models
  const [llmModels, setLLMModels] = useState<LLMModel[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)

  // State for upgrade modal
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

  // Ref for textarea auto-resize
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Sync local state when configData changes (from SSE/AI updates)
  useEffect(() => {
    if (configData?.decision?.user_prompt !== undefined) {
      setCurrentStrategy(configData.decision.user_prompt)
    }
  }, [configData?.decision?.user_prompt])

  useEffect(() => {
    if (configData?.decision?.analysis_frequency !== undefined && configData.decision.analysis_frequency !== null) {
      setAnalysisFrequency(configData.decision.analysis_frequency)
    }
  }, [configData?.decision?.analysis_frequency])

  useEffect(() => {
    if (configData?.llm_config?.model !== undefined) {
      setLlmModel(configData.llm_config.model)
    }
  }, [configData?.llm_config?.model])

  useEffect(() => {
    // Sync reasoning_tier from config, with backward compatibility for thinking_mode
    const tier = configData?.llm_config?.reasoning_tier
    if (tier) {
      setReasoningTier(tier as 'economy' | 'standard' | 'premium')
    } else if (configData?.llm_config?.thinking_mode !== undefined) {
      // Legacy fallback
      setReasoningTier(configData.llm_config.thinking_mode ? 'premium' : 'standard')
    }
  }, [configData?.llm_config?.reasoning_tier, configData?.llm_config?.thinking_mode])

  // Fetch available LLM models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setModelsLoading(true)
        const models = await apiClient.getLLMModels()
        setLLMModels(models.filter(m => m.enabled))
      } catch (error) {
        console.error('Failed to fetch LLM models:', error)
        setLLMModels([])
      } finally {
        setModelsLoading(false)
      }
    }
    fetchModels()
  }, [])

  // Auto-resize textarea when content changes
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [currentStrategy])

  // Handle strategy text change - update local state + notify parent
  const handleStrategyChange = (value: string) => {
    // Limit to 10,000 characters
    const truncated = value.length > 10000 ? value.substring(0, 10000) : value
    setCurrentStrategy(truncated)

    // Notify parent (batched save happens at page.tsx level)
    onUpdate?.({
      decision: {
        ...(configData?.decision || {}),
        user_prompt: truncated,
        analysis_frequency: analysisFrequency || '1h',
        system_prompt: configData?.decision?.system_prompt || ''
      }
    })
  }

  // Handle frequency selection
  const handleFrequencyChange = (freq: string) => {
    // Check permissions for high-frequency options
    if ((freq === '5m' || freq === '15m') && !hasPremiumAccess) {
      setUpgradeModalOpen(true)
      return
    }

    setAnalysisFrequency(freq)
    onUpdate?.({
      decision: {
        ...(configData?.decision || {}),
        analysis_frequency: freq,
        user_prompt: currentStrategy,
        system_prompt: configData?.decision?.system_prompt || ''
      }
    })
  }

  // Handle model selection
  const handleModelChange = (modelId: string) => {
    if (!hasPremiumAccess) {
      setUpgradeModalOpen(true)
      return
    }

    setLlmModel(modelId)
    onUpdate?.({
      llm_config: {
        ...(configData?.llm_config || { use_platform_keys: true, use_own_key: false, provider: 'openrouter', thinking_mode: false }),
        model: modelId
      }
    })
  }

  // Handle reasoning tier change
  const handleReasoningTierChange = (tier: 'economy' | 'standard' | 'premium') => {
    setReasoningTier(tier)
    onUpdate?.({
      llm_config: {
        ...(configData?.llm_config || { use_platform_keys: true, use_own_key: false, provider: 'openrouter', model: llmModel }),
        reasoning_tier: tier,
        // Keep thinking_mode for backward compatibility
        thinking_mode: tier === 'premium'
      }
    })
  }

  // Auto-resize textarea on input
  const handleTextareaResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
    handleStrategyChange(textarea.value)
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Trading Strategy - Main Section */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
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
              className="w-full p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] resize-none overflow-hidden"
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
        </div>
      </div>

      {/* LLM Model Selection */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
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
                          // Map reasoning tier to pricing (premium uses thinking pricing)
                          const cost = reasoningTier === 'premium'
                            ? model.cost_per_decision?.thinking
                            : model.cost_per_decision?.standard
                          return cost != null ? `$${cost.toFixed(3)}/decision` : 'Pricing unavailable'
                        })()}
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          )}

          {/* Reasoning Tier Selector - Below model selection */}
          {hasPremiumAccess && (
            <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div className="text-sm font-medium text-[var(--text-primary)] mb-3">
                Reasoning Level
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { tier: 'economy' as const, label: 'Economy', desc: 'Fast & cheap' },
                  { tier: 'standard' as const, label: 'Standard', desc: 'Balanced' },
                  { tier: 'premium' as const, label: 'Premium', desc: 'Best quality' }
                ].map(({ tier, label, desc }) => (
                  <button
                    key={tier}
                    onClick={() => handleReasoningTierChange(tier)}
                    className={`p-3 rounded-lg border text-center transition-all ${
                      reasoningTier === tier
                        ? 'bg-[var(--accent)] text-[#edebe7] dark:text-[#1a1816] border-[var(--accent)]'
                        : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-tertiary)]'
                    }`}
                  >
                    <div className="text-sm font-medium">{label}</div>
                    <div className={`text-xs ${reasoningTier === tier ? 'opacity-80' : 'text-[var(--text-muted)]'}`}>
                      {desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Current Selection Display */}
          <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="text-sm text-[var(--text-muted)]">
              Current: <span className="text-[var(--text-primary)] font-medium">
                {llmModels.find(m => m.model_id === llmModel)?.display_name || llmModel}
                <span className="text-[var(--text-muted)]"> ({reasoningTier})</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Frequency - Hide for signal_validation configs */}
      {currentConfigType !== 'signal_validation' && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
            Analysis Frequency
          </h3>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            How often your bot analyzes the market and makes decisions
          </p>

          <div className="grid grid-cols-3 lg:grid-cols-7 gap-2">
            {['5m', '15m', '30m', '1h', '4h', '1d', '1w'].map((freq) => {
              const isPremium = freq === '5m' || freq === '15m'
              const hasAccess = !isPremium || hasPremiumAccess
              const isLocked = isPremium && !hasAccess

              return (
                <button
                  key={freq}
                  onClick={() => handleFrequencyChange(freq)}
                  className={`px-3 py-2 text-sm rounded-lg border transition-all relative ${
                    analysisFrequency === freq
                      ? 'bg-[var(--accent)] text-[#edebe7] dark:text-[#1a1816] border-[var(--accent)] hover:bg-[var(--accent-hover)]'
                      : isLocked
                        ? 'bg-[var(--bg-primary)] text-[var(--text-muted)] border-[var(--border)] opacity-60 hover:opacity-80'
                        : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1">
                    <span>{freq}</span>
                    {isLocked && <Crown className="h-3 w-3" />}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </div>
  )
}
