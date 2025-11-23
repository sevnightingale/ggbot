'use client'

import { useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'

interface RiskAcknowledgmentModalProps {
  isOpen: boolean
  onClose: () => void
  onAccept: () => void
  tradingMode: 'paper' | 'symphony' | 'aster'
  botName: string
}

export function RiskAcknowledgmentModal({
  isOpen,
  onClose,
  onAccept,
  tradingMode,
  botName
}: RiskAcknowledgmentModalProps) {
  const [acknowledged, setAcknowledged] = useState(false)

  if (!isOpen) return null

  const isLiveTrading = tradingMode === 'symphony' || tradingMode === 'aster'
  const platformName = tradingMode === 'symphony' ? 'Symphony.io' : 'AsterDEX'

  const handleAccept = () => {
    if (acknowledged) {
      onAccept()
      setAcknowledged(false) // Reset for next time
    }
  }

  const handleClose = () => {
    setAcknowledged(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl mx-4 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-500" />
            <h2 className="text-xl font-bold text-[var(--text-primary)]">
              {isLiveTrading ? 'Live Trading Risk Acknowledgment' : 'Bot Activation'}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
          <p className="text-[var(--text-primary)] font-semibold">
            You are about to activate &quot;{botName}&quot; {isLiveTrading && `in ${platformName} live trading mode`}.
          </p>

          {isLiveTrading && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
              <p className="text-yellow-200 font-semibold mb-2">⚠️ This bot will trade with real funds</p>
              <p className="text-yellow-200/80 text-sm">
                All trades executed by this bot will use your actual {platformName} account balance.
              </p>
            </div>
          )}

          <div className="space-y-3 text-sm text-[var(--text-secondary)]">
            <p className="font-semibold text-[var(--text-primary)]">Please acknowledge the following risks:</p>

            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-[var(--accent)] font-bold">•</span>
                <p><strong>Market Risk:</strong> Digital assets are highly volatile. You may lose your entire trading capital.</p>
              </div>

              <div className="flex items-start gap-2">
                <span className="text-[var(--accent)] font-bold">•</span>
                <p><strong>AI Decision Risk:</strong> AI-generated trading decisions may be incorrect or based on flawed data. AI models can and do make losing trades.</p>
              </div>

              <div className="flex items-start gap-2">
                <span className="text-[var(--accent)] font-bold">•</span>
                <p><strong>Technical Risk:</strong> Software bugs, API failures, or network issues may cause unintended trades or prevent trades from executing.</p>
              </div>

              <div className="flex items-start gap-2">
                <span className="text-[var(--accent)] font-bold">•</span>
                <p><strong>No Financial Advice:</strong> ggbots AI models are not financial advisors and do not provide investment advice. You are solely responsible for all trading decisions.</p>
              </div>

              <div className="flex items-start gap-2">
                <span className="text-[var(--accent)] font-bold">•</span>
                <p><strong>No Guarantees:</strong> Past performance is not indicative of future results. There is no guarantee of profit.</p>
              </div>
            </div>
          </div>

          <div className="bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg p-4 mt-4">
            <p className="text-xs text-[var(--text-secondary)]">
              By activating this bot, you confirm that you have read and agree to our{' '}
              <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline">
                Terms of Service
              </a>
              {' '}and understand the risks involved in {isLiveTrading ? 'live' : 'automated'} trading.
            </p>
          </div>

          {/* Acknowledgment Checkbox */}
          <label className="flex items-start gap-3 cursor-pointer p-4 border border-[var(--border)] rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-[var(--border)] bg-[var(--bg-primary)] text-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-0"
            />
            <span className="text-sm text-[var(--text-primary)] font-medium">
              I acknowledge the risks and understand that I am solely responsible for all trading activity and losses.
              {isLiveTrading && ' I confirm this bot will trade with real funds on my behalf.'}
            </span>
          </label>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-[var(--border)]">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAccept}
            disabled={!acknowledged}
            className={`px-6 py-2 text-sm font-medium rounded-lg transition-all ${
              acknowledged
                ? 'bg-[var(--accent)] text-white hover:opacity-90'
                : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] cursor-not-allowed opacity-50'
            }`}
          >
            Activate Bot
          </button>
        </div>
      </div>
    </div>
  )
}
