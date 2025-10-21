'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { BotConfiguration } from '@/lib/api'
import { usePermissions } from '@/lib/permissions'

interface BotManagementMenuProps {
  bot: BotConfiguration
  onRename: (configId: string, newName: string) => void
  onDuplicate: (configId: string) => void
  onDelete: (configId: string) => void
  onResetAccount?: (configId: string) => void
  onDuplicateAsLive?: (configId: string) => void
  isBotAction: boolean
  hasUnsavedChanges?: boolean
}

export function BotManagementMenu({
  bot,
  onRename,
  onDuplicate,
  onDelete,
  onResetAccount,
  onDuplicateAsLive,
  isBotAction,
  hasUnsavedChanges = false
}: BotManagementMenuProps) {
  const { canAccess } = usePermissions()
  const [isOpen, setIsOpen] = useState(false)
  const [isRenamingLocal, setIsRenamingLocal] = useState(false)
  const [newName, setNewName] = useState(bot.config_name)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const isPaperBot = !bot.trading_mode || bot.trading_mode === 'paper'
  const canUseLiveTrading = canAccess('live_trading')

  // Cancel rename function
  const handleRenameCancel = useCallback(() => {
    setIsRenamingLocal(false)
    setNewName(bot.config_name)
  }, [bot.config_name])

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setShowDeleteConfirm(false)
        setShowResetConfirm(false)
        if (isRenamingLocal) {
          handleRenameCancel() // Automatically discard changes
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isRenamingLocal, handleRenameCancel])

  // Focus input when entering rename mode
  useEffect(() => {
    if (isRenamingLocal && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isRenamingLocal])

  const handleRename = () => {
    setIsRenamingLocal(true)
    setIsOpen(false)
  }

  const handleRenameSubmit = () => {
    const trimmedName = newName.trim()
    if (trimmedName && trimmedName !== bot.config_name) {
      onRename(bot.config_id, trimmedName)
    }
    setIsRenamingLocal(false)
  }

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true)
    setIsOpen(false)
  }

  const handleDeleteConfirm = () => {
    onDelete(bot.config_id)
    setShowDeleteConfirm(false)
  }

  const handleResetClick = () => {
    setShowResetConfirm(true)
    setIsOpen(false)
  }

  const handleResetConfirm = () => {
    onResetAccount?.(bot.config_id)
    setShowResetConfirm(false)
  }

  if (isRenamingLocal) {
    return (
      <div ref={menuRef} className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 shadow-lg min-w-64">
          <div className="text-xs text-[var(--text-primary)] mb-2">
            Rename Bot
          </div>
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRenameSubmit()
                if (e.key === 'Escape') handleRenameCancel()
              }}
              className="flex-1 bg-[var(--bg-primary)] border border-[var(--border)] rounded px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isBotAction}
              placeholder="Enter bot name"
            />
            <button
              onClick={handleRenameSubmit}
              disabled={isBotAction}
              className="px-3 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50 text-xs"
            >
              Save
            </button>
            <button
              onClick={handleRenameCancel}
              disabled={isBotAction}
              className="px-3 py-2 border border-[var(--border)] rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] text-xs"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (showDeleteConfirm) {
    return (
      <div ref={menuRef} className="absolute right-0 top-8 z-50 min-w-48 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] shadow-lg">
        <div className="p-3">
          <div className="text-xs text-[var(--text-primary)] mb-2">
            Delete &ldquo;{bot.config_name}&rdquo;?
          </div>
          <div className="text-xs text-[var(--text-muted)] mb-3">
            This action cannot be undone.
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleDeleteConfirm}
              disabled={isBotAction}
              className="flex-1 px-2 py-1 text-xs bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50"
            >
              {isBotAction ? 'Deleting...' : 'Delete'}
            </button>
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="flex-1 px-2 py-1 text-xs border border-[var(--border)] rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (showResetConfirm) {
    return (
      <div ref={menuRef} className="absolute right-0 top-8 z-50 min-w-56 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] shadow-lg">
        <div className="p-3">
          <div className="text-xs text-[var(--text-primary)] mb-2">
            Reset Trading Account?
          </div>
          <div className="text-xs text-[var(--text-muted)] mb-3">
            This will:
            <ul className="list-disc list-inside mt-1 space-y-0.5">
              <li>Close all open positions</li>
              <li>Reset balance to $10,000</li>
              <li>Clear all trading statistics</li>
            </ul>
            <div className="mt-2">
              Your bot configuration will not be affected. Trade history is preserved for analysis.
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleResetConfirm}
              disabled={isBotAction}
              className="flex-1 px-2 py-1 text-xs bg-amber-600 text-white rounded hover:bg-amber-700 disabled:opacity-50"
            >
              {isBotAction ? 'Resetting...' : 'Reset Account'}
            </button>
            <button
              onClick={() => setShowResetConfirm(false)}
              className="flex-1 px-2 py-1 text-xs border border-[var(--border)] rounded hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        aria-label="Bot actions"
      >
        ⋯
      </button>

      {isOpen && (
        <div className="absolute right-0 top-6 z-50 min-w-44 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] shadow-lg">
          <div className="py-1">
            <button
              onClick={handleRename}
              disabled={isBotAction || hasUnsavedChanges}
              className="w-full px-3 py-2 text-left text-xs text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
              title={hasUnsavedChanges ? "Finish editing configuration first" : undefined}
            >
              ✏️ Rename
            </button>
            <button
              onClick={() => {
                onDuplicate(bot.config_id)
                setIsOpen(false)
              }}
              disabled={isBotAction}
              className="w-full px-3 py-2 text-left text-xs text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              📋 Duplicate
            </button>
            {isPaperBot && onDuplicateAsLive && (
              <button
                onClick={() => {
                  if (canUseLiveTrading) {
                    onDuplicateAsLive(bot.config_id)
                    setIsOpen(false)
                  } else {
                    // TODO: Show upgrade modal
                    alert('Live trading requires Pro Plan')
                    setIsOpen(false)
                  }
                }}
                disabled={isBotAction}
                className="w-full px-3 py-2 text-left text-xs text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ⚡ Deploy Live Version
              </button>
            )}
            {onResetAccount && (
              <button
                onClick={handleResetClick}
                disabled={isBotAction}
                className="w-full px-3 py-2 text-left text-xs text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                🔄 Reset Account
              </button>
            )}
            <hr className="my-1 border-[var(--border)]" />
            <button
              onClick={handleDeleteClick}
              disabled={isBotAction}
              className="w-full px-3 py-2 text-left text-xs text-rose-400 hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  )
}