'use client'

import { useState } from 'react'
import { Bot, BotStatus } from '@/store/botStore'

interface BotControlModalProps {
  bot: Bot
  isOpen: boolean
  onClose: () => void
  onSave: (updatedBot: Bot) => void
  onStart: (config_id: string) => void
  onDelete: (config_id: string) => void
  mode?: 'demo' | 'production'
}

type TabId = 'general' | 'extraction' | 'decision' | 'trading'

interface Tab {
  id: TabId
  title: string
  icon: string
  alwaysVisible?: boolean
}

const TABS: Tab[] = [
  { id: 'general', title: 'General', icon: '🎛️', alwaysVisible: true },
  { id: 'extraction', title: 'Extraction', icon: '📊' },
  { id: 'decision', title: 'Decision', icon: '🧠' },
  { id: 'trading', title: 'Trading', icon: '💰' }
]

export default function BotControlModal({
  bot,
  isOpen,
  onClose,
  onSave,
  onStart,
  onDelete,
  mode = 'demo'
}: BotControlModalProps) {
  const [activeTab, setActiveTab] = useState<TabId>('general')
  const [formData, setFormData] = useState({
    name: bot.name,
    strategy: bot.strategy || 'meanrev',
    crypto: bot.crypto || 'BTC',
    riskLevel: bot.riskLevel || 'medium'
  })

  const visibleTabs = mode === 'demo' 
    ? TABS.filter(tab => tab.alwaysVisible)
    : TABS

  const getStatusColor = (phase: BotStatus['phase']) => {
    switch (phase) {
      case 'idle': return 'text-blue-400'
      case 'extraction': return 'text-blue-400'
      case 'decision': return 'text-green-400'
      case 'trading': return 'text-orange-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusLabel = (phase: BotStatus['phase']) => {
    switch (phase) {
      case 'idle': return 'Idle'
      case 'extraction': return 'Extracting'
      case 'decision': return 'Deciding'
      case 'trading': return 'Trading'
      default: return 'Unknown'
    }
  }

  const getAvailableActions = (isActive: boolean, phase: BotStatus['phase']) => {
    if (!isActive) {
      return ['start', 'delete']
    }
    
    switch (phase) {
      case 'idle': return ['stop', 'delete']
      case 'extraction':
      case 'decision':
      case 'trading': return ['stop']
      default: return ['delete']
    }
  }

  const handleSave = () => {
    const updatedBot: Bot = {
      ...bot,
      name: formData.name,
      strategy: formData.strategy,
      crypto: formData.crypto,
      riskLevel: formData.riskLevel
    }
    onSave(updatedBot)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="modal-background bg-charcoal-900 border-2 border-charcoal-700 w-full max-w-4xl h-[90vh] flex flex-col relative">
        {/* Tabs with Close Button */}
        <div className="flex items-center justify-between border-b border-charcoal-700 px-8">
          <div className="flex">
            {visibleTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-agent-extraction text-agent-extraction'
                    : 'border-transparent text-gray-400 hover:text-bone'
                }`}
              >
                <span className="text-lg">{tab.icon}</span>
                <span className="text-subheader">{tab.title}</span>
              </button>
            ))}
          </div>
          <button
            onClick={onClose}
            className="text-2xl text-gray-400 hover:text-bone transition-colors p-2"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* Status Bar - Compact */}
          <div className="flex items-center justify-between px-8 py-4 border-b border-charcoal-600 bg-charcoal-800/30 flex-shrink-0">
              <div className="flex items-center gap-4">
                {/* Bot Name with Edit */}
                <div className="flex items-center gap-2">
                  {isEditingName ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      onBlur={() => setIsEditingName(false)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') setIsEditingName(false)
                      }}
                      className="bg-charcoal-900 border border-charcoal-600 text-bone px-2 py-1 text-body focus:border-agent-extraction transition-colors"
                      autoFocus
                    />
                  ) : (
                    <>
                      <span className="text-body font-medium text-bone">{formData.name}</span>
                      <button
                        onClick={() => setIsEditingName(true)}
                        className="text-gray-400 hover:text-bone transition-colors"
                        title="Edit name"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                        </svg>
                      </button>
                    </>
                  )}
                </div>
                <span className="text-gray-500">•</span>
                <div className={`flex items-center gap-3 ${getStatusColor(bot.status.phase)}`}>
                  <div className="w-4 h-4 bg-current"></div>
                  <span className="text-body font-medium">{getStatusLabel(bot.status.phase)}</span>
                </div>
                <span className="text-gray-500">•</span>
                <span className="text-footnote text-gray-400">
                  {bot.isActive ? 'Active' : 'Inactive'} • Created: {bot.createdAt ? bot.createdAt.toLocaleDateString() : 'Just now'}
                </span>
              </div>
              
              {/* Action Icons */}
              <div className="flex items-center gap-3">
                {/* Start/Stop Toggle */}
                {getAvailableActions(bot.isActive, bot.status.phase).includes('start') && (
                  <button
                    onClick={() => onStart(bot.config_id)}
                    className="p-2 text-green-400 hover:text-green-300 hover:bg-green-400/10 transition-colors rounded group"
                    title="Start Bot"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                  </button>
                )}
                
                {getAvailableActions(bot.isActive, bot.status.phase).includes('stop') && (
                  <button
                    onClick={() => onStart(bot.config_id)} // TODO: use stopBot when implemented
                    className="p-2 text-orange-400 hover:text-orange-300 hover:bg-orange-400/10 transition-colors rounded group"
                    title="Stop Bot"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                    </svg>
                  </button>
                )}

                {/* Delete Button */}
                {getAvailableActions(bot.isActive, bot.status.phase).includes('delete') && (
                  <button
                    onClick={() => onDelete(bot.config_id)}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 transition-colors rounded group"
                    title="Delete Bot"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 6v18h18v-18h-18zm5 14c0 .552-.448 1-1 1s-1-.448-1-1v-10c0-.552.448-1 1-1s1 .448 1 1v10zm5 0c0 .552-.448 1-1 1s-1-.448-1-1v-10c0-.552.448-1 1-1s1 .448 1 1v10zm5 0c0 .552-.448 1-1 1s-1-.448-1-1v-10c0-.552.448-1 1-1s1 .448 1 1v10zm4-18v2h-20v-2h5.711c.9 0 1.631-1.099 1.631-2h5.315c0 .901.73 2 1.631 2h5.712z"/>
                    </svg>
                  </button>
                )}
              </div>
            </div>

          {/* Scrollable Form Content */}
          <div className="flex-1 overflow-y-auto px-8 py-6 scroll-area">
            {activeTab === 'general' && (
              <div className="space-y-6">
                {/* Trading Strategy Section */}
                <div className="form-section p-4 border border-charcoal-600 bg-charcoal-800/20">
                  <label className="block text-subheader text-bone mb-4">
                      Trading Strategy
                    </label>
                  <div className="space-y-3">
                      {[
                        { id: 'momentum', label: 'I like momentum breakouts' },
                        { id: 'meanrev', label: 'I prefer mean reversion strategies' },
                        { id: 'trend', label: 'I follow trend continuations' },
                        { id: 'ai', label: 'Let the AI decide' }
                      ].map((strategy) => (
                        <label key={strategy.id} className="flex items-center gap-3 cursor-pointer p-2 hover:bg-charcoal-700/30 transition-colors">
                          <input
                            type="radio"
                            name="strategy"
                            value={strategy.id}
                            checked={formData.strategy === strategy.id}
                            onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                            className="scale-125 accent-agent-extraction"
                          />
                          <span className="text-body text-bone">{strategy.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Market Configuration Section */}
                <div className="form-section p-4 border border-charcoal-600 bg-charcoal-800/20">
                  <div className="space-y-4">
                      {/* Target Crypto */}
                      <div>
                        <label className="block text-subheader text-bone mb-4">
                          Target Cryptocurrency
                        </label>
                        <select
                          value={formData.crypto}
                          onChange={(e) => setFormData({ ...formData, crypto: e.target.value })}
                          className="w-full bg-charcoal-900 border-2 border-charcoal-700 text-bone p-4 focus:border-agent-extraction transition-colors text-body"
                        >
                          <option value="BTC">BTC - Bitcoin</option>
                          <option value="ETH">ETH - Ethereum</option>
                          <option value="SOL">SOL - Solana</option>
                        </select>
                      </div>

                      {/* Risk Tolerance */}
                      <div>
                        <label className="block text-subheader text-bone mb-4">
                          Risk Tolerance
                        </label>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-footnote text-gray-400">Low</span>
                            <span className="text-footnote text-gray-400">High</span>
                          </div>
                          <input
                            type="range"
                            min="1"
                            max="5"
                            value={formData.riskLevel === 'low' ? '1' : formData.riskLevel === 'medium' ? '3' : '5'}
                            onChange={(e) => {
                              const value = parseInt(e.target.value)
                              const level = value <= 2 ? 'low' : value <= 4 ? 'medium' : 'high'
                              setFormData({ ...formData, riskLevel: level })
                            }}
                            className="w-full h-3 bg-charcoal-700 appearance-none cursor-pointer slider"
                          />
                          <div className="text-center text-agent-extraction text-body font-medium">
                            {formData.riskLevel === 'low' ? '1% per trade' : 
                             formData.riskLevel === 'medium' ? '2% per trade' : '3% per trade'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
            )}

            {activeTab === 'extraction' && (
              <div className="text-gray-400 text-center py-8">
                Extraction module configuration coming soon...
              </div>
            )}

            {activeTab === 'decision' && (
              <div className="text-gray-400 text-center py-8">
                Decision module configuration coming soon...
              </div>
            )}

            {activeTab === 'trading' && (
              <div className="text-gray-400 text-center py-8">
                Trading module configuration coming soon...
              </div>
            )}
          </div>
        </div>

        {/* Fixed Action Buttons */}
        <div className="border-t border-charcoal-700 px-8 py-3 bg-charcoal-900 flex justify-end gap-3 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-6 py-3 border-2 border-charcoal-600 text-bone hover:bg-charcoal-700/50 transition-colors text-body"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-3 bg-agent-extraction hover:bg-agent-extraction/90 text-bone text-body font-medium transition-colors border-2 border-agent-extraction hover:border-agent-extraction/90"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
}