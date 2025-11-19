'use client'

import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api'
import ReactMarkdown from 'react-markdown'

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
    <div className={`flex flex-col rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] ${className}`} style={{ height: '500px' }}>
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
              {msg.role === 'assistant' ? (
                <div className="text-sm markdown-content">
                  <ReactMarkdown
                    components={{
                      p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                      li: ({children}) => <li className="text-sm">{children}</li>,
                      strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      code: ({children}) => <code className="bg-[var(--bg-primary)] px-1 py-0.5 rounded text-xs">{children}</code>,
                      h1: ({children}) => <h1 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h1>,
                      h2: ({children}) => <h2 className="text-sm font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                      h3: ({children}) => <h3 className="text-sm font-semibold mb-1 mt-2 first:mt-0">{children}</h3>,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="text-sm whitespace-pre-wrap">
                  {msg.content}
                </div>
              )}
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
