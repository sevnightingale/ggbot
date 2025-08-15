'use client'

import React from 'react'
import GGBot from '@/components/GGBot'
import BotControlModal from '@/components/BotControlModal'
import { useBotStore, Bot } from '@/store/botStore'
import { useBotWebSocket } from '@/hooks/useBotWebSocket'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'

// Production user ID from backend
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

// Sample profit/loss data (from last 2 weeks of signals_cleaned_fix.csv)
const profitLossData = [
  { date: '08-12', profit: 0 },
  { date: '08-12', profit: 25.07 },
  { date: '08-12', profit: 87.10 },
  { date: '08-13', profit: 130.95 },
  { date: '08-13', profit: 147.74 },
  { date: '08-13', profit: 164.50 },
  { date: '08-13', profit: 188.39 },
  { date: '08-13', profit: 232.23 },
  { date: '08-13', profit: 276.07 },
  { date: '08-13', profit: 295.95 },
  { date: '08-13', profit: 296.84 },
  { date: '08-13', profit: 284.07 },
  { date: '08-13', profit: 279.36 }
]

// Trade statistics (calculated from signals_cleaned_fix.csv)
const tradeStats = {
  totalTrades: 20,
  winCount: 15,
  lossCount: 3,
  neutralCount: 2,
  winRate: 75.0,
  lossRate: 15.0,
  neutralRate: 10.0,
  avgProfitPerTrade: 18.97,
  avgLossPerTrade: -3.69,
  avgTradeDuration: '5h 24m'
}

// Open trades (mock data based on recent ggshot_filter entries)
const openTrades = [
  { symbol: 'ZRO/USDT', direction: 'SHORT', pnl: -12.45, positionSize: 500, entryPrice: 2.220 },
  { symbol: 'MKR/USDT', direction: 'SHORT', pnl: 34.67, positionSize: 250, entryPrice: 1896.20 },
  { symbol: 'STORJ/USDT', direction: 'SHORT', pnl: -8.92, positionSize: 750, entryPrice: 0.268 },
  { symbol: 'ONT/USDT', direction: 'SHORT', pnl: 15.23, positionSize: 600, entryPrice: 0.139 },
  { symbol: 'PYTH/USDT', direction: 'SHORT', pnl: -3.45, positionSize: 400, entryPrice: 0.123 }
]

// Closed trades (from recent signals_cleaned_fix.csv entries)
const closedTrades = [
  { symbol: 'SKL/USDT', direction: 'LONG', pnl: 62.03, positionSize: 1000, entryPrice: 0.022 },
  { symbol: 'CHR/USDT', direction: 'LONG', pnl: 16.90, positionSize: 800, entryPrice: 0.098 },
  { symbol: 'STRK/USDT', direction: 'LONG', pnl: 44.03, positionSize: 600, entryPrice: 0.137 },
  { symbol: 'TIA/USDT', direction: 'LONG', pnl: 43.88, positionSize: 500, entryPrice: 1.851 },
  { symbol: 'PYTH/USDT', direction: 'LONG', pnl: 26.76, positionSize: 750, entryPrice: 0.128 },
  { symbol: 'QTUM/USDT', direction: 'LONG', pnl: 22.62, positionSize: 400, entryPrice: 2.194 },
  { symbol: 'ZIL/USDT', direction: 'LONG', pnl: 25.07, positionSize: 900, entryPrice: 0.012 }
]

export default function DemoPage() {
  const [currentBotIndex, setCurrentBotIndex] = React.useState(0)
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [selectedBot, setSelectedBot] = React.useState<Bot | null>(null)
  
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
        <div className="w-full max-w-7xl mx-auto grid grid-cols-3 relative">
          
          {/* Left Vertical Divider */}
          <div className="absolute left-1/3 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-bone-300 to-transparent opacity-60 transform -translate-x-0.5"></div>
          
          {/* Right Vertical Divider */}
          <div className="absolute right-1/3 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-bone-300 to-transparent opacity-60 transform translate-x-0.5"></div>
          
          {/* Left Column - Historical Performance */}
          <div className="hidden lg:block pr-8">
            <div className="flex flex-col min-h-[500px] gap-6">
              
              {/* Profit/Loss Chart Card */}
              <div className="relative p-6 corner-top-left flex-1 min-h-[280px]">
                <h3 className="text-body text-bone font-medium mb-4">Profit/Loss</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={profitLossData}>
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
              <div className="relative p-6 corner-top-left min-h-[200px]">
                <h3 className="text-body text-bone font-medium mb-4">Trade Statistics</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># of closed trades</span>
                    <span className="text-body text-bone font-medium">{tradeStats.totalTrades}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># and % of trades won</span>
                    <span className="text-body text-green-400 font-medium">{tradeStats.winCount} ({tradeStats.winRate}%)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># and % of trades lost</span>
                    <span className="text-body text-red-400 font-medium">{tradeStats.lossCount} ({tradeStats.lossRate}%)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400"># and % of trades neutral</span>
                    <span className="text-body text-gray-400 font-medium">{tradeStats.neutralCount} ({tradeStats.neutralRate}%)</span>
                  </div>
                  <div className="gradient-divider"></div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">Average profit per trade (%)</span>
                    <span className="text-body text-green-400 font-medium">{tradeStats.avgProfitPerTrade}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">Average loss per trade (%)</span>
                    <span className="text-body text-red-400 font-medium">{tradeStats.avgLossPerTrade}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-footnote text-gray-400">Average trade duration</span>
                    <span className="text-body text-bone font-medium">{tradeStats.avgTradeDuration}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center Column - ggbot Component (Fixed Width) */}
          <div className="flex flex-col items-center justify-center px-8">
            {/* ggbot with flanking arrows/plus */}
            <div className="flex items-center gap-8 mb-6">
              <button 
                className={`text-3xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
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
                onClick={() => handleBotClick(currentBot)}
              />
              
              <button 
                className="text-3xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center text-bone-300 hover:text-bone-200 hover:scale-110"
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
          <div className="hidden lg:block pl-8">
            <div className="flex flex-col min-h-[500px] gap-6">
              
              {/* Open Trades Table */}
              <div className="relative p-6 corner-top-right flex-1 min-h-[240px]">
                <h3 className="text-body text-bone font-medium mb-4">Open Trades</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="overflow-y-auto max-h-[180px]">
                  <table className="w-full text-footnote">
                    <thead className="text-gray-400 border-b border-gray-700">
                      <tr>
                        <th className="text-left py-2">PnL ($)</th>
                        <th className="text-left py-2">Symbol</th>
                        <th className="text-left py-2">Size ($)</th>
                        <th className="text-left py-2">Direction</th>
                        <th className="text-left py-2">Entry</th>
                      </tr>
                    </thead>
                    <tbody>
                      {openTrades.map((trade, index) => (
                        <tr key={index} className={`${index % 2 === 1 ? 'bg-gray-800 bg-opacity-30' : ''}`}>
                          <td className={`py-2 font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                          </td>
                          <td className="py-2 text-bone">{trade.symbol}</td>
                          <td className="py-2 text-gray-400">{trade.positionSize}</td>
                          <td className={`py-2 ${trade.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.direction}
                          </td>
                          <td className="py-2 text-gray-400">{trade.entryPrice.toFixed(3)}</td>
                        </tr>
                      ))}</tbody>
                  </table>
                </div>
              </div>
              
              {/* Closed Trades Table */}
              <div className="relative p-6 corner-top-right flex-1 min-h-[240px]">
                <h3 className="text-body text-bone font-medium mb-4">Closed Trades</h3>
                <div className="gradient-divider mb-4"></div>
                <div className="overflow-y-auto max-h-[180px]">
                  <table className="w-full text-footnote">
                    <thead className="text-gray-400 border-b border-gray-700">
                      <tr>
                        <th className="text-left py-2">PnL ($)</th>
                        <th className="text-left py-2">Symbol</th>
                        <th className="text-left py-2">Size ($)</th>
                        <th className="text-left py-2">Direction</th>
                        <th className="text-left py-2">Entry</th>
                      </tr>
                    </thead>
                    <tbody>
                      {closedTrades.map((trade, index) => (
                        <tr key={index} className={`${index % 2 === 1 ? 'bg-gray-800 bg-opacity-30' : ''}`}>
                          <td className={`py-2 font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                          </td>
                          <td className="py-2 text-bone">{trade.symbol}</td>
                          <td className="py-2 text-gray-400">{trade.positionSize}</td>
                          <td className={`py-2 ${trade.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.direction}
                          </td>
                          <td className="py-2 text-gray-400">{trade.entryPrice.toFixed(3)}</td>
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