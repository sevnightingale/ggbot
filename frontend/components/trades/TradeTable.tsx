'use client'

import { useBotStore } from '@/store/bot'
import { cn } from '@/lib/utils/cn'
import { formatDistanceToNow } from 'date-fns'

export function TradeTable() {
  const { trades, isLoading } = useBotStore()

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-12 bg-charcoal-700/50 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  if (trades.length === 0) {
    return (
      <div className="text-center py-8 text-bone-400">
        <p>No active trades</p>
        <p className="text-sm mt-1">Start the bot to begin trading</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="grid grid-cols-6 gap-3 px-3 py-2 text-xs font-medium text-bone-400 border-b border-bone-200/10">
        <div>Symbol</div>
        <div>Side</div>
        <div>Entry</div>
        <div>Current</div>
        <div>P&L</div>
        <div>Time</div>
      </div>

      {/* Trade rows */}
      <div className="space-y-1">
        {trades.map((trade) => (
          <div
            key={trade.id}
            className="grid grid-cols-6 gap-3 px-3 py-3 bg-charcoal-700/30 hover:bg-charcoal-700/50 rounded-lg transition-colors cursor-pointer group"
          >
            <div className="font-medium text-bone-200">
              {trade.symbol}
            </div>
            
            <div className={cn(
              "text-sm font-medium px-2 py-1 rounded w-fit",
              trade.side === 'long' 
                ? "bg-status-success/20 text-status-success" 
                : "bg-status-error/20 text-status-error"
            )}>
              {trade.side?.toUpperCase() || 'N/A'}
            </div>
            
            <div className="text-sm text-bone-300">
              ${trade.entry_price?.toLocaleString() || 'N/A'}
            </div>
            
            <div className="text-sm text-bone-300">
              ${trade.current_price?.toLocaleString() || 'N/A'}
            </div>
            
            <div className={cn(
              "text-sm font-medium",
              trade.pnl > 0 ? "text-status-success" : trade.pnl < 0 ? "text-status-error" : "text-bone-300"
            )}>
              {trade.pnl > 0 ? '+' : ''}${trade.pnl?.toFixed(2) || '0.00'}
              {trade.pnl_percentage && (
                <span className="text-xs ml-1">
                  ({trade.pnl_percentage > 0 ? '+' : ''}{trade.pnl_percentage.toFixed(2)}%)
                </span>
              )}
            </div>
            
            <div className="text-xs text-bone-400">
              {trade.created_at ? formatDistanceToNow(new Date(trade.created_at), { addSuffix: true }) : 'N/A'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}