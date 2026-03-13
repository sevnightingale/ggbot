'use client'

import React, { useState } from 'react'
import { Crown, ChevronDown, ChevronRight } from 'lucide-react'
import { ConfigData } from '@/lib/api'
import { usePermissions } from '@/lib/permissions'
import { UpgradeModal } from '@/components/UpgradeModal'

const ALL_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]

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
  configId: string
  configName?: string
  configType?: string
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
  // configId, configName, configType - unused, batched save handled by parent
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
  const [showTimeframes, setShowTimeframes] = useState(false)
  const [expandedIndicator, setExpandedIndicator] = useState<string | null>(null)
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

  // Get current global timeframes from technical_analysis config
  const currentTimeframes = configData?.extraction?.selected_data_sources?.technical_analysis?.timeframes || ALL_TIMEFRAMES
  const perIndicatorTimeframes = configData?.extraction?.selected_data_sources?.technical_analysis?.per_indicator_timeframes || {}

  // Check if an indicator has custom timeframe overrides
  const hasCustomTimeframes = (indicatorName: string): boolean => {
    return indicatorName in perIndicatorTimeframes
  }

  // Get effective timeframes for a specific indicator
  const getIndicatorTimeframes = (indicatorName: string): string[] => {
    return perIndicatorTimeframes[indicatorName] || currentTimeframes
  }

  // Handle data point toggle - batched save handled by parent
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
      timeframes: ALL_TIMEFRAMES
    }

    const isSelected = categoryData.data_points.includes(dataPoint.name)

    let updatedDataPoints: string[]
    if (isSelected) {
      // Remove data point
      updatedDataPoints = categoryData.data_points.filter(name => name !== dataPoint.name)
      // Collapse if this indicator was expanded
      if (expandedIndicator === dataPoint.name) {
        setExpandedIndicator(null)
      }
    } else {
      // Add data point
      updatedDataPoints = [...categoryData.data_points, dataPoint.name]
    }

    // Clean up per_indicator_timeframes when removing an indicator
    const updatedPerIndicator = { ...perIndicatorTimeframes }
    if (isSelected && dataPoint.name in updatedPerIndicator) {
      delete updatedPerIndicator[dataPoint.name]
    }
    // Remove per_indicator_timeframes key if empty
    const hasOverrides = Object.keys(updatedPerIndicator).length > 0

    // Build the category update
    const categoryUpdate = updatedDataPoints.length > 0 ? {
      data_points: updatedDataPoints,
      timeframes: categoryData.timeframes,
      ...(hasOverrides ? { per_indicator_timeframes: updatedPerIndicator } : {})
    } : undefined

    // Create update object
    const update: Partial<ConfigData> = {
      extraction: {
        ...(configData?.extraction || {}),
        selected_data_sources: {
          ...currentConfig,
          [category]: categoryUpdate
        }
      }
    }

    // Remove undefined categories
    if (updatedDataPoints.length === 0) {
      delete update.extraction!.selected_data_sources[category]
    }

    onUpdate(update)
  }

  const isAllTimeframes = ALL_TIMEFRAMES.every(tf => currentTimeframes.includes(tf))

  const applyTimeframes = (timeframes: string[]) => {
    const sources = configData?.extraction?.selected_data_sources
    if (!sources?.technical_analysis || !onUpdate) return
    const ta = sources.technical_analysis
    onUpdate({
      extraction: {
        ...(configData?.extraction || {}),
        selected_data_sources: {
          ...sources,
          technical_analysis: {
            ...ta,
            timeframes,
            // Keep per_indicator_timeframes if they exist
            ...(ta.per_indicator_timeframes ? { per_indicator_timeframes: ta.per_indicator_timeframes } : {})
          }
        }
      }
    })
  }

  const handleTimeframeToggle = (tf: string) => {
    if (currentTimeframes.includes(tf)) {
      if (currentTimeframes.length <= 1) return
      applyTimeframes(ALL_TIMEFRAMES.filter(t => currentTimeframes.includes(t) && t !== tf))
    } else {
      applyTimeframes(ALL_TIMEFRAMES.filter(t => currentTimeframes.includes(t) || t === tf))
    }
  }

  // Toggle a timeframe for a specific indicator
  const handleIndicatorTimeframeToggle = (indicatorName: string, tf: string) => {
    if (!onUpdate) return
    const sources = configData?.extraction?.selected_data_sources
    if (!sources?.technical_analysis) return

    const currentIndicatorTfs = getIndicatorTimeframes(indicatorName)
    let newTfs: string[]

    if (currentIndicatorTfs.includes(tf)) {
      // Don't allow removing the last timeframe
      if (currentIndicatorTfs.length <= 1) return
      newTfs = ALL_TIMEFRAMES.filter(t => currentIndicatorTfs.includes(t) && t !== tf)
    } else {
      newTfs = ALL_TIMEFRAMES.filter(t => currentIndicatorTfs.includes(t) || t === tf)
    }

    // If the new set matches global timeframes, remove the override
    const matchesGlobal = newTfs.length === currentTimeframes.length &&
      newTfs.every(t => currentTimeframes.includes(t))

    const updatedPerIndicator = { ...perIndicatorTimeframes }
    if (matchesGlobal) {
      delete updatedPerIndicator[indicatorName]
    } else {
      updatedPerIndicator[indicatorName] = newTfs
    }

    const hasOverrides = Object.keys(updatedPerIndicator).length > 0
    const ta = sources.technical_analysis

    onUpdate({
      extraction: {
        ...(configData?.extraction || {}),
        selected_data_sources: {
          ...sources,
          technical_analysis: {
            data_points: ta.data_points,
            timeframes: ta.timeframes,
            ...(hasOverrides ? { per_indicator_timeframes: updatedPerIndicator } : {})
          }
        }
      }
    })
  }

  // Reset indicator to use global timeframes
  const handleResetIndicatorTimeframes = (indicatorName: string) => {
    if (!onUpdate) return
    const sources = configData?.extraction?.selected_data_sources
    if (!sources?.technical_analysis) return

    const updatedPerIndicator = { ...perIndicatorTimeframes }
    delete updatedPerIndicator[indicatorName]

    const hasOverrides = Object.keys(updatedPerIndicator).length > 0
    const ta = sources.technical_analysis

    onUpdate({
      extraction: {
        ...(configData?.extraction || {}),
        selected_data_sources: {
          ...sources,
          technical_analysis: {
            data_points: ta.data_points,
            timeframes: ta.timeframes,
            ...(hasOverrides ? { per_indicator_timeframes: updatedPerIndicator } : {})
          }
        }
      }
    })
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
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
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
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {filteredDataPoints.length > 0 ? (
            filteredDataPoints.map(dataPoint => {
              const isSelected = selectedDataPoints.includes(dataPoint.name)
              const isPremium = dataPoint.requires_premium
              const hasAccess = !isPremium || hasPaidDataPoint(dataPoint.name)
              const isLocked = isPremium && !hasAccess
              const isExpanded = expandedIndicator === dataPoint.name
              const isTA = activeTab === 'technical_analysis'
              const hasCustom = isTA && hasCustomTimeframes(dataPoint.name)
              const indicatorTfs = isTA ? getIndicatorTimeframes(dataPoint.name) : []

              return (
                <div key={dataPoint.data_point_id} className="relative">
                  <div
                    className={`border transition-all rounded-xl overflow-hidden ${
                      isSelected
                        ? 'bg-[var(--agent-extraction)]/10 border-[var(--agent-extraction)] text-[var(--text-primary)]'
                        : isLocked
                          ? 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-muted)] opacity-60 hover:opacity-80'
                          : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--agent-extraction)] hover:bg-[var(--agent-extraction)]/5'
                    }`}
                  >
                    {/* Main card row */}
                    <div className="flex items-center p-3">
                      {/* Checkbox + label area — toggles indicator */}
                      <button
                        onClick={() => handleToggleDataPoint(dataPoint.data_point_id)}
                        className="flex items-center gap-3 flex-1 text-left"
                      >
                        <div className={`w-4 h-4 border-2 rounded flex-shrink-0 flex items-center justify-center ${
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
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium flex items-center gap-2">
                            {dataPoint.display_name}
                            {isLocked && <Crown className="h-3 w-3" />}
                            {isSelected && hasCustom && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--agent-extraction)]/20 text-[var(--agent-extraction)]">
                                {indicatorTfs.length} TF{indicatorTfs.length !== 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-[var(--text-muted)] mt-1">{dataPoint.description}</div>
                        </div>
                      </button>

                      {/* Expand chevron — only for selected TA indicators */}
                      {isSelected && isTA && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setExpandedIndicator(isExpanded ? null : dataPoint.name)
                          }}
                          className="ml-2 p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] transition-colors flex-shrink-0"
                          title="Customize timeframes for this indicator"
                        >
                          {isExpanded
                            ? <ChevronDown className="h-4 w-4 text-[var(--agent-extraction)]" />
                            : <ChevronRight className="h-4 w-4 text-[var(--text-muted)]" />
                          }
                        </button>
                      )}
                    </div>

                    {/* Expanded per-indicator timeframe selector */}
                    {isSelected && isTA && isExpanded && (
                      <div className="px-3 pb-3 pt-1 border-t border-[var(--border)]/50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">
                            {hasCustom ? 'Custom Timeframes' : 'Using Default Timeframes'}
                          </span>
                          {hasCustom && (
                            <button
                              onClick={() => handleResetIndicatorTimeframes(dataPoint.name)}
                              className="text-[10px] text-[var(--agent-extraction)] hover:underline"
                            >
                              Reset to Default
                            </button>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {ALL_TIMEFRAMES.map(tf => {
                            const isActive = indicatorTfs.includes(tf)
                            const isLastOne = isActive && indicatorTfs.length === 1
                            return (
                              <button
                                key={tf}
                                onClick={() => handleIndicatorTimeframeToggle(dataPoint.name, tf)}
                                disabled={isLastOne}
                                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                                  isActive
                                    ? 'bg-[var(--agent-extraction)]/30 text-[var(--agent-extraction)] border border-[var(--agent-extraction)]'
                                    : 'bg-transparent border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--agent-extraction)]'
                                } ${isLastOne ? 'opacity-50 cursor-not-allowed' : ''}`}
                              >
                                {tf}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
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

      {/* Timeframe Selector - only shown when TA indicators are selected (MI sources don't use timeframes) */}
      {configData?.extraction?.selected_data_sources?.technical_analysis?.data_points?.length && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
          <button
            onClick={() => setShowTimeframes(!showTimeframes)}
            className="w-full flex items-center justify-between text-sm font-medium text-[var(--text-primary)]"
          >
            <span>
              Default Timeframes: {isAllTimeframes ? `All (${ALL_TIMEFRAMES.length})` : `${currentTimeframes.length} selected`}
            </span>
            <ChevronDown className={`h-4 w-4 transition-transform ${showTimeframes ? 'rotate-180' : ''}`} />
          </button>
          {showTimeframes && (
            <>
              <div className="flex flex-wrap gap-2 mt-3">
                <button
                  onClick={() => applyTimeframes([...ALL_TIMEFRAMES])}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    isAllTimeframes
                      ? 'bg-[var(--agent-extraction)] text-white'
                      : 'bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--agent-extraction)]'
                  }`}
                >
                  All
                </button>
                {ALL_TIMEFRAMES.map(tf => {
                  const isActive = currentTimeframes.includes(tf)
                  const isLastOne = isActive && currentTimeframes.length === 1
                  return (
                    <button
                      key={tf}
                      onClick={() => handleTimeframeToggle(tf)}
                      disabled={isLastOne}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-[var(--agent-extraction)]/30 text-[var(--agent-extraction)] border border-[var(--agent-extraction)]'
                          : 'bg-transparent border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--agent-extraction)]'
                      } ${isLastOne ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {tf}
                    </button>
                  )
                })}
              </div>
              {Object.keys(perIndicatorTimeframes).length > 0 && (
                <div className="mt-2 text-[10px] text-[var(--text-muted)]">
                  Some indicators have custom timeframes. Expand them to see details.
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Upgrade Modal */}
      <UpgradeModal
        open={upgradeModalOpen}
        onOpenChange={setUpgradeModalOpen}
      />
    </div>
  )
}
