'use client'

import React, { useState } from 'react'
import { usePermissions } from '@/lib/permissions'
import { ExternalLink, Lock, CheckCircle, AlertCircle } from 'lucide-react'
import { ConfigData } from '@/lib/api'

interface SignalsConfigurationProps {
  configData?: ConfigData
  onUpdate?: (updates: Partial<ConfigData>) => void
  className?: string
}

export function SignalsConfiguration({
  configData,
  onUpdate,
  className = ''
}: SignalsConfigurationProps) {
  const [showGgShotModal, setShowGgShotModal] = useState(false)
  const [currentSignalMode, setCurrentSignalMode] = useState<'validate' | 'monitor'>('validate')
  const [currentConfidenceThreshold, setCurrentConfidenceThreshold] = useState(70)

  // Get current signal configuration from config data
  const signalsConfig = configData?.extraction?.selected_data_sources?.signals_group_chats || { data_points: [] as string[] }
  const isGgShotEnabled = signalsConfig.data_points?.includes('ggshot') || false

  // For now, we'll simulate the subscription status
  // In real implementation, this would come from user profile or API
  const { canAccess } = usePermissions()
  const isGgShotSubscribed = canAccess('ggshot')

  const handleSubscribeClick = () => {
    setShowGgShotModal(true)
  }

  const closeModal = () => {
    setShowGgShotModal(false)
  }

  // Update config data helper
  const updateConfig = (updates: Partial<ConfigData>) => {
    if (onUpdate) {
      onUpdate(updates)
    }
  }

  // Toggle ggShot enabled/disabled
  const toggleGgShot = (enabled: boolean) => {
    // Check permission before enabling
    if (enabled && !isGgShotSubscribed) {
      alert('ggShot signals require a ggbase subscription. Upgrade to access external signal sources!')
      return
    }
    const currentConfig = configData?.extraction?.selected_data_sources || {}
    const currentSignalsConfig = currentConfig.signals_group_chats || {
      data_points: [],
      timeframes: ["15m"] // Default timeframe for signals
    }

    let updatedDataPoints: string[]
    if (enabled) {
      // Add ggshot if not present
      updatedDataPoints = currentSignalsConfig.data_points?.includes('ggshot')
        ? currentSignalsConfig.data_points
        : [...(currentSignalsConfig.data_points || []), 'ggshot']
    } else {
      // Remove ggshot
      updatedDataPoints = (currentSignalsConfig.data_points || []).filter(point => point !== 'ggshot')
    }

    const update: Partial<ConfigData> = {
      extraction: {
        ...(configData?.extraction || {}),  // Guard: fallback to empty object
        selected_data_sources: {
          ...currentConfig,
          signals_group_chats: updatedDataPoints.length > 0 ? {
            data_points: updatedDataPoints,
            timeframes: ["15m"]
          } : undefined
        }
      }
    }

    // Remove undefined categories
    if (updatedDataPoints.length === 0) {
      delete update.extraction!.selected_data_sources!.signals_group_chats
    }

    updateConfig(update)
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* ggShot Signals Section */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <div className="flex items-center gap-3 mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            ggShot Premium Signals
          </h3>
          {isGgShotEnabled ? (
            <span className="px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs border border-emerald-500/30 flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              Enabled
            </span>
          ) : (
            <span className="px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs border border-amber-500/30 flex items-center gap-1">
              <Lock className="h-3 w-3" />
              {isGgShotSubscribed ? 'Disabled' : 'Premium'}
            </span>
          )}
        </div>

        {isGgShotSubscribed ? (
          /* Subscribed State - Show Configuration Options */
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-emerald-400" />
                <span className="font-medium text-emerald-400">ggShot Subscription Active</span>
              </div>
              <div className="text-sm text-[var(--text-muted)]">
                Receiving AI-filtered premium trading signals from 140+ crypto pairs with advanced confidence scoring.
              </div>
            </div>

            {/* Enable/Disable Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div>
                <div className="font-medium text-[var(--text-primary)]">Enable ggShot Signals</div>
                <div className="text-sm text-[var(--text-muted)]">Add ggShot signals to your bot&apos;s data sources</div>
              </div>
              <button
                onClick={() => toggleGgShot(!isGgShotEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  isGgShotEnabled
                    ? 'bg-emerald-500'
                    : 'bg-[var(--border)]'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isGgShotEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Signal Configuration - only show when enabled */}
            {isGgShotEnabled && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                    Minimum Signal Confidence
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="5"
                    value={currentConfidenceThreshold}
                    onChange={(e) => {
                      setCurrentConfidenceThreshold(Number(e.target.value))
                      // TODO: Update config when we add this field
                    }}
                    className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-transparent"
                    placeholder="70"
                  />
                  <div className="text-xs text-[var(--text-muted)] mt-1">
                    Only process signals above this confidence level (recommended: 70%+)
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                    Signal Processing Mode
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    <label className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] cursor-pointer hover:bg-[var(--bg-tertiary)]">
                      <input
                        type="radio"
                        name="signal_mode"
                        value="validate"
                        checked={currentSignalMode === 'validate'}
                        onChange={(e) => {
                          setCurrentSignalMode(e.target.value as 'validate' | 'monitor')
                          // TODO: Update config when we add this field
                        }}
                        className="text-[var(--agent-decision)]"
                      />
                      <div>
                        <div className="font-medium text-[var(--text-primary)]">Validate & Execute</div>
                        <div className="text-xs text-[var(--text-muted)]">AI validates each signal before executing trades</div>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] cursor-pointer hover:bg-[var(--bg-tertiary)]">
                      <input
                        type="radio"
                        name="signal_mode"
                        value="monitor"
                        checked={currentSignalMode === 'monitor'}
                        onChange={(e) => {
                          setCurrentSignalMode(e.target.value as 'validate' | 'monitor')
                          // TODO: Update config when we add this field
                        }}
                        className="text-[var(--agent-decision)]"
                      />
                      <div>
                        <div className="font-medium text-[var(--text-primary)]">Monitor Only</div>
                        <div className="text-xs text-[var(--text-muted)]">Track signals for analysis without executing trades</div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Not Subscribed State - Show Subscription CTA + Config Toggle */
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-4 w-4 text-amber-400" />
                <span className="font-medium text-amber-400">External Premium Service</span>
              </div>
              <div className="text-sm text-[var(--text-muted)]">
                ggShot signals are provided by an external premium service. To access ggShot signals, you need to subscribe directly with them.
              </div>
            </div>

            {/* Enable/Disable Toggle - disabled for non-subscribed users */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
              <div>
                <div className="font-medium text-[var(--text-primary)]">Enable ggShot Signals</div>
                <div className="text-sm text-[var(--text-muted)]">
                  {isGgShotEnabled
                    ? 'ggShot signals are enabled - subscribe to ggShot to use this feature'
                    : 'Subscribe to ggShot to enable premium signals'
                  }
                </div>
              </div>
              <button
                onClick={() => toggleGgShot(!isGgShotEnabled)}
                disabled={!isGgShotSubscribed}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  isGgShotEnabled
                    ? 'bg-amber-500'
                    : 'bg-[var(--border)] opacity-50 cursor-not-allowed'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isGgShotEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="text-sm text-[var(--text-secondary)] space-y-3">
              <p>
                ggShot provides AI-filtered premium trading signals from 140+ crypto pairs with advanced confidence scoring.
              </p>
              <div className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl p-4">
                <h4 className="font-medium text-[var(--text-primary)] mb-2">What you get:</h4>
                <ul className="text-xs text-[var(--text-muted)] space-y-1">
                  <li>• Real-time signals from 140+ trading pairs</li>
                  <li>• AI-powered confidence scoring</li>
                  <li>• Pre-filtered high-quality signals</li>
                  <li>• Integration with ggbots strategy validation</li>
                </ul>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                This is a third-party service with its own subscription and pricing.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={closeModal}
                className="flex-1 px-4 py-2 border border-[var(--border)] text-[var(--text-secondary)] text-sm rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors"
              >
                Maybe Later
              </button>
              <button
                onClick={handleSubscribeClick}
                className="flex-1 px-4 py-2 bg-[var(--agent-trading)] text-white text-sm rounded-xl hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              >
                Subscribe to ggShot
                <ExternalLink className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Future Signals Sources */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 opacity-60">
        <div className="flex items-center gap-3 mb-4">
          <Lock className="h-5 w-5 text-[var(--text-muted)]" />
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Additional Signal Sources
          </h3>
          <span className="px-2 py-1 rounded-full bg-[var(--agent-extraction)]/20 text-xs text-[var(--agent-extraction)] border border-[var(--agent-extraction)]/30">
            Coming Soon
          </span>
        </div>

        <div className="space-y-3">
          <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="font-medium text-[var(--text-primary)] mb-1">Discord Trading Communities</div>
            <div className="text-xs text-[var(--text-muted)]">Connect to verified Discord trading groups and channels</div>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="font-medium text-[var(--text-primary)] mb-1">Twitter Signal Aggregation</div>
            <div className="text-xs text-[var(--text-muted)]">Monitor and validate signals from trusted Twitter accounts</div>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="font-medium text-[var(--text-primary)] mb-1">Custom Signal APIs</div>
            <div className="text-xs text-[var(--text-muted)]">Connect your own signal sources via webhook integrations</div>
          </div>
        </div>
      </div>

      {/* ggShot Subscription Modal */}
      {showGgShotModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Subscribe to ggShot Signals
            </h3>

            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 mb-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-4 w-4 text-amber-400" />
                <div className="text-sm text-amber-400 font-medium">External Premium Service</div>
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                ggShot signals are provided by an external premium service. To access ggShot signals, you need to subscribe directly with them.
              </p>
            </div>

            <div className="text-sm text-[var(--text-secondary)] mb-6">
              <p className="mb-3">
                ggShot provides AI-filtered premium trading signals from 140+ crypto pairs with advanced confidence scoring.
              </p>
              <p className="text-xs text-[var(--text-muted)]">
                This is a third-party service with its own subscription and pricing.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={closeModal}
                className="flex-1 px-4 py-2 border border-[var(--border)] text-[var(--text-secondary)] text-sm rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors"
              >
                Cancel
              </button>
              <a
                href="https://t.me/GGShot_Bot?start=1054536871"
                target="_blank"
                rel="noopener noreferrer"
                onClick={closeModal}
                className="flex-1 px-4 py-2 bg-[var(--agent-trading)] text-white text-sm rounded-xl hover:opacity-90 transition-opacity text-center flex items-center justify-center gap-2"
              >
                Subscribe Now
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}