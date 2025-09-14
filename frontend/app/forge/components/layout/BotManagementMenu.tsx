'use client'

import React, { useState, useRef, useEffect } from 'react'
import { BotConfiguration } from '@/lib/api'

interface BotManagementMenuProps {
  bot: BotConfiguration
  onRename: (configId: string, newName: string) => void
  onDuplicate: (configId: string) => void
  onDelete: (configId: string) => void
  isBotAction: boolean
}

export function BotManagementMenu({
  bot,
  onRename,
  onDuplicate,
  onDelete,
  isBotAction
}: BotManagementMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isRenamingLocal, setIsRenamingLocal] = useState(false)
  const [newName, setNewName] = useState(bot.config_name)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setShowDeleteConfirm(false)
        if (isRenamingLocal) {
          setIsRenamingLocal(false)
          setNewName(bot.config_name)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isRenamingLocal, bot.config_name])

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

  const handleRenameCancel = () => {
    setIsRenamingLocal(false)
    setNewName(bot.config_name)
  }

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true)
    setIsOpen(false)
  }

  const handleDeleteConfirm = () => {
    onDelete(bot.config_id)
    setShowDeleteConfirm(false)
  }

  if (isRenamingLocal) {
    return (
      <div className="flex items-center gap-1">
        <input
          ref={inputRef}
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleRenameSubmit()
            if (e.key === 'Escape') handleRenameCancel()
          }}
          className="flex-1 bg-[var(--bg-primary)] border border-[var(--border)] rounded px-2 py-1 text-xs text-[var(--text-primary)]"
          disabled={isBotAction}
        />
        <button
          onClick={handleRenameSubmit}
          disabled={isBotAction}
          className="text-xs text-emerald-400 hover:text-emerald-300 disabled:opacity-50"
        >
          ✓
        </button>
        <button
          onClick={handleRenameCancel}
          disabled={isBotAction}
          className="text-xs text-rose-400 hover:text-rose-300 disabled:opacity-50"
        >
          ✕
        </button>
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
        <div className="absolute right-0 top-6 z-50 min-w-32 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] shadow-lg">
          <div className="py-1">
            <button
              onClick={handleRename}
              disabled={isBotAction}
              className="w-full px-3 py-2 text-left text-xs text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Rename
            </button>
            <button
              onClick={() => {
                onDuplicate(bot.config_id)
                setIsOpen(false)
              }}
              disabled={isBotAction}
              className="w-full px-3 py-2 text-left text-xs text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Duplicate
            </button>
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