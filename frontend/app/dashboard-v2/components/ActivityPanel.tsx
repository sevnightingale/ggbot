'use client'

import React from 'react'
import { useBotActivity } from '../hooks/useBotActivity'

interface ActivityPanelProps {
  botId: string | null
  className?: string
}

interface DecisionHistoryItem {
  decision_id: string;
  symbol: string;
  action: string;
  confidence: number;
  reasoning: string;
  prompt?: string;
  market_data?: Record<string, unknown>;
  decision_data?: Record<string, unknown>;
  created_at: string;
  timestamp?: string;
}

export default function ActivityPanel({ botId, className = '' }: ActivityPanelProps) {
  const { activity, isLoading, error } = useBotActivity(botId)
  const [expandedReasoningIds, setExpandedReasoningIds] = React.useState<Set<string>>(new Set())
  const [selectedDecision, setSelectedDecision] = React.useState<DecisionHistoryItem | null>(null)

  const toggleReasoningExpansion = (tradeId: string) => {
    setExpandedReasoningIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tradeId)) {
        newSet.delete(tradeId)
      } else {
        newSet.add(tradeId)
      }
      return newSet
    })
  }

  if (error) {
    return (
      <div className={`activity-panel bg-charcoal-800  p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-bone-200 mb-4">Activity</h2>
        <div className="text-red-400">
          Failed to load activity data
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`activity-panel bg-charcoal-800  p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-bone-200 mb-4">Activity</h2>
        <div className="text-bone-400">
          Loading activity data...
        </div>
      </div>
    )
  }

  if (!botId) {
    return (
      <div className={`activity-panel bg-charcoal-800  p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-bone-200 mb-4">Activity</h2>
        <div className="text-bone-400">
          Select a bot to view activity
        </div>
      </div>
    )
  }

  return (
    <div className={`activity-panel bg-charcoal-800 corner-top-right corner-bottom-left p-6 max-w-full ${className}`}>
      <h2 className="text-xl font-semibold text-bone-200 mb-4">Activity</h2>
      <div className="gradient-divider mb-4"></div>
      
      {/* Live Positions - Rich Table */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-bone-300">Live Positions</h3>
          <span className="text-sm text-gray-500">
            {activity?.positions && activity.positions.length > 0 ? `${activity.positions.length} position${activity.positions.length !== 1 ? 's' : ''}` : 'No positions'}
          </span>
        </div>
        <div className="overflow-x-auto overflow-y-auto max-h-80">
          <table className="w-full min-w-0 text-xs">
            <thead className="text-gray-400 border-b border-gray-700">
              <tr>
                <th className="text-left py-1 pr-2">P&L</th>
                <th className="text-left py-1 px-1">Symbol</th>
                <th className="text-left py-1 px-1">Size</th>
                <th className="text-left py-1 px-1">Dir</th>
                <th className="text-left py-1 px-1">Entry</th>
                <th className="text-left py-1 px-1">Price</th>
                <th className="text-left py-1 pl-1">Time</th>
              </tr>
            </thead>
            <tbody>
              {!activity?.positions || activity.positions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-500">
                    {isLoading ? (
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-6 h-6 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
                        <span>Loading positions...</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-2xl">📊</span>
                        <span>No active positions</span>
                        <span className="text-xs">Start your bot to begin trading</span>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                activity.positions.map((position, index) => {
                  const tradeId = position.id || `position-${index}`
                  const isExpanded = expandedReasoningIds.has(tradeId)
                  
                  return (
                    <React.Fragment key={tradeId}>
                      <tr 
                        className={`${index % 2 === 1 ? 'bg-gray-600 bg-opacity-30' : ''} cursor-pointer hover:bg-gray-500/30 transition-colors`}
                        onClick={() => toggleReasoningExpansion(tradeId)}
                      >
                        <td className={`py-1 pr-2 ${(position.unrealizedPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(position.unrealizedPnL || 0) >= 0 ? '+' : ''}{(position.unrealizedPnL || 0).toFixed(0)}
                        </td>
                        <td className="py-1 px-1 text-bone-200">{(position.symbol || '').replace('/USDT', '')}</td>
                        <td className="py-1 px-1 text-gray-400">{position.size || 0}</td>
                        <td className={`py-1 px-1 ${position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                          {(position.side || '').slice(0, 1)}
                        </td>
                        <td className="py-1 px-1 text-gray-400">{(position.entryPrice || 0).toFixed(3)}</td>
                        <td className="py-1 px-1 text-gray-400">{(position.currentPrice || 0).toFixed(3)}</td>
                        <td className="py-1 pl-1 text-gray-400 flex items-center justify-between">
                          {position.timeInTrade || '0m'}
                          <span className="text-agent-extraction ml-1">
                            {isExpanded ? '▼' : '▶'}
                          </span>
                        </td>
                      </tr>
                      
                      {/* AI Reasoning Expansion */}
                      {isExpanded && (
                        <tr className="bg-charcoal-600/50">
                          <td colSpan={7} className="p-3">
                            <div className="space-y-3">
                              <div className="flex items-center gap-2 border-b border-charcoal-600 pb-2">
                                <span className="text-lg">🧠</span>
                                <h4 className="text-xs text-agent-extraction font-medium">
                                  AI Analysis (Confidence: {position.confidence || 0}%)
                                </h4>
                              </div>
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                                <div>
                                  <div className="text-gray-400 mb-1">Signal Timeframe:</div>
                                  <div className="text-bone-200 text-xs">
                                    {position.signal_timeframe || "1h"}
                                  </div>
                                </div>
                                
                                <div>
                                  <div className="text-gray-400 mb-1">Volume Analysis:</div>
                                  <div className="text-bone-200 text-xs">
                                    {position.volume_analysis || "Volume confirmation completed"}
                                  </div>
                                </div>
                              </div>
                              
                              {position.reasoning_text && (
                                <div className="pt-2 border-t border-charcoal-700">
                                  <div className="text-gray-400 mb-1 text-xs">AI Reasoning:</div>
                                  <div className="text-bone-200 text-xs leading-relaxed max-h-20 overflow-y-auto">
                                    {position.reasoning_text}
                                  </div>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="gradient-divider mb-4"></div>

      {/* Recent Decisions */}
      <div>
        <h3 className="text-lg font-medium text-bone-300 mb-2">Recent Decisions</h3>
        {activity?.decisions && activity.decisions.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {activity.decisions.map((decision, index) => (
              <div 
                key={index} 
                className="bg-charcoal-700 p-3 rounded text-sm cursor-pointer hover:bg-charcoal-600/50 transition-colors"
                onClick={() => setSelectedDecision({
                  decision_id: decision.decision_id || `decision-${index}`,
                  symbol: decision.symbol || '',
                  action: decision.action || '',
                  confidence: decision.confidence || 0,
                  reasoning: decision.reasoning || '',
                  prompt: decision.prompt,
                  market_data: decision.market_data,
                  decision_data: decision.decision_data,
                  created_at: decision.created_at || decision.timestamp || new Date().toISOString()
                })}
              >
                <div className="flex justify-between items-center">
                  <span className="text-bone-300">
                    {new Date(decision.timestamp || decision.created_at || new Date()).toLocaleTimeString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${
                      decision.action === 'BUY' || decision.action === 'enter' ? 'text-green-400' :
                      decision.action === 'SELL' || decision.action === 'exit' ? 'text-red-400' : 'text-bone-400'
                    }`}>
                      {decision.action?.toUpperCase()}
                    </span>
                    <span className="text-agent-extraction">▶</span>
                  </div>
                </div>
                <div className="text-bone-400 mt-1 truncate">
                  {decision.reasoning || 'Analysis in progress...'}
                </div>
                {decision.confidence && (
                  <div className="text-bone-500 text-xs mt-1">
                    Confidence: {((decision.confidence || 0) * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-charcoal-700 p-3 rounded text-bone-400 text-sm">
            No recent decisions
          </div>
        )}
      </div>

      {/* Decision Detail Modal */}
      {selectedDecision && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-charcoal-700 max-w-4xl max-h-[90vh] overflow-y-auto w-full">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <span className="text-2xl">🧠</span>
                  <div>
                    <h2 className="text-xl text-bone-200 font-semibold">Decision Details</h2>
                    <p className="text-gray-400 text-sm">
                      {new Date(selectedDecision.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedDecision(null)}
                  className="text-gray-400 hover:text-bone-200 text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Decision Summary */}
              <div className="mb-6 p-4 bg-charcoal-600">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">Action</span>
                    <div className={`text-sm font-medium px-2 py-1 mt-1 inline-block ${
                      selectedDecision.action === 'enter' && selectedDecision.decision_data?.direction === 'LONG' ? 'bg-green-500/20 text-green-400' :
                      selectedDecision.action === 'enter' && selectedDecision.decision_data?.direction === 'SHORT' ? 'bg-red-500/20 text-red-400' :
                      selectedDecision.action === 'exit' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {selectedDecision.action === 'enter' 
                        ? `ENTER ${selectedDecision.decision_data?.direction || 'TRADE'}`
                        : selectedDecision.action.toUpperCase()}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Symbol</span>
                    <div className="text-bone-200 font-medium">{selectedDecision.symbol}</div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Confidence</span>
                    <div className="text-bone-200 font-medium">
                      {Math.round((selectedDecision.confidence || 0) * 100)}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Decision ID</span>
                    <div className="text-gray-400 text-xs font-mono">
                      {selectedDecision.decision_id.substring(0, 8)}...
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Reasoning */}
              <div className="mb-6">
                <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                  <span className="text-agent-decision">🤖</span>
                  AI Reasoning
                </h3>
                <div className="bg-charcoal-800 p-4">
                  <div className="text-bone-200 text-sm leading-relaxed whitespace-pre-wrap">
                    {selectedDecision.reasoning || 'No reasoning provided'}
                  </div>
                </div>
              </div>

              {/* Market Data Context */}
              {selectedDecision.market_data && (
                <div className="mb-6">
                  <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                    <span className="text-agent-extraction">📊</span>
                    Market Context
                  </h3>
                  <div className="bg-charcoal-800 p-4">
                    <pre className="text-xs text-gray-300 overflow-x-auto">
                      {JSON.stringify(selectedDecision.market_data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Decision Data */}
              {selectedDecision.decision_data && (
                <div className="mb-6">
                  <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                    <span className="text-agent-trading">⚡</span>
                    Decision Parameters
                  </h3>
                  <div className="bg-charcoal-800 p-4">
                    <pre className="text-xs text-gray-300 overflow-x-auto">
                      {JSON.stringify(selectedDecision.decision_data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* LLM Prompt */}
              {selectedDecision.prompt && (
                <div className="mb-6">
                  <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                    <span>💬</span>
                    LLM Prompt
                  </h3>
                  <div className="bg-charcoal-800 p-4">
                    <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
                      {selectedDecision.prompt}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}