'use client'

import React from 'react'
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
  const currentStrategy = configData?.decision?.user_prompt || 'if RSI 1hr below 50 enter long, if above enter short'
  const analysisFrequency = configData?.decision?.analysis_frequency || '1h'

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Analysis Frequency */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Analysis Frequency
        </h3>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {['5m', '15m', '1h', '4h'].map((freq) => (
            <button
              key={freq}
              className={`px-4 py-3 text-sm rounded-xl border transition-colors ${
                analysisFrequency === freq
                  ? 'bg-[var(--agent-decision)] text-white border-[var(--agent-decision)]'
                  : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-tertiary)]'
              }`}
            >
              Every {freq}
            </button>
          ))}
        </div>

        <div className="mt-4 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
          <div className="text-sm text-[var(--text-muted)]">
            Current: <span className="text-[var(--text-primary)] font-medium">Every {analysisFrequency}</span>
          </div>
        </div>
      </div>

      {/* Strategy Prompt */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Trading Strategy
        </h3>

        <div className="space-y-4">
          {/* System Prompt (Locked) */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-2">
              System Instructions (Locked)
            </label>
            <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] opacity-60">
              <div className="text-sm text-[var(--text-secondary)]">
                You are an expert cryptocurrency trader analyzing market data. Your analysis is based on the provided market data and technical indicators. Provide clear, reasoned responses about trading actions. Format your response with clear sections for Decision, Confidence, and Reasoning.
              </div>
            </div>
          </div>

          {/* User Strategy (Editable) */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Your Trading Strategy
            </label>
            <textarea
              value={currentStrategy}
              onChange={(e) => {
                onUpdate?.({
                  decision: {
                    ...configData?.decision,
                    user_prompt: e.target.value
                  }
                })
              }}
              rows={6}
              className="w-full p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-decision)] focus:border-transparent resize-none"
              placeholder="Describe your trading strategy..."
            />
            <div className="mt-2 text-xs text-[var(--text-muted)]">
              Describe when to enter long/short positions, exit conditions, and risk management rules.
            </div>
          </div>
        </div>
      </div>

      {/* LLM Provider */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          AI Provider
        </h3>

        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {[
              { id: 'deepseek', name: 'DeepSeek R1', recommended: true },
              { id: 'openai', name: 'OpenAI GPT-4', premium: true }
            ].map((provider) => (
              <button
                key={provider.id}
                className={`p-4 rounded-xl border text-left transition-colors ${
                  configData?.llm_config?.provider === provider.id
                    ? 'bg-[var(--agent-decision)]/20 border-[var(--agent-decision)] text-[var(--text-primary)]'
                    : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium">{provider.name}</div>
                  {provider.recommended && (
                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-500">
                      Recommended
                    </span>
                  )}
                  {provider.premium && (
                    <span className="text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-500">
                      Premium
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>

          <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)]">
            <div className="text-sm text-[var(--text-muted)]">
              Using platform keys • <span className="text-[var(--text-primary)]">DeepSeek R1</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}