'use client'

import React, { useState, useEffect } from 'react'
import { Crown, Clock, CheckSquare, Bot, Rocket, Loader2, AlertCircle, Zap } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'

type BotType = 'scheduled_trading' | 'signal_validation' | 'agent'
type TradingMode = 'paper' | 'symphony' | 'aster'

interface BotCreationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (botType: BotType, tradingMode: TradingMode, symphonyAgentId?: string) => void
}

export function BotCreationModal({
  open,
  onOpenChange,
  onConfirm
}: BotCreationModalProps) {
  const [selectedType, setSelectedType] = useState<BotType>('scheduled_trading')
  const [tradingMode, setTradingMode] = useState<TradingMode>('paper')
  const [symphonyAgentId, setSymphonyAgentId] = useState('')
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const [symphonyConnected, setSymphonyConnected] = useState(false)
  const [asterConnected, setAsterConnected] = useState(false)
  const [checkingConnections, setCheckingConnections] = useState(true)
  const { canAccess } = usePermissions()

  const hasAgentAccess = canAccess('agents')

  // Check Symphony and Aster connection status on mount
  useEffect(() => {
    if (open) {
      checkConnectionStatus()
    }
  }, [open])

  const checkConnectionStatus = async () => {
    try {
      setCheckingConnections(true)

      const supabase = (await import('@/lib/supabase')).createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        setCheckingConnections(false)
        return
      }

      // Check both Symphony and Aster in parallel
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

  const botTypes = [
    {
      type: 'scheduled_trading' as const,
      Icon: Clock,
      label: 'Scheduled Trading',
      description: 'Automated trading on a fixed schedule (5m, 15m, 1h, etc.)',
      color: 'var(--agent-extraction)',
      available: true,
      tier: 'Free'
    },
    {
      type: 'signal_validation' as const,
      Icon: CheckSquare,
      label: 'Signal Validation',
      description: 'Validate external signals (Telegram, webhooks) with AI analysis',
      color: 'var(--agent-decision)',
      available: true,
      tier: 'Free'
    },
    {
      type: 'agent' as const,
      Icon: Bot,
      label: 'Agent',
      description: 'Autonomous AI agent that defines its own trading strategy through conversation',
      color: '#9333ea', // purple-600
      available: hasAgentAccess,
      tier: 'Pro'
    }
  ]

  const tradingModes = [
    {
      mode: 'paper' as const,
      Icon: Zap,
      label: 'Paper Trading',
      description: 'Practice with virtual money, no risk',
      color: 'var(--agent-extraction)',
      available: true,
      tier: 'Free',
      requiresConnection: false
    },
    {
      mode: 'symphony' as const,
      Icon: Rocket,
      label: 'Symphony Live',
      description: 'Real trades via Symphony.io',
      color: 'var(--signal)', // signal blue
      available: true,
      tier: 'Free',
      requiresConnection: true,
      connected: symphonyConnected
    },
    {
      mode: 'aster' as const,
      Icon: Bot,
      label: 'AsterDEX',
      description: 'Real trades on AsterDEX',
      color: 'var(--ember)', // ember red
      available: true,
      tier: 'Free',
      requiresConnection: true,
      connected: asterConnected
    }
  ]

  const handleConfirm = () => {
    const selectedBotType = botTypes.find(t => t.type === selectedType)
    const selectedTradingMode = tradingModes.find(m => m.mode === tradingMode)

    // Check bot type availability
    if (!selectedBotType?.available) {
      setUpgradeModalOpen(true)
      return
    }

    // Check trading mode availability
    if (!selectedTradingMode?.available) {
      setUpgradeModalOpen(true)
      return
    }

    // Check connection requirement
    if (selectedTradingMode.requiresConnection && !selectedTradingMode.connected) {
      alert(`Please connect your ${selectedTradingMode.label} account in Settings before creating a ${selectedTradingMode.label} bot.`)
      return
    }

    // Validate Symphony Agent ID if Symphony is selected
    if (tradingMode === 'symphony') {
      if (!symphonyAgentId.trim()) {
        alert('Symphony Agent ID is required for Symphony live trading.')
        return
      }

      // Basic UUID validation
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      if (!uuidRegex.test(symphonyAgentId.trim())) {
        alert('Invalid Symphony Agent ID format (should be a UUID).')
        return
      }
    }

    onConfirm(selectedType, tradingMode, symphonyAgentId.trim() || undefined)
    onOpenChange(false)

    // Reset form
    setTradingMode('paper')
    setSymphonyAgentId('')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Create New Bot</DialogTitle>
          <DialogDescription>
            Choose the type of bot you want to create
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {botTypes.map(({ type, Icon, label, description, color, available, tier }) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                selectedType === type
                  ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                  : 'border-[var(--border)] hover:border-[var(--border-hover)]'
              } ${!available ? 'opacity-60' : ''}`}
            >
              <div className="flex items-start gap-3">
                <div
                  className="flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: available ? `${color}20` : 'var(--bg-tertiary)' }}
                >
                  <Icon className="h-6 w-6" style={{ color: available ? color : 'var(--text-muted)' }} />
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-[var(--text-primary)]">
                      {label}
                    </span>
                    {!available && tier === 'Pro' && (
                      <Crown className="h-3 w-3 text-[var(--text-muted)]" />
                    )}
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                      {tier}
                    </span>
                  </div>

                  <p className="text-sm text-[var(--text-secondary)]">
                    {description}
                  </p>
                </div>

                <div className={`flex-shrink-0 w-5 h-5 rounded-full border-2 mt-1 ${
                  selectedType === type
                    ? 'border-[var(--accent)] bg-[var(--accent)]'
                    : 'border-[var(--border)]'
                }`}>
                  {selectedType === type && (
                    <div className="w-full h-full flex items-center justify-center text-obsidian">
                      <Crown className="h-3 w-3" />
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Step 2: Trading Mode Selection */}
        <div className="space-y-3 py-4 border-t border-[var(--border)]">
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">Trading Mode</h3>
            <p className="text-xs text-[var(--text-secondary)]">Choose how this bot will execute trades</p>
          </div>

          {checkingConnections ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-5 w-5 animate-spin text-[var(--text-secondary)]" />
            </div>
          ) : (
            <div className="space-y-2">
              {tradingModes.map(({ mode, Icon, label, description, color, available, tier, requiresConnection, connected }) => {
                const isDisabled = !available || (requiresConnection && !connected)
                const showWarning = requiresConnection && !connected

                return (
                  <button
                    key={mode}
                    onClick={() => setTradingMode(mode)}
                    disabled={isDisabled}
                    className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                      tradingMode === mode
                        ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                        : 'border-[var(--border)] hover:border-[var(--border-hover)]'
                    } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: !isDisabled ? `${color}20` : 'var(--bg-tertiary)' }}
                      >
                        <Icon className="h-5 w-5" style={{ color: !isDisabled ? color : 'var(--text-muted)' }} />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-sm font-medium text-[var(--text-primary)]">
                            {label}
                          </span>
                          {!available && (
                            <Crown className="h-3 w-3 text-[var(--text-muted)]" />
                          )}
                          <span className="text-xs px-1.5 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                            {tier}
                          </span>
                          {showWarning && (
                            <span className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                              <AlertCircle className="h-3 w-3" />
                              Not connected
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-[var(--text-secondary)]">
                          {description}
                        </p>
                      </div>

                      <div className={`flex-shrink-0 w-4 h-4 rounded-full border-2 ${
                        tradingMode === mode
                          ? 'border-[var(--accent)] bg-[var(--accent)]'
                          : 'border-[var(--border)]'
                      }`}>
                        {tradingMode === mode && (
                          <div className="w-full h-full flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-obsidian"></div>
                          </div>
                        )}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          )}

          {/* Symphony Agent ID Input (conditional) */}
          {tradingMode === 'symphony' && (
            <div className="mt-4 p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
              <label className="block text-sm font-medium mb-2 text-[var(--text-primary)]">
                Symphony Agent ID *
              </label>
              <input
                type="text"
                value={symphonyAgentId}
                onChange={(e) => setSymphonyAgentId(e.target.value)}
                placeholder="00000000-0000-0000-0000-000000000000"
                className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] placeholder:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-500/50 font-mono text-sm"
              />
              <p className="text-xs text-[var(--text-secondary)] mt-1.5">
                Find your Agent ID in the{' '}
                <a
                  href="https://agent-portal.symphony.io"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-red-500 hover:text-red-600 underline"
                >
                  Symphony portal
                </a>
                {' '}under &ldquo;My Agents&rdquo;
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border)]">
          <button
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleConfirm}
            className="px-4 py-2 rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#edebe7] dark:text-[#1a1816] font-medium transition-colors"
          >
            {botTypes.find(t => t.type === selectedType)?.available ? 'Create Bot' : 'Upgrade to Create'}
          </button>
        </div>
      </DialogContent>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </Dialog>
  )
}
