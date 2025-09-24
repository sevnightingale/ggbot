'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { ChevronDown, Search, X } from 'lucide-react'

interface SymbolSelectorProps {
  value: string
  onChange: (symbol: string) => void
  className?: string
}

interface SymbolData {
  platform: string[]
  display: string[]
  count: number
}

export function SymbolSelector({ value, onChange, className = '' }: SymbolSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [symbols, setSymbols] = useState<SymbolData>({ platform: [], display: [], count: 0 })
  const [loading, setLoading] = useState(false)
  const [filteredSymbols, setFilteredSymbols] = useState<{ platform: string[], display: string[] }>({ platform: [], display: [] })

  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  // Convert between formats (internal uses BTC/USDT, display shows BTC/USDT)
  const displayValue = value || 'BTC/USDT'

  // Load all symbols on component mount
  useEffect(() => {
    loadSymbols()
  }, [])

  const searchSymbols = useCallback(async (query: string) => {
    if (!query.trim()) {
      setFilteredSymbols({ platform: symbols.platform, display: symbols.display })
      return
    }

    try {
      const response = await fetch(`/api/v2/symbols/search/${encodeURIComponent(query)}`)
      const result = await response.json()

      if (result.status === 'success') {
        setFilteredSymbols({ platform: result.data.platform, display: result.data.display })
      }
    } catch (error) {
      console.error('Failed to search symbols:', error)
      // Fallback to client-side filtering
      const filtered = symbols.display.filter(symbol =>
        symbol.toLowerCase().includes(query.toLowerCase()) ||
        symbol.split('/')[0].toLowerCase().includes(query.toLowerCase())
      )
      const indices = filtered.map(display => symbols.display.indexOf(display))
      setFilteredSymbols({
        display: filtered,
        platform: indices.map(i => symbols.platform[i])
      })
    }
  }, [symbols])

  // Handle search/filter
  useEffect(() => {
    if (searchQuery.trim()) {
      searchSymbols(searchQuery)
    } else {
      setFilteredSymbols({ platform: symbols.platform, display: symbols.display })
    }
  }, [searchQuery, symbols, searchSymbols])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchRef.current) {
      setTimeout(() => searchRef.current?.focus(), 100)
    }
  }, [isOpen])

  const loadSymbols = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v2/symbols/supported')
      const result = await response.json()

      if (result.status === 'success') {
        setSymbols(result.data)
        setFilteredSymbols({ platform: result.data.platform, display: result.data.display })
      }
    } catch (error) {
      console.error('Failed to load symbols:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (displaySymbol: string) => {
    onChange(displaySymbol) // Use display format (BTC/USDT) for consistency
    setIsOpen(false)
    setSearchQuery('')
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Selected Value Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-trading)] focus:border-transparent flex items-center justify-between hover:bg-[var(--bg-tertiary)] transition-colors"
      >
        <span>{displayValue}</span>
        <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl shadow-2xl max-h-80 flex flex-col">
          {/* Search Input */}
          <div className="p-3 border-b border-[var(--border)]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
              <input
                ref={searchRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search symbols (e.g., BTC, ETH, SOL)"
                className="w-full pl-10 pr-8 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-trading)] focus:border-transparent"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-[var(--bg-tertiary)] rounded"
                >
                  <X className="h-3 w-3 text-[var(--text-muted)]" />
                </button>
              )}
            </div>
          </div>

          {/* Symbol List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-[var(--text-muted)]">
                Loading {symbols.count || 141} symbols...
              </div>
            ) : filteredSymbols.display.length > 0 ? (
              <div className="p-2">
                {filteredSymbols.display.map((displaySymbol) => {
                  const isSelected = displaySymbol === displayValue
                  const baseCurrency = displaySymbol.split('/')[0]

                  return (
                    <button
                      key={displaySymbol}
                      onClick={() => handleSelect(displaySymbol)}
                      className={`w-full p-3 rounded-lg text-left hover:bg-[var(--bg-tertiary)] transition-colors flex items-center justify-between ${
                        isSelected ? 'bg-[var(--agent-trading)]/20 text-[var(--agent-trading)]' : 'text-[var(--text-primary)]'
                      }`}
                    >
                      <div>
                        <div className="font-medium">{displaySymbol}</div>
                        <div className="text-xs text-[var(--text-muted)]">{baseCurrency}</div>
                      </div>
                      {isSelected && (
                        <div className="h-2 w-2 rounded-full bg-[var(--agent-trading)]"></div>
                      )}
                    </button>
                  )
                })}
              </div>
            ) : (
              <div className="p-4 text-center text-[var(--text-muted)]">
                {searchQuery ? `No symbols found for "${searchQuery}"` : 'No symbols available'}
              </div>
            )}
          </div>

          {/* Footer */}
          {!loading && (
            <div className="p-3 border-t border-[var(--border)] text-xs text-[var(--text-muted)] text-center">
              {searchQuery
                ? `${filteredSymbols.display.length} results`
                : `${symbols.count} supported symbols`
              }
            </div>
          )}
        </div>
      )}
    </div>
  )
}