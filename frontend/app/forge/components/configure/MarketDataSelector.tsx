'use client'

import React, { useState } from 'react'
import { Crown } from 'lucide-react'
import { ConfigData } from '@/lib/api'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'

// Types based on database schema
interface DataPoint {
  data_point_id: string
  name: string
  display_name: string
  description: string
  requires_premium: boolean
  enabled: boolean
  sort_order: number
}

interface DataSource {
  source_id: string
  name: string
  display_name: string
  description: string
  enabled: boolean
  requires_premium: boolean
  data_points: DataPoint[]
}

interface MarketDataSelectorProps {
  configData?: ConfigData
  dataSources?: DataSource[]
  activeTab?: string
  searchTerm?: string
  onUpdate?: (updates: Partial<ConfigData>) => void
  onTabChange?: (tab: string) => void
  onSearchChange?: (term: string) => void
  className?: string
}

export function MarketDataSelector({
  configData,
  dataSources = [],
  activeTab = 'technical_analysis',
  searchTerm = '',
  onUpdate,
  onTabChange,
  onSearchChange,
  className = ''
}: MarketDataSelectorProps) {
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const { hasPaidDataPoint } = usePermissions()

  // Get selected data points from config (derived state)
  const selectedDataPoints: string[] = []
  if (configData?.extraction?.selected_data_sources) {
    Object.values(configData.extraction.selected_data_sources).forEach(source => {
      if (source?.data_points) {
        selectedDataPoints.push(...source.data_points)
      }
    })
  }

  // Get active data source
  const activeDataSource = dataSources.find(source => source.name === activeTab)

  // Filter data points by search term
  const filteredDataPoints = activeDataSource?.data_points.filter(point =>
    !searchTerm ||
    point.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    point.description.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  // Handle data point toggle
  const handleToggleDataPoint = (dataPointId: string) => {
    if (!onUpdate || !activeDataSource) return

    const dataPoint = activeDataSource.data_points.find(p => p.data_point_id === dataPointId)
    if (!dataPoint) return

    // Check if this is a premium data point and user doesn't have access
    if (dataPoint.requires_premium && !hasPaidDataPoint(dataPoint.name)) {
      setUpgradeModalOpen(true)
      return
    }

    const currentConfig = configData?.extraction?.selected_data_sources || {}
    const category = activeDataSource.name as keyof typeof currentConfig
    const categoryData = currentConfig[category] || {
      data_points: [],
      timeframes: ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    }

    // Always use all 7 timeframes for technical analysis
    const allTimeframes = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]

    const isSelected = categoryData.data_points.includes(dataPoint.name)

    let updatedDataPoints: string[]
    if (isSelected) {
      // Remove data point
      updatedDataPoints = categoryData.data_points.filter(name => name !== dataPoint.name)
    } else {
      // Add data point
      updatedDataPoints = [...categoryData.data_points, dataPoint.name]
    }

    // Create update object
    const update: Partial<ConfigData> = {
      extraction: {
        ...(configData?.extraction || {}),  // Guard: fallback to empty object
        selected_data_sources: {
          ...currentConfig,
          [category]: updatedDataPoints.length > 0 ? {
            data_points: updatedDataPoints,
            timeframes: allTimeframes
          } : undefined
        }
      }
    }

    // Remove undefined categories
    if (updatedDataPoints.length === 0) {
      delete update.extraction!.selected_data_sources[category]
    }

    onUpdate(update)
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Selected Summary */}
      {selectedDataPoints.length > 0 && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
          <div className="text-sm font-medium text-[var(--text-primary)] mb-3">
            Selected Indicators ({selectedDataPoints.length})
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedDataPoints.map(pointName => (
              <span
                key={pointName}
                className="px-2 py-1 rounded-md bg-[var(--agent-extraction)]/20 text-[var(--agent-extraction)] text-xs border border-[var(--agent-extraction)]/30"
              >
                {pointName}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Data Sources Section */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Data Sources
        </h3>

        {/* Tab Navigation */}
        <div className="flex gap-1 flex-wrap mb-4 border-b border-[var(--border)]">
          {dataSources.map(source => (
            <button
              key={source.source_id}
              onClick={() => onTabChange?.(source.name)}
              className={`px-3 py-2 text-xs transition-colors border-b-2 ${
                activeTab === source.name
                  ? 'border-[var(--agent-extraction)] text-[var(--agent-extraction)] bg-[var(--agent-extraction)]/5'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              {source.display_name}
            </button>
          ))}
        </div>

        {/* Search Bar */}
        {activeDataSource && activeDataSource.data_points.length > 0 && (
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search indicators..."
              value={searchTerm}
              onChange={(e) => onSearchChange?.(e.target.value)}
              className="w-full p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--agent-extraction)] focus:border-transparent"
            />
          </div>
        )}

        {/* Data Points Grid */}
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {filteredDataPoints.length > 0 ? (
            filteredDataPoints.map(dataPoint => {
              const isSelected = selectedDataPoints.includes(dataPoint.name)
              const isPremium = dataPoint.requires_premium
              const hasAccess = !isPremium || hasPaidDataPoint(dataPoint.name)
              const isLocked = isPremium && !hasAccess

              return (
                <div key={dataPoint.data_point_id} className="relative">
                  <button
                    onClick={() => handleToggleDataPoint(dataPoint.data_point_id)}
                    className={`w-full text-left p-3 border transition-all rounded-xl ${
                      isSelected
                        ? 'bg-[var(--agent-extraction)]/10 border-[var(--agent-extraction)] text-[var(--text-primary)]'
                        : isLocked
                          ? 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-muted)] opacity-60 hover:opacity-80'
                          : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--agent-extraction)] hover:bg-[var(--agent-extraction)]/5'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                          isSelected
                            ? 'bg-[var(--agent-extraction)] border-[var(--agent-extraction)]'
                            : 'border-[var(--border)]'
                        }`}>
                          {isSelected && (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="text-white">
                              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                            </svg>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium flex items-center gap-2">
                            {dataPoint.display_name}
                            {isLocked && <Crown className="h-3 w-3" />}
                          </div>
                          <div className="text-xs text-[var(--text-muted)] mt-1">{dataPoint.description}</div>
                        </div>
                      </div>
                    </div>
                  </button>
                </div>
              )
            })
          ) : (
            // Coming Soon message for data sources without data points
            <div className="text-center py-12">
              <div className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg p-6 max-w-sm mx-auto">
                <div className="text-amber-500 text-sm font-medium mb-2">
                  {activeDataSource?.display_name} - Coming Soon
                </div>
                <div className="text-[var(--text-muted)] text-xs mb-4">
                  {activeTab === 'fundamental_analysis' && 'Financial metrics, earnings data, and company fundamentals'}
                  {activeTab === 'sentiment_and_trends' && 'Social media sentiment analysis and trending topics'}
                  {activeTab === 'news_and_regulations' && 'Breaking news analysis and regulatory updates'}
                  {activeTab === 'onchain_analytics' && 'Blockchain metrics, whale movements, and on-chain data'}
                </div>
                <div className="text-xs text-[var(--text-muted)]">
                  We&apos;re working hard to bring you these advanced data sources
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </div>
  )
}