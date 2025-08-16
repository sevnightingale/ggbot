'use client'

import React from 'react'
import GGBot from '@/components/GGBot'
import BotControlModal from '@/components/BotControlModal'
import { useBotStore, Bot } from '@/store/botStore'
import { useBotWebSocket } from '@/hooks/useBotWebSocket'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'

// Production user ID from backend
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

// Real ggShot trading data (117 approved signals from 2-week test period)
const realTradingData = {
  profitLossData: [
    { date: '28', profit: -78.38 },
    { date: '29', profit: 41.02 },
    { date: '30', profit: 192.44 },
    { date: '31', profit: 264.27 },
    { date: '01', profit: 334.40 },
    { date: '02', profit: 562.91 },
    { date: '03', profit: 735.44 },
    { date: '04', profit: 1187.95 },
    { date: '05', profit: 1436.84 },
    { date: '06', profit: 1789.33 },
    { date: '07', profit: 2156.44 },
    { date: '08', profit: 2389.21 },
    { date: '09', profit: 2534.88 },
    { date: '10', profit: 2798.76 },
    { date: '11', profit: 2934.23 },
    { date: '12', profit: 3055.68 },
    { date: '13', profit: 3055.68 }
  ],
  tradeStats: {
    totalTrades: 117,
    winCount: 83,
    lossCount: 27,
    neutralCount: 7,
    winRate: 70.9,
    lossRate: 23.1,
    neutralRate: 6.0,
    avgProfitPerTrade: 49.13,
    avgLossPerTrade: -37.87,
    totalProfit: 3055.68,
    avgTradeDuration: '4h 15m'
  },
  closedTrades: [
    { symbol: 'NEO/USDT', direction: 'LONG', pnl: -4.71, positionSize: 1000, entryPrice: 6.525 },
    { symbol: 'ROSE/USDT', direction: 'LONG', pnl: 12.51, positionSize: 1000, entryPrice: 0.0299 },
    { symbol: 'COTI/USDT', direction: 'LONG', pnl: 23.91, positionSize: 1000, entryPrice: 0.0574 },
    { symbol: 'CAKE/USDT', direction: 'LONG', pnl: 0.89, positionSize: 1000, entryPrice: 2.870 },
    { symbol: 'CHR/USDT', direction: 'LONG', pnl: 16.90, positionSize: 1000, entryPrice: 0.0983 },
    { symbol: 'STRK/USDT', direction: 'LONG', pnl: 44.03, positionSize: 1000, entryPrice: 0.137 },
    { symbol: 'TIA/USDT', direction: 'LONG', pnl: 43.88, positionSize: 1000, entryPrice: 1.851 },
    { symbol: 'PYTH/USDT', direction: 'LONG', pnl: 26.76, positionSize: 1000, entryPrice: 0.128 },
    { symbol: 'ZIL/USDT', direction: 'LONG', pnl: 25.07, positionSize: 1000, entryPrice: 0.0119 },
    { symbol: 'SKL/USDT', direction: 'LONG', pnl: 62.03, positionSize: 1000, entryPrice: 0.0220 },
    { symbol: 'APT/USDT', direction: 'LONG', pnl: 30.15, positionSize: 1000, entryPrice: 4.778 },
    { symbol: 'INJ/USDT', direction: 'LONG', pnl: 48.93, positionSize: 1000, entryPrice: 14.55 },
    { symbol: 'RUNE/USDT', direction: 'LONG', pnl: 28.36, positionSize: 1000, entryPrice: 1.439 },
    { symbol: 'NTRN/USDT', direction: 'LONG', pnl: 27.83, positionSize: 1000, entryPrice: 0.0945 },
    { symbol: 'ALPHA/USDT', direction: 'LONG', pnl: 77.29, positionSize: 1000, entryPrice: 0.0568 }
  ],
  openTrades: [
    { symbol: 'AVAX/USDT', direction: 'LONG', pnl: -7.0, positionSize: 750, entryPrice: 20.45 },
    { symbol: 'LINK/USDT', direction: 'SHORT', pnl: 23.0, positionSize: 750, entryPrice: 10.89 },
    { symbol: 'JASMY/USDT', direction: 'LONG', pnl: 2.0, positionSize: 750, entryPrice: 0.0173 },
    { symbol: 'RLC/USDT', direction: 'LONG', pnl: 13.0, positionSize: 750, entryPrice: 1.245 },
    { symbol: 'THETA/USDT', direction: 'SHORT', pnl: -18.5, positionSize: 750, entryPrice: 1.089 }
  ]
}

export default function DemoPage() {
  const [currentBotIndex, setCurrentBotIndex] = React.useState(0)
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [selectedBot, setSelectedBot] = React.useState<Bot | null>(null)
  const [livePositions, setLivePositions] = React.useState<Array<{
    id?: string;
    symbol: string;
    direction: string;
    pnl: number;
    positionSize: number;
    entryPrice: number;
    currentPrice: number;
    timeInTrade: string;
    leverage?: number;
    confidence?: number;
    reasoning_text?: string;
    volume_analysis?: string;
    signal_timeframe?: string;
  }>>([])
  const [expandedReasoningIds, setExpandedReasoningIds] = React.useState<Set<string>>(new Set())
  
  // Zustand store hooks
  const { 
    getBotsByUser, 
    updateBot,
    startBot,
    deleteBot,
    createBot,
    stopBot
  } = useBotStore()
  
  // WebSocket connection for real-time updates
  const { isLoadingBots } = useBotWebSocket(DEMO_USER_ID)

  // Demo completion handler - adds position when demo finishes
  React.useEffect(() => {
    console.log('🔍 Setting up demo WebSocket listener')
    
    // Function to start live P&L updates for a position
    const startLivePnLUpdates = (position: typeof livePositions[0]) => {
      const updatePnL = async () => {
        try {
          const response = await fetch('/api/live-position-data')
          const data = await response.json()
          
          if (data.status === 'success' && data.positions && data.positions.length > 0) {
            const latestData = data.positions[0]
            
            setLivePositions(prevPositions => 
              prevPositions.map(pos => 
                pos.id === position.id 
                  ? {
                      ...pos,
                      currentPrice: latestData.current_price || pos.entryPrice,
                      pnl: latestData.pnl || 0,
                      timeInTrade: latestData.time_in_trade || pos.timeInTrade
                    }
                  : pos
              )
            )
          }
        } catch (error) {
          console.error('Failed to update P&L:', error)
        }
      }

      // Update P&L every 15 seconds
      const interval = setInterval(updatePnL, 15000)
      
      // Store interval for cleanup (in a real app, you'd want better cleanup management)
      ;(window as unknown as { pnlUpdateInterval?: NodeJS.Timeout }).pnlUpdateInterval = interval
    }

    // Listen to all WebSocket messages on the window
    const handleWebSocketMessage = (event: MessageEvent) => {
      console.log('📨 WebSocket message received:', event.data)
      
      try {
        // Handle both string and object formats
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
        console.log('📊 Parsed message:', data)
        
        // Check for demo position creation message
        if (data.type === 'demo_position_create' && 
            data.config_id === 'e249bb49-0455-4596-9657-09bf9e14ca14' &&
            data.signal_data) {
          
          console.log('🎯 Demo position creation detected!')
          
          // Create position directly from signal data
          const signalData = data.signal_data
          const newPosition = {
            id: `demo-${Date.now()}`,
            symbol: signalData.symbol,
            direction: signalData.signal_direction,
            pnl: 0, // Start with 0 P&L
            positionSize: 1000, // Fixed demo size
            entryPrice: signalData.entry_price,
            currentPrice: signalData.entry_price, // Start with entry price
            timeInTrade: '0m',
            leverage: 10,
            confidence: Math.round(signalData.confidence_score * 100),
            reasoning_text: signalData.reasoning_text,
            volume_analysis: signalData.volume_analysis,
            signal_timeframe: signalData.signal_timeframe
          }
          
          setLivePositions([newPosition])
          
          // Start updating P&L with live prices
          startLivePnLUpdates(newPosition)
          
          console.log('🎯 Demo position created:', newPosition)
        }
        
        // Also check for the old demo completion format (backup)
        else if (data.type === 'bot_status_update' && 
            data.config_id === 'e249bb49-0455-4596-9657-09bf9e14ca14' &&
            data.status?.demo_mode && 
            data.status?.phase === 'idle' &&
            data.status?.message?.includes('Demo complete')) {
          
          console.log('🎯 Demo completion detected (backup method)')
          
          // Fetch the latest signal data and add it as a live position
          fetch('/api/live-position-data')
            .then(response => response.json())
            .then(apiData => {
              if (apiData.status === 'success' && apiData.positions && apiData.positions.length > 0) {
                // Take the first (latest) position and add it to live positions
                const latestSignal = apiData.positions[0]
                const newPosition = {
                  id: `demo-${Date.now()}`,
                  symbol: latestSignal.symbol,
                  direction: latestSignal.direction,
                  pnl: 0, // Start with 0 P&L
                  positionSize: latestSignal.position_size,
                  entryPrice: latestSignal.entry_price,
                  currentPrice: latestSignal.entry_price, // Start with entry price
                  timeInTrade: '0m',
                  leverage: latestSignal.leverage,
                  confidence: latestSignal.confidence,
                  reasoning_text: latestSignal.reasoning_text,
                  volume_analysis: latestSignal.volume_analysis,
                  signal_timeframe: latestSignal.signal_timeframe
                }
                
                setLivePositions([newPosition])
                
                // Start updating P&L with live prices
                startLivePnLUpdates(newPosition)
                
                console.log('🎯 Demo position created (backup):', newPosition)
              }
            })
            .catch(error => console.error('Failed to fetch signal data:', error))
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    // Add global event listener for WebSocket messages
    window.addEventListener('message', handleWebSocketMessage)
    
    // Also try to find existing WebSocket and add listener
    const checkForWebSocket = () => {
      const ws = (window as unknown as { ggbotWebSocket?: WebSocket }).ggbotWebSocket
      if (ws) {
        console.log('🔌 Found existing WebSocket, adding listener')
        ws.addEventListener('message', handleWebSocketMessage)
        return () => ws.removeEventListener('message', handleWebSocketMessage)
      }
      return undefined
    }
    
    const wsCleanup = checkForWebSocket()
    
    // Cleanup
    return () => {
      window.removeEventListener('message', handleWebSocketMessage)
      if (wsCleanup) wsCleanup()
    }
  }, [])

  // Live position data fetching - disabled for demo to start with empty trades
  // React.useEffect(() => {
  //   const fetchLivePositions = async () => {
  //     try {
  //       const response = await fetch('/api/live-position-data')
  //       const data = await response.json()
  //       
  //       if (data.status === 'success' && data.positions) {
  //         // Transform API data to match frontend structure
  //         const transformedPositions = data.positions.map((pos: {
  //           id?: string;
  //           symbol: string;
  //           direction: string;
  //           pnl: number;
  //           position_size: number;
  //           entry_price: number;
  //           current_price?: number;
  //           time_in_trade?: string;
  //           leverage: number;
  //           confidence: number;
  //           reasoning_text?: string;
  //           volume_analysis?: string;
  //           signal_timeframe?: string;
  //         }) => ({
  //           id: pos.id || `${pos.symbol}-${Date.now()}`,
  //           symbol: pos.symbol,
  //           direction: pos.direction,
  //           pnl: pos.pnl,
  //           positionSize: pos.position_size,
  //           entryPrice: pos.entry_price,
  //           currentPrice: pos.current_price || pos.entry_price,
  //           timeInTrade: pos.time_in_trade || 'N/A',
  //           leverage: pos.leverage,
  //           confidence: pos.confidence,
  //           reasoning_text: pos.reasoning_text,
  //           volume_analysis: pos.volume_analysis,
  //           signal_timeframe: pos.signal_timeframe
  //         }))
  //         
  //         setLivePositions(transformedPositions)
  //         setLastUpdated(new Date().toLocaleTimeString())
  //       }
  //     } catch (error) {
  //       console.error('Failed to fetch live positions:', error)
  //     }
  //   }

  //   // Initial fetch
  //   fetchLivePositions()

  //   // Set up polling every 15 seconds for live updates (reduced from 5s to save memory)
  //   const interval = setInterval(fetchLivePositions, 15000)

  //   return () => clearInterval(interval)
  // }, [])
  
  const demoBots = getBotsByUser(DEMO_USER_ID)

  // Note: Bots are now loaded automatically via useBotWebSocket hook
  // Real backend data will be fetched on component mount

  // Add virtual "create bot" state
  const isCreatingBot = currentBotIndex >= demoBots.length
  const currentBot = isCreatingBot 
    ? { 
        config_id: "create-new",
        instance_name: "new-bot",
        name: "Create New", 
        config_type: "demo" as const,
        strategy: "meanrev",
        crypto: "BTC",
        riskLevel: "medium",
        userId: DEMO_USER_ID,
        isActive: false,
        createdAt: new Date(),
        status: {
          phase: "idle" as const,
          color: "gray" as const,
          message: "Click to configure your ggbot",
          timestamp: new Date().toISOString()
        }
      }
    : demoBots[currentBotIndex]

  const handleBotClick = (bot: Bot) => {
    if (bot.name === 'Create New' || isCreatingBot) {
      // Handle creating new bot
      setSelectedBot(bot)
      setIsModalOpen(true)
      return
    }
    
    // Handle clicking existing bot - open configuration
    setSelectedBot(bot)
    setIsModalOpen(true)
  }

  const handleModalSave = async (updatedBot: Bot) => {
    try {
      if (updatedBot.config_id === 'create-new') {
        // Create new bot using Zustand action
        await createBot({
          instance_name: `${updatedBot.name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`,
          name: updatedBot.name,
          config_type: 'demo',
          strategy: updatedBot.strategy,
          crypto: updatedBot.crypto,
          riskLevel: updatedBot.riskLevel,
          userId: DEMO_USER_ID,
          isActive: false
        })
        
        // Navigate to new bot
        setCurrentBotIndex(demoBots.length)
      } else {
        // Update existing bot using Zustand action
        updateBot(updatedBot.config_id, {
          name: updatedBot.name,
          strategy: updatedBot.strategy,
          crypto: updatedBot.crypto,
          riskLevel: updatedBot.riskLevel
        })
      }
      
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to save bot:', error)
      // Error handling - could show toast notification
    }
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setSelectedBot(null)
  }

  const handleStartBot = async (config_id: string) => {
    try {
      const bot = demoBots.find(b => b.config_id === config_id)
      if (bot?.isActive) {
        await stopBot(config_id)
      } else {
        await startBot(config_id)
      }
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to toggle bot:', error)
    }
  }

  const handleDeleteBot = async (config_id: string) => {
    try {
      await deleteBot(config_id)
      
      // Adjust current index if we deleted a bot before current position
      if (currentBotIndex >= demoBots.length - 1) {
        setCurrentBotIndex(Math.max(0, demoBots.length - 2))
      }
      
      setIsModalOpen(false)
      setSelectedBot(null)
    } catch (error) {
      console.error('Failed to delete bot:', error)
    }
  }

  const toggleReasoningExpansion = (tradeId: string) => {
    setExpandedReasoningIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tradeId)) {
        newSet.delete(tradeId)
      } else {
        newSet.add(tradeId)
      }
      return newSet
    })
  }

  const nextBot = () => {
    setCurrentBotIndex((prev) => prev + 1)
  }

  const prevBot = () => {
    setCurrentBotIndex((prev) => Math.max(0, prev - 1))
  }

  // Show loading state while fetching bots
  if (isLoadingBots) {
    return (
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-bone-300">Loading bots...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-900 relative">
      {/* Connection Status - Hidden for now to avoid layout interference */}
      {/* <div className="absolute top-4 right-4 flex items-center gap-2 z-50">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
        <span className="text-footnote text-gray-400">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div> */}

      {/* 3-Column Layout with Sharp Dividers */}
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="w-full max-w-[1680px] mx-auto grid grid-cols-[1fr_400px_1fr] gap-8 relative">
          
          {/* Left Column - Historical Performance */}
          <div className="hidden lg:block">
            <div className="flex flex-col min-h-[500px] gap-6">
              
              {/* Profit/Loss Chart Card */}
              <div className="relative p-3 corner-top-left flex-1 min-h-[280px]">
                <h3 className="text-subheader text-bone-200 mb-4">Profit/Loss</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={realTradingData.profitLossData}>
                      <XAxis 
                        dataKey="date" 
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: '#9ca3af' }}
                      />
                      <YAxis 
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: '#9ca3af' }}
                        tickFormatter={(value) => `$${value}`}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="profit" 
                        stroke="#10b981" 
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              
              {/* Trade Statistics Card */}
              <div className="relative p-3 corner-top-left min-h-[200px]">
                <h3 className="text-subheader text-bone-200 mb-4">Trade Statistics</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># of closed trades</span>
                    <span className="text-footnote text-bone-200">{realTradingData.tradeStats.totalTrades}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># and % of trades won</span>
                    <span className="text-footnote text-green-400">{realTradingData.tradeStats.winCount} ({realTradingData.tradeStats.winRate}%)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># and % of trades lost</span>
                    <span className="text-footnote text-red-400">{realTradingData.tradeStats.lossCount} ({realTradingData.tradeStats.lossRate}%)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># and % of trades neutral</span>
                    <span className="text-footnote text-gray-400">{realTradingData.tradeStats.neutralCount} ({realTradingData.tradeStats.neutralRate}%)</span>
                  </div>
                  <div className="gradient-divider"></div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">Average profit per trade (%)</span>
                    <span className="text-footnote text-green-400">{realTradingData.tradeStats.avgProfitPerTrade}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">Average loss per trade (%)</span>
                    <span className="text-footnote text-red-400">{realTradingData.tradeStats.avgLossPerTrade}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">Average trade duration</span>
                    <span className="text-footnote text-bone-200">{realTradingData.tradeStats.avgTradeDuration}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center Column - ggbot Component (Fixed Width) */}
          <div className="flex flex-col items-center justify-center">
            {/* ggbot with flanking arrows/plus */}
            <div className="flex items-center gap-10 mb-6 px-4">
              <button 
                className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  currentBotIndex === 0 
                    ? 'text-bone-500 cursor-not-allowed opacity-50' 
                    : 'text-bone-300 hover:text-bone-200 hover:scale-110'
                }`}
                onClick={prevBot}
                disabled={currentBotIndex === 0}
              >
                ‹
              </button>
              
              <GGBot
                name={currentBot.name}
                status={currentBot.status.phase}
                message={currentBot.status.message}
                showSpinner={currentBot.status.showSpinner}
                demoMode={currentBot.config_id === 'e249bb49-0455-4596-9657-09bf9e14ca14' && currentBot.status.phase !== 'inactive'}
                onClick={() => handleBotClick(currentBot)}
              />
              
              <button 
                className="text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center text-bone-300 hover:text-bone-200 hover:scale-110"
                onClick={isCreatingBot ? () => handleBotClick(currentBot) : nextBot}
              >
                {isCreatingBot ? '○' : (currentBotIndex === demoBots.length - 1 ? '+' : '›')}
              </button>
            </div>

            {/* Dots navigation */}
            <div className="flex justify-center">
              <div className="flex items-center gap-3">
                {demoBots.map((_, index) => (
                  <button
                    key={index}
                    className={`w-3 h-3 rounded-full transition-all duration-200 ${
                      index === currentBotIndex
                        ? 'bg-bone-200'
                        : 'bg-bone-500 hover:bg-bone-300'
                    }`}
                    onClick={() => setCurrentBotIndex(index)}
                  />
                ))}
                {isCreatingBot && (
                  <button
                    className="w-3 h-3 rounded-full bg-bone-200 transition-all duration-200"
                    onClick={() => setCurrentBotIndex(demoBots.length)}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Activity */}
          <div className="hidden lg:block">
            <div className="flex flex-col min-h-[500px] gap-6">
              
              {/* Open Trades Table */}
              <div className="relative p-3 corner-top-right flex-1 min-h-[320px]">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-subheader text-bone-200">Open Trades</h3>
                  <span className="text-footnote text-gray-500">
                    {livePositions.length > 0 ? `${livePositions.length} position${livePositions.length !== 1 ? 's' : ''}` : 'No positions'}
                  </span>
                </div>
                <div className="gradient-divider mb-4"></div>
                <div className="overflow-x-auto overflow-y-auto max-h-[260px]">
                  <table className="w-full text-footnote">
                    <thead className="text-gray-400 border-b border-gray-700">
                      <tr>
                        <th className="text-left py-1 pr-2">PnL</th>
                        <th className="text-left py-1 px-1">Symbol</th>
                        <th className="text-left py-1 px-1">Size</th>
                        <th className="text-left py-1 px-1">Dir</th>
                        <th className="text-left py-1 px-1">Entry</th>
                        <th className="text-left py-1 px-1">Price</th>
                        <th className="text-left py-1 pl-1">Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {livePositions.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="text-center py-8 text-gray-500">
                            <div className="flex flex-col items-center gap-2">
                              <span className="text-2xl">📊</span>
                              <span>No active positions</span>
                              <span className="text-xs">Start ggbot-01 demo to see AI trading in action</span>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        livePositions.map((trade, index) => {
                        const tradeId = trade.id || `trade-${index}`
                        const isExpanded = expandedReasoningIds.has(tradeId)
                        
                        return (
                          <React.Fragment key={tradeId}>
                            <tr 
                              className={`${index % 2 === 1 ? 'bg-gray-800 bg-opacity-30' : ''} cursor-pointer hover:bg-gray-700/30 transition-colors`}
                              onClick={() => toggleReasoningExpansion(tradeId)}
                            >
                              <td className={`py-1 pr-2 ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(0)}
                              </td>
                              <td className="py-1 px-1 text-bone-200">{trade.symbol.replace('/USDT', '')}</td>
                              <td className="py-1 px-1 text-gray-400">{trade.positionSize}</td>
                              <td className={`py-1 px-1 ${trade.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                                {trade.direction.slice(0, 1)}
                              </td>
                              <td className="py-1 px-1 text-gray-400">{trade.entryPrice.toFixed(3)}</td>
                              <td className="py-1 px-1 text-gray-400">
                                {trade.currentPrice.toFixed(3)}
                              </td>
                              <td className="py-1 pl-1 text-gray-400 flex items-center justify-between">
                                {trade.timeInTrade}
                                <span className="text-agent-extraction ml-1">
                                  {isExpanded ? '▼' : '▶'}
                                </span>
                              </td>
                            </tr>
                            
                            {/* AI Reasoning Expansion */}
                            {isExpanded && (
                              <tr className="bg-charcoal-800/50">
                                <td colSpan={7} className="p-3">
                                  <div className="space-y-3">
                                    <div className="flex items-center gap-2 border-b border-charcoal-600 pb-2">
                                      <span className="text-lg">🧠</span>
                                      <h4 className="text-footnote text-agent-extraction font-medium">
                                        4-Pillar AI Analysis (Confidence: {trade.confidence || 0}%)
                                      </h4>
                                    </div>
                                    
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-footnote">
                                      <div>
                                        <div className="text-gray-400 mb-1">Market Regime Assessment:</div>
                                        <div className="text-bone-200 text-xs leading-relaxed">
                                          {trade.reasoning_text?.includes('regime') ? 
                                            trade.reasoning_text.split('regime')[1]?.split('.')[0] + '...' : 
                                            "Trend alignment and volatility analysis confirmed"}
                                        </div>
                                      </div>
                                      
                                      <div>
                                        <div className="text-gray-400 mb-1">Volume Confirmation:</div>
                                        <div className="text-bone-200 text-xs">
                                          {trade.volume_analysis || "Volume confirmation analysis completed"}
                                        </div>
                                      </div>
                                      
                                      <div>
                                        <div className="text-gray-400 mb-1">Signal Timeframe:</div>
                                        <div className="text-bone-200 text-xs">
                                          {trade.signal_timeframe || "1h"}
                                        </div>
                                      </div>
                                      
                                      <div>
                                        <div className="text-gray-400 mb-1">4-Pillar Framework:</div>
                                        <div className="text-bone-200 text-xs grid grid-cols-2 gap-1">
                                          <span>• Market Regime ✓</span>
                                          <span>• Signal Confirmation ✓</span>
                                          <span>• Multi-timeframe Context ✓</span>
                                          <span>• Risk Assessment ✓</span>
                                        </div>
                                      </div>
                                    </div>
                                    
                                    {trade.reasoning_text && (
                                      <div className="pt-2 border-t border-charcoal-700">
                                        <div className="text-gray-400 mb-1 text-footnote">Full AI Reasoning:</div>
                                        <div className="text-bone-200 text-xs leading-relaxed max-h-20 overflow-y-auto">
                                          {trade.reasoning_text}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        )
                      }))}
                    </tbody>
                  </table>
                </div>
              </div>
              
              {/* Closed Trades Table */}
              <div className="relative p-3 corner-top-right flex-1 min-h-[320px]">
                <h3 className="text-subheader text-bone-200 mb-4">Closed Trades</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="overflow-x-auto overflow-y-auto max-h-[260px]">
                  <table className="w-full text-footnote">
                    <thead className="text-gray-400 border-b border-gray-700">
                      <tr>
                        <th className="text-left py-1 pr-2">PnL</th>
                        <th className="text-left py-1 px-1">Symbol</th>
                        <th className="text-left py-1 px-1">Size</th>
                        <th className="text-left py-1 px-1">Dir</th>
                        <th className="text-left py-1 pl-1">Entry</th>
                      </tr>
                    </thead>
                    <tbody>
                      {realTradingData.closedTrades.map((trade, index) => (
                        <tr key={index} className={`${index % 2 === 1 ? 'bg-gray-800 bg-opacity-30' : ''}`}>
                          <td className={`py-1 pr-2 ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(0)}
                          </td>
                          <td className="py-1 px-1 text-bone-200">{trade.symbol.replace('/USDT', '')}</td>
                          <td className="py-1 px-1 text-gray-400">{trade.positionSize}</td>
                          <td className={`py-1 px-1 ${trade.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.direction.slice(0, 1)}
                          </td>
                          <td className="py-1 pl-1 text-gray-400">{trade.entryPrice.toFixed(3)}</td>
                        </tr>
                      ))}</tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bot Count Info */}
      {demoBots.length > 0 && (
        <div className="absolute bottom-4 left-4 text-footnote text-gray-400">
          Showing {demoBots.length} bot{demoBots.length !== 1 ? 's' : ''}
        </div>
      )}

      {/* Control Modal */}
      {selectedBot && (
        <BotControlModal
          bot={selectedBot}
          isOpen={isModalOpen}
          onClose={handleModalClose}
          onSave={handleModalSave}
          onStart={handleStartBot}
          onDelete={handleDeleteBot}
          mode="demo"
        />
      )}
    </div>
  )
}