'use client'

import { Star } from 'lucide-react'
import { Indicator, AVAILABLE_TIMEFRAMES, CATEGORY_COLORS, CATEGORY_LABELS } from './constants'
import { cn } from '@/lib/utils/cn'

interface IndicatorCardProps {
  indicator: Indicator
  selected: boolean
  selectedTimeframes: string[]
  onToggle: (selected: boolean) => void
  onTimeframeChange: (timeframes: string[]) => void
}

export function IndicatorCard({
  indicator,
  selected,
  selectedTimeframes,
  onToggle,
  onTimeframeChange
}: IndicatorCardProps) {
  const toggleTimeframe = (timeframe: string) => {
    if (selectedTimeframes.includes(timeframe)) {
      onTimeframeChange(selectedTimeframes.filter(tf => tf !== timeframe))
    } else {
      onTimeframeChange([...selectedTimeframes, timeframe])
    }
  }

  return (
    <div
      className={cn(
        "p-4 border rounded-lg transition-all duration-200",
        selected
          ? "bg-charcoal-700/70 border-bone-200/80 shadow-md"
          : "bg-charcoal-700/30 border-bone-200/40 hover:border-bone-200/60"
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {indicator.isPremium && (
              <Star size={16} className="text-yellow-400 fill-yellow-400" />
            )}
            <h4 className="font-medium text-bone-200">{indicator.label}</h4>
            <span className={cn(
              "text-xs px-2 py-0.5 rounded",
              CATEGORY_COLORS[indicator.category]
            )}>
              {CATEGORY_LABELS[indicator.category]}
            </span>
          </div>
          <p className="text-sm text-bone-400">{indicator.description}</p>
        </div>
        
        <label className="relative inline-flex items-center cursor-pointer ml-4">
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => onToggle(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-charcoal-600 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-agents-extraction"></div>
        </label>
      </div>

      {selected && (
        <div className="mt-3 pt-3 border-t border-bone-200/20">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-bone-400">Timeframes:</span>
            {AVAILABLE_TIMEFRAMES.map(tf => (
              <button
                key={tf.value}
                onClick={() => toggleTimeframe(tf.value)}
                className={cn(
                  "px-3 py-1 text-xs rounded-full border transition-colors",
                  selectedTimeframes.includes(tf.value)
                    ? "bg-agents-extraction/20 border-agents-extraction text-bone-200"
                    : "bg-charcoal-700 border-bone-200/40 text-bone-400 hover:border-bone-200/60"
                )}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}