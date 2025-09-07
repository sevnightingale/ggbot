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

// Data source display name mapping
const dataSourceDisplayNames: Record<string, string> = {
  'technical_analysis': 'Technical Analysis',
  'signals_group_chats': 'Signals',
  'fundamental_analysis': 'Fundamental Analysis',
  'sentiment_and_trends': 'Sentiment & Trends',
  'influencer_kol': 'Influencer/KOL',
  'news_and_regulations': 'News & Regulations',
  'onchain_analytics': 'On-chain Analytics'
}

// All data sources (including coming soon ones)
const allDataSources = [
  'technical_analysis',
  'signals_group_chats', 
  'fundamental_analysis',
  'sentiment_and_trends',
  'influencer_kol',
  'news_and_regulations',
  'onchain_analytics'
]

interface DataSourceSectionProps {
  dataSources: DataSource[]
  selectedDataPoints: string[]  // Now contains data point names, not IDs
  onToggleDataPoint: (dataPointId: string) => void
  onShowGgShotModal: () => void
  isLoading: boolean
}

const DataSourceSection: React.FC<DataSourceSectionProps> = ({
  dataSources,
  selectedDataPoints,
  onToggleDataPoint,
  onShowGgShotModal,
  isLoading
}) => {
  const [searchTerm, setSearchTerm] = React.useState('')
  const [activeTab, setActiveTab] = React.useState<string>('technical_analysis')

  // Get the active data source
  const activeDataSource = dataSources.find(source => source.name === activeTab)
  
  // Filter data points within the active source based on search
  const filteredDataPoints = React.useMemo(() => {
    if (!activeDataSource) return []
    if (!searchTerm) return activeDataSource.data_points
    
    return activeDataSource.data_points.filter(point =>
      point.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      point.description.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [activeDataSource, searchTerm])

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
      {/* Header and Selected Count */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs text-gray-400 font-medium">DATA POINT SELECTION</h4>
        <span className="text-footnote text-gray-400">{selectedDataPoints.length} selected</span>
      </div>
      
      {/* Selected Data Points Summary */}
      <div className="bg-charcoal-800 border border-charcoal-600 p-3 mb-4 rounded">
        {selectedDataPoints.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {selectedDataPoints.map(dataPointName => {
              // Find the data point by name to get its ID for removal
              const dataPoint = dataSources
                .flatMap(source => source.data_points)
                .find(dp => dp.name === dataPointName)
              
              return (
                <span
                  key={dataPointName}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-agent-extraction text-charcoal-900 text-xs rounded"
                >
                  {dataPointName}
                  <button
                    onClick={() => dataPoint && onToggleDataPoint(dataPoint.data_point_id)}
                    className="hover:bg-black/20 rounded"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                  </button>
                </span>
              )
            })}
          </div>
        ) : (
          <div className="text-gray-500 text-xs">No data sources selected</div>
        )}
      </div>

      {/* Data Source Tabs */}
      <div className="mb-4">
        <div className="flex gap-1 flex-wrap mb-4 border-b border-charcoal-600">
          {allDataSources.map(sourceName => (
            <button
              key={sourceName}
              onClick={() => setActiveTab(sourceName)}
              className={`px-3 py-2 text-xs transition-colors border-b-2 ${
                activeTab === sourceName
                  ? 'border-agent-extraction text-agent-extraction bg-agent-extraction/5'
                  : 'border-transparent text-gray-400 hover:text-bone-200 hover:border-gray-600'
              }`}
            >
              {dataSourceDisplayNames[sourceName] || sourceName}
            </button>
          ))}
        </div>
        
        {/* Search within active tab */}
        <div className="relative">
          <input
            type="text"
            placeholder={`Search ${dataSourceDisplayNames[activeTab] || activeTab} data points...`}
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

      {/* Active Tab Content */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {filteredDataPoints.length > 0 ? (
          filteredDataPoints.map(dataPoint => {
          const isSelected = selectedDataPoints.includes(dataPoint.name)
          const canAccess = canAccessDataPoint(dataPoint)
          const isLocked = dataPoint.is_locked
          
          return (
            <div key={dataPoint.data_point_id} className="relative">
              <button
                onClick={() => {
                  if (!canAccess && dataPoint.name.toLowerCase().includes('ggshot')) {
                    onShowGgShotModal()
                  } else if (canAccess) {
                    onToggleDataPoint(dataPoint.data_point_id)
                  }
                }}
                disabled={isLocked && !dataPoint.name.toLowerCase().includes('ggshot')}
                className={`w-full text-left p-3 border transition-colors relative ${
                  isSelected && canAccess
                    ? 'bg-agent-extraction/10 border-agent-extraction text-bone-200'
                    : isLocked && !dataPoint.name.toLowerCase().includes('ggshot')
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
                    {dataPoint.name.toLowerCase().includes('ggshot') ? 'Click to subscribe' : 'Upgrade required'}
                  </div>
                </div>
              )}
            </div>
          )
        })
        ) : (
          // Coming Soon message for data sources without data points
          <div className="text-center py-12">
            <div className="bg-charcoal-800 border border-charcoal-600 rounded-lg p-6 max-w-sm mx-auto">
              <div className="text-orange-400 text-sm font-medium mb-2">
                {dataSourceDisplayNames[activeTab]} - Coming Soon
              </div>
              <div className="text-gray-400 text-xs mb-4">
                {activeTab === 'fundamental_analysis' && 'Financial metrics, earnings data, and company fundamentals'}
                {activeTab === 'sentiment_and_trends' && 'Social media sentiment analysis and trending topics'}
                {activeTab === 'influencer_kol' && 'Key opinion leader insights and influencer signals'}
                {activeTab === 'news_and_regulations' && 'Breaking news analysis and regulatory updates'}
                {activeTab === 'onchain_analytics' && 'Blockchain metrics, whale movements, and on-chain data'}
                {activeTab === 'signals_group_chats' && 'Premium trading signals from verified sources'}
                {activeTab === 'technical_analysis' && 'Technical indicators and chart analysis'}
              </div>
              <div className="text-xs text-gray-500">
                We&apos;re working hard to bring you these advanced data sources
              </div>
            </div>
          </div>
        )}
        
        {filteredDataPoints.length === 0 && searchTerm && (
          <div className="text-center py-8 text-gray-500 text-xs">
            No matching data points found
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

  // State for credential management (separate from config data)
  const [userCredentials, setUserCredentials] = React.useState<{ credential_name: string; provider: string; created_at: string }[]>([])
  const [credentialInput, setCredentialInput] = React.useState<string>('')
  const [savingCredential, setSavingCredential] = React.useState(false)
  const [credentialError, setCredentialError] = React.useState<string | null>(null)
  
  // UI state
  const [tradingAgentTab, setTradingAgentTab] = React.useState('position-sizing')
  const [pairSearchTerm, setPairSearchTerm] = React.useState('')
  const [showPairDropdown, setShowPairDropdown] = React.useState(false)
  const [showGgShotModal, setShowGgShotModal] = React.useState(false)

  // Initialize component
  React.useEffect(() => {
    const initializeComponent = async () => {
      if (!isOpen) return
      
      console.log('GGBotConfig initializing component, isOpen:', isOpen)
      setIsLoading(true)
      setError(null)
      
      try {
        console.log('🔄 Starting API calls...')
        
        // Load data sources, user profile, and credentials in parallel
        const [dataSourcesResponse, userProfileResponse, credentialsResponse] = await Promise.all([
          apiClient.getDataSourcesWithPoints(),
          apiClient.getUserProfile(),
          apiClient.listCredentials()
        ])
        
        console.log('✅ API calls successful:', { dataSourcesResponse, userProfileResponse, credentialsResponse })
        
        setDataSources(dataSourcesResponse)
        setUserProfile(userProfileResponse)
        setUserCredentials(credentialsResponse)
        
        // Load existing config if editing
        if (bot?.config_id) {
          const config = await apiClient.getConfig(bot.config_id)
          setConfigData(config.config_data)
          setBotName(config.config_name)
        } else {
          // New bot - use defaults
          setConfigData(createDefaultConfigData())
          setBotName('New ggbot')
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

  // Get selected data points from config - now using data point names
  const selectedDataPoints = React.useMemo(() => {
    const dataSources = configData.extraction.selected_data_sources
    const allDataPoints: string[] = []
    
    // Extract data point names from all data source categories
    Object.values(dataSources).forEach(source => {
      if (source && source.data_points) {
        allDataPoints.push(...source.data_points)
      }
    })
    
    return allDataPoints
  }, [configData])

  // Credential management functions
  const handleSaveCredential = async () => {
    if (!credentialInput.trim()) return

    setCredentialError(null)
    setSavingCredential(true)
    
    try {
      await apiClient.storeCredential(configData.llm_config.provider, credentialInput.trim())
      
      // Reload credentials and reset input
      const credentials = await apiClient.listCredentials()
      setUserCredentials(credentials)
      setCredentialInput('')
      
      // Update config to use own key
      updateConfigData(prev => ({
        ...prev,
        llm_config: {
          ...prev.llm_config,
          use_own_key: true,
          use_platform_keys: false
        }
      }))
      
    } catch (error) {
      setCredentialError(error instanceof Error ? error.message : 'Failed to save credential')
    } finally {
      setSavingCredential(false)
    }
  }

  // Check if user has credential for current provider
  const hasCredentialForProvider = (provider: string): boolean => {
    return userCredentials.some(cred => cred.provider === provider)
  }

  // Handle credential deletion
  const handleDeleteCredential = async (provider: string) => {
    try {
      const credential = userCredentials.find(cred => cred.provider === provider)
      if (credential) {
        await apiClient.deleteCredential(credential.credential_name)
        const credentials = await apiClient.listCredentials()
        setUserCredentials(credentials)
        
        // If this was the current provider, switch back to platform keys
        if (configData.llm_config.provider === provider) {
          updateConfigData(prev => ({
            ...prev,
            llm_config: {
              ...prev.llm_config,
              use_own_key: false,
              use_platform_keys: true
            }
          }))
        }
      }
    } catch (error) {
      console.error('Failed to delete credential:', error)
    }
  }

  // Handle data point selection
  const handleToggleDataPoint = (dataPointId: string) => {
    updateConfigData(prev => {
      const newConfig = { ...prev }
      
      // Find the data point by ID to get its name and source
      const dataPoint = dataSources
        .flatMap(source => source.data_points)
        .find(dp => dp.data_point_id === dataPointId)
      
      if (!dataPoint) return newConfig
      
      // Find which data source this data point belongs to
      const sourceInfo = dataSources.find(ds => 
        ds.data_points.some(dp => dp.data_point_id === dataPointId)
      )
      
      if (!sourceInfo) return newConfig
      
      // Map data source name to config category
      const categoryMapping: Record<string, keyof typeof newConfig.extraction.selected_data_sources> = {
        'technical_analysis': 'technical_analysis',
        'signals_group_chats': 'signals_group_chats',
        'fundamental_analysis': 'fundamental_analysis', 
        'sentiment_and_trends': 'sentiment_and_trends',
        'influencer_kol': 'influencer_kol',
        'news_and_regulations': 'news_and_regulations',
        'onchain_analytics': 'onchain_analytics'
      }
      
      const category = categoryMapping[sourceInfo.name]
      if (!category) return newConfig
      
      // Initialize the category if it doesn't exist
      if (!newConfig.extraction.selected_data_sources[category]) {
        newConfig.extraction.selected_data_sources[category] = {
          data_points: [],
          timeframes: ["5m", "15m", "30m", "1h", "4h", "1d", "1w"] // Default all timeframes
        }
      }
      
      const categoryData = newConfig.extraction.selected_data_sources[category]!
      const dataPointName = dataPoint.name
      
      // Check if already selected (by name)
      const isCurrentlySelected = categoryData.data_points.includes(dataPointName)
      
      if (isCurrentlySelected) {
        // Remove data point name
        categoryData.data_points = categoryData.data_points.filter(name => name !== dataPointName)
        
        // If no data points left, remove the entire category
        if (categoryData.data_points.length === 0) {
          delete newConfig.extraction.selected_data_sources[category]
        }
      } else {
        // Add data point name
        categoryData.data_points = [...categoryData.data_points, dataPointName]
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
                  {/* ggbot Type Selection - Horizontal Layout */}
                  <div className="mb-6">
                    <div className="mb-3">
                      <h4 className="text-footnote text-bone-200 font-medium">ggbot TYPE</h4>
                    </div>
                    
                    {/* Horizontal Radio Options */}
                    <div className="flex gap-4">
                      {/* Autonomous Trading Option */}
                      <label className="flex-1 cursor-pointer">
                        <div className="flex items-center gap-3 mb-2">
                          <input
                            type="radio"
                            name="config_type"
                            value="autonomous_trading"
                            checked={configData.config_type === 'autonomous_trading'}
                            onChange={(e) => {
                              updateConfigData(prev => ({
                                ...prev,
                                config_type: e.target.value
                              }))
                            }}
                            className="w-4 h-4 text-blue-500 focus:ring-blue-500"
                          />
                          <div className="text-xs text-bone-200 font-medium">Autonomous Trading</div>
                        </div>
                        <div className="text-xs text-gray-400 ml-7">
                          AI makes trading decisions automatically based on market analysis
                        </div>
                      </label>

                      {/* Signal Validation Option */}
                      <label className={`flex-1 ${!userProfile?.can_use_signal_validation ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
                        <div className="flex items-center gap-3 mb-2">
                          <input
                            type="radio"
                            name="config_type"
                            value="signal_validation"
                            checked={configData.config_type === 'signal_validation'}
                            onChange={(e) => {
                              if (userProfile?.can_use_signal_validation) {
                                updateConfigData(prev => ({
                                  ...prev,
                                  config_type: e.target.value
                                }))
                              } else {
                                // Show upgrade modal
                                alert('Signal Validation requires an upgraded plan')
                              }
                            }}
                            disabled={!userProfile?.can_use_signal_validation}
                            className="w-4 h-4 text-blue-500 focus:ring-blue-500"
                          />
                          <div className="text-xs text-bone-200 font-medium">
                            Signal Validation
                            {!userProfile?.can_use_signal_validation && (
                              <span className="ml-2 text-orange-400">(Upgrade Required)</span>
                            )}
                          </div>
                        </div>
                        <div className="text-xs text-gray-400 ml-7">
                          Validate and analyze signals from external sources like ggShot
                        </div>
                      </label>
                    </div>
                  </div>

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


                          {/* Timeframes Info */}
                          <div className="bg-blue-900/20 border border-blue-700/50 p-3 rounded">
                            <div className="flex items-center gap-2">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="text-blue-400">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                              </svg>
                              <div>
                                <div className="text-xs text-blue-400 font-medium">Multi-Timeframe Analysis</div>
                                <div className="text-xs text-blue-300">All selected indicators analyzed across 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w) for comprehensive market context</div>
                              </div>
                            </div>
                          </div>

                          {/* Data Source Content */}
                          <DataSourceSection
                            dataSources={dataSources}
                            selectedDataPoints={selectedDataPoints}
                            onToggleDataPoint={handleToggleDataPoint}
                            onShowGgShotModal={() => setShowGgShotModal(true)}
                            isLoading={dataSourcesLoading}
                          />
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
                                    configData.decision?.analysis_frequency === freq.value
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
                              <div className="mt-1">Review frequency: <span className="text-bone-200">Every {frequencyOptions.find(f => f.value === configData.decision?.analysis_frequency)?.label?.toLowerCase()}</span></div>
                            </div>
                          </div>

                          {/* LLM Configuration - moved from separate section */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">AI MODEL CONFIGURATION</h4>
                            </div>
                            
                            {/* Tier Status */}
                            <div className={`bg-charcoal-800 border p-3 rounded mb-4 ${
                              userProfile?.requires_own_llm_keys ? 'border-orange-600' : 'border-green-600'
                            }`}>
                              {userProfile?.requires_own_llm_keys ? (
                                <div className="flex items-center gap-3">
                                  <div className="w-3 h-3 rounded-full bg-orange-400" />
                                  <div>
                                    <div className="text-xs text-orange-400 font-medium">Free Tier - Using DeepSeek R1</div>
                                    <div className="text-xs text-gray-400 mt-1">You can add your own API key for better performance, or upgrade for premium models.</div>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-center gap-3">
                                  <div className="w-3 h-3 rounded-full bg-green-400" />
                                  <div>
                                    <div className="text-xs text-green-400 font-medium">Paid Tier - Premium Models Available</div>
                                    <div className="text-xs text-gray-400 mt-1">You can use premium models or provide your own API key for more control.</div>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Provider Selection */}
                            <div className="space-y-3 mb-4">
                              {[
                                { id: 'deepseek', name: 'DeepSeek', note: 'Free' },
                                { id: 'openai', name: 'OpenAI', note: 'GPT-4' },
                                { id: 'anthropic', name: 'Anthropic', note: 'Claude' },
                                { id: 'xai', name: 'xAI', note: 'Grok' },
                                { id: 'google', name: 'Google', note: 'Gemini' }
                              ].map(provider => (
                                <label key={provider.id} className="flex items-center gap-3 cursor-pointer">
                                  <input
                                    type="radio"
                                    name="llm_provider"
                                    value={provider.id}
                                    checked={configData.llm_config.provider === provider.id}
                                    onChange={(e) => {
                                      updateConfigData(prev => ({
                                        ...prev,
                                        llm_config: {
                                          ...prev.llm_config,
                                          provider: e.target.value,
                                          use_platform_keys: e.target.value === 'deepseek' || (e.target.value === 'openai' && !userProfile?.requires_own_llm_keys),
                                          use_own_key: false
                                        }
                                      }))
                                    }}
                                    className="w-4 h-4 text-agents-decision focus:ring-agents-decision"
                                  />
                                  <div className="flex items-center justify-between flex-1">
                                    <div>
                                      <div className="text-xs text-bone-200 font-medium">{provider.name}</div>
                                      <div className="text-xs text-gray-400">{provider.note}</div>
                                    </div>
                                    {provider.id === 'deepseek' && (
                                      <div className="text-xs bg-green-900/30 text-green-400 px-2 py-1 rounded border border-green-700">
                                        Default
                                      </div>
                                    )}
                                  </div>
                                </label>
                              ))}
                            </div>

                            {/* Additional Options for Selected Provider */}
                            {configData.llm_config.provider === 'openai' && (
                              <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded space-y-4 mb-4">
                                {hasCredentialForProvider('openai') ? (
                                  // User has saved OpenAI credential
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <div className="w-2 h-2 rounded-full bg-green-400" />
                                      <span className="text-xs text-green-400">Using your saved OpenAI API key</span>
                                    </div>
                                    <button
                                      onClick={() => handleDeleteCredential('openai')}
                                      className="text-xs text-red-400 hover:underline"
                                    >
                                      Remove Key
                                    </button>
                                  </div>
                                ) : userProfile?.requires_own_llm_keys ? (
                                  // Free user - show upgrade OR add key
                                  <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                      <button
                                        disabled
                                        className="px-4 py-2 bg-blue-600/50 text-blue-300 text-xs rounded cursor-not-allowed opacity-50"
                                      >
                                        Upgrade for Managed Keys
                                      </button>
                                      <span className="text-xs text-gray-400">OR</span>
                                    </div>
                                    
                                    {/* API Key Input */}
                                    <div className="space-y-3">
                                      <div>
                                        <label className="block text-xs text-gray-400 mb-2">Enter your OpenAI API Key:</label>
                                        <input
                                          type="password"
                                          value={credentialInput}
                                          onChange={(e) => setCredentialInput(e.target.value)}
                                          placeholder="sk-..."
                                          className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors rounded"
                                        />
                                      </div>
                                      
                                      {credentialError && (
                                        <div className="text-xs text-red-400">{credentialError}</div>
                                      )}
                                      
                                      <div className="flex items-center justify-between">
                                        <div className="text-xs text-gray-500">
                                          Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">OpenAI Platform</a>
                                        </div>
                                        <button
                                          onClick={handleSaveCredential}
                                          disabled={!credentialInput.trim() || savingCredential}
                                          className="px-3 py-2 bg-agents-decision text-charcoal-900 text-xs rounded hover:bg-agents-decision/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                          {savingCredential ? 'Saving...' : 'Save Key'}
                                        </button>
                                      </div>
                                    </div>
                                  </div>
                                ) : (
                                  // Paid user - using managed keys with option to add own
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <div className="w-2 h-2 rounded-full bg-green-400" />
                                      <span className="text-xs text-green-400">Using managed OpenAI keys</span>
                                    </div>
                                    <button
                                      onClick={() => setCredentialInput('')}
                                      className="text-xs text-blue-400 hover:underline"
                                    >
                                      Add my own key instead
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Other providers that need API keys */}
                            {['anthropic', 'xai', 'google'].includes(configData.llm_config.provider) && (
                              <div className="bg-charcoal-800 border border-charcoal-600 p-4 rounded space-y-4 mb-4">
                                {hasCredentialForProvider(configData.llm_config.provider) ? (
                                  // User has saved credential for this provider
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <div className="w-2 h-2 rounded-full bg-green-400" />
                                      <span className="text-xs text-green-400">
                                        Using your saved {configData.llm_config.provider === 'anthropic' ? 'Anthropic' : configData.llm_config.provider === 'xai' ? 'xAI' : 'Google'} API key
                                      </span>
                                    </div>
                                    <button
                                      onClick={() => handleDeleteCredential(configData.llm_config.provider)}
                                      className="text-xs text-red-400 hover:underline"
                                    >
                                      Remove Key
                                    </button>
                                  </div>
                                ) : (
                                  // Need to add API key
                                  <div className="space-y-3">
                                    <div>
                                      <label className="block text-xs text-gray-400 mb-2">
                                        Enter your {configData.llm_config.provider === 'anthropic' ? 'Anthropic' : configData.llm_config.provider === 'xai' ? 'xAI' : 'Google'} API Key:
                                      </label>
                                      <input
                                        type="password"
                                        value={credentialInput}
                                        onChange={(e) => setCredentialInput(e.target.value)}
                                        placeholder="API key..."
                                        className="w-full bg-charcoal-900 border border-charcoal-700 text-bone-200 px-3 py-2 text-xs focus:border-agents-decision focus:outline-none transition-colors rounded"
                                      />
                                    </div>
                                    
                                    {credentialError && (
                                      <div className="text-xs text-red-400">{credentialError}</div>
                                    )}
                                    
                                    <div className="flex justify-end">
                                      <button
                                        onClick={handleSaveCredential}
                                        disabled={!credentialInput.trim() || savingCredential}
                                        className="px-3 py-2 bg-agents-decision text-charcoal-900 text-xs rounded hover:bg-agents-decision/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                      >
                                        {savingCredential ? 'Saving...' : 'Save Key'}
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Strategy Configuration */}
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-footnote text-bone-200 font-medium">USER PROMPT</h4>
                            </div>
                            <div>
                              <label className="block text-xs text-gray-400 mb-2">Your trading strategy:</label>
                              <textarea
                                value={configData.decision?.user_prompt || ''}
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

      {/* ggShot Modal */}
      {showGgShotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-charcoal-900 border border-charcoal-600 rounded-lg max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg text-bone-200 font-medium">ggShot Premium Signals</h3>
              <button
                onClick={() => setShowGgShotModal(false)}
                className="text-gray-400 hover:text-bone-200 transition-colors"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="bg-orange-900/20 border border-orange-700 p-4 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                  <div className="text-sm text-orange-400 font-medium">External Premium Service</div>
                </div>
                <p className="text-sm text-gray-300">
                  ggShot signals are provided by an external premium service. To access ggShot signals, you need to subscribe directly with them.
                </p>
              </div>

              <div className="text-sm text-gray-300">
                <p className="mb-3">
                  ggShot provides AI-filtered premium trading signals from 140+ crypto pairs with advanced confidence scoring.
                </p>
                <p className="text-xs text-gray-400">
                  This is a third-party service with its own subscription and pricing.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowGgShotModal(false)}
                  className="flex-1 px-4 py-2 bg-charcoal-700 text-bone-200 text-sm rounded hover:bg-charcoal-600 transition-colors"
                >
                  Cancel
                </button>
                <a
                  href="https://t.me/ggshot_filter_bot" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 px-4 py-2 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 transition-colors text-center"
                  onClick={() => setShowGgShotModal(false)}
                >
                  Subscribe to ggShot
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GGBotConfig