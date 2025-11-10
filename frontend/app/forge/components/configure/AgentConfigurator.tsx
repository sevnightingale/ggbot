'use client'

import React, { useEffect, useRef } from 'react'
import { Send, Bot, MessageSquare, PlayCircle } from 'lucide-react'

interface Message {
  role: 'user' | 'agent'
  content: string
  timestamp: string
}

interface AgentConfiguratorProps {
  messages: Message[]
  inputValue: string
  isWaiting: boolean
  strategyContent: string
  onSendMessage: () => void
  onInputChange: (value: string) => void
  onStrategyChange: (content: string) => void
  onStartAgent: () => void
  agentStarted: boolean
}

export function AgentConfigurator({
  messages,
  inputValue,
  isWaiting,
  strategyContent,
  onSendMessage,
  onInputChange,
  onStrategyChange,
  onStartAgent,
  agentStarted
}: AgentConfiguratorProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  const handleStrategyTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    onStrategyChange(newValue)
  }

  return (
    <div className="grid grid-cols-2 gap-6 h-[600px]">
      {/* Left Column: Chat Interface */}
      <div className="flex flex-col border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--bg-secondary)]">
        {/* Chat Header */}
        <div className="px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-primary)]">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-[var(--accent)]" />
            <div>
              <div className="font-medium text-[var(--text-primary)]">Strategy Builder</div>
              <div className="text-xs text-[var(--text-muted)]">
                {agentStarted ? 'Agent Active' : 'Chat Inactive'}
              </div>
            </div>
          </div>
        </div>

        {/* Messages or Empty State */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!agentStarted && messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <MessageSquare className="h-16 w-16 text-[var(--text-muted)] mb-4" />
              <div className="text-lg font-medium text-[var(--text-primary)] mb-2">
                Strategy Builder Agent
              </div>
              <div className="text-sm text-[var(--text-muted)] max-w-sm mb-6">
                Start the AI agent to collaboratively build your trading strategy. You can edit the strategy manually on the right, or chat with the agent to make changes.
              </div>
              <button
                onClick={onStartAgent}
                className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <PlayCircle className="h-5 w-5" />
                Start Strategy Builder
              </button>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-[var(--accent)] text-[#edebe7]'
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
            </>
          )}
        </div>

        {/* Input Area - Show only when agent is started */}
        {agentStarted && (
          <div className="p-4 border-t border-[var(--border)]">
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
          </div>
        )}
      </div>

      {/* Right Column: Editable Strategy */}
      <div className="flex flex-col border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--bg-secondary)]">
        <div className="px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-primary)]">
          <div className="font-medium text-[var(--text-primary)]">Trading Strategy</div>
          <div className="text-xs text-[var(--text-muted)] mt-0.5">
            Auto-saves as you type
          </div>
        </div>

        <div className="flex-1 p-4 overflow-hidden">
          <textarea
            value={strategyContent}
            onChange={handleStrategyTextChange}
            placeholder="Define your trading strategy here... Or use the Strategy Builder agent to help you create one."
            className="w-full h-full p-4 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none font-mono text-sm"
          />
        </div>
      </div>
    </div>
  )
}
