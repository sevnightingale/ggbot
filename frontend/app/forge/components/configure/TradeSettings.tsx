'use client'

import React, { useEffect, useState } from 'react'
import { Lock } from 'lucide-react'
import { ConfigData, createDefaultConfigData } from '@/lib/api'
import { SymbolSelector } from '@/components/SymbolSelector'
import { usePermissions } from '@/lib/permissions'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { useFieldValidation, ValidationRules } from '@/lib/useTradeValidation'
import { ValidationMessage } from '@/components/ValidationMessage'

interface TradeSettingsProps {
  configData?: ConfigData
  configId?: string  // Needed for test signal publishing feature
  tradingMode?: 'paper' | 'symphony' | 'aster'
  onUpdate?: (updates: Partial<ConfigData>) => void
  onValidationChange?: (hasErrors: boolean) => void
  className?: string
}

/**
 * TradeSettings - Controlled component for trading configuration
 *
 * This component is fully controlled - all changes are passed to parent
 * via onUpdate(), and parent handles batched saving.
 */
export function TradeSettings({
  configData,
  configId,
  onUpdate,
  onValidationChange,
  className = ''
}: TradeSettingsProps) {
  const { canAccess } = usePermissions()
  const [session, setSession] = useState<{ access_token?: string } | null>(null)

  useEffect(() => {
    const supabase = createClientComponentClient()
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setSession(session)
    }
    getSession()
  }, [])

  const defaultConfig = createDefaultConfigData()
  const trading = configData?.trading || defaultConfig.trading
  const positionSizing = trading.position_sizing || defaultConfig.trading.position_sizing
  const riskManagement = trading.risk_management || defaultConfig.trading.risk_management
  const telegramConfig = configData?.telegram_integration || defaultConfig.telegram_integration
  const publisher = telegramConfig.publisher || defaultConfig.telegram_integration.publisher

  // Validation hooks
  const leverageValidation = useFieldValidation(trading.leverage, ValidationRules.leverage)
  const stopLossValidation = useFieldValidation(riskManagement.default_stop_loss_percent, ValidationRules.stopLoss)
  const takeProfitValidation = useFieldValidation(riskManagement.default_take_profit_percent, ValidationRules.takeProfit)
  const maxMarginPercentValidation = useFieldValidation(positionSizing.max_margin_percent, ValidationRules.maxMarginPercent)

  // Notify parent of validation state
  useEffect(() => {
    const hasErrors = !leverageValidation.isValid ||
                     !stopLossValidation.isValid ||
                     !takeProfitValidation.isValid ||
                     !maxMarginPercentValidation.isValid

    if (onValidationChange) {
      onValidationChange(hasErrors)
    }
  }, [
    leverageValidation.isValid,
    stopLossValidation.isValid,
    takeProfitValidation.isValid,
    maxMarginPercentValidation.isValid,
    onValidationChange
  ])

  // Update config - just notify parent (batched save happens at page.tsx level)
  const updateConfig = (updates: Partial<ConfigData>) => {
    onUpdate?.(updates)
  }

  // Helper to update trading config with proper type handling
  const updateTradingConfig = (tradingUpdates: Partial<ConfigData['trading']>) => {
    updateConfig({
      trading: {
        ...defaultConfig.trading,
        ...trading,
        ...tradingUpdates
      }
    })
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Trading Pair Selection */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Trading Pair
        </h3>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Choose the cryptocurrency pair you want to trade
        </p>

        <div>
          <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
            Symbol
          </label>
          <SymbolSelector
            value={configData?.selected_pair || 'BTC/USDT'}
            onChange={(symbol) => updateConfig({ selected_pair: symbol })}
          />
          <div className="text-xs text-[var(--text-muted)] mt-1">
            Choose from 141 supported trading pairs
          </div>
        </div>
      </div>

      {/* Position Sizing */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Position Sizing
        </h3>

        <div>
          <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
            Max Margin % (when AI is 100% confident)
          </label>
          <input
            type="number"
            value={(positionSizing.max_margin_percent as number) || 20}
            onChange={(e) => updateTradingConfig({
                position_sizing: { ...positionSizing, max_margin_percent: Number(e.target.value) }
            })}
            min="1"
            max="100"
            step="0.5"
            className={`w-full p-3 rounded-xl bg-[var(--bg-primary)] border text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:border-transparent ${
              maxMarginPercentValidation.error
                ? 'border-red-500 focus:ring-red-500'
                : maxMarginPercentValidation.warning
                ? 'border-yellow-500 focus:ring-yellow-500'
                : 'border-[var(--border)] focus:ring-[var(--agent-trading)]'
            }`}
            placeholder="20"
          />
          <ValidationMessage error={maxMarginPercentValidation.error} warning={maxMarginPercentValidation.warning} />
          {!maxMarginPercentValidation.error && !maxMarginPercentValidation.warning && (
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Margin = collateral you risk. Position = margin × leverage. AI confidence scales this percentage.
            </div>
          )}
        </div>
      </div>

      {/* Leverage */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Leverage
        </h3>

        <div>
          <input
            type="number"
            value={(trading.leverage as number) || 5}
            onChange={(e) => updateTradingConfig({
                leverage: Number(e.target.value)
            })}
            min="1"
            max="100"
            className={`w-full p-3 rounded-xl bg-[var(--bg-primary)] border text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:border-transparent ${
              leverageValidation.error
                ? 'border-red-500 focus:ring-red-500'
                : leverageValidation.warning
                ? 'border-yellow-500 focus:ring-yellow-500'
                : 'border-[var(--border)] focus:ring-[var(--agent-trading)]'
            }`}
            placeholder="5"
          />
          <ValidationMessage error={leverageValidation.error} warning={leverageValidation.warning} />
          {!leverageValidation.error && !leverageValidation.warning && (
            <div className="text-xs text-[var(--text-muted)] mt-1">
              5x leverage = 5x gains AND 5x losses
            </div>
          )}
        </div>
      </div>

      {/* Risk Management */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Risk Management
        </h3>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Set price movement thresholds to automatically close positions. With leverage, P&L impact is multiplied.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              Stop Loss (price drop %)
            </label>
            <input
              type="number"
              value={(riskManagement.default_stop_loss_percent as number) || 1.5}
              onChange={(e) => updateTradingConfig({
                  risk_management: { ...riskManagement, default_stop_loss_percent: Number(e.target.value) }
              })}
              min="0.5"
              max="50"
              step="0.1"
              className={`w-full p-3 rounded-xl bg-[var(--bg-primary)] border text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:border-transparent ${
                stopLossValidation.error
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-[var(--border)] focus:ring-rose-500'
              }`}
              placeholder="1.5"
            />
            <ValidationMessage error={stopLossValidation.error} />
            {!stopLossValidation.error && (
              <div className="text-xs text-[var(--text-muted)] mt-1">
                Close when price moves {(riskManagement.default_stop_loss_percent as number) || 1.5}% against you
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              Take Profit (price gain %)
            </label>
            <input
              type="number"
              value={(riskManagement.default_take_profit_percent as number) || 3}
              onChange={(e) => updateTradingConfig({
                  risk_management: { ...riskManagement, default_take_profit_percent: Number(e.target.value) }
              })}
              min="0.5"
              max="500"
              step="0.1"
              className={`w-full p-3 rounded-xl bg-[var(--bg-primary)] border text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:border-transparent ${
                takeProfitValidation.error
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-[var(--border)] focus:ring-emerald-500'
              }`}
              placeholder="3"
            />
            <ValidationMessage error={takeProfitValidation.error} />
            {!takeProfitValidation.error && (
              <div className="text-xs text-[var(--text-muted)] mt-1">
                Close when price moves {(riskManagement.default_take_profit_percent as number) || 3}% in your favor
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Telegram Integration */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Telegram Publishing
          </h3>
          {!canAccess('telegram_publishing') && (
            <span className="text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-500 border border-amber-500/30">
              Premium Feature
            </span>
          )}
        </div>

        {/* Premium Gate */}
        {!canAccess('telegram_publishing') ? (
          <div className="p-4 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border)]">
            <div className="flex items-center gap-3 mb-3">
              <Lock className="h-5 w-5 text-[var(--text-muted)]" />
              <div className="font-medium text-[var(--text-primary)]">
                Premium Feature Locked
              </div>
            </div>
            <div className="text-sm text-[var(--text-muted)] mb-4">
              Telegram signal publishing is available with a paid subscription. Upgrade to automatically publish your bot&apos;s trading decisions to your Telegram channel.
            </div>
            <button
              onClick={() => window.open('/pricing', '_blank')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--agent-decision)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
            >
              Upgrade to activate →
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Enable Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div>
                <div className="font-medium text-[var(--text-primary)]">Publish Signals</div>
                <div className="text-sm text-[var(--text-muted)]">Send trading decisions to Telegram channel</div>
              </div>
              <button
                onClick={() => updateConfig({
                  telegram_integration: {
                    ...telegramConfig,
                    publisher: { ...publisher, enabled: !publisher.enabled }
                  }
                })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  publisher.enabled
                    ? 'bg-emerald-500'
                    : 'bg-[var(--border)]'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    publisher.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

          {/* Channel Settings (when enabled) */}
          {publisher.enabled && (
            <div className="space-y-4">
              {/* Setup Instructions */}
              <div className="p-4 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                <h4 className="font-medium text-[var(--text-primary)] mb-3">Setup Instructions</h4>
                <ol className="text-sm text-[var(--text-muted)] space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 bg-[var(--agent-decision)] text-white text-xs rounded-full flex items-center justify-center font-medium">1</span>
                    <span>Add <code className="px-1 py-0.5 bg-[var(--bg-tertiary)] rounded text-[var(--text-primary)]">@ggFilter_Bot</code> bot to your Telegram channel</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 bg-[var(--agent-decision)] text-white text-xs rounded-full flex items-center justify-center font-medium">2</span>
                    <span>Make the bot an admin with &quot;Post Messages&quot; permission</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 bg-[var(--agent-decision)] text-white text-xs rounded-full flex items-center justify-center font-medium">3</span>
                    <span>Send <code className="px-1 py-0.5 bg-[var(--bg-tertiary)] rounded text-[var(--text-primary)]">/chatid</code> in the channel to get your Channel ID</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 bg-[var(--agent-decision)] text-white text-xs rounded-full flex items-center justify-center font-medium">4</span>
                    <span>Copy the Channel ID below</span>
                  </li>
                </ol>
              </div>

              {/* Channel ID Input */}
              <div>
                <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                  Channel ID
                </label>
                <input
                  type="text"
                  value={(publisher.filter_channel as string) || ''}
                  onChange={(e) => updateConfig({
                    telegram_integration: {
                      ...telegramConfig,
                      publisher: { ...publisher, filter_channel: e.target.value }
                    }
                  })}
                  placeholder="-1001234567890 or @YourChannel"
                  className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-transparent"
                />
                <div className="text-xs text-[var(--text-muted)] mt-1">
                  Get this by sending /chatid in your channel after adding our bot
                </div>
              </div>

              {/* Test Message Button */}
              {publisher.filter_channel && (
                <div>
                  <button
                    onClick={async () => {
                      try {
                        const response = await fetch(`/api/v2/test/signal-publishing/${configId}`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${session?.access_token}`
                          }
                        })

                        if (response.ok) {
                          alert('✅ Test message sent successfully!')
                        } else {
                          const error = await response.text()
                          alert(`❌ Failed to send test message: ${error}`)
                        }
                      } catch (error) {
                        alert(`❌ Error sending test message: ${error}`)
                      }
                    }}
                    className="w-full p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
                  >
                    Send Test Message
                  </button>
                  <div className="text-xs text-[var(--text-muted)] mt-1">
                    Verify that our bot can send messages to your channel
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                  Confidence Threshold (%)
                </label>
                <input
                  type="number"
                  value={((publisher.confidence_threshold as number) || 0.7) * 100}
                  onChange={(e) => updateConfig({
                    telegram_integration: {
                      ...telegramConfig,
                      publisher: { ...publisher, confidence_threshold: Number(e.target.value) / 100 }
                    }
                  })}
                  min="0"
                  max="100"
                  step="1"
                  className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-transparent"
                  placeholder="70"
                />
                <div className="text-xs text-[var(--text-muted)] mt-1">Only publish signals above this confidence level</div>
              </div>

            </div>
          )}
          </div>
        )}
      </div>
    </div>
  )
}