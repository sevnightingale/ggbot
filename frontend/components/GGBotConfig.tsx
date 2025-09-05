'use client'

import React from 'react'
import { Bot } from '@/store/botStore'
import { apiClient, ConfigData, DataSource, DataPoint, createDefaultConfigData, UserProfile, BotConfiguration } from '@/lib/api'

interface GGBotConfigProps {
  bot: Bot | null
  isOpen: boolean
  onClose: () => void
  onConfigSaved?: (configId: string) => void
}

// Analysis frequency options
const frequencyOptions = [
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '1d', label: '1 day' },
  { value: '1w', label: '1 week' }
]


// Trading pairs data - will eventually be dynamic
const tradingPairs = {
  popular: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT'],
  all: [
    'AAVE/USDT', 'ADA/USDT', 'ALGO/USDT', 'APT/USDT', 'ARB/USDT', 'ATOM/USDT', 'AVAX/USDT',
    'AXS/USDT', 'BAL/USDT', 'BCH/USDT', 'BNB/USDT', 'BTC/USDT', 'CAKE/USDT', 'CHZ/USDT',
    'COMP/USDT', 'CRV/USDT', 'DOT/USDT', 'DYDX/USDT', 'EGLD/USDT', 'ENJ/USDT', 'EOS/USDT',
    'ETC/USDT', 'ETH/USDT', 'FIL/USDT', 'FLOW/USDT', 'FTM/USDT', 'GALA/USDT', 'GMT/USDT',
    'GRT/USDT', 'HBAR/USDT', 'ICP/USDT', 'IMX/USDT', 'INJ/USDT', 'JUP/USDT', 'KSM/USDT',
    'LINK/USDT', 'LRC/USDT', 'LTC/USDT', 'MANA/USDT', 'MATIC/USDT', 'MINA/USDT', 'MKR/USDT',
    'NEAR/USDT', 'NEO/USDT', 'OP/USDT', 'PYTH/USDT', 'QNT/USDT', 'RNDR/USDT', 'ROSE/USDT',
    'RUNE/USDT', 'SAND/USDT', 'SEI/USDT', 'SHIB/USDT', 'SNX/USDT', 'SOL/USDT', 'STX/USDT',
    'SUI/USDT', 'SUSHI/USDT', 'TIA/USDT', 'TRX/USDT', 'UNI/USDT', 'VET/USDT', 'WLD/USDT',
    'WOO/USDT', 'XLM/USDT', 'XRP/USDT', 'XTZ/USDT', 'ZIL/USDT', 'ZRX/USDT'
  ].sort()
}

// Position sizing methods that map to backend enums
const positionSizingMethods = [
  { value: 'fixed_usd', label: 'Fixed Amount', description: 'Fixed USD amount per trade' },
  { value: 'account_percentage', label: 'Account Percentage', description: 'Percentage of account balance' },
  { value: 'confidence_based', label: 'Confidence-Based', description: 'Position size based on AI confidence' }
]

// Exchange options
const exchangeOptions = [
  { value: 'binance', label: 'Binance' },
  { value: 'coinbase', label: 'Coinbase' },
  { value: 'kraken', label: 'Kraken' },
  { value: 'bybit', label: 'Bybit' }
]

interface DataSourceSectionProps {
  dataSources: DataSource[]
  selectedDataPoints: string[]
  onToggleDataPoint: (dataPointId: string) => void
  isLoading: boolean
}

const DataSourceSection: React.FC<DataSourceSectionProps> = ({
  dataSources,
  selectedDataPoints,
  onToggleDataPoint,
  isLoading
}) => {
  const [searchTerm, setSearchTerm] = React.useState('')

  const filteredDataSources = React.useMemo(() => {
    if (!searchTerm) return dataSources
    
    return dataSources.map(source => ({
      ...source,
      data_points: source.data_points.filter(point =>
        point.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        point.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    })).filter(source => source.data_points.length > 0)
  }, [dataSources, searchTerm])

  const canAccessDataPoint = (dataPoint: DataPoint): boolean => {
    return dataPoint.has_access
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-400">Loading data sources...</div>
      </div>
    )
  }

  return (
    <div>
      {/* Header and Search */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs text-gray-400 font-medium">DATA POINT SELECTION</h4>
        <span className="text-footnote text-gray-400">{selectedDataPoints.length} selected</span>
      </div>
      
      <div className="flex gap-4 mb-4">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search data points..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agent-extraction focus:outline-none transition-colors"
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-gray-400">
              <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Data Sources Content */}
      <div className="space-y-6 max-h-96 overflow-y-auto">
        {filteredDataSources.map(source => (
          <div key={source.source_id}>
            <h5 className="text-xs text-bone-200 font-medium mb-3 bg-charcoal-800 px-3 py-2 border-l-2 border-agent-extraction">
              {source.name.toUpperCase()}
            </h5>
            <div className="space-y-2">
              {source.data_points.map(dataPoint => {
                const isSelected = selectedDataPoints.includes(dataPoint.data_point_id)
                const canAccess = canAccessDataPoint(dataPoint)
                const isLocked = dataPoint.is_locked
                
                return (
                  <div key={dataPoint.data_point_id} className="relative">
                    <button
                      onClick={() => canAccess && onToggleDataPoint(dataPoint.data_point_id)}
                      disabled={isLocked}
                      className={`w-full text-left p-3 border transition-colors relative ${
                        isSelected && canAccess
                          ? 'bg-agent-extraction/10 border-agent-extraction text-bone-200'
                          : isLocked
                          ? 'bg-charcoal-800/50 border-charcoal-700 text-gray-600 cursor-not-allowed'
                          : 'bg-charcoal-800 border-charcoal-700 text-bone-200 hover:border-agent-extraction hover:bg-agent-extraction/5'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                            isSelected && canAccess
                              ? 'bg-agent-extraction border-agent-extraction'
                              : 'border-gray-600'
                          }`}>
                            {isSelected && canAccess && (
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="text-charcoal-900">
                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                              </svg>
                            )}
                          </div>
                          <div>
                            <div className="text-footnote font-medium flex items-center gap-2">
                              {dataPoint.name}
                              {dataPoint.requires_premium && (
                                <span className="text-xs text-orange-400">Premium</span>
                              )}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">{dataPoint.description}</div>
                          </div>
                        </div>
                        {isLocked && (
                          <div className="text-orange-400">
                            🔒
                          </div>
                        )}
                      </div>
                    </button>
                    {isLocked && (
                      <div className="absolute inset-0 bg-charcoal-900/50 flex items-center justify-center">
                        <div className="bg-charcoal-800 border border-orange-700 px-3 py-2 rounded text-xs text-orange-400">
                          Upgrade required
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
        
        {filteredDataSources.length === 0 && (
          <div className="text-center py-8 text-gray-500 text-xs">
            No data sources found
          </div>
        )}
      </div>
    </div>
  )
}

const GGBotConfig: React.FC<GGBotConfigProps> = ({ bot, isOpen, onClose, onConfigSaved }) => {
  // UI State
  const [isEditingName, setIsEditingName] = React.useState(false)
  const [hasChanges, setHasChanges] = React.useState(false)
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(new Set(['extraction']))
  const [isVisible, setIsVisible] = React.useState(false)
  const [isMounted, setIsMounted] = React.useState(false)
  const [isLoading, setIsLoading] = React.useState(true)
  const [isSaving, setIsSaving] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  // Configuration State (single source of truth)
  const [configData, setConfigData] = React.useState<ConfigData>(createDefaultConfigData())
  const [botName, setBotName] = React.useState('')
  
  // Data loading state
  const [dataSources, setDataSources] = React.useState<DataSource[]>([])
  const [userProfile, setUserProfile] = React.useState<UserProfile | null>(null)
  const [dataSourcesLoading, setDataSourcesLoading] = React.useState(true)
  
  // UI state
  const [tradingAgentTab, setTradingAgentTab] = React.useState('risk-management')
  const [pairSearchTerm, setPairSearchTerm] = React.useState('')
  const [showPairDropdown, setShowPairDropdown] = React.useState(false)

  // Initialize component
  React.useEffect(() => {
    const initializeComponent = async () => {
      if (!isOpen) return
      
      console.log('GGBotConfig initializing component, isOpen:', isOpen)
      setIsLoading(true)
      setError(null)
      
      try {
        console.log('🔄 Starting API calls...')
        
        // Load data sources and user profile in parallel
        const [dataSourcesResponse, userProfileResponse] = await Promise.all([
          apiClient.getDataSourcesWithPoints(),
          apiClient.getUserProfile()
        ])
        
        console.log('✅ API calls successful:', { dataSourcesResponse, userProfileResponse })
        
        setDataSources(dataSourcesResponse)
        setUserProfile(userProfileResponse)
        
        // Load existing config if editing
        if (bot?.config_id) {
          const config = await apiClient.getConfig(bot.config_id)
          setConfigData(config.config_data)
          setBotName(config.config_name)
        } else {
          // New bot - use defaults
          setConfigData(createDefaultConfigData())
          setBotName('New Bot')
        }
        
      } catch (error) {
        console.error('Failed to initialize config:', error)
        setError(error instanceof Error ? error.message : 'Failed to load configuration')
      } finally {
        setIsLoading(false)
        setDataSourcesLoading(false)
      }
    }
    
    initializeComponent()
  }, [isOpen, bot?.config_id])

  // Helper function to update config data and trigger change detection
  const updateConfigData = (updater: (prev: ConfigData) => ConfigData) => {
    setConfigData(updater)
    setHasChanges(true)
  }

  // Get selected data points from config
  const selectedDataPoints = React.useMemo(() => {
    const technicalIndicators = configData.extraction.data_sources.technical_indicators || []
    const fundamentalAnalysis = configData.extraction.data_sources.fundamental_analysis || []
    const sentimentTrends = configData.extraction.data_sources.sentiment_and_trends || []
    const influencerKol = configData.extraction.data_sources.influencer_kol || []
    const newsRegulations = configData.extraction.data_sources.news_and_regulations || []
    const onchainAnalytics = configData.extraction.data_sources.onchain_analytics || []
    
    return [
      ...technicalIndicators,
      ...fundamentalAnalysis,
      ...sentimentTrends,
      ...influencerKol,
      ...newsRegulations,
      ...onchainAnalytics
    ]
  }, [configData])

  // Handle data point selection
  const handleToggleDataPoint = (dataPointId: string) => {
    updateConfigData(prev => {
      const newConfig = { ...prev }
      const configDataSources = newConfig.extraction.data_sources
      
      // Find which data source this data point belongs to
      const sourceInfo = dataSources.find(ds => 
        ds.data_points.some(dp => dp.data_point_id === dataPointId)
      )
      
      // Map data source name to config category
      const categoryMapping: Record<string, keyof typeof configDataSources> = {
        'technical_indicators': 'technical_indicators',
        'fundamental_analysis': 'fundamental_analysis', 
        'sentiment_and_trends': 'sentiment_and_trends',
        'influencer_kol': 'influencer_kol',
        'news_and_regulations': 'news_and_regulations',
        'onchain_analytics': 'onchain_analytics'
      }
      
      // Determine category - default to technical_indicators if source not found
      const category = sourceInfo ? categoryMapping[sourceInfo.name] || 'technical_indicators' : 'technical_indicators'
      
      // Check if already selected
      const isCurrentlySelected = configDataSources[category].includes(dataPointId)
      
      if (isCurrentlySelected) {
        // Remove from category
        configDataSources[category] = configDataSources[category].filter(id => id !== dataPointId)
      } else {
        // Add to category
        configDataSources[category] = [...configDataSources[category], dataPointId]
      }
      
      return newConfig
    })
  }

  // Filter trading pairs based on search
  const filteredPairs = React.useMemo(() => {
    if (!pairSearchTerm) return tradingPairs
    
    const searchLower = pairSearchTerm.toLowerCase()
    return {
      popular: tradingPairs.popular.filter(pair => 
        pair.toLowerCase().includes(searchLower)
      ),
      all: tradingPairs.all.filter(pair => 
        pair.toLowerCase().includes(searchLower)
      )
    }
  }, [pairSearchTerm])

  // Handle save
  const handleSave = async () => {
    if (!hasChanges) return
    
    setIsSaving(true)
    setError(null)
    
    try {
      let savedConfig: BotConfiguration
      
      if (bot?.config_id) {
        // Update existing config
        savedConfig = await apiClient.updateConfig(bot.config_id, configData, botName)
      } else {
        // Create new config
        savedConfig = await apiClient.createConfig(botName, configData)
      }
      
      setHasChanges(false)
      
      // Notify parent component
      onConfigSaved?.(savedConfig.config_id)
      
      // Close the config
      onClose()
      
    } catch (error) {
      console.error('Failed to save config:', error)
      setError(error instanceof Error ? error.message : 'Failed to save configuration')
    } finally {
      setIsSaving(false)
    }
  }

  // Handle reset
  const handleReset = () => {
    if (bot?.config_id) {
      // Reload from server
      // This is a simplified reset - could reload original data
      setBotName(bot.name)
    } else {
      // Reset to defaults
      setConfigData(createDefaultConfigData())
      setBotName('New Bot')
    }
    setHasChanges(false)
  }

  // Animation effects
  React.useEffect(() => {
    if (isOpen) {
      setIsMounted(true)
      setTimeout(() => setIsVisible(true), 50)
    } else {
      setIsVisible(false)
      setTimeout(() => setIsMounted(false), 500)
    }
  }, [isOpen])

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (showPairDropdown && !(e.target as HTMLElement).closest('.pair-dropdown-container')) {
        setShowPairDropdown(false)
        setPairSearchTerm('')
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showPairDropdown])

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }

  const handleNameChange = (newName: string) => {
    setBotName(newName)
    setHasChanges(true)
  }

  if (!isMounted) return null

  return (
    <div className={`fixed inset-0 z-50 ${isOpen ? 'pointer-events-auto' : 'pointer-events-none'}`}>
      {/* Backdrop overlay */}
      <div 
        className={`fixed inset-0 bg-black transition-opacity duration-500 ${
          isVisible ? 'opacity-50' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Bottom sheet */}
      <div 
        className={`fixed bottom-0 left-0 right-0 transition-transform duration-500 ease-out ${
          isVisible ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ height: '90vh' }}
      >
        <div className="h-full bg-charcoal-900 relative flex flex-col">
          {/* Top sharp gradient border */}
          <div 
            className="absolute top-0 left-0 right-0 z-30"
            style={{
              height: '1px',
              background: 'linear-gradient(to right, transparent 0%, #e3e5e6 20%, #e3e5e6 80%, transparent 100%)',
              opacity: 0.6
            }}
          />

          {/* Sticky Top Bar */}
          <div className="flex-shrink-0 z-20 bg-charcoal-900" style={{
            boxShadow: '0 8px 16px -8px rgba(22, 22, 24, 1)'
          }}>
            <div className="w-full max-w-none px-4 md:max-w-4xl md:mx-auto md:px-8 py-8">
              <div className="flex items-center justify-between">
                {/* Left side - Bot name */}
                <div className="flex items-center gap-2">
                  {isEditingName ? (
                    <input
                      type="text"
                      value={botName}
                      onChange={(e) => handleNameChange(e.target.value)}
                      onBlur={() => setIsEditingName(false)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') setIsEditingName(false)
                      }}
                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-subheader focus:border-agent-extraction focus:outline-none transition-colors"
                      autoFocus
                    />
                  ) : (
                    <>
                      <h2 
                        className="text-subheader text-bone-200 font-medium cursor-pointer hover:text-bone-100 transition-colors"
                        onClick={() => setIsEditingName(true)}
                        title="Click to edit name"
                      >
                        {botName}
                      </h2>
                      <button
                        onClick={() => setIsEditingName(true)}
                        className="text-gray-400 hover:text-bone-200 transition-colors"
                        title="Edit name"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                        </svg>
                      </button>
                    </>
                  )}
                  {hasChanges && (
                    <>
                      <span className="text-gray-500">•</span>
                      <span className="text-footnote text-orange-400">unsaved changes</span>
                    </>
                  )}
                  {isLoading && (
                    <>
                      <span className="text-gray-500">•</span>
                      <span className="text-footnote text-blue-400">loading...</span>
                    </>
                  )}
                </div>

                {/* Right side - Action buttons */}
                <div className="flex items-center gap-6">
                  {/* Reset button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleReset}
                      disabled={!hasChanges || isSaving}
                      className={`floating-action-btn ${hasChanges && !isSaving ? 'floating-action-enabled' : 'floating-action-disabled'}`}
                      title="Reset changes"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8c-.45-.83-.7-1.79-.7-2.8 0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z"/>
                      </svg>
                    </button>
                    <span className={`text-footnote ${hasChanges && !isSaving ? 'text-bone-300' : 'text-gray-500'}`}>reset</span>
                  </div>

                  {/* Save button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSave}
                      disabled={!hasChanges || isSaving}
                      className={`floating-action-btn ${hasChanges && !isSaving ? 'floating-action-enabled' : 'floating-action-disabled'}`}
                      title="Save changes"
                    >
                      {isSaving ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="animate-spin">
                          <path d="M12 2v4l-2-2-2 2V2c0-1.1.9-2 2-2s2 .9 2 2z"/>
                        </svg>
                      ) : (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                      )}
                    </button>
                    <span className={`text-footnote ${hasChanges && !isSaving ? 'text-bone-300' : 'text-gray-500'}`}>
                      {isSaving ? 'saving...' : 'save'}
                    </span>
                  </div>

                  {/* Exit button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={onClose}
                      className="floating-action-btn floating-action-enabled"
                      title="Close config"
                      disabled={isSaving}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                      </svg>
                    </button>
                    <span className="text-footnote text-bone-300">exit</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-900/20 border-b border-red-700/50 px-4 py-3">
              <div className="flex items-center gap-2 text-red-400 text-xs">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                </svg>
                {error}
              </div>
            </div>
          )}

          {/* Content area - scrollable */}
          <div className="flex-1 overflow-y-auto">
            <div className="w-full max-w-none px-4 md:max-w-4xl md:mx-auto md:px-8 py-8">
              
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-gray-400">Loading configuration...</div>
                </div>
              ) : (
                <>
                  {/* Extraction Agent Section */}
                  <div className="mb-8">
                    {!expandedSections.has('extraction') ? (
                      <button
                        onClick={() => toggleSection('extraction')}
                        className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                      >
                        <h3 className="text-subheader text-bone-200 font-medium">Extraction Agent</h3>
                        <span className="text-xl transition-transform duration-200" style={{ color: '#38a1c7' }}>
                          ▶
                        </span>
                      </button>
                    ) : (
                      <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                        <div 
                          onClick={() => toggleSection('extraction')}
                          className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                        >
                          <h3 className="text-subheader text-bone-200 font-medium">Extraction Agent</h3>
                          <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#38a1c7' }}>
                            ▶
                          </span>
                        </div>
                        <div className="p-6 space-y-6">
                          {/* Trading Pair Selection */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">TRADING PAIR</h4>
                            </div>
                            <div className="relative pair-dropdown-container">
                              <div 
                                className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs cursor-pointer hover:border-agent-extraction transition-colors flex items-center justify-between"
                                onClick={() => setShowPairDropdown(!showPairDropdown)}
                              >
                                <span>{configData.selected_pair}</span>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className={`text-gray-400 transition-transform ${showPairDropdown ? 'rotate-180' : ''}`}>
                                  <path d="M7 10l5 5 5-5z"/>
                                </svg>
                              </div>
                              
                              {showPairDropdown && (
                                <div className="absolute top-full mt-1 w-full bg-charcoal-800 border border-charcoal-600 z-10">
                                  {/* Search input */}
                                  <div className="p-2 border-b border-charcoal-600">
                                    <input
                                      type="text"
                                      placeholder="Search pairs..."
                                      value={pairSearchTerm}
                                      onChange={(e) => setPairSearchTerm(e.target.value)}
                                      onClick={(e) => e.stopPropagation()}
                                      className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-2 py-1 text-xs focus:border-agent-extraction focus:outline-none transition-colors"
                                      autoFocus
                                    />
                                  </div>
                                  
                                  {/* Scrollable list */}
                                  <div className="max-h-64 overflow-y-auto">
                                    {filteredPairs.popular.length > 0 && (
                                      <div>
                                        <div className="px-2 py-1 text-xs text-gray-500 bg-charcoal-900">Popular Pairs</div>
                                        {filteredPairs.popular.map(pair => (
                                          <button
                                            key={pair}
                                            onClick={() => {
                                              updateConfigData(prev => ({
                                                ...prev,
                                                selected_pair: pair
                                              }))
                                              setShowPairDropdown(false)
                                              setPairSearchTerm('')
                                            }}
                                            className={`w-full text-left px-3 py-2 text-xs hover:bg-agent-extraction/10 transition-colors ${
                                              configData.selected_pair === pair ? 'bg-agent-extraction/20 text-bone-200' : 'text-bone-200'
                                            }`}
                                          >
                                            {pair}
                                          </button>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {filteredPairs.all.length > 0 && (
                                      <div>
                                        <div className="px-2 py-1 text-xs text-gray-500 bg-charcoal-900">All Pairs</div>
                                        {filteredPairs.all.map(pair => (
                                          <button
                                            key={pair}
                                            onClick={() => {
                                              updateConfigData(prev => ({
                                                ...prev,
                                                selected_pair: pair
                                              }))
                                              setShowPairDropdown(false)
                                              setPairSearchTerm('')
                                            }}
                                            className={`w-full text-left px-3 py-2 text-xs hover:bg-agent-extraction/10 transition-colors ${
                                              configData.selected_pair === pair ? 'bg-agent-extraction/20 text-bone-200' : 'text-bone-200'
                                            }`}
                                          >
                                            {pair}
                                          </button>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {filteredPairs.popular.length === 0 && filteredPairs.all.length === 0 && (
                                      <div className="px-3 py-4 text-xs text-gray-500 text-center">
                                        No pairs found
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Selected Data Points Summary */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">SELECTED DATA POINTS</h4>
                            </div>
                            <div className="bg-charcoal-800 border border-charcoal-600 p-3">
                              {selectedDataPoints.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                  {selectedDataPoints.map(dataPointId => (
                                    <span
                                      key={dataPointId}
                                      className="inline-flex items-center gap-1 px-2 py-1 bg-agent-extraction text-charcoal-900 text-xs rounded"
                                    >
                                      {dataPointId}
                                      <button
                                        onClick={() => handleToggleDataPoint(dataPointId)}
                                        className="hover:bg-black/20 rounded"
                                      >
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                                        </svg>
                                      </button>
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <div className="text-gray-500 text-xs">No data sources selected</div>
                              )}
                            </div>
                          </div>

                          {/* Data Source Content */}
                          <DataSourceSection
                            dataSources={dataSources}
                            selectedDataPoints={selectedDataPoints}
                            onToggleDataPoint={handleToggleDataPoint}
                            isLoading={dataSourcesLoading}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* LLM Configuration Section */}
                  <div className="mb-8">
                    {!expandedSections.has('llm') ? (
                      <button
                        onClick={() => toggleSection('llm')}
                        className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                      >
                        <h3 className="text-subheader text-bone-200 font-medium">LLM Configuration</h3>
                        <span className="text-xl transition-transform duration-200" style={{ color: '#9333ea' }}>
                          ▶
                        </span>
                      </button>
                    ) : (
                      <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                        <div 
                          onClick={() => toggleSection('llm')}
                          className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                        >
                          <h3 className="text-subheader text-bone-200 font-medium">LLM Configuration</h3>
                          <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#9333ea' }}>
                            ▶
                          </span>
                        </div>
                        <div className="p-6 space-y-6">
                          {/* Tier Status */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">SUBSCRIPTION STATUS</h4>
                            </div>
                            <div className={`bg-charcoal-800 border p-4 rounded ${
                              userProfile?.requires_own_llm_keys ? 'border-orange-600' : 'border-green-600'
                            }`}>
                              {userProfile?.requires_own_llm_keys ? (
                                <div className="flex items-center gap-3">
                                  <div className="w-3 h-3 rounded-full bg-orange-400" />
                                  <div>
                                    <div className="text-xs text-orange-400 font-medium">Free Tier - API Keys Required</div>
                                    <div className="text-xs text-gray-400 mt-1">You need to provide your own LLM API keys. Upgrade to Base tier to use our managed keys.</div>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-center gap-3">
                                  <div className="w-3 h-3 rounded-full bg-green-400" />
                                  <div>
                                    <div className="text-xs text-green-400 font-medium">Paid Tier - Platform Keys Available</div>
                                    <div className="text-xs text-gray-400 mt-1">You can use our managed LLM keys or provide your own for more control.</div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Provider Selection */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">LLM PROVIDER</h4>
                            </div>
                            <div className="flex gap-2 flex-wrap mb-4">
                              <button
                                onClick={() => {
                                  updateConfigData(prev => ({
                                    ...prev,
                                    llm_config: {
                                      ...prev.llm_config,
                                      provider: 'openai'
                                    }
                                  }))
                                }}
                                className={`px-3 py-1 text-xs rounded transition-colors ${
                                  configData.llm_config.provider === 'openai'
                                    ? 'bg-[#9333ea] text-white font-medium'
                                    : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                }`}
                              >
                                OpenAI GPT-4
                              </button>
                              <button
                                onClick={() => {
                                  updateConfigData(prev => ({
                                    ...prev,
                                    llm_config: {
                                      ...prev.llm_config,
                                      provider: 'deepseek'
                                    }
                                  }))
                                }}
                                className={`px-3 py-1 text-xs rounded transition-colors ${
                                  configData.llm_config.provider === 'deepseek'
                                    ? 'bg-[#9333ea] text-white font-medium'
                                    : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                }`}
                              >
                                DeepSeek R1
                              </button>
                            </div>
                          </div>

                          {/* API Key Configuration */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">API KEY CONFIGURATION</h4>
                            </div>
                            
                            {!userProfile?.requires_own_llm_keys && (
                              <div className="mb-4">
                                <label className="flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={configData.llm_config.use_platform_keys}
                                    onChange={(e) => {
                                      updateConfigData(prev => ({
                                        ...prev,
                                        llm_config: {
                                          ...prev.llm_config,
                                          use_platform_keys: e.target.checked
                                        }
                                      }))
                                    }}
                                    className="w-4 h-4 accent-[#9333ea]"
                                  />
                                  <span className="text-xs text-bone-200">Use platform-managed API keys (recommended)</span>
                                </label>
                              </div>
                            )}

                            {(userProfile?.requires_own_llm_keys || !configData.llm_config.use_platform_keys) && (
                              <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded space-y-4">
                                {configData.llm_config.provider === 'openai' && (
                                  <div>
                                    <label className="block text-xs text-gray-400 mb-2">OpenAI API Key:</label>
                                    <input
                                      type="password"
                                      value={configData.llm_config.openai_api_key || ''}
                                      onChange={(e) => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          llm_config: {
                                            ...prev.llm_config,
                                            openai_api_key: e.target.value
                                          }
                                        }))
                                      }}
                                      placeholder="sk-..."
                                      className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-[#9333ea] focus:outline-none transition-colors rounded"
                                    />
                                    <div className="text-xs text-gray-500 mt-1">
                                      Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">OpenAI Platform</a>
                                    </div>
                                  </div>
                                )}

                                {configData.llm_config.provider === 'deepseek' && (
                                  <div>
                                    <label className="block text-xs text-gray-400 mb-2">DeepSeek API Key:</label>
                                    <input
                                      type="password"
                                      value={configData.llm_config.deepseek_api_key || ''}
                                      onChange={(e) => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          llm_config: {
                                            ...prev.llm_config,
                                            deepseek_api_key: e.target.value
                                          }
                                        }))
                                      }}
                                      placeholder="sk-..."
                                      className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-[#9333ea] focus:outline-none transition-colors rounded"
                                    />
                                    <div className="text-xs text-gray-500 mt-1">
                                      Get your API key from <a href="https://platform.deepseek.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">DeepSeek Platform</a>
                                    </div>
                                  </div>
                                )}

                                {userProfile?.requires_own_llm_keys && (
                                  <div className="bg-orange-900/20 border border-orange-700/50 p-3 rounded">
                                    <div className="flex items-center gap-2">
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-orange-400">
                                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                      </svg>
                                      <div>
                                        <div className="text-xs text-orange-400 font-medium">API Key Required</div>
                                        <div className="text-xs text-orange-300">You must provide your own LLM API key to use AI decision making. Consider upgrading to Base tier for managed keys.</div>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Security Notice */}
                          <div className="bg-charcoal-800 border border-charcoal-700 p-3 rounded">
                            <div className="flex items-center gap-2">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-green-400">
                                <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9L10,17Z"/>
                              </svg>
                              <div>
                                <div className="text-xs text-green-400 font-medium">Secure Storage</div>
                                <div className="text-xs text-gray-400">All API keys are encrypted using Supabase Vault before storage.</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Decision Agent Section */}
                  <div className="mb-8">
                    {!expandedSections.has('decision') ? (
                      <button
                        onClick={() => toggleSection('decision')}
                        className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                      >
                        <h3 className="text-subheader text-bone-200 font-medium">Decision Agent</h3>
                        <span className="text-xl transition-transform duration-200" style={{ color: '#2cbe77' }}>
                          ▶
                        </span>
                      </button>
                    ) : (
                      <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                        <div 
                          onClick={() => toggleSection('decision')}
                          className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                        >
                          <h3 className="text-subheader text-bone-200 font-medium">Decision Agent</h3>
                          <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#2cbe77' }}>
                            ▶
                          </span>
                        </div>
                        <div className="p-6 space-y-6">
                          {/* Analysis Frequency */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">ANALYSIS FREQUENCY</h4>
                            </div>
                            <div className="flex gap-2 flex-wrap">
                              {frequencyOptions.map(freq => (
                                <button
                                  key={freq.value}
                                  onClick={() => {
                                    updateConfigData(prev => ({
                                      ...prev,
                                      decision: {
                                        ...prev.decision,
                                        analysis_frequency: freq.value
                                      }
                                    }))
                                  }}
                                  className={`px-3 py-1 text-xs rounded transition-colors ${
                                    configData.decision.analysis_frequency === freq.value
                                      ? 'bg-agents-decision text-charcoal-900 font-medium'
                                      : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                  }`}
                                >
                                  {freq.label}
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Context Display */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">MARKET CONTEXT</h4>
                            </div>
                            <div className="bg-charcoal-800 border border-charcoal-600 p-3 text-xs text-gray-300">
                              <div>Analyzing: <span className="text-bone-200">{configData.selected_pair}</span></div>
                              <div className="mt-1">Using data points: <span className="text-bone-200">{selectedDataPoints.length} selected</span></div>
                              <div className="mt-1">Review frequency: <span className="text-bone-200">Every {frequencyOptions.find(f => f.value === configData.decision.analysis_frequency)?.label.toLowerCase()}</span></div>
                            </div>
                          </div>

                          {/* Strategy Configuration */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">USER PROMPT</h4>
                            </div>
                            <div>
                              <label className="block text-xs text-gray-400 mb-2">Your trading strategy:</label>
                              <textarea
                                value={configData.decision.user_prompt || ''}
                                onChange={(e) => {
                                  updateConfigData(prev => ({
                                    ...prev,
                                    decision: {
                                      ...prev.decision,
                                      user_prompt: e.target.value
                                    }
                                  }))
                                }}
                                placeholder="Enter your trading strategy and decision criteria..."
                                rows={4}
                                className="w-full bg-charcoal-800 border border-charcoal-600 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors resize-none"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Trading Agent Section */}
                  <div className="mb-8">
                    {!expandedSections.has('trading') ? (
                      <button
                        onClick={() => toggleSection('trading')}
                        className="w-full flex items-center justify-between p-6 bg-charcoal-900 relative transition-all duration-300 ggbot-accordion-btn cursor-pointer"
                      >
                        <h3 className="text-subheader text-bone-200 font-medium">Trading Agent</h3>
                        <span className="text-xl transition-transform duration-200" style={{ color: '#be6a47' }}>
                          ▶
                        </span>
                      </button>
                    ) : (
                      <div className="bg-charcoal-900 relative ggbot-accordion-expanded">
                        <div 
                          onClick={() => toggleSection('trading')}
                          className="flex items-center justify-between p-6 cursor-pointer border-b border-charcoal-600"
                        >
                          <h3 className="text-subheader text-bone-200 font-medium">Trading Agent</h3>
                          <span className="text-xl transition-transform duration-200 rotate-90" style={{ color: '#be6a47' }}>
                            ▶
                          </span>
                        </div>
                        <div className="p-6 space-y-6">
                          {/* Tab Navigation */}
                          <div>
                            <div className="flex gap-2 flex-wrap">
                              <button
                                onClick={() => setTradingAgentTab('position-sizing')}
                                className={`px-3 py-1 text-xs rounded transition-colors ${
                                  tradingAgentTab === 'position-sizing'
                                    ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                    : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                }`}
                              >
                                Position Sizing
                              </button>
                              <button
                                onClick={() => setTradingAgentTab('risk-management')}
                                className={`px-3 py-1 text-xs rounded transition-colors ${
                                  tradingAgentTab === 'risk-management'
                                    ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                    : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                }`}
                              >
                                Risk Management
                              </button>
                              <button
                                onClick={() => setTradingAgentTab('telegram')}
                                className={`px-3 py-1 text-xs rounded transition-colors ${
                                  tradingAgentTab === 'telegram'
                                    ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                    : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                }`}
                              >
                                Telegram Publishing
                              </button>
                              <button
                                onClick={() => setTradingAgentTab('exchange')}
                                className={`px-3 py-1 text-xs rounded transition-colors relative ${
                                  tradingAgentTab === 'exchange'
                                    ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                    : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                }`}
                                title="Exchange Connection - Coming Soon"
                              >
                                Exchange Connection
                                <span className="absolute -top-1 -right-1 bg-orange-500 text-white text-xs px-1 py-0.5 rounded text-[10px] leading-none">
                                  Soon
                                </span>
                              </button>
                            </div>
                            <div className="mt-2 text-xs text-gray-400">
                              {tradingAgentTab === 'position-sizing' 
                                ? 'Configure how much capital to allocate per trade'
                                : tradingAgentTab === 'risk-management'
                                ? 'Set position limits and stop loss/take profit defaults'
                                : tradingAgentTab === 'telegram'
                                ? 'Configure Telegram publishing for decision signals'
                                : 'Exchange connection for live trading (coming soon)'}
                            </div>
                          </div>

                          {/* Tab Content */}
                          {tradingAgentTab === 'position-sizing' && (
                          <div>
                          {/* Position Sizing */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">POSITION SIZING</h4>
                            </div>
                            <div className="flex gap-2 flex-wrap mb-4">
                              {positionSizingMethods.map(method => (
                                <button
                                  key={method.value}
                                  onClick={() => {
                                    updateConfigData(prev => ({
                                      ...prev,
                                      trading: {
                                        ...prev.trading,
                                        position_sizing: {
                                          ...prev.trading.position_sizing,
                                          method: method.value as 'fixed_usd' | 'account_percentage' | 'confidence_based'
                                        }
                                      }
                                    }))
                                  }}
                                  className={`px-3 py-1 text-xs rounded transition-colors ${
                                    configData.trading.position_sizing.method === method.value
                                      ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                      : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                  }`}
                                >
                                  {method.label}
                                </button>
                              ))}
                            </div>
                            
                            <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded">
                              {configData.trading.position_sizing.method === 'fixed_usd' && (
                                <div className="grid grid-cols-2 gap-4 items-center">
                                  <span className="text-xs text-gray-400">Amount per trade:</span>
                                  <div className="flex items-center">
                                    <span className="text-bone-200 text-xs mr-2">$</span>
                                    <input
                                      type="number"
                                      value={configData.trading.position_sizing.fixed_amount_usd || 100}
                                      onChange={(e) => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          trading: {
                                            ...prev.trading,
                                            position_sizing: {
                                              ...prev.trading.position_sizing,
                                              fixed_amount_usd: Number(e.target.value)
                                            }
                                          }
                                        }))
                                      }}
                                      min="10"
                                      step="10"
                                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-20 focus:border-[#be6a47] focus:outline-none transition-colors"
                                    />
                                  </div>
                                </div>
                              )}
                              {configData.trading.position_sizing.method === 'account_percentage' && (
                                <div className="grid grid-cols-2 gap-4 items-center">
                                  <span className="text-xs text-gray-400">Percentage of account:</span>
                                  <div className="flex items-center">
                                    <input
                                      type="number"
                                      value={configData.trading.position_sizing.account_percent || 5}
                                      onChange={(e) => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          trading: {
                                            ...prev.trading,
                                            position_sizing: {
                                              ...prev.trading.position_sizing,
                                              account_percent: Number(e.target.value)
                                            }
                                          }
                                        }))
                                      }}
                                      min="0.1"
                                      max="50"
                                      step="0.1"
                                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                                    />
                                    <span className="text-bone-200 text-xs ml-2">%</span>
                                  </div>
                                </div>
                              )}
                              {configData.trading.position_sizing.method === 'confidence_based' && (
                                <div className="grid grid-cols-2 gap-4 items-center">
                                  <span className="text-xs text-gray-400">Max position size:</span>
                                  <div className="flex items-center">
                                    <input
                                      type="number"
                                      value={configData.trading.position_sizing.max_position_percent || 10}
                                      onChange={(e) => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          trading: {
                                            ...prev.trading,
                                            position_sizing: {
                                              ...prev.trading.position_sizing,
                                              max_position_percent: Number(e.target.value)
                                            }
                                          }
                                        }))
                                      }}
                                      min="1"
                                      max="25"
                                      step="1"
                                      className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                                    />
                                    <span className="text-bone-200 text-xs ml-2">% when confidence = 100%</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Risk Management */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">RISK MANAGEMENT</h4>
                            </div>
                            <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded space-y-4">
                              <div className="grid grid-cols-2 gap-4 items-center">
                                <span className="text-xs text-gray-400">Max active positions:</span>
                                <div className="flex gap-2">
                                  {[1,2,3,4,5].map(num => (
                                    <button
                                      key={num}
                                      onClick={() => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          trading: {
                                            ...prev.trading,
                                            risk_management: {
                                              ...prev.trading.risk_management,
                                              max_positions: num
                                            }
                                          }
                                        }))
                                      }}
                                      className={`px-2 py-1 text-xs rounded transition-colors ${
                                        configData.trading.risk_management.max_positions === num
                                          ? 'bg-[#be6a47] text-charcoal-900 font-medium'
                                          : 'bg-charcoal-800 text-gray-400 hover:text-bone-200'
                                      }`}
                                    >
                                      {num}
                                    </button>
                                  ))}
                                </div>
                              </div>

                              <div className="grid grid-cols-2 gap-4 items-center">
                                <span className="text-xs text-gray-400">Default stop loss:</span>
                                <div className="flex items-center">
                                  <input
                                    type="number"
                                    value={configData.trading.risk_management.default_stop_loss_percent || 3}
                                    onChange={(e) => {
                                      updateConfigData(prev => ({
                                        ...prev,
                                        trading: {
                                          ...prev.trading,
                                          risk_management: {
                                            ...prev.trading.risk_management,
                                            default_stop_loss_percent: Number(e.target.value)
                                          }
                                        }
                                      }))
                                    }}
                                    min="0.5"
                                    max="20"
                                    step="0.1"
                                    className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                                  />
                                  <span className="text-bone-200 text-xs ml-2">%</span>
                                </div>
                              </div>

                              <div className="grid grid-cols-2 gap-4 items-center">
                                <span className="text-xs text-gray-400">Default take profit:</span>
                                <div className="flex items-center">
                                  <input
                                    type="number"
                                    value={configData.trading.risk_management.default_take_profit_percent || 6}
                                    onChange={(e) => {
                                      updateConfigData(prev => ({
                                        ...prev,
                                        trading: {
                                          ...prev.trading,
                                          risk_management: {
                                            ...prev.trading.risk_management,
                                            default_take_profit_percent: Number(e.target.value)
                                          }
                                        }
                                      }))
                                    }}
                                    min="0.5"
                                    max="50"
                                    step="0.1"
                                    className="bg-charcoal-800 border border-charcoal-600 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors"
                                  />
                                  <span className="text-bone-200 text-xs ml-2">%</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          </div>
                          )}

                          {tradingAgentTab === 'telegram' && (
                          <div>
                          {/* Telegram Publishing Configuration */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">TELEGRAM PUBLISHING STATUS</h4>
                            </div>
                            <div className={`bg-charcoal-800 border p-4 rounded mb-6 ${
                              userProfile?.can_publish_telegram_signals ? 'border-green-600' : 'border-orange-600'
                            }`}>
                              {userProfile?.can_publish_telegram_signals ? (
                                <div className="flex items-center gap-3">
                                  <div className="w-3 h-3 rounded-full bg-green-400" />
                                  <div>
                                    <div className="text-xs text-green-400 font-medium">Telegram Publishing Available</div>
                                    <div className="text-xs text-gray-400 mt-1">You can publish bot decisions to Telegram channels.</div>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-center gap-3">
                                  <div className="w-3 h-3 rounded-full bg-orange-400" />
                                  <div>
                                    <div className="text-xs text-orange-400 font-medium">Telegram Publishing Locked</div>
                                    <div className="text-xs text-gray-400 mt-1">Upgrade to Base tier to publish bot decisions to Telegram. Free tier is paper trading only.</div>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Telegram Configuration - only show if user has access */}
                            {userProfile?.can_publish_telegram_signals ? (
                              <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded space-y-4">
                                <div>
                                  <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                      type="checkbox"
                                      checked={configData.telegram_integration.publisher.enabled}
                                      onChange={(e) => {
                                        updateConfigData(prev => ({
                                          ...prev,
                                          telegram_integration: {
                                            ...prev.telegram_integration,
                                            publisher: {
                                              ...prev.telegram_integration.publisher,
                                              enabled: e.target.checked
                                            }
                                          }
                                        }))
                                      }}
                                      className="w-4 h-4 accent-[#be6a47]"
                                    />
                                    <span className="text-xs text-bone-200">Enable Telegram publishing</span>
                                  </label>
                                </div>

                                {configData.telegram_integration.publisher.enabled && (
                                  <>
                                    <div>
                                      <label className="block text-xs text-gray-400 mb-2">Telegram Bot Token:</label>
                                      <input
                                        type="password"
                                        value={configData.telegram_integration.publisher.bot_token || ''}
                                        onChange={(e) => {
                                          updateConfigData(prev => ({
                                            ...prev,
                                            telegram_integration: {
                                              ...prev.telegram_integration,
                                              publisher: {
                                                ...prev.telegram_integration.publisher,
                                                bot_token: e.target.value
                                              }
                                            }
                                          }))
                                        }}
                                        placeholder="Enter bot token from @BotFather..."
                                        className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-[#be6a47] focus:outline-none transition-colors rounded"
                                      />
                                      <div className="text-xs text-gray-500 mt-1">
                                        Create a bot via <a href="https://t.me/botfather" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">@BotFather</a> on Telegram
                                      </div>
                                    </div>

                                    <div>
                                      <label className="block text-xs text-gray-400 mb-2">Channel ID:</label>
                                      <input
                                        type="text"
                                        value={configData.telegram_integration.publisher.filter_channel || ''}
                                        onChange={(e) => {
                                          updateConfigData(prev => ({
                                            ...prev,
                                            telegram_integration: {
                                              ...prev.telegram_integration,
                                              publisher: {
                                                ...prev.telegram_integration.publisher,
                                                filter_channel: e.target.value
                                              }
                                            }
                                          }))
                                        }}
                                        placeholder="@channel_username or -1001234567890"
                                        className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-[#be6a47] focus:outline-none transition-colors rounded"
                                      />
                                      <div className="text-xs text-gray-500 mt-1">
                                        Add the bot as admin to your channel first
                                      </div>
                                    </div>

                                    <div>
                                      <label className="block text-xs text-gray-400 mb-2">Confidence Threshold:</label>
                                      <div className="flex items-center">
                                        <input
                                          type="number"
                                          value={configData.telegram_integration.publisher.confidence_threshold || 0.7}
                                          onChange={(e) => {
                                            updateConfigData(prev => ({
                                              ...prev,
                                              telegram_integration: {
                                                ...prev.telegram_integration,
                                                publisher: {
                                                  ...prev.telegram_integration.publisher,
                                                  confidence_threshold: Number(e.target.value)
                                                }
                                              }
                                            }))
                                          }}
                                          min="0.1"
                                          max="1.0"
                                          step="0.05"
                                          className="bg-charcoal-900 border border-charcoal-700 text-bone-200 px-2 py-1 text-xs w-16 focus:border-[#be6a47] focus:outline-none transition-colors rounded"
                                        />
                                        <span className="text-bone-200 text-xs ml-2">min confidence to publish</span>
                                      </div>
                                    </div>
                                  </>
                                )}
                              </div>
                            ) : (
                              <div className="bg-charcoal-800/50 border border-charcoal-700 p-4 rounded opacity-50 cursor-not-allowed relative">
                                <div className="absolute inset-0 bg-charcoal-900/50 flex items-center justify-center rounded">
                                  <div className="text-orange-400 text-xs font-medium">Upgrade Required</div>
                                </div>
                                <div className="space-y-3 blur-sm">
                                  <div className="flex items-center">
                                    <input type="checkbox" disabled className="w-4 h-4" />
                                    <span className="text-xs text-gray-400 ml-2">Enable Telegram publishing</span>
                                  </div>
                                  <input disabled placeholder="Bot token..." className="w-full bg-charcoal-900 border border-charcoal-700 text-gray-400 px-3 py-2 text-xs rounded" />
                                  <input disabled placeholder="Channel ID..." className="w-full bg-charcoal-900 border border-charcoal-700 text-gray-400 px-3 py-2 text-xs rounded" />
                                </div>
                              </div>
                            )}
                          </div>
                          </div>
                          )}

                          {/* Exchange Connection Tab - Grayed Out */}
                          {tradingAgentTab === 'exchange' && (
                          <div className="relative">
                            {/* Actual Exchange Configuration Content */}
                            <div className="space-y-6 opacity-30">
                              <div>
                                <div className="flex items-center justify-between mb-4">
                                  <h4 className="text-footnote text-bone-200 font-medium">EXCHANGE</h4>
                                </div>
                                <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded">
                                  <div className="grid grid-cols-2 gap-4 items-center mb-4">
                                    <span className="text-xs text-gray-400">Selected exchange:</span>
                                    <div className="flex gap-2">
                                      {exchangeOptions.map(exchange => (
                                        <button
                                          key={exchange.value}
                                          disabled
                                          className="px-2 py-1 text-xs rounded bg-charcoal-800 text-gray-400 cursor-not-allowed"
                                        >
                                          {exchange.label}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                  
                                  <div className="space-y-3">
                                    <div>
                                      <label className="block text-xs text-gray-400 mb-2">API Key:</label>
                                      <input
                                        type="password"
                                        disabled
                                        placeholder="Enter API key..."
                                        className="w-full bg-charcoal-900 border border-charcoal-700 text-gray-400 px-3 py-2 text-xs rounded cursor-not-allowed"
                                      />
                                    </div>
                                    
                                    <div>
                                      <label className="block text-xs text-gray-400 mb-2">Secret Key:</label>
                                      <input
                                        type="password"
                                        disabled
                                        placeholder="Enter secret key..."
                                        className="w-full bg-charcoal-900 border border-charcoal-700 text-gray-400 px-3 py-2 text-xs rounded cursor-not-allowed"
                                      />
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Gray Overlay with Coming Soon Message */}
                            <div className="absolute inset-0 bg-charcoal-900/70 flex items-center justify-center rounded pointer-events-auto">
                              <div className="text-center bg-charcoal-800 border border-orange-600 p-6 rounded max-w-sm">
                                <div className="text-orange-400 text-sm font-medium mb-2">🚀 Coming Soon - Full Autonomous Trading</div>
                                <div className="text-xs text-gray-300 mb-3">
                                  Direct exchange API integration for fully autonomous trading. Connect your CEX accounts and let your bot trade automatically.
                                </div>
                                <div className="text-xs text-orange-300 font-medium">
                                  Currently only paper trading is available.
                                </div>
                              </div>
                            </div>
                          </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GGBotConfig