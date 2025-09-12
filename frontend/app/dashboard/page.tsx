'use client'

import React from 'react'
import GGBot from '@/components/GGBot'
import GGBotConfig from '@/components/GGBotConfig'
import FloatingActionButtons from '@/components/FloatingActionButtons'
import { useBotStore, Bot } from '@/store/botStore'
import { useDashboardSSE } from '@/hooks/useDashboardSSE'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'
import { createClient } from '@/lib/supabase'
import type { User } from '@supabase/supabase-js'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api'

export default function DashboardPage() {
  // Core state - selectedConfigId as single source of truth
  const [selectedConfigId, setSelectedConfigId] = React.useState<string | null>(null)
  const [isConfigOpen, setIsConfigOpen] = React.useState(false)
  const [selectedBot, setSelectedBot] = React.useState<Bot | null>(null)
  
  // Real user data state (replacing demo mock data)
  const [userProfitLossData, setUserProfitLossData] = React.useState<Array<{ date: string; profit: number }>>([])
  const [userTradeStats, setUserTradeStats] = React.useState({
    totalTrades: 0,
    winCount: 0,
    lossCount: 0,
    neutralCount: 0,
    winRate: 0,
    lossRate: 0,
    neutralRate: 0,
    avgProfitPerTrade: 0,
    avgLossPerTrade: 0,
    totalProfit: 0,
    avgTradeDuration: '0m'
  })
  
  // Paper trading account state
  const [paperAccountData, setPaperAccountData] = React.useState({
    initial_balance: 10000.0,
    current_balance: 10000.0,
    total_pnl: 0.0,
    total_return_pct: 0.0
  })
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
  const [isLoadingBotData, setIsLoadingBotData] = React.useState(false)

  // Decision history state
  interface DecisionHistoryItem {
    decision_id: string;
    symbol: string;
    action: string;
    confidence: number;
    reasoning: string;
    prompt?: string;
    market_data?: Record<string, unknown>;
    decision_data?: Record<string, unknown>;
    created_at: string;
  }
  
  const [decisionHistory, setDecisionHistory] = React.useState<DecisionHistoryItem[]>([])
  const [selectedDecision, setSelectedDecision] = React.useState<DecisionHistoryItem | null>(null)

  // Supabase client and router for logout
  const supabase = createClient()
  const router = useRouter()

  // Real Supabase auth integration
  const [user, setUser] = React.useState<User | null>(null)
  const [isLoadingAuth, setIsLoadingAuth] = React.useState(true)
  
  // Get current user from Supabase
  React.useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
      setIsLoadingAuth(false)
    }
    getUser()
  }, [supabase.auth])
  
  const userId = user?.id
  
  // Zustand store hooks
  const { 
    getBotsByUser, 
    getBotById,
    startBot,
    deleteBot,
    stopBot,
    loadBots
  } = useBotStore()
  
  // Load bots from V2 API on mount (only when authenticated)
  React.useEffect(() => {
    if (userId) {
      console.log('📡 Dashboard loading bots for userId:', userId)
      loadBots(userId) // Load bots from V2 API with current userId
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]) // Only depend on userId to prevent infinite re-renders
  
  // Get user's bots directly from store (reactive to store changes)
  const userBots = userId ? getBotsByUser(userId) : []
  
  // Log when bots change for debugging
  React.useEffect(() => {
    console.log(`📊 Dashboard found ${userBots.length} bots for userId: ${userId}`)
  }, [userBots.length, userId])
  const selectedBotData = selectedConfigId ? getBotById(selectedConfigId) : null
  
  // 🔥 SSE connection for real-time updates (replaces WebSocket!)
  const { isLoading: isLoadingBots } = useDashboardSSE(userId)
  
  // Auto-select first bot if none selected and bots exist
  React.useEffect(() => {
    if (!selectedConfigId && userBots.length > 0) {
      setSelectedConfigId(userBots[0].config_id)
    }
  }, [selectedConfigId, userBots])

  // Fetch bot-specific data when selection changes
  React.useEffect(() => {
    if (selectedConfigId) {
      fetchBotData(selectedConfigId)
    }
  }, [selectedConfigId])

  // V2 API integration with authentication
  const fetchBotData = async (configId: string) => {
    setIsLoadingBotData(true)
    try {
      const baseUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
      
      // Use apiClient for authenticated requests
      const [metricsResponse, tradesResponse, positionsResponse, accountResponse, decisionsResponse] = await Promise.all([
        apiClient.authenticatedFetch(`${baseUrl}/api/v2/bot/${configId}/metrics`).then(r => r.json()),
        apiClient.authenticatedFetch(`${baseUrl}/api/v2/bot/${configId}/trades`).then(r => r.json()),
        apiClient.authenticatedFetch(`${baseUrl}/api/v2/bot/${configId}/positions`).then(r => r.json()),
        // Add account endpoint call (we'll create this)
        apiClient.authenticatedFetch(`${baseUrl}/api/v2/bot/${configId}/account`).then(r => r.json()).catch(() => ({ status: 'error' })),
        // Add decisions endpoint call
        apiClient.authenticatedFetch(`${baseUrl}/api/v2/bot/${configId}/decisions`).then(r => r.json()).catch(() => ({ status: 'error' }))
      ])

      // Update state with real API data
      if (metricsResponse.status === 'success') {
        const metrics = metricsResponse.metrics
        setUserProfitLossData(metrics.profit_loss_data || [])
        setUserTradeStats(metrics.trade_stats || {
          totalTrades: 0,
          winCount: 0,
          lossCount: 0,
          neutralCount: 0,
          winRate: 0,
          lossRate: 0,
          neutralRate: 0,
          avgProfitPerTrade: 0,
          avgLossPerTrade: 0,
          totalProfit: 0,
          avgTradeDuration: '0m'
        })
        
        // Update paper account data from metrics
        setPaperAccountData({
          initial_balance: metrics.initial_balance || 10000.0,
          current_balance: metrics.account_balance || 10000.0,
          total_pnl: metrics.total_pnl || 0.0,
          total_return_pct: metrics.initial_balance > 0 ? 
            (((metrics.account_balance || 10000.0) - (metrics.initial_balance || 10000.0)) / (metrics.initial_balance || 10000.0)) * 100 : 0.0
        })
      }
      
      // Also update paper account data from account endpoint if available
      if (accountResponse.status === 'success') {
        const account = accountResponse.account
        setPaperAccountData({
          initial_balance: account.initial_balance || 10000.0,
          current_balance: account.current_balance || 10000.0,
          total_pnl: account.total_pnl || 0.0,
          total_return_pct: account.total_return_pct || 0.0
        })
      }

      if (positionsResponse.status === 'success') {
        setLivePositions(positionsResponse.positions || [])
      }

      // Trades response processing removed - using decision history instead

      if (decisionsResponse.status === 'success') {
        setDecisionHistory(decisionsResponse.decisions || [])
      }

      console.log('✅ V2 API data loaded:', {
        metrics: metricsResponse,
        trades: tradesResponse,
        positions: positionsResponse,
        decisions: decisionsResponse
      })
      
    } catch (error) {
      console.error('❌ Failed to fetch bot data from V2 API:', error)
      // Reset to empty state on error
      setUserProfitLossData([])
      setUserTradeStats({
        totalTrades: 0,
        winCount: 0,
        lossCount: 0,
        neutralCount: 0,
        winRate: 0,
        lossRate: 0,
        neutralRate: 0,
        avgProfitPerTrade: 0,
        avgLossPerTrade: 0,
        totalProfit: 0,
        avgTradeDuration: '0m'
      })
      setLivePositions([])
      setDecisionHistory([])
    } finally {
      setIsLoadingBotData(false)
    }
  }

  // TODO: Implement real-time Supabase subscriptions
  React.useEffect(() => {
    if (selectedConfigId) {
      // TODO: Set up Supabase real-time subscription for selected bot
      // const subscription = supabase
      //   .channel(`bot:${selectedConfigId}`)
      //   .on('postgres_changes', { event: '*', schema: 'public' }, handleUpdate)
      //   .subscribe()
      // 
      // return () => subscription.unsubscribe()
    }
  }, [selectedConfigId])

  // Handle bot selection (updated to use selectedConfigId pattern)
  const handleBotClick = (bot: Bot) => {
    setSelectedBot(bot)
    setIsConfigOpen(true)
  }

  const handleConfigClose = () => {
    setIsConfigOpen(false)
    setSelectedBot(null)
  }

  const handleConfigSaved = (configId: string) => {
    // Reload bots to get the newly created one
    if (userId) {
      loadBots(userId)
    }
    // Select the newly created bot
    setSelectedConfigId(configId)
  }

  const handleDeleteBot = async (config_id: string) => {
    try {
      await deleteBot(config_id)
      
      // If we deleted the selected bot, select another one
      if (selectedConfigId === config_id) {
        const remainingBots = userBots.filter(b => b.config_id !== config_id)
        if (remainingBots.length > 0) {
          setSelectedConfigId(remainingBots[0].config_id)
        } else {
          setSelectedConfigId(null)
        }
      }
    } catch (error) {
      console.error('Failed to delete bot:', error)
    }
  }

  // Handle floating action button clicks (no demo-specific logic)
  const handleFloatingStart = async (config_id: string) => {
    try {
      const bot = userBots.find(b => b.config_id === config_id)
      if (!bot) return

      if (bot.isActive) {
        await stopBot(config_id)
      } else {
        await startBot(config_id)
      }
    } catch (error) {
      console.error('Failed to handle floating start action:', error)
    }
  }

  const handleFloatingAdd = () => {
    console.log('handleFloatingAdd called')
    setSelectedBot(null)
    setIsConfigOpen(true)
    console.log('isConfigOpen set to true, selectedBot set to null')
  }

  // Logout handler
  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/login')
    } catch (error) {
      console.error('Error logging out:', error)
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

  // Bot selection handlers (updated for selectedConfigId pattern)
  // const handleBotSelect = (configId: string) => {
  //   setSelectedConfigId(configId)
  // }

  const nextBot = () => {
    if (userBots.length === 0) return
    const currentIndex = selectedConfigId ? userBots.findIndex(b => b.config_id === selectedConfigId) : -1
    const nextIndex = currentIndex < userBots.length - 1 ? currentIndex + 1 : 0
    setSelectedConfigId(userBots[nextIndex].config_id)
  }

  const prevBot = () => {
    if (userBots.length === 0) return
    const currentIndex = selectedConfigId ? userBots.findIndex(b => b.config_id === selectedConfigId) : -1
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : userBots.length - 1
    setSelectedConfigId(userBots[prevIndex].config_id)
  }

  // Authentication guard
  if (isLoadingAuth) {
    return (
      <div className="min-h-screen bg-charcoal-700 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-bone-300">Loading...</p>
        </div>
      </div>
    )
  }
  
  if (!user) {
    router.push('/login')
    return null
  }

  // Show loading state while fetching bots
  if (isLoadingBots) {
    return (
      <div className="min-h-screen bg-charcoal-700 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-bone-300">Loading bots...</p>
        </div>
      </div>
    )
  }

  // Show empty state if no bots
  if (userBots.length === 0) {
    return (
      <div className="min-h-screen bg-charcoal-700 relative">
        <div className="flex items-center justify-center p-8 min-h-screen">
          <div className="flex flex-col items-center gap-4 max-w-md text-center">
            <div className="text-6xl mb-4">🤖</div>
            <h2 className="text-xl text-bone-200 mb-2">Welcome to GGBot</h2>
            <p className="text-gray-400 mb-6">You don&apos;t have any bots configured yet. Create your first bot to get started with AI-powered trading.</p>
            <div className="flex gap-4 flex-col sm:flex-row">
              <button
                onClick={handleFloatingAdd}
                className="px-6 py-3 bg-bone-200 text-charcoal-900 rounded-lg hover:bg-bone-300 transition-colors"
              >
                Create Your First Bot
              </button>
              <button
                onClick={handleLogout}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Sheet Config */}
        <GGBotConfig 
          bot={selectedBot}
          isOpen={isConfigOpen}
          onClose={handleConfigClose}
          onConfigSaved={handleConfigSaved}
        />
      </div>
    )
  }

  // Get current bot for display
  const currentBot = selectedBotData || userBots[0]
  // const currentIndex = selectedConfigId ? userBots.findIndex(b => b.config_id === selectedConfigId) : 0

  return (
    <div className="min-h-screen bg-charcoal-700 relative">
      {/* 3-Column Layout with Sharp Dividers */}
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="w-full max-w-[1680px] mx-auto grid grid-cols-[1fr_400px_1fr] gap-8 relative">
          
          {/* Left Column - Historical Performance */}
          <div className="hidden lg:block">
            <div className="flex flex-col min-h-[500px] gap-6">
              
              {/* Combined Paper Trading Account & Profit/Loss Chart Card */}
              <div className="relative p-3 corner-top-left flex-1 min-h-[320px] shadow-lg shadow-black/10">
                <h3 className="text-subheader text-bone-200 mb-4">Paper Trading Performance</h3>
                <div className="gradient-divider mb-4"></div>
                
                {isLoadingBotData ? (
                  <div className="h-[240px] flex items-center justify-center">
                    <div className="w-6 h-6 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Account Summary Section */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-footnote text-gray-400">Started</span>
                          <span className="text-footnote text-gray-400">${paperAccountData.initial_balance.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-footnote text-gray-400">Balance</span>
                          <span className="text-footnote text-bone-200 font-medium">${paperAccountData.current_balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-footnote text-gray-400">P&L</span>
                          <span className={`text-footnote font-medium ${
                            paperAccountData.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {paperAccountData.total_pnl >= 0 ? '+' : ''}${paperAccountData.total_pnl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-footnote text-gray-400">Return</span>
                          <span className={`text-footnote font-medium ${
                            paperAccountData.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {paperAccountData.total_return_pct >= 0 ? '+' : ''}{paperAccountData.total_return_pct.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="gradient-divider"></div>
                    
                    {/* Chart Section */}
                    {userProfitLossData.length > 0 ? (
                      <div className="h-[140px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={userProfitLossData}>
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
                    ) : (
                      <div className="h-[140px] flex items-center justify-center text-gray-500">
                        <div className="text-center">
                          <div className="text-2xl mb-2">📈</div>
                          <p className="text-footnote">No trading history yet</p>
                          <p className="text-xs">Start your bot to see performance data</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Trade Statistics Card */}
              <div className="relative p-3 corner-bottom-left min-h-[200px] shadow-lg shadow-black/10">
                <h3 className="text-subheader text-bone-200 mb-4">Trade Statistics</h3>
                <div className="gradient-divider mb-4"></div>
                {isLoadingBotData ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-6 h-6 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400"># of closed trades</span>
                      <span className="text-footnote text-bone-200">{userTradeStats.totalTrades}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400"># and % of trades won</span>
                      <span className="text-footnote text-green-400">{userTradeStats.winCount} ({userTradeStats.winRate}%)</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400"># and % of trades lost</span>
                      <span className="text-footnote text-red-400">{userTradeStats.lossCount} ({userTradeStats.lossRate}%)</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400"># and % of trades neutral</span>
                      <span className="text-footnote text-gray-400">{userTradeStats.neutralCount} ({userTradeStats.neutralRate}%)</span>
                    </div>
                    <div className="gradient-divider"></div>
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400">Average profit per trade (%)</span>
                      <span className="text-footnote text-green-400">{userTradeStats.avgProfitPerTrade}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400">Average loss per trade (%)</span>
                      <span className="text-footnote text-red-400">{userTradeStats.avgLossPerTrade}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-footnote text-gray-400">Average trade duration</span>
                      <span className="text-footnote text-bone-200">{userTradeStats.avgTradeDuration}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Center Column - ggbot Component (Fixed Width) */}
          <div className="flex flex-col items-center justify-center">
            {/* ggbot with flanking arrows */}
            <div className="flex items-center gap-10 mb-6 px-4">
              <button 
                className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  userBots.length <= 1
                    ? 'text-bone-500 cursor-not-allowed opacity-50' 
                    : 'text-bone-300 hover:text-bone-200 hover:scale-110'
                }`}
                onClick={prevBot}
                disabled={userBots.length <= 1}
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
                className={`text-4xl transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  userBots.length <= 1
                    ? 'text-bone-500 cursor-not-allowed opacity-50' 
                    : 'text-bone-300 hover:text-bone-200 hover:scale-110'
                }`}
                onClick={nextBot}
                disabled={userBots.length <= 1}
              >
                ›
              </button>
            </div>

            {/* Dots navigation */}
            <div className="flex justify-center mb-4">
              <div className="flex items-center gap-3">
                {userBots.map((bot) => (
                  <button
                    key={bot.config_id}
                    className={`w-3 h-3 rounded-full transition-all duration-200 ${
                      bot.config_id === selectedConfigId
                        ? 'bg-bone-200'
                        : 'bg-bone-500 hover:bg-bone-300'
                    }`}
                    onClick={() => setSelectedConfigId(bot.config_id)}
                  />
                ))}
              </div>
            </div>

            {/* Floating Action Buttons - positioned below dots */}
            <div>
              <FloatingActionButtons 
                currentBot={currentBot}
                onStart={handleFloatingStart}
                onDelete={handleDeleteBot}
                onAdd={handleFloatingAdd}
              />
            </div>
          </div>

          {/* Right Column - Activity */}
          <div className="hidden lg:block">
            <div className="flex flex-col min-h-[500px] gap-6">
              
              {/* Open Trades Table */}
              <div className="relative p-3 corner-top-right flex-1 min-h-[320px] shadow-lg shadow-black/10">
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
                            {isLoadingBotData ? (
                              <div className="flex flex-col items-center gap-2">
                                <div className="w-6 h-6 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
                                <span>Loading positions...</span>
                              </div>
                            ) : (
                              <div className="flex flex-col items-center gap-2">
                                <span className="text-2xl">📊</span>
                                <span>No active positions</span>
                                <span className="text-xs">Start your bot to begin trading</span>
                              </div>
                            )}
                          </td>
                        </tr>
                      ) : (
                        livePositions.map((trade, index) => {
                        const tradeId = trade.id || `trade-${index}`
                        const isExpanded = expandedReasoningIds.has(tradeId)
                        
                        return (
                          <React.Fragment key={tradeId}>
                            <tr 
                              className={`${index % 2 === 1 ? 'bg-gray-600 bg-opacity-30' : ''} cursor-pointer hover:bg-gray-500/30 transition-colors`}
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
                              <tr className="bg-charcoal-600/50">
                                <td colSpan={7} className="p-3">
                                  <div className="space-y-3">
                                    <div className="flex items-center gap-2 border-b border-charcoal-600 pb-2">
                                      <span className="text-lg">🧠</span>
                                      <h4 className="text-footnote text-agent-extraction font-medium">
                                        AI Analysis (Confidence: {trade.confidence || 0}%)
                                      </h4>
                                    </div>
                                    
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-footnote">
                                      <div>
                                        <div className="text-gray-400 mb-1">Signal Timeframe:</div>
                                        <div className="text-bone-200 text-xs">
                                          {trade.signal_timeframe || "1h"}
                                        </div>
                                      </div>
                                      
                                      <div>
                                        <div className="text-gray-400 mb-1">Volume Analysis:</div>
                                        <div className="text-bone-200 text-xs">
                                          {trade.volume_analysis || "Volume confirmation completed"}
                                        </div>
                                      </div>
                                    </div>
                                    
                                    {trade.reasoning_text && (
                                      <div className="pt-2 border-t border-charcoal-700">
                                        <div className="text-gray-400 mb-1 text-footnote">AI Reasoning:</div>
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
              
              {/* TODO: Bring back closed trades in combined trades card later */}
              {/* 
              <div className="relative p-3 corner-bottom-right flex-1 min-h-[320px] shadow-lg shadow-black/10">
                <h3 className="text-subheader text-bone-200 mb-4">Closed Trades</h3>
                <div className="gradient-divider mb-4"></div>
                ... closed trades table content ...
              </div>
              */}

              {/* Your ggbots Activity Card */}
              <div className="relative p-3 corner-bottom-right flex-1 min-h-[320px] shadow-lg shadow-black/10">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-subheader text-bone-200">Your ggbots Activity</h3>
                  <span className="text-footnote text-gray-500">
                    {decisionHistory.length > 0 ? `${decisionHistory.length} decision${decisionHistory.length !== 1 ? 's' : ''}` : 'No activity'}
                  </span>
                </div>
                <div className="gradient-divider mb-4"></div>
                <div className="overflow-y-auto max-h-[260px]">
                  {decisionHistory.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      {isLoadingBotData ? (
                        <div className="flex flex-col items-center gap-2">
                          <div className="w-6 h-6 border-2 border-bone-300 border-t-transparent rounded-full animate-spin"></div>
                          <span>Loading activity...</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2">
                          <span className="text-2xl">🧠</span>
                          <span>No activity yet</span>
                          <span className="text-xs">Decision history will appear here</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {decisionHistory.map((decision, index) => (
                        <div
                          key={decision.decision_id}
                          className={`p-3 rounded-lg cursor-pointer hover:bg-gray-600/30 transition-colors border border-gray-700/50 ${
                            index % 2 === 1 ? 'bg-gray-600/20' : ''
                          }`}
                          onClick={() => setSelectedDecision(decision)}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <span className="text-footnote text-gray-400">
                                {new Date(decision.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                              </span>
                              <span className={`text-footnote font-medium px-2 py-1 rounded ${
                                decision.action === 'enter' && decision.decision_data?.direction === 'LONG' ? 'bg-green-500/20 text-green-400' :
                                decision.action === 'enter' && decision.decision_data?.direction === 'SHORT' ? 'bg-red-500/20 text-red-400' :
                                decision.action === 'exit' ? 'bg-blue-500/20 text-blue-400' :
                                'bg-gray-500/20 text-gray-400'
                              }`}>
                                {decision.action === 'enter' 
                                  ? `ENTER ${decision.decision_data?.direction || 'TRADE'}`
                                  : decision.action.toUpperCase()}
                              </span>
                              <span className="text-footnote text-bone-300">
                                {decision.symbol.replace('/USDT', '')}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-footnote text-gray-400">
                                {Math.round((decision.confidence || 0) * 100)}%
                              </span>
                              <span className="text-agent-extraction">▶</span>
                            </div>
                          </div>
                          <div className="text-xs text-gray-400 truncate">
                            {decision.reasoning?.substring(0, 120)}...
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bot Count Info */}
      {userBots.length > 0 && (
        <div className="absolute bottom-4 left-4 text-footnote text-gray-400">
          Showing {userBots.length} bot{userBots.length !== 1 ? 's' : ''} • Selected: {currentBot.name}
        </div>
      )}

      {/* Decision Detail Modal */}
      {selectedDecision && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-charcoal-700 rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto w-full">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <span className="text-2xl">🧠</span>
                  <div>
                    <h2 className="text-xl text-bone-200 font-display">Decision Details</h2>
                    <p className="text-gray-400 text-footnote">
                      {new Date(selectedDecision.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedDecision(null)}
                  className="text-gray-400 hover:text-bone-200 text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Decision Summary */}
              <div className="mb-6 p-4 bg-charcoal-600 rounded-lg">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-gray-400 text-footnote">Action</span>
                    <div className={`text-footnote font-medium px-2 py-1 rounded mt-1 inline-block ${
                      selectedDecision.action === 'enter' && selectedDecision.decision_data?.direction === 'LONG' ? 'bg-green-500/20 text-green-400' :
                      selectedDecision.action === 'enter' && selectedDecision.decision_data?.direction === 'SHORT' ? 'bg-red-500/20 text-red-400' :
                      selectedDecision.action === 'exit' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {selectedDecision.action === 'enter' 
                        ? `ENTER ${selectedDecision.decision_data?.direction || 'TRADE'}`
                        : selectedDecision.action.toUpperCase()}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-footnote">Symbol</span>
                    <div className="text-bone-200 font-medium">{selectedDecision.symbol}</div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-footnote">Confidence</span>
                    <div className="text-bone-200 font-medium">
                      {Math.round((selectedDecision.confidence || 0) * 100)}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-footnote">Decision ID</span>
                    <div className="text-gray-400 text-xs font-mono">
                      {selectedDecision.decision_id.substring(0, 8)}...
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Reasoning */}
              <div className="mb-6">
                <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                  <span className="text-agent-decision">🤖</span>
                  AI Reasoning
                </h3>
                <div className="bg-charcoal-800 p-4 rounded-lg">
                  <div className="text-bone-200 text-sm leading-relaxed whitespace-pre-wrap">
                    {selectedDecision.reasoning || 'No reasoning provided'}
                  </div>
                </div>
              </div>

              {/* Market Data Context */}
              {selectedDecision.market_data && (
                <div className="mb-6">
                  <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                    <span className="text-agent-extraction">📊</span>
                    Market Context
                  </h3>
                  <div className="bg-charcoal-800 p-4 rounded-lg">
                    <pre className="text-xs text-gray-300 overflow-x-auto">
                      {JSON.stringify(selectedDecision.market_data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Decision Data */}
              {selectedDecision.decision_data && (
                <div className="mb-6">
                  <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                    <span className="text-agent-trading">⚡</span>
                    Decision Parameters
                  </h3>
                  <div className="bg-charcoal-800 p-4 rounded-lg">
                    <pre className="text-xs text-gray-300 overflow-x-auto">
                      {JSON.stringify(selectedDecision.decision_data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* LLM Prompt */}
              {selectedDecision.prompt && (
                <div className="mb-6">
                  <h3 className="text-bone-200 font-medium mb-3 flex items-center gap-2">
                    <span>💬</span>
                    LLM Prompt
                  </h3>
                  <div className="bg-charcoal-800 p-4 rounded-lg">
                    <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
                      {selectedDecision.prompt}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bottom Sheet Config */}
      <GGBotConfig 
        bot={selectedBot}
        isOpen={isConfigOpen}
        onClose={handleConfigClose}
        onConfigSaved={handleConfigSaved}
      />
    </div>
  )
}