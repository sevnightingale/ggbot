'use client'

import React, { useState, useEffect, useRef } from 'react'
import { ChevronLeft, ChevronRight, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Decision {
  decision_id: string
  config_id?: string
  symbol: string
  action: string
  confidence: number
  reasoning: string
  created_at: string
}

interface DecisionFeedProps {
  decisions?: Decision[]
  className?: string
}

export function DecisionFeed({ decisions = [], className = '' }: DecisionFeedProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [expandedDecisions, setExpandedDecisions] = useState<Set<string>>(new Set())
  const prevDecisionsRef = useRef<Decision[]>([])

  // Auto-advance to newest decision when new decisions arrive
  useEffect(() => {
    if (decisions.length > 0 && decisions.length > prevDecisionsRef.current.length) {
      // New decision arrived - advance to newest (index 0)
      setCurrentIndex(0)
    }
    prevDecisionsRef.current = decisions
  }, [decisions])

  if (decisions.length === 0) {
    return (
      <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Recent Decisions</h3>
        <div className="text-center py-8">
          <div className="text-[var(--text-muted)] mb-2">No decisions yet</div>
          <div className="text-sm text-[var(--text-muted)]">
            Activate your bot to see AI decision history
          </div>
        </div>
      </div>
    )
  }

  const currentDecision = decisions[currentIndex]

  const getActionIcon = (action: string) => {
    if (action?.toLowerCase().includes('long') || action?.toLowerCase().includes('buy')) {
      return <TrendingUp className="h-4 w-4" />
    } else if (action?.toLowerCase().includes('short') || action?.toLowerCase().includes('sell')) {
      return <TrendingDown className="h-4 w-4" />
    }
    return <Minus className="h-4 w-4" />
  }

  const getActionColor = (action: string) => {
    if (action?.toLowerCase().includes('long') || action?.toLowerCase().includes('buy')) {
      return 'text-[var(--success)]'
    } else if (action?.toLowerCase().includes('short') || action?.toLowerCase().includes('sell')) {
      return 'text-[var(--danger)]'
    }
    return 'text-[var(--text-muted)]'
  }

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const then = new Date(timestamp)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    return new Date(timestamp).toLocaleDateString()
  }

  const truncateReasoning = (reasoning: string, maxLength: number = 150) => {
    if (reasoning.length <= maxLength) return reasoning
    return reasoning.substring(0, maxLength).trim() + '...'
  }

  const toggleExpanded = (decisionId: string) => {
    const newExpanded = new Set(expandedDecisions)
    if (newExpanded.has(decisionId)) {
      newExpanded.delete(decisionId)
    } else {
      newExpanded.add(decisionId)
    }
    setExpandedDecisions(newExpanded)
  }

  const goToPrevious = () => {
    setCurrentIndex(prev => prev > 0 ? prev - 1 : decisions.length - 1)
  }

  const goToNext = () => {
    setCurrentIndex(prev => prev < decisions.length - 1 ? prev + 1 : 0)
  }

  return (
    <div className={`rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Recent Decisions</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={goToPrevious}
            className="p-1 rounded-full hover:bg-[var(--bg-tertiary)] transition-colors"
            disabled={decisions.length <= 1}
          >
            <ChevronLeft className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
          <button
            onClick={goToNext}
            className="p-1 rounded-full hover:bg-[var(--bg-tertiary)] transition-colors"
            disabled={decisions.length <= 1}
          >
            <ChevronRight className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>
      </div>

      {/* Decision Card */}
      <div className="border border-[var(--border)] rounded-xl p-4 bg-[var(--bg-primary)]">
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <div className={`flex items-center gap-1 ${getActionColor(currentDecision.action)}`}>
            {getActionIcon(currentDecision.action)}
            <span className="font-semibold text-sm uppercase">
              {currentDecision.action}
            </span>
          </div>
          <span className="text-[var(--text-secondary)]">•</span>
          <span className="text-[var(--text-secondary)] font-medium">
            {currentDecision.symbol}
          </span>
          <span className="text-[var(--text-secondary)]">•</span>
          <span className="text-[var(--text-primary)] font-semibold">
            {Math.round(currentDecision.confidence * 100)}%
          </span>
          <div className="ml-auto text-xs text-[var(--text-muted)]">
            {getTimeAgo(currentDecision.created_at)}
          </div>
        </div>

        {/* Reasoning */}
        <div className="text-[var(--text-secondary)] text-sm leading-relaxed">
          {expandedDecisions.has(currentDecision.decision_id) ? (
            <div>
              {currentDecision.reasoning}
              <button
                onClick={() => toggleExpanded(currentDecision.decision_id)}
                className="block mt-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-xs"
              >
                Show less ↑
              </button>
            </div>
          ) : (
            <div>
              {truncateReasoning(currentDecision.reasoning)}
              {currentDecision.reasoning.length > 150 && (
                <button
                  onClick={() => toggleExpanded(currentDecision.decision_id)}
                  className="block mt-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-xs"
                >
                  Show more ↓
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Dots Indicator */}
      {decisions.length > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          {decisions.slice(0, 5).map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`h-2 w-2 rounded-full transition-colors ${
                index === currentIndex
                  ? 'bg-[var(--text-primary)]'
                  : 'bg-[var(--text-muted)] hover:bg-[var(--text-secondary)]'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  )
}