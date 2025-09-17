'use client'

import React from 'react'
import { Bot } from '@/store/botStore'

interface FloatingActionButtonsProps {
  currentBot: Bot
  className?: string
  onStart?: (config_id: string) => void
  onDelete?: (config_id: string) => void
  onManualTrigger?: (config_id: string) => void
  onAdd?: () => void
  demoStarted?: boolean
}

const FloatingActionButtons: React.FC<FloatingActionButtonsProps> = ({ 
  currentBot, 
  className = '',
  onStart,
  onDelete,
  onManualTrigger,
  onAdd,
  demoStarted = false
}) => {
  // Determine button states based on current bot
  // For ggbot-01, use demoStarted state instead of isActive before demo
  const isGgbot01 = currentBot.config_id === 'e249bb49-0455-4596-9657-09bf9e14ca14'
  const isActive = isGgbot01 ? demoStarted : currentBot.isActive
  const canDelete = !isActive // Can only delete inactive bots
  const canToggle = true // Can always toggle start/stop

  return (
    <div className={`floating-action-buttons ${className}`}>
      <div className="flex items-center gap-3 justify-center">
        
        {/* Start/Stop Toggle Button */}
        <button
          className={`floating-action-btn ${canToggle ? 'floating-action-enabled' : 'floating-action-disabled'}`}
          disabled={!canToggle}
          title={isActive ? 'Stop Bot' : 'Start Bot'}
          onClick={() => onStart?.(currentBot.config_id)}
        >
          {isActive ? (
            // Stop Icon (Pause/Square)
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            </svg>
          ) : (
            // Start Icon (Play Triangle)
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          )}
        </button>

        {/* Manual Trigger Button */}
        <button
          className="floating-action-btn floating-action-enabled"
          title="Manual Trigger (Test Run)"
          onClick={() => onManualTrigger?.(currentBot.config_id)}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7 2v11h3v9l7-12h-4l4-8z"/>
          </svg>
        </button>

        {/* Delete Button */}
        <button
          className={`floating-action-btn ${canDelete ? 'floating-action-enabled' : 'floating-action-disabled'}`}
          disabled={!canDelete}
          title="Delete Bot"
          onClick={() => onDelete?.(currentBot.config_id)}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 6v18h18v-18h-18zm5 14c0 .552-.448 1-1 1s-1-.448-1-1v-10c0-.552.448-1 1-1s1 .448 1 1v10zm5 0c0 .552-.448 1-1 1s-1-.448-1-1v-10c0-.552.448-1 1-1s1 .448 1 1v10zm5 0c0 .552-.448 1-1 1s-1-.448-1-1v-10c0-.552.448-1 1-1s1 .448 1 1v10zm4-18v2h-20v-2h5.711c.9 0 1.631-1.099 1.631-2h5.315c0 .901.73 2 1.631 2h5.712z"/>
          </svg>
        </button>

        {/* Add New ggbot Button */}
        <button
          className="floating-action-btn floating-action-enabled"
          title="Create New ggbot"
          onClick={() => onAdd?.()}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
        </button>

      </div>
    </div>
  )
}

export default FloatingActionButtons