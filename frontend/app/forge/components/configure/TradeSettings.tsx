'use client'

import React from 'react'
import { ConfigData } from '@/lib/api'

interface TradeSettingsProps {
  configData?: ConfigData
  onUpdate?: (updates: Partial<ConfigData>) => void
  className?: string
}

export function TradeSettings({
  configData,
  onUpdate,
  className = ''
}: TradeSettingsProps) {
  const trading = configData?.trading || {}
  const positionSizing = trading.position_sizing || {}
  const riskManagement = trading.risk_management || {}

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Position Sizing */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Position Sizing
        </h3>

        <div className="space-y-4">
          {/* Position Size Method */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-3">
              Sizing Method
            </label>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {[
                { id: 'fixed_usd', name: 'Fixed USD Amount', desc: 'Use same dollar amount per trade' },
                { id: 'account_percent', name: 'Account Percentage', desc: 'Use percentage of total balance' }
              ].map((method) => (
                <button
                  key={method.id}
                  className={`p-4 rounded-xl border text-left transition-colors ${
                    positionSizing.method === method.id
                      ? 'bg-[var(--agent-trading)]/20 border-[var(--agent-trading)] text-[var(--text-primary)]'
                      : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  <div className="font-medium">{method.name}</div>
                  <div className="text-sm text-[var(--text-muted)] mt-1">{method.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Size Inputs */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                Fixed Amount (USD)
              </label>
              <input
                type="number"
                value={positionSizing.fixed_amount_usd || 100}
                className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-trading)] focus:border-transparent"
                placeholder="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                Account Percentage (%)
              </label>
              <input
                type="number"
                value={positionSizing.account_percent || 5}
                min="0.1"
                max="100"
                step="0.1"
                className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-trading)] focus:border-transparent"
                placeholder="5"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Risk Management */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Risk Management
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              Stop Loss (%)
            </label>
            <input
              type="number"
              value={riskManagement.default_stop_loss_percent || 5}
              min="0.1"
              max="50"
              step="0.1"
              className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
              placeholder="5"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              Take Profit (%)
            </label>
            <input
              type="number"
              value={riskManagement.default_take_profit_percent || 10}
              min="0.1"
              max="100"
              step="0.1"
              className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              Max Positions
            </label>
            <input
              type="number"
              value={riskManagement.max_positions || 1}
              min="1"
              max="10"
              className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-trading)] focus:border-transparent"
              placeholder="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              Daily Loss Limit (USD)
            </label>
            <input
              type="number"
              value={riskManagement.max_daily_loss_usd || 500}
              min="10"
              className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
              placeholder="500"
            />
          </div>
        </div>
      </div>

      {/* Telegram Integration */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Telegram Publishing
        </h3>

        <div className="space-y-4">
          {/* Enable Toggle */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div>
              <div className="font-medium text-[var(--text-primary)]">Publish Signals</div>
              <div className="text-sm text-[var(--text-muted)]">Send trading decisions to Telegram channel</div>
            </div>
            <button
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                configData?.telegram_integration?.publisher?.enabled
                  ? 'bg-emerald-500'
                  : 'bg-[var(--border)]'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  configData?.telegram_integration?.publisher?.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Channel Settings (when enabled) */}
          {configData?.telegram_integration?.publisher?.enabled && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                  Bot Token
                </label>
                <input
                  type="password"
                  placeholder="Your Telegram bot token"
                  className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
                  Channel ID
                </label>
                <input
                  type="text"
                  placeholder="-1001234567890"
                  className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-transparent"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}