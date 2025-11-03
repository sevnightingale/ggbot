'use client'

import React, { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'

interface Message {
  role: 'user' | 'agent'
  content: string
  timestamp: string
}

interface AgentStrategy {
  content: string
  version?: number
  last_updated_at?: string
  autonomously_editable?: boolean
}

interface AgentConfiguratorProps {
  messages: Message[]
  inputValue: string
  isWaiting: boolean
  showConfirmButton: boolean
  currentStrategy?: AgentStrategy | null
  onSendMessage: () => void
  onConfirmStrategy: (autonomouslyEditable: boolean) => void
  onInputChange: (value: string) => void
}

export function AgentConfigurator({
  messages,
  inputValue,
  isWaiting,
  showConfirmButton,
  currentStrategy,
  onSendMessage,
  onConfirmStrategy,
  onInputChange
}: AgentConfiguratorProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [autonomouslyEditable, setAutonomouslyEditable] = useState(false)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSendMessage()
    }
  }

  return (
    <div className="grid grid-cols-2 gap-6 h-[600px]">
      {/* Left Column: Chat Interface */}
      <div className="flex flex-col border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--bg-secondary)]">
        {/* Chat Header */}
        <div className="px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-primary)]">
          <div className="flex items-center gap-2">
            <div className="text-xl">🤖</div>
            <div>
              <div className="font-medium text-[var(--text-primary)]">Strategy Definition</div>
              <div className="text-xs text-[var(--text-muted)]">
                {currentStrategy ? 'Strategy Confirmed' : 'Conversation Mode'}
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-4xl mb-4">💬</div>
              <div className="text-lg font-medium text-[var(--text-primary)] mb-2">
                Start Strategy Discussion
              </div>
              <div className="text-sm text-[var(--text-muted)] max-w-sm">
                Chat with the agent to define your trading strategy. The agent will guide you through the process.
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] px-4 py-2 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)]'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                <div className="text-xs opacity-60 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {isWaiting && (
            <div className="flex items-center gap-2 text-[var(--text-muted)]">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
              </div>
              <span className="text-sm">Agent is thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        {!currentStrategy && (
          <div className="p-4 border-t border-[var(--border)]">
            {showConfirmButton ? (
              <div className="space-y-3">
                {/* Autonomously Editable Checkbox */}
                <label className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] cursor-pointer hover:bg-[var(--bg-tertiary)] transition-colors">
                  <input
                    type="checkbox"
                    checked={autonomouslyEditable}
                    onChange={(e) => setAutonomouslyEditable(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-[var(--border)] text-emerald-600 focus:ring-2 focus:ring-emerald-500"
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-[var(--text-primary)]">
                      Allow agent to modify strategy autonomously
                    </div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">
                      Advanced: Agent can update its own strategy based on performance and learnings
                    </div>
                  </div>
                </label>

                {/* Confirm Button */}
                <button
                  onClick={() => onConfirmStrategy(autonomouslyEditable)}
                  className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors"
                >
                  ✓ Confirm Strategy
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => onInputChange(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  disabled={isWaiting}
                />
                <button
                  onClick={onSendMessage}
                  disabled={!inputValue.trim() || isWaiting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            )}
          </div>
        )}

        {currentStrategy && (
          <div className="p-4 border-t border-[var(--border)] bg-emerald-500/10">
            <div className="text-sm text-emerald-600 dark:text-emerald-400">
              ✓ Strategy confirmed. Activate the agent to begin autonomous trading.
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Strategy Display */}
      <div className="border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--bg-secondary)]">
        <div className="px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-primary)]">
          <div className="font-medium text-[var(--text-primary)]">Strategy</div>
        </div>

        <div className="p-4 overflow-y-auto h-[calc(600px-57px)]">
          {!currentStrategy ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-4xl mb-4">📋</div>
              <div className="text-lg font-medium text-[var(--text-primary)] mb-2">
                No Strategy Yet
              </div>
              <div className="text-sm text-[var(--text-muted)] max-w-sm">
                Strategy will appear here after confirmation
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-[var(--text-primary)]">
                  {currentStrategy.content}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-[var(--border)] text-xs text-[var(--text-muted)] space-y-1">
                {currentStrategy.version && (
                  <div>Version: {currentStrategy.version}</div>
                )}
                {currentStrategy.last_updated_at && (
                  <div>Last updated: {new Date(currentStrategy.last_updated_at).toLocaleString()}</div>
                )}
                {currentStrategy.autonomously_editable !== undefined && (
                  <div>Autonomously editable: {currentStrategy.autonomously_editable ? 'Yes' : 'No'}</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
