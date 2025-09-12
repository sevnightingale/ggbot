'use client'

import React from 'react'
import { useBotActivity } from '../hooks/useBotActivity'

interface ActivityPanelProps {
  botId: string | null
  className?: string
}

export default function ActivityPanel({ botId, className = '' }: ActivityPanelProps) {
  const { activity, isLoading, error } = useBotActivity(botId)

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
    <div className={`activity-panel bg-charcoal-800  p-6 ${className}`}>
      <h2 className="text-xl font-semibold text-bone-200 mb-4">Activity</h2>
      
      {/* Live Positions */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-bone-300 mb-2">Live Positions</h3>
        {activity?.positions && activity.positions.length > 0 ? (
          <div className="space-y-2">
            {activity.positions.map((position, index) => (
              <div key={index} className="bg-charcoal-700 p-3 rounded text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-bone-300">{position.symbol}</span>
                  <span className={`font-semibold ${
                    position.side === 'LONG' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {position.side}
                  </span>
                </div>
                <div className="flex justify-between text-bone-400 mt-1">
                  <span>Size: {position.size}</span>
                  <span className={
                    (position.unrealizedPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }>
                    P&L: ${position.unrealizedPnL?.toFixed(2) || '0.00'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-charcoal-700 p-3 rounded text-bone-400 text-sm">
            No active positions
          </div>
        )}
      </div>

      {/* Recent Decisions */}
      <div>
        <h3 className="text-lg font-medium text-bone-300 mb-2">Recent Decisions</h3>
        {activity?.decisions && activity.decisions.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {activity.decisions.map((decision, index) => (
              <div key={index} className="bg-charcoal-700 p-3 rounded text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-bone-300">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`font-semibold ${
                    decision.action === 'BUY' ? 'text-green-400' :
                    decision.action === 'SELL' ? 'text-red-400' : 'text-bone-400'
                  }`}>
                    {decision.action}
                  </span>
                </div>
                <div className="text-bone-400 mt-1">
                  {decision.reasoning || 'Analysis in progress...'}
                </div>
                {decision.confidence && (
                  <div className="text-bone-500 text-xs mt-1">
                    Confidence: {(decision.confidence * 100).toFixed(0)}%
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
    </div>
  )
}