'use client'

import { useState, useRef, useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ConversationMessage {
  role: string
  content: string
}

interface StrategyAdvisorPanelProps {
  configId: string
  botType: 'agent' | 'scheduled' | 'signal_validation'
  onConfigUpdate: () => void
  className?: string
}

/**
 * Inline Strategy Advisor chat panel
 *
 * Always visible at top of configuration interface.
 * AI can update config, user sees changes in forms below.
 * User can manually adjust forms, changes auto-save.
 */
export function StrategyAdvisorPanel({
  configId,
  botType,
  onConfigUpdate,
  className = ''
}: StrategyAdvisorPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to UI immediately
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])

    try {
      const baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      const response = await apiClient.authenticatedFetch(`${baseUrl}/api/v2/assistant/chat`, {
        method: 'POST',
        body: JSON.stringify({
          config_id: configId,
          bot_type: botType,
          message: userMessage,
          conversation_history: conversationHistory,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      // Add assistant response to UI
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ])

      // Update conversation history for next request
      setConversationHistory(data.conversation_history)

      // If config was updated, refresh parent component
      if (data.config_updated) {
        onConfigUpdate()
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={`flex flex-col rounded-2xl border border-[var(--accent)]/30 bg-[var(--bg-secondary)] ${className}`} style={{ height: '350px' }}>
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-[var(--border)] flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-[var(--accent)]" />
        <h3 className="font-semibold text-[var(--text-primary)]">
          Strategy Advisor
        </h3>
        <span className="text-xs text-[var(--text-muted)] ml-2">
          {botType === 'agent'
            ? 'Strategy Builder'
            : botType === 'scheduled'
            ? 'Config Helper'
            : 'Signal Validator'}
        </span>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="text-center text-[var(--text-muted)] mt-8">
            <Sparkles className="w-12 h-12 mx-auto mb-4 text-[var(--accent)] opacity-50" />
            <p className="text-sm">
              Hi! I can help you configure your trading bot.
            </p>
            <p className="text-xs mt-2">
              I&apos;ll update your settings as we chat - you&apos;ll see changes in the forms below.
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-[var(--accent)] text-[var(--bg-primary)]'
                  : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border)]'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">
                {msg.content}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg px-4 py-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 p-4 border-t border-[var(--border)]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me to configure your bot..."
            className="flex-1 px-4 py-2 border border-[var(--border)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
            disabled={loading}
            autoFocus
          />
          <Button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] font-medium px-6"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  )
}
