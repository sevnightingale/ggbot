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
      <div className="bg-charcoal-900 border-2 border-charcoal-700 w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-charcoal-700">
          <h2 className="text-2xl font-bold text-bone">
            {bot.name} Control Panel
          </h2>
          <button
            onClick={onClose}
            className="text-2xl text-gray-400 hover:text-bone transition-colors"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-charcoal-700 px-6">
          {visibleTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-400 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-bone'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span className="font-medium">{tab.title}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Main Content Area */}
          <div className="flex-1 p-6">
            {/* Status Bar */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className={`flex items-center gap-2 ${getStatusColor(bot.status.phase)}`}>
                  <div className="w-3 h-3 rounded-full bg-current"></div>
                  <span className="font-medium">{getStatusLabel(bot.status.phase)}</span>
                </div>
                <span className="text-gray-400">•</span>
                <span className="text-gray-400 text-sm">
                  {bot.isActive ? 'Active' : 'Inactive'} • Created: {bot.createdAt ? bot.createdAt.toLocaleDateString() : 'Just now'}
                </span>
              </div>
            </div>

            {/* Scrollable Form Content */}
            <div className="max-h-96 overflow-y-auto pr-2">
              {activeTab === 'general' && (
                <div className="space-y-6">
                  {/* Bot Name */}
                  <div>
                    <label className="block text-bone font-medium mb-2">
                      Bot Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full bg-charcoal-900 border-2 border-charcoal-700 text-bone p-3 focus:border-blue-400 transition-colors font-mono"
                      placeholder="Enter bot name"
                    />
                  </div>

                  {/* Trading Strategy */}
                  <div>
                    <label className="block text-bone font-medium mb-3">
                      Trading Strategy
                    </label>
                    <div className="space-y-3">
                      {[
                        { id: 'momentum', label: 'I like momentum breakouts' },
                        { id: 'meanrev', label: 'I prefer mean reversion strategies' },
                        { id: 'trend', label: 'I follow trend continuations' },
                        { id: 'ai', label: 'Let the AI decide' }
                      ].map((strategy) => (
                        <label key={strategy.id} className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="strategy"
                            value={strategy.id}
                            checked={formData.strategy === strategy.id}
                            onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                            className="scale-125 accent-blue-400"
                          />
                          <span className="text-bone">{strategy.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Target Crypto */}
                  <div>
                    <label className="block text-bone font-medium mb-2">
                      Target Cryptocurrency
                    </label>
                    <select
                      value={formData.crypto}
                      onChange={(e) => setFormData({ ...formData, crypto: e.target.value })}
                      className="w-full bg-charcoal-900 border-2 border-charcoal-700 text-bone p-3 focus:border-blue-400 transition-colors font-mono"
                    >
                      <option value="BTC">BTC - Bitcoin</option>
                      <option value="ETH">ETH - Ethereum</option>
                      <option value="SOL">SOL - Solana</option>
                    </select>
                  </div>

                  {/* Risk Tolerance */}
                  <div>
                    <label className="block text-bone font-medium mb-2">
                      Risk Tolerance
                    </label>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400">Low</span>
                        <span className="text-gray-400">High</span>
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
                        className="w-full h-2 bg-charcoal-700 rounded-lg appearance-none cursor-pointer slider"
                      />
                      <div className="text-center text-blue-400 font-medium">
                        {formData.riskLevel === 'low' ? '1% per trade' : 
                         formData.riskLevel === 'medium' ? '2% per trade' : '3% per trade'}
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
          <div className="w-48 border-l border-charcoal-700 p-6">
            <h3 className="text-bone font-medium mb-4">Quick Actions</h3>
            <div className="space-y-3">
              {getAvailableActions(bot.isActive, bot.status.phase).includes('start') && (
                <button
                  onClick={() => onStart(bot.config_id)}
                  className="w-full bg-green-600 hover:bg-green-700 text-bone font-medium py-3 px-4 transition-colors"
                >
                  START BOT
                </button>
              )}
              
              {getAvailableActions(bot.isActive, bot.status.phase).includes('stop') && (
                <button
                  onClick={() => onStart(bot.config_id)} // For now, use same handler - will need stopBot later
                  className="w-full bg-orange-600 hover:bg-orange-700 text-bone font-medium py-3 px-4 transition-colors"
                >
                  STOP BOT
                </button>
              )}

              {getAvailableActions(bot.isActive, bot.status.phase).includes('delete') && (
                <button
                  onClick={() => onDelete(bot.config_id)}
                  className="w-full bg-red-600 hover:bg-red-700 text-bone font-medium py-3 px-4 transition-colors"
                >
                  DELETE BOT
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-charcoal-700 p-6 flex items-center justify-between">
          <div className="text-gray-400 text-sm flex items-center gap-2">
            <span>💡</span>
            <span>
              {mode === 'demo' 
                ? 'Demo mode: Changes apply to next analysis cycle'
                : 'Changes can be made while bot is running'
              }
            </span>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-6 py-3 border-2 border-charcoal-700 text-bone hover:bg-charcoal-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-bone font-medium transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}