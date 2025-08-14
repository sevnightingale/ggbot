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
      <div className="modal-background bg-charcoal-900 border-2 border-charcoal-700 w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-8 border-b border-charcoal-700">
          <h1 className="text-header text-bone">
            {bot.name} Control Panel
          </h1>
          <button
            onClick={onClose}
            className="text-2xl text-gray-400 hover:text-bone transition-colors"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-charcoal-700 px-8">
          {visibleTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-4 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-400 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-bone'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span className="text-subheader">{tab.title}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Main Content Area */}
          <div className="flex-1 p-8">
            {/* Status Bar */}
            <div className="flex items-center justify-between mb-8 p-4 border border-charcoal-600 bg-charcoal-800/30">
              <div className="flex items-center gap-4">
                <div className={`flex items-center gap-3 ${getStatusColor(bot.status.phase)}`}>
                  <div className="w-4 h-4 bg-current"></div>
                  <span className="text-body font-medium">{getStatusLabel(bot.status.phase)}</span>
                </div>
                <span className="text-gray-500">•</span>
                <span className="text-footnote text-gray-400">
                  {bot.isActive ? 'Active' : 'Inactive'} • Created: {bot.createdAt ? bot.createdAt.toLocaleDateString() : 'Just now'}
                </span>
              </div>
            </div>

            {/* Scrollable Form Content */}
            <div className="max-h-80 overflow-y-auto pr-3 scroll-area">
              {activeTab === 'general' && (
                <div className="space-y-10">
                  {/* Bot Name Section */}
                  <div className="form-section p-6 border border-charcoal-600 bg-charcoal-800/20">
                    <label className="block text-subheader text-bone mb-4">
                      Bot Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full bg-charcoal-900 border-2 border-charcoal-700 text-bone p-4 focus:border-blue-400 transition-colors text-body"
                      placeholder="Enter bot name"
                    />
                  </div>

                  {/* Trading Strategy Section */}
                  <div className="form-section p-6 border border-charcoal-600 bg-charcoal-800/20">
                    <label className="block text-subheader text-bone mb-6">
                      Trading Strategy
                    </label>
                    <div className="space-y-5">
                      {[
                        { id: 'momentum', label: 'I like momentum breakouts' },
                        { id: 'meanrev', label: 'I prefer mean reversion strategies' },
                        { id: 'trend', label: 'I follow trend continuations' },
                        { id: 'ai', label: 'Let the AI decide' }
                      ].map((strategy) => (
                        <label key={strategy.id} className="flex items-center gap-4 cursor-pointer p-2 hover:bg-charcoal-700/30 transition-colors">
                          <input
                            type="radio"
                            name="strategy"
                            value={strategy.id}
                            checked={formData.strategy === strategy.id}
                            onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                            className="scale-125 accent-blue-400"
                          />
                          <span className="text-body text-bone">{strategy.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Market Configuration Section */}
                  <div className="form-section p-6 border border-charcoal-600 bg-charcoal-800/20">
                    <div className="space-y-6">
                      {/* Target Crypto */}
                      <div>
                        <label className="block text-subheader text-bone mb-4">
                          Target Cryptocurrency
                        </label>
                        <select
                          value={formData.crypto}
                          onChange={(e) => setFormData({ ...formData, crypto: e.target.value })}
                          className="w-full bg-charcoal-900 border-2 border-charcoal-700 text-bone p-4 focus:border-blue-400 transition-colors text-body"
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
                        <div className="space-y-4">
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
                          <div className="text-center text-blue-400 text-body font-medium">
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

          {/* Quick Actions Sidebar */}
          <div className="w-56 border-l border-charcoal-700 p-8 bg-charcoal-800/10">
            <h3 className="text-subheader text-bone mb-6">Quick Actions</h3>
            <div className="space-y-4">
              {getAvailableActions(bot.isActive, bot.status.phase).includes('start') && (
                <button
                  onClick={() => onStart(bot.config_id)}
                  className="w-full bg-green-600 hover:bg-green-700 text-bone text-body font-medium py-4 px-6 transition-colors border-2 border-green-600 hover:border-green-700"
                >
                  START BOT
                </button>
              )}
              
              {getAvailableActions(bot.isActive, bot.status.phase).includes('stop') && (
                <button
                  onClick={() => onStart(bot.config_id)} // For now, use same handler - will need stopBot later
                  className="w-full bg-transparent hover:bg-orange-600/20 text-orange-400 hover:text-orange-300 text-body font-medium py-4 px-6 transition-colors border-2 border-orange-500 hover:border-orange-400"
                >
                  STOP BOT
                </button>
              )}

              {getAvailableActions(bot.isActive, bot.status.phase).includes('delete') && (
                <button
                  onClick={() => onDelete(bot.config_id)}
                  className="w-full bg-transparent hover:bg-red-600/10 text-red-400 hover:text-red-300 text-footnote py-3 px-4 transition-colors border border-red-600 hover:border-red-500"
                >
                  DELETE BOT
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-charcoal-700 p-8 flex items-center justify-between bg-charcoal-800/20">
          <div className="text-footnote text-gray-400 flex items-center gap-2">
            <span>💡</span>
            <span>
              {mode === 'demo' 
                ? 'Demo mode: Changes apply to next analysis cycle'
                : 'Changes can be made while bot is running'
              }
            </span>
          </div>
          
          <div className="flex gap-4">
            <button
              onClick={onClose}
              className="px-8 py-4 border-2 border-charcoal-600 text-bone hover:bg-charcoal-700/50 transition-colors text-body"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-bone text-body font-medium transition-colors border-2 border-blue-600 hover:border-blue-700"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}