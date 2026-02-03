'use client'

import { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'
import { Bot, Rocket, Loader2, AlertCircle, Zap, ChevronRight, ChevronLeft, Sparkles, X } from 'lucide-react'
import { Modal, ModalBody, ModalFooter } from '@/components/ui/modal'
import { SymbolSelector } from '@/components/SymbolSelector'
import { apiClient } from '@/lib/api'
import { getArchetypeConfig, getArchetypeSummaries } from '@/lib/archetypes'

type BotType = 'scheduled_trading' | 'signal_validation' | 'agent'
type TradingMode = 'paper' | 'symphony' | 'aster'

// LLM Model types
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

// Get archetype summaries from archetypes.ts
const ARCHETYPES = getArchetypeSummaries()

// Available timeframes
const TIMEFRAMES = [
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '1d', label: '1 day' },
]

interface BotCreationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (botType: BotType, tradingMode: TradingMode, symphonyAgentId?: string, botName?: string, configData?: Record<string, unknown>) => void
  existingBotCount: number
  forceOpen?: boolean // When true, modal cannot be closed (for new users with 0 bots)
}

export function BotCreationModal({
  open,
  onOpenChange,
  onConfirm,
  existingBotCount,
  forceOpen = false
}: BotCreationModalProps) {
  // Step tracking
  const [currentStep, setCurrentStep] = useState(1)
  const totalSteps = 5

  // Form state
  const [botName, setBotName] = useState('')
  const [tradingMode, setTradingMode] = useState<TradingMode>('paper')
  const [symphonyAgentId, setSymphonyAgentId] = useState('')
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('1h')
  const [description, setDescription] = useState('')
  const [selectedArchetype, setSelectedArchetype] = useState<string | null>(null)
  const [llmModel, setLlmModel] = useState('grok')
  const [reasoningTier, setReasoningTier] = useState<'economy' | 'standard' | 'premium'>('standard')

  // Loading states
  const [isGenerating, setIsGenerating] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [llmModels, setLLMModels] = useState<LLMModel[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)

  // Connection states
  const [symphonyConnected, setSymphonyConnected] = useState(false)
  const [asterConnected, setAsterConnected] = useState(false)
  const [checkingConnections, setCheckingConnections] = useState(true)

  // Error state
  const [error, setError] = useState<string | null>(null)

  // Generate default bot name
  const generateDefaultName = useCallback(() => {
    const botCount = existingBotCount + 1
    return `ggbot ${botCount}`
  }, [existingBotCount])

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setCurrentStep(1)
      setBotName(generateDefaultName())
      setTradingMode('paper')
      setSymphonyAgentId('')
      setSymbol('BTC/USDT')
      setTimeframe('1h')
      setDescription('')
      setSelectedArchetype(null)
      setLlmModel('grok')
      setReasoningTier('standard')
      setError(null)
      checkConnectionStatus()
      fetchLLMModels()
    }
  }, [open, generateDefaultName])

  const checkConnectionStatus = async () => {
    try {
      setCheckingConnections(true)
      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setCheckingConnections(false)
        return
      }

      const [symphonyRes, asterRes] = await Promise.all([
        fetch('/api/v2/symphony/status', {
          headers: { 'Authorization': `Bearer ${session.access_token}` }
        }),
        fetch('/api/v2/aster/status', {
          headers: { 'Authorization': `Bearer ${session.access_token}` }
        })
      ])

      if (symphonyRes.ok) {
        const data = await symphonyRes.json()
        setSymphonyConnected(data.connected || false)
      }

      if (asterRes.ok) {
        const data = await asterRes.json()
        setAsterConnected(data.connected || false)
      }
    } catch (e) {
      console.error('Failed to check connection status:', e)
    } finally {
      setCheckingConnections(false)
    }
  }

  const fetchLLMModels = async () => {
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

  // Trading mode options
  const tradingModes = [
    {
      mode: 'paper' as const,
      Icon: Zap,
      label: 'Paper Trading',
      description: 'Practice with $10k virtual money',
      color: 'var(--agent-extraction)',
      available: true,
      requiresConnection: false
    },
    {
      mode: 'symphony' as const,
      Icon: Rocket,
      label: 'Symphony Live',
      description: 'Real trades via Symphony.io',
      color: 'var(--signal)',
      available: true,
      requiresConnection: true,
      connected: symphonyConnected
    },
    {
      mode: 'aster' as const,
      Icon: Bot,
      label: 'AsterDEX',
      description: 'Real trades on AsterDEX',
      color: 'var(--ember)',
      available: true,
      requiresConnection: true,
      connected: asterConnected
    }
  ]

  // Step validation
  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return botName.trim().length > 0
      case 2:
        if (tradingMode === 'symphony') {
          return symphonyAgentId.trim().length > 0
        }
        return true
      case 3:
        return symbol && timeframe
      case 4:
        return description.trim().length > 0 || selectedArchetype !== null
      case 5:
        return llmModel
      default:
        return false
    }
  }

  // Navigation
  const handleNext = () => {
    if (currentStep < totalSteps && canProceed()) {
      // If archetype selected on step 4, skip to final step
      if (currentStep === 4 && selectedArchetype) {
        setCurrentStep(5)
      } else {
        setCurrentStep(prev => prev + 1)
      }
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1)
    }
  }

  // Archetype selection
  const handleArchetypeClick = (archetypeId: string) => {
    setSelectedArchetype(archetypeId)
    setDescription('') // Clear custom description
    setCurrentStep(5) // Jump to final step
  }

  // Handle modal close
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && forceOpen) {
      // Don't allow closing if forceOpen is true
      return
    }
    onOpenChange(newOpen)
  }

  // Create bot
  const handleCreate = async () => {
    setIsCreating(true)
    setError(null)

    try {
      let userPrompt: string
      let extractionConfig: Record<string, unknown>
      let finalTimeframe = timeframe

      if (selectedArchetype) {
        // Use full archetype config from archetypes.ts
        const archetypeConfig = getArchetypeConfig(selectedArchetype)
        if (!archetypeConfig) {
          throw new Error(`Unknown archetype: ${selectedArchetype}`)
        }
        userPrompt = archetypeConfig.userPrompt
        extractionConfig = archetypeConfig.extraction
        finalTimeframe = archetypeConfig.defaultTimeframe
      } else {
        // Generate complete config from description (strategy + extraction)
        setIsGenerating(true)
        try {
          const result = await apiClient.createBotConfig(description, symbol, timeframe)
          if (!result.success || !result.user_prompt) {
            throw new Error(result.error || 'Failed to create bot config')
          }
          userPrompt = result.user_prompt
          extractionConfig = result.extraction  // Use AI-generated extraction config
        } finally {
          setIsGenerating(false)
        }
      }

      // Build full config
      const configData = {
        schema_version: '2.1',
        config_type: 'scheduled_trading' as BotType,
        trading_mode: tradingMode,
        symphony_agent_id: tradingMode === 'symphony' ? symphonyAgentId : undefined,
        selected_pair: symbol,
        extraction: extractionConfig,
        decision: {
          analysis_frequency: finalTimeframe,
          user_prompt: userPrompt,
          system_prompt: 'You are an expert cryptocurrency trader. Analyze the provided market data and make trading decisions based on the strategy defined below. Always include your reasoning and confidence level.'
        },
        llm_config: {
          provider: 'openrouter',
          model: llmModel,
          reasoning_tier: reasoningTier,
          thinking_mode: reasoningTier === 'premium',
          use_platform_keys: true,
          use_own_key: false
        },
        trading: {
          leverage: 5,
          position_sizing: {
            max_margin_percent: 20.0
          },
          risk_management: {
            default_stop_loss_percent: 1.5,
            default_take_profit_percent: 3.0
          }
        },
        telegram_integration: {
          listener: { enabled: false },
          publisher: { enabled: false }
        }
      }

      // Call parent onConfirm with full config
      onConfirm(
        'scheduled_trading',
        tradingMode,
        tradingMode === 'symphony' ? symphonyAgentId.trim() : undefined,
        botName.trim(),
        configData
      )

      // Close modal
      if (!forceOpen) {
        onOpenChange(false)
      }

    } catch (err) {
      console.error('Failed to create bot:', err)
      setError(err instanceof Error ? err.message : 'Failed to create bot')
    } finally {
      setIsCreating(false)
    }
  }

  // Progress indicator
  const ProgressBar = () => (
    <div className="flex items-center gap-2 mb-6">
      {Array.from({ length: totalSteps }, (_, i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-colors ${
            i + 1 <= currentStep ? 'bg-[var(--accent)]' : 'bg-[var(--border)]'
          }`}
        />
      ))}
      <span className="text-xs text-[var(--text-muted)] ml-2">
        {currentStep}/{totalSteps}
      </span>
    </div>
  )

  // Step content
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
                What should we call your ggbot?
              </h2>
              <p className="text-[var(--text-muted)]">
                Give your trading bot a memorable name
              </p>
            </div>

            <input
              type="text"
              value={botName}
              onChange={(e) => setBotName(e.target.value)}
              placeholder="e.g., BTC Scalper, Night Owl, Moon Hunter"
              className="w-full px-4 py-4 text-lg border border-[var(--border)] rounded-xl bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] text-center"
              autoFocus
            />
          </div>
        )

      case 2:
        return (
          <div className="space-y-4">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
                How will your bot trade?
              </h2>
              <p className="text-[var(--text-muted)]">
                Choose between practice mode or real trading
              </p>
            </div>

            {checkingConnections ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-5 w-5 animate-spin text-[var(--text-secondary)]" />
              </div>
            ) : (
              <div className="space-y-3">
                {tradingModes.map(({ mode, Icon, label, description, color, available, requiresConnection, connected }) => {
                  const isDisabled = !available || (requiresConnection && !connected)
                  const showWarning = requiresConnection && !connected

                  return (
                    <button
                      key={mode}
                      onClick={() => setTradingMode(mode)}
                      disabled={isDisabled}
                      className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                        tradingMode === mode
                          ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                          : 'border-[var(--border)] hover:border-[var(--border-hover)]'
                      } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
                          style={{ backgroundColor: !isDisabled ? `${color}20` : 'var(--bg-tertiary)' }}
                        >
                          <Icon className="h-6 w-6" style={{ color: !isDisabled ? color : 'var(--text-muted)' }} />
                        </div>

                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-[var(--text-primary)]">{label}</span>
                            {showWarning && (
                              <span className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                                <AlertCircle className="h-3 w-3" />
                                Not connected
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-[var(--text-secondary)]">{description}</p>
                        </div>

                        <div className={`flex-shrink-0 w-5 h-5 rounded-full border-2 ${
                          tradingMode === mode
                            ? 'border-[var(--accent)] bg-[var(--accent)]'
                            : 'border-[var(--border)]'
                        }`}>
                          {tradingMode === mode && (
                            <div className="w-full h-full flex items-center justify-center">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {/* Symphony Agent ID Input */}
            {tradingMode === 'symphony' && (
              <div className="mt-4 p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)]">
                <label className="block text-sm font-medium mb-2 text-[var(--text-primary)]">
                  Symphony Agent ID *
                </label>
                <input
                  type="text"
                  value={symphonyAgentId}
                  onChange={(e) => setSymphonyAgentId(e.target.value)}
                  placeholder="00000000-0000-0000-0000-000000000000"
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] font-mono text-sm"
                />
                <p className="text-xs text-[var(--text-muted)] mt-2">
                  Find your Agent ID in the{' '}
                  <a href="https://agent-portal.symphony.io" target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline">
                    Symphony portal
                  </a>
                </p>
              </div>
            )}
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
                What will your bot trade?
              </h2>
              <p className="text-[var(--text-muted)]">
                Choose your trading pair and analysis frequency
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-[var(--text-primary)]">
                  Trading Pair
                </label>
                <SymbolSelector
                  value={symbol}
                  onChange={setSymbol}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-[var(--text-primary)]">
                  Analysis Frequency
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {TIMEFRAMES.map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => setTimeframe(value)}
                      className={`px-4 py-3 rounded-xl border-2 text-sm font-medium transition-all ${
                        timeframe === value
                          ? 'border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]'
                          : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-hover)]'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-2">
                  How often your bot will analyze the market and make decisions
                </p>
              </div>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
                Describe your trading strategy
              </h2>
              <p className="text-[var(--text-muted)]">
                Tell us how you want your bot to trade - we&apos;ll turn it into a real strategy
              </p>
            </div>

            <div>
              <textarea
                value={description}
                onChange={(e) => {
                  setDescription(e.target.value)
                  setSelectedArchetype(null) // Clear archetype if typing
                }}
                placeholder="Describe your trading style in plain English. Examples:
• A patient bot that waits for RSI extremes
• Follow the trend using moving averages
• Buy when everyone is fearful, sell when greedy"
                className="w-full px-4 py-4 h-32 border border-[var(--border)] rounded-xl bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] resize-none"
              />
              <div className="flex justify-between mt-2">
                <span className="text-xs text-[var(--text-muted)]">
                  Describe your trading philosophy, personality, or specific rules
                </span>
                <span className="text-xs text-[var(--text-muted)]">
                  {description.length}/1000
                </span>
              </div>
            </div>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[var(--border)]"></div>
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 bg-[var(--bg-secondary)] text-sm text-[var(--text-muted)]">
                  or choose a proven strategy
                </span>
              </div>
            </div>

            <div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {ARCHETYPES.map((archetype) => (
                  <button
                    key={archetype.id}
                    onClick={() => handleArchetypeClick(archetype.id)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      selectedArchetype === archetype.id
                        ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                        : 'border-[var(--border)] hover:border-[var(--border-hover)]'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <Sparkles className="h-5 w-5" style={{ color: archetype.color }} />
                      <span className="font-semibold text-[var(--text-primary)]">{archetype.name}</span>
                    </div>
                    <p className="text-xs text-[var(--text-muted)]">{archetype.shortDescription}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
                Choose your bot&apos;s AI brain
              </h2>
              <p className="text-[var(--text-muted)]">
                Select which AI model will make trading decisions
              </p>
            </div>

            {/* Model Selection */}
            {modelsLoading ? (
              <div className="p-8 text-center">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-[var(--text-muted)]" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {llmModels.map((model) => {
                  const logoPath = MODEL_LOGOS[model.model_id]
                  return (
                    <button
                      key={model.model_id}
                      onClick={() => setLlmModel(model.model_id)}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        llmModel === model.model_id
                          ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                          : 'border-[var(--border)] hover:border-[var(--border-hover)]'
                      }`}
                    >
                      <div className="flex flex-col items-center gap-2">
                        {logoPath && (
                          <div
                            className="flex items-center justify-center rounded-full"
                            style={{
                              backgroundColor: MODEL_COLORS[model.model_id] || '#333',
                              width: '40px',
                              height: '40px',
                              padding: '8px'
                            }}
                          >
                            <Image
                              src={logoPath}
                              alt={`${model.display_name} logo`}
                              width={24}
                              height={24}
                              className="object-contain"
                            />
                          </div>
                        )}
                        <span className="font-medium text-sm capitalize text-[var(--text-primary)]">
                          {model.model_id}
                        </span>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {/* Reasoning Tier */}
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
              <label className="block text-sm font-medium mb-3 text-[var(--text-primary)]">
                Reasoning Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { tier: 'economy' as const, label: 'Economy', desc: 'Fast & cheap' },
                  { tier: 'standard' as const, label: 'Standard', desc: 'Balanced' },
                  { tier: 'premium' as const, label: 'Premium', desc: 'Deep thinking' },
                ].map(({ tier, label, desc }) => (
                  <button
                    key={tier}
                    onClick={() => setReasoningTier(tier)}
                    className={`px-4 py-3 rounded-lg border-2 text-center transition-all ${
                      reasoningTier === tier
                        ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                        : 'border-[var(--border)] hover:border-[var(--border-hover)]'
                    }`}
                  >
                    <div className="font-medium text-sm text-[var(--text-primary)]">{label}</div>
                    <div className="text-xs text-[var(--text-muted)]">{desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Summary */}
            <div className="p-4 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border)]">
              <h4 className="text-sm font-medium text-[var(--text-primary)] mb-2">Summary</h4>
              <div className="text-sm text-[var(--text-muted)] space-y-1">
                <p><span className="text-[var(--text-secondary)]">Name:</span> {botName}</p>
                <p><span className="text-[var(--text-secondary)]">Mode:</span> {tradingMode === 'paper' ? 'Paper Trading' : tradingMode === 'symphony' ? 'Symphony Live' : 'AsterDEX'}</p>
                <p><span className="text-[var(--text-secondary)]">Trading:</span> {symbol} every {TIMEFRAMES.find(t => t.value === timeframe)?.label}</p>
                <p><span className="text-[var(--text-secondary)]">Strategy:</span> {selectedArchetype ? ARCHETYPES.find(a => a.id === selectedArchetype)?.name : 'Custom'}</p>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Modal open={open} onOpenChange={handleOpenChange} size="xl" preventClose={forceOpen}>
      {/* Custom Header with progress bar */}
      <div className="p-4 sm:p-6 pb-0 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-sm font-medium text-[var(--text-muted)]">Create New Bot</h1>
          {forceOpen ? (
            <div
              className="p-1 rounded text-[var(--text-muted)] cursor-not-allowed opacity-50"
              title="Create your first bot to continue"
            >
              <X className="h-4 w-4" />
            </div>
          ) : (
            <button
              onClick={() => onOpenChange(false)}
              className="p-1 rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-muted)]"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <ProgressBar />
      </div>

      {/* Step Content */}
      <ModalBody className="min-h-[400px]">
        {renderStep()}

        {/* Error display */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-500 text-sm">
            {error}
          </div>
        )}
      </ModalBody>

      {/* Navigation */}
      <ModalFooter>
        <div className="flex justify-between items-center w-full">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              currentStep === 1
                ? 'text-[var(--text-muted)] cursor-not-allowed'
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
            }`}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </button>

          {currentStep < totalSteps ? (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
                canProceed()
                  ? 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white'
                  : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-not-allowed'
              }`}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={isCreating || !canProceed()}
              className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
                isCreating || !canProceed()
                  ? 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-not-allowed'
                  : 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white'
              }`}
            >
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isGenerating ? 'Generating Strategy...' : 'Creating...'}
                </>
              ) : (
                <>
                  {existingBotCount === 0 ? 'Create & Test Run' : 'Create'}
                  <Sparkles className="h-4 w-4" />
                </>
              )}
            </button>
          )}
        </div>
      </ModalFooter>
    </Modal>
  )
}
