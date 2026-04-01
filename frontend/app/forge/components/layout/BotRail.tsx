'use client'

import React from 'react'
import Image from 'next/image'
import { BarChart2, Loader2, Circle, Zap, TrendingUp, TrendingDown } from 'lucide-react'
import { BotConfiguration } from '@/lib/api'
import { BotManagementMenu } from './BotManagementMenu'
import { EloTierBadge } from '../shared/EloTierBadge'

interface AccountData {
  config_id: string
  performance_pct?: number
}

// Logo mapping for LLM models (shared with StrategyEditor)
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
  'kimi': '#00c2cb',
}

interface BotRailProps {
  bots: BotConfiguration[]
  liveBot: BotConfiguration | null
  hyperliquidConnected: boolean
  selectedId: string | null
  onSelect: (configId: string) => void
  onCreateNew?: () => void
  onOpenHyperliquidSetup?: () => void
  onPromoteToLive?: (configId: string) => void
  isCreatingNew?: boolean
  onRename?: (configId: string, newName: string) => void
  onDuplicate?: (configId: string) => void
  onDelete?: (configId: string) => void
  onResetAccount?: (configId: string) => void
  isBotAction?: boolean
  accounts?: AccountData[]
  className?: string
}

export function BotRail({
  bots,
  liveBot,
  hyperliquidConnected,
  selectedId,
  onSelect,
  onCreateNew,
  onOpenHyperliquidSetup,
  onPromoteToLive,
  isCreatingNew = false,
  onRename,
  onDuplicate,
  onDelete,
  onResetAccount,
  isBotAction = false,
  accounts = [],
  className = ''
}: BotRailProps) {
  // Paper bots only (live bot shown separately)
  const paperBots = bots.filter(b => b.trading_mode !== 'hyperliquid')
  const currentBotCount = paperBots.length

  const handleCreateNew = () => {
    onCreateNew?.()
  }

  // Determine live slot state
  const hasStrategy = liveBot && liveBot.config_data?.selected_pair && liveBot.config_data?.decision

  return (
    <aside className={className}>
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
        {/* Live Trading Slot — always visible */}
        <div className="mb-3">
          <div className="text-xs font-medium text-[var(--text-muted)] mb-2 uppercase tracking-wide">
            Live Trading
          </div>

          {!hyperliquidConnected && !liveBot ? (
            // State 1: Not connected, no live bot yet
            <button
              onClick={onOpenHyperliquidSetup}
              className="w-full rounded-xl border-2 border-dashed border-[var(--border)] px-3 py-3 text-left opacity-60 hover:opacity-80 hover:border-[var(--accent)] transition-all"
            >
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-3 w-3 text-[var(--text-muted)]" />
                <span className="text-sm font-medium text-[var(--text-muted)]">Live Trading Slot</span>
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                Connect Hyperliquid to go live
              </div>
            </button>
          ) : !hyperliquidConnected && liveBot ? (
            // State 4: Disconnected but live bot preserved
            <button
              onClick={onOpenHyperliquidSetup}
              className="w-full rounded-xl border-l-2 border-[var(--border)] px-3 py-3 text-left opacity-50 hover:opacity-70 transition-all"
            >
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-3 w-3 text-[var(--text-muted)]" />
                <span className="text-sm font-medium text-[var(--text-muted)]">{liveBot.config_name}</span>
                <span
                  className="rounded-full px-1.5 py-0 text-[10px] font-semibold"
                  style={{
                    backgroundColor: 'color-mix(in srgb, var(--text-muted) 15%, transparent)',
                    color: 'var(--text-muted)'
                  }}
                >
                  LIVE
                </span>
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                Reconnect to resume live trading
              </div>
            </button>
          ) : liveBot && !hasStrategy ? (
            // State 2: Connected but no strategy promoted yet
            <div
              onClick={() => onSelect(liveBot.config_id)}
              className={`rounded-xl border-l-2 border-[var(--accent)] px-3 py-3 cursor-pointer transition-colors ${
                selectedId === liveBot.config_id ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-3 w-3 text-[var(--accent)]" />
                <span className="text-sm font-medium text-[var(--text-primary)]">{liveBot.config_name}</span>
                <span
                  className="rounded-full px-1.5 py-0 text-[10px] font-semibold"
                  style={{
                    backgroundColor: 'color-mix(in srgb, var(--accent) 15%, transparent)',
                    color: 'var(--accent)'
                  }}
                >
                  LIVE
                </span>
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                Promote a paper bot&apos;s strategy
              </div>
            </div>
          ) : liveBot && hasStrategy ? (
            // State 3: Has strategy (may be active or inactive)
            <LiveBotRow
              bot={liveBot}
              isSelected={selectedId === liveBot.config_id}
              onClick={() => onSelect(liveBot.config_id)}
              onRename={onRename}
              onResetAccount={onResetAccount}
              isBotAction={isBotAction}
              performancePct={accounts.find(a => a.config_id === liveBot.config_id)?.performance_pct}
            />
          ) : hyperliquidConnected && !liveBot ? (
            // Edge case: connected but no live bot config yet (should not happen normally)
            <div className="rounded-xl border-l-2 border-[var(--accent)] px-3 py-3 opacity-60">
              <div className="flex items-center gap-2">
                <Zap className="h-3 w-3 text-[var(--accent)]" />
                <span className="text-sm text-[var(--text-muted)]">Setting up live bot...</span>
              </div>
            </div>
          ) : null}
        </div>

        {/* Separator */}
        <hr className="border-[var(--border)] mb-3" />

        {/* Paper Bots Section */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium text-[var(--text-primary)]">
            <BarChart2 className="h-4 w-4" />
            <div className="flex items-center gap-2">
              <span>Paper Bots</span>
              <span className="text-xs text-[var(--text-muted)] font-normal">
                {currentBotCount}
              </span>
            </div>
          </div>
          <button
            onClick={handleCreateNew}
            disabled={isCreatingNew}
            className="rounded-xl border border-[var(--border)] px-2 py-1 text-xs transition-all text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--bg-tertiary)]"
          >
            {isCreatingNew ? (
              <span className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" /> Creating...
              </span>
            ) : '+ New'}
          </button>
        </div>

        <div className="space-y-2">
          {paperBots.length === 0 ? (
            <div className="text-sm text-[var(--text-muted)] p-4 text-center">
              No paper bots yet
            </div>
          ) : (
            paperBots.map((bot) => (
              <BotRow
                key={bot.config_id}
                bot={bot}
                isSelected={bot.config_id === selectedId}
                onClick={() => onSelect(bot.config_id)}
                onRename={onRename}
                onDuplicate={onDuplicate}
                onDelete={onDelete}
                onResetAccount={onResetAccount}
                onPromoteToLive={hyperliquidConnected ? onPromoteToLive : undefined}
                isBotAction={isBotAction}
                performancePct={accounts.find(a => a.config_id === bot.config_id)?.performance_pct}
              />
            ))
          )}
        </div>
      </div>
    </aside>
  )
}

// Live bot row — special styling, limited menu (no delete/duplicate)
interface LiveBotRowProps {
  bot: BotConfiguration
  isSelected: boolean
  onClick: () => void
  onRename?: (configId: string, newName: string) => void
  onResetAccount?: (configId: string) => void
  isBotAction: boolean
  performancePct?: number
}

function LiveBotRow({
  bot,
  isSelected,
  onClick,
  onRename,
  onResetAccount,
  isBotAction,
  performancePct
}: LiveBotRowProps) {
  const analysisFreq = bot.config_data.decision?.analysis_frequency || '1h'
  const pair = bot.config_data.selected_pair || 'No pair'

  let frequency = ''
  if (analysisFreq === 'signal_driven') frequency = 'Signal driven'
  else if (analysisFreq === 'agent_driven') frequency = 'Agent driven'
  else frequency = `Every ${analysisFreq}`

  const llmModel = bot.config_data.llm_config?.model || 'grok'
  const logoPath = MODEL_LOGOS[llmModel]
  const logoColor = MODEL_COLORS[llmModel]

  return (
    <div
      className={`rounded-xl border-l-2 border-[var(--accent)] px-3 py-3 transition-colors relative ${
        isSelected ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
      }`}
    >
      <div
        onClick={(e) => {
          const target = e.target as HTMLElement
          if (target.closest('[data-menu-trigger]') || target.closest('[data-bot-menu]')) return
          onClick()
        }}
        className="cursor-pointer mb-2"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Zap
              className={`h-3 w-3 ${bot.state === 'active' ? 'text-[var(--accent)] fill-[var(--accent)]' : 'text-[var(--accent)]'}`}
            />
            <div className="text-sm font-medium text-[var(--text-primary)]">{bot.config_name}</div>
            <span
              className="rounded-full px-1.5 py-0 text-[10px] font-semibold"
              style={{
                backgroundColor: 'color-mix(in srgb, var(--accent) 15%, transparent)',
                color: 'var(--accent)'
              }}
            >
              LIVE
            </span>
          </div>
          {onRename && (
            <BotManagementMenu
              bot={bot}
              onRename={onRename}
              onDuplicate={() => {}}
              onDelete={() => {}}
              onResetAccount={onResetAccount}
              isBotAction={isBotAction}
              isLiveBot
            />
          )}
        </div>

        {/* Metadata badges: model, pair, performance */}
        <div className="flex flex-wrap gap-1 mb-2">
          {logoPath && (
            <span className="rounded-full border border-[var(--border)] px-1.5 py-0.5 flex items-center gap-1">
              <div
                className="flex items-center justify-center rounded-full"
                style={{
                  width: '16px',
                  height: '16px',
                  backgroundColor: logoColor || 'transparent',
                  padding: logoColor ? '2px' : '0'
                }}
              >
                <Image
                  src={logoPath}
                  alt={`${llmModel} logo`}
                  width={16}
                  height={16}
                  className="object-contain"
                />
              </div>
            </span>
          )}
          <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
            {pair}
          </span>
          {performancePct != null && performancePct !== 0 && (
            <span className={`rounded-full border border-[var(--border)] px-2 py-0.5 text-xs font-medium flex items-center gap-0.5 ${
              performancePct >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
            }`}>
              {performancePct >= 0
                ? <TrendingUp className="h-3 w-3" />
                : <TrendingDown className="h-3 w-3" />
              }
              {performancePct >= 0 ? '+' : ''}{performancePct.toFixed(1)}%
            </span>
          )}
        </div>

        {/* Frequency */}
        <div className="text-xs text-[var(--text-muted)]">{frequency}</div>
      </div>
    </div>
  )
}

// Standard paper bot row
interface BotRowProps {
  bot: BotConfiguration
  isSelected: boolean
  onClick: () => void
  onRename?: (configId: string, newName: string) => void
  onDuplicate?: (configId: string) => void
  onDelete?: (configId: string) => void
  onResetAccount?: (configId: string) => void
  onPromoteToLive?: (configId: string) => void
  isBotAction: boolean
  performancePct?: number
}

function BotRow({
  bot,
  isSelected,
  onClick,
  onRename,
  onDuplicate,
  onDelete,
  onResetAccount,
  onPromoteToLive,
  isBotAction,
  performancePct
}: BotRowProps) {
  // Get bot metadata
  const analysisFreq = bot.config_data.decision?.analysis_frequency || '1h'
  const pair = bot.config_data.selected_pair || 'No pair'

  // Format frequency text based on mode
  let frequency = ''
  if (analysisFreq === 'signal_driven') {
    frequency = 'Signal driven'
  } else if (analysisFreq === 'agent_driven') {
    frequency = 'Agent driven'
  } else {
    frequency = `Frequency: ${analysisFreq}`
  }

  // Get LLM model info
  const llmModel = bot.config_data.llm_config?.model || 'grok'
  const logoPath = MODEL_LOGOS[llmModel]
  const logoColor = MODEL_COLORS[llmModel]

  return (
    <div
      className={`rounded-xl px-3 py-3 transition-colors relative ${
        isSelected ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-primary)]'
      }`}
    >
      <div
        onClick={(e) => {
          // Don't select bot if clicking menu button or inside menu dropdown
          const target = e.target as HTMLElement
          if (target.closest('[data-menu-trigger]') || target.closest('[data-bot-menu]')) return
          onClick()
        }}
        className="cursor-pointer mb-2"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Circle
              className={`h-3 w-3 ${bot.state === 'active' ? 'text-[var(--accent)] fill-[var(--accent)]' : 'text-[var(--text-muted)]'}`}
            />
            <div className="text-sm font-medium text-[var(--text-primary)]">{bot.config_name}</div>
          </div>
          {(onRename || onDuplicate || onDelete || onResetAccount) && (
            <BotManagementMenu
              bot={bot}
              onRename={onRename || (() => {})}
              onDuplicate={onDuplicate || (() => {})}
              onDelete={onDelete || (() => {})}
              onResetAccount={onResetAccount}
              onPromoteToLive={onPromoteToLive}
              isBotAction={isBotAction}
            />
          )}
        </div>

        {/* Metadata badges: model, pair, performance, Elo */}
        <div className="flex flex-wrap gap-1 mb-2">
          {logoPath && (
            <span className="rounded-full border border-[var(--border)] px-1.5 py-0.5 flex items-center gap-1">
              <div
                className="flex items-center justify-center rounded-full"
                style={{
                  width: '16px',
                  height: '16px',
                  backgroundColor: logoColor || 'transparent',
                  padding: logoColor ? '2px' : '0'
                }}
              >
                <Image
                  src={logoPath}
                  alt={`${llmModel} logo`}
                  width={16}
                  height={16}
                  className="object-contain"
                />
              </div>
            </span>
          )}
          <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
            {pair}
          </span>
          {performancePct != null && performancePct !== 0 && (
            <span className={`rounded-full border border-[var(--border)] px-2 py-0.5 text-xs font-medium flex items-center gap-0.5 ${
              performancePct >= 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'
            }`}>
              {performancePct >= 0
                ? <TrendingUp className="h-3 w-3" />
                : <TrendingDown className="h-3 w-3" />
              }
              {performancePct >= 0 ? '+' : ''}{performancePct.toFixed(1)}%
            </span>
          )}
          {bot.trading_mode !== 'hyperliquid' && bot.elo_rating != null && (
            <EloTierBadge elo={bot.elo_rating} size="sm" />
          )}
        </div>

        {/* Frequency */}
        <div className="text-xs text-[var(--text-muted)]">{frequency}</div>
      </div>
    </div>
  )
}
