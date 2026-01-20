'use client'

import { useState, useEffect, useRef } from 'react'
import { Sparkles, BarChart3, Wand2, AlertTriangle, TrendingUp, Target, Loader2 } from 'lucide-react'
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

interface AnalysisReport {
  config_id: string
  config_name: string
  trade_count: number
  basic_stats: {
    total_trades: number
    wins: number
    losses: number
    win_rate: number
    avg_win: number
    avg_loss: number
    risk_reward_ratio: number
    breakeven_winrate: number
    total_pnl: number
    largest_win: number
    largest_loss: number
  }
  direction_stats: Array<{
    side: string
    trades: number
    wins: number
    win_rate: number
    avg_pnl: number
    total_pnl: number
  }>
  confidence_calibration: Array<{
    range: string
    trades: number
    actual_win_rate: number
    expected_win_rate: number
    calibration_gap: number
    total_pnl: number
  }>
  exit_classifications: Array<{
    type: string
    trades: number
    win_rate: number
    avg_pnl: number
    total_pnl: number
  }>
  confirmation_patterns: Array<{
    pattern: string
    trades: number
    win_rate: number
    total_pnl: number
  }>
  risk_patterns: Array<{
    pattern: string
    trades: number
    win_rate: number
    total_pnl: number
  }>
  best_combinations: Array<{
    pattern: string
    trades: number
    win_rate: number
    total_pnl: number
  }>
  worst_combinations: Array<{
    pattern: string
    trades: number
    win_rate: number
    total_pnl: number
  }>
  insights: {
    critical_issues: Array<{ title: string; detail: string; impact: string }>
    positive_edges: Array<{ title: string; detail: string; impact: string }>
    recommendations: Array<{ title: string; detail: string; impact: string }>
  }
}

interface StrategyAdvisorPanelProps {
  configId: string
  botType: 'agent' | 'scheduled' | 'signal_validation'
  onConfigUpdate: () => void
  className?: string
}

const CREATE_STRATEGY_PROMPT = "I'd like help creating a trading strategy for my bot. Can you guide me through the process?"

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
  const [analysisReport, setAnalysisReport] = useState<AnalysisReport | null>(null)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [hasClosedTrades, setHasClosedTrades] = useState(false)
  const [checkingTrades, setCheckingTrades] = useState(true)

  // Ref for the scrollable messages container
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    if (messagesContainerRef.current) {
      // Small delay to ensure DOM has updated with new content
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
        }
      })
    }
  }, [messages, loading])

  // Check if bot has any closed trades on mount
  useEffect(() => {
    const checkClosedTrades = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const response = await apiClient.authenticatedFetch(
          `${baseUrl}/api/v2/bot/${configId}/account`
        )
        if (response.ok) {
          const data = await response.json()
          // Check if there's at least 1 closed trade (total_trades is nested under account)
          setHasClosedTrades((data.account?.total_trades || 0) > 0)
        }
      } catch (error) {
        console.error('Failed to check trade count:', error)
      } finally {
        setCheckingTrades(false)
      }
    }
    checkClosedTrades()
  }, [configId])

  const handleCreateStrategy = () => {
    // Set the prompt and trigger send
    setInput(CREATE_STRATEGY_PROMPT)
    // Use setTimeout to ensure state is updated before sending
    setTimeout(() => {
      sendMessageWithContent(CREATE_STRATEGY_PROMPT)
    }, 0)
  }

  const discussAnalysisWithAdvisor = () => {
    if (!analysisReport) return

    const { basic_stats, insights, direction_stats } = analysisReport

    // Build a concise summary for the advisor
    let summary = `I just analyzed my bot's performance. Here are the key findings:\n\n`
    summary += `**Performance:** ${basic_stats.win_rate}% win rate, $${basic_stats.total_pnl.toFixed(2)} total P&L, ${basic_stats.total_trades} trades\n`

    if (direction_stats.length > 0) {
      const dirSummary = direction_stats.map(d => `${d.side.toUpperCase()}: ${d.win_rate}% WR, $${d.total_pnl.toFixed(2)}`).join(' | ')
      summary += `**Direction:** ${dirSummary}\n`
    }

    if (insights.critical_issues.length > 0) {
      summary += `\n**Critical Issues:**\n`
      insights.critical_issues.forEach(issue => {
        summary += `- ${issue.title}: ${issue.detail}\n`
      })
    }

    if (insights.positive_edges.length > 0) {
      summary += `\n**Positive Edges:**\n`
      insights.positive_edges.forEach(edge => {
        summary += `- ${edge.title}: ${edge.detail}\n`
      })
    }

    if (insights.recommendations.length > 0) {
      summary += `\n**Recommendations:**\n`
      insights.recommendations.forEach(rec => {
        summary += `- ${rec.title}: ${rec.detail}\n`
      })
    }

    summary += `\nCan you help me address these findings and improve my bot's strategy?`

    // Hide analysis view and send the message
    setShowAnalysis(false)
    setInput(summary)
    setTimeout(() => {
      sendMessageWithContent(summary)
    }, 0)
  }

  const sendMessageWithContent = async (content: string) => {
    if (!content.trim() || loading) return

    setInput('')
    setLoading(true)
    setShowAnalysis(false)

    // Add user message to UI immediately
    setMessages((prev) => [...prev, { role: 'user', content }])

    try {
      const baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      const response = await apiClient.authenticatedFetch(`${baseUrl}/api/v2/assistant/chat`, {
        method: 'POST',
        body: JSON.stringify({
          config_id: configId,
          bot_type: botType,
          message: content,
          conversation_history: conversationHistory,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ])

      setConversationHistory(data.conversation_history)

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

  const fetchAnalysis = async () => {
    setAnalysisLoading(true)
    setAnalysisError(null)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      const response = await apiClient.authenticatedFetch(`${baseUrl}/api/v2/assistant/analyze/${configId}`)

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      if (!data.success) {
        setAnalysisError(data.message || 'Analysis failed')
        setAnalysisReport(null)
      } else {
        setAnalysisReport(data.report)
        setShowAnalysis(true)
      }
    } catch (error) {
      console.error('Analysis error:', error)
      setAnalysisError(error instanceof Error ? error.message : 'Failed to fetch analysis')
    } finally {
      setAnalysisLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    await sendMessageWithContent(input.trim())
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Render analysis report
  const renderAnalysisReport = () => {
    if (!analysisReport) return null

    const { basic_stats, insights, direction_stats, best_combinations, worst_combinations } = analysisReport

    return (
      <div className="space-y-4 text-sm">
        {/* Basic Stats Card */}
        <div className="bg-[var(--bg-primary)] rounded-lg p-4 border border-[var(--border)]">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Performance Overview
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[var(--text-muted)] text-xs">Win Rate</p>
              <p className="font-medium">{basic_stats.win_rate}%</p>
            </div>
            <div>
              <p className="text-[var(--text-muted)] text-xs">Total P&L</p>
              <p className={`font-medium ${basic_stats.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                ${basic_stats.total_pnl.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-[var(--text-muted)] text-xs">R:R Ratio</p>
              <p className="font-medium">{basic_stats.risk_reward_ratio}:1</p>
            </div>
            <div>
              <p className="text-[var(--text-muted)] text-xs">Trades</p>
              <p className="font-medium">{basic_stats.total_trades} ({basic_stats.wins}W/{basic_stats.losses}L)</p>
            </div>
          </div>
        </div>

        {/* Direction Stats */}
        {direction_stats.length > 0 && (
          <div className="bg-[var(--bg-primary)] rounded-lg p-4 border border-[var(--border)]">
            <h4 className="font-semibold mb-3">Direction Breakdown</h4>
            <div className="space-y-2">
              {direction_stats.map((ds, idx) => (
                <div key={idx} className="flex justify-between items-center">
                  <span className="uppercase text-xs font-medium">{ds.side}</span>
                  <span className="text-xs">
                    {ds.trades} trades, {ds.win_rate}% WR,
                    <span className={ds.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                      {' '}${ds.total_pnl.toFixed(2)}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Critical Issues */}
        {insights.critical_issues.length > 0 && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <h4 className="font-semibold mb-3 text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Critical Issues
            </h4>
            <div className="space-y-3">
              {insights.critical_issues.map((issue, idx) => (
                <div key={idx}>
                  <p className="font-medium text-red-300">{issue.title}</p>
                  <p className="text-xs text-[var(--text-muted)] mt-1">{issue.detail}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Positive Edges */}
        {insights.positive_edges.length > 0 && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
            <h4 className="font-semibold mb-3 text-green-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Positive Edges
            </h4>
            <div className="space-y-3">
              {insights.positive_edges.map((edge, idx) => (
                <div key={idx}>
                  <p className="font-medium text-green-300">{edge.title}</p>
                  <p className="text-xs text-[var(--text-muted)] mt-1">{edge.detail}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {insights.recommendations.length > 0 && (
          <div className="bg-[var(--accent)]/10 border border-[var(--accent)]/20 rounded-lg p-4">
            <h4 className="font-semibold mb-3 text-[var(--accent)] flex items-center gap-2">
              <Target className="w-4 h-4" />
              Recommendations
            </h4>
            <div className="space-y-3">
              {insights.recommendations.map((rec, idx) => (
                <div key={idx}>
                  <p className="font-medium">{rec.title}</p>
                  <p className="text-xs text-[var(--text-muted)] mt-1">{rec.detail}</p>
                  <p className="text-xs text-[var(--accent)] mt-1">Impact: {rec.impact}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Best Patterns */}
        {best_combinations.length > 0 && (
          <div className="bg-[var(--bg-primary)] rounded-lg p-4 border border-[var(--border)]">
            <h4 className="font-semibold mb-3">Best Pattern Combinations</h4>
            <div className="space-y-2">
              {best_combinations.slice(0, 3).map((p, idx) => (
                <div key={idx} className="text-xs">
                  <p className="font-mono text-[var(--text-muted)]">{p.pattern}</p>
                  <p className="text-green-400">{p.trades} trades, {p.win_rate}% WR, ${p.total_pnl.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Worst Patterns */}
        {worst_combinations.length > 0 && (
          <div className="bg-[var(--bg-primary)] rounded-lg p-4 border border-[var(--border)]">
            <h4 className="font-semibold mb-3">Patterns to Avoid</h4>
            <div className="space-y-2">
              {worst_combinations.slice(0, 3).map((p, idx) => (
                <div key={idx} className="text-xs">
                  <p className="font-mono text-[var(--text-muted)]">{p.pattern}</p>
                  <p className="text-red-400">{p.trades} trades, {p.win_rate}% WR, ${p.total_pnl.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={discussAnalysisWithAdvisor}
          className="w-full"
        >
          Discuss with Strategy Advisor
        </Button>
      </div>
    )
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
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
      >
        {/* Show analysis report if available and toggled */}
        {showAnalysis && analysisReport ? (
          renderAnalysisReport()
        ) : (
          <>
            {/* Empty state with action buttons */}
            {messages.length === 0 && (
              <div className="text-center mt-4">
                <Sparkles className="w-10 h-10 mx-auto mb-3 text-[var(--accent)] opacity-50" />
                <p className="text-sm text-[var(--text-muted)] mb-4">
                  {hasClosedTrades
                    ? "How can I help you improve your bot?"
                    : "Let's create a trading strategy for your bot."}
                </p>

                {/* Action buttons - show based on bot state */}
                {!checkingTrades && (
                  <div className={`flex ${hasClosedTrades ? 'gap-3' : ''} justify-center mb-4`}>
                    {/* Always show Create Strategy */}
                    <button
                      onClick={handleCreateStrategy}
                      disabled={loading || analysisLoading}
                      className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] transition-colors"
                    >
                      <Wand2 className="w-4 h-4 text-[var(--accent)]" />
                      <span>Create Strategy</span>
                    </button>

                    {/* Only show Analyze Performance if bot has closed trades */}
                    {hasClosedTrades && (
                      <button
                        onClick={fetchAnalysis}
                        disabled={loading || analysisLoading}
                        className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] transition-colors"
                      >
                        <BarChart3 className="w-4 h-4 text-[var(--accent)]" />
                        <span>Analyze Performance</span>
                      </button>
                    )}
                  </div>
                )}

                {analysisLoading && (
                  <div className="flex items-center justify-center gap-2 text-sm text-[var(--text-muted)]">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing performance...
                  </div>
                )}

                {analysisError && (
                  <p className="text-xs text-red-400 mt-2">{analysisError}</p>
                )}
              </div>
            )}

            {/* Chat messages */}
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
                      ? 'bg-[var(--accent)] text-[#0b0b0c]'
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
          </>
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
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[#0b0b0c] font-medium px-6"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  )
}
