import { useEffect } from 'react'
import { useBotStore } from '@/store/botStore'

/**
 * Custom hook to manage WebSocket connection for bot status updates
 * This will integrate with your backend WebSocket service
 */
export function useBotWebSocket(userId: string, wsUrl?: string) {
  const { 
    loadBots, 
    connectWebSocket, 
    disconnectWebSocket, 
    isWebSocketConnected, 
    subscribeToBot, 
    getBotsByUser,
    isLoading
  } = useBotStore()
  
  const userBots = getBotsByUser(userId)
  
  useEffect(() => {
    let isMounted = true
    
    const initializeConnection = async (): Promise<(() => void) | undefined> => {
      try {
        console.log('🔗 Initializing bot WebSocket connection for user:', userId)
        
        // First, load bots from the API
        console.log('📡 Loading bots from API...')
        await loadBots(userId)
        
        if (!isMounted) return undefined // Component unmounted during load
        
        // Determine WebSocket URL
        let finalWsUrl = wsUrl
        if (!finalWsUrl) {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL
          if (apiUrl?.includes('localhost')) {
            finalWsUrl = `ws://localhost:8000/ws/bot-status/${userId}`
          } else {
            // For production, use wss protocol
            const host = apiUrl?.replace(/^https?:\/\//, '') || window.location.host
            finalWsUrl = `wss://${host}/ws/bot-status/${userId}`
          }
        }

        // Connect to WebSocket
        console.log('🔌 Connecting to WebSocket:', finalWsUrl)
        await connectWebSocket(userId, finalWsUrl)
        
        if (!isMounted) return undefined
        
        // Subscribe to all user's bots after connection
        const subscribeTimer = setTimeout(() => {
          if (isMounted) {
            const currentBots = getBotsByUser(userId)
            currentBots.forEach(bot => {
              subscribeToBot(bot.config_id)
            })
          }
        }, 1000) // Wait 1 second for connection to establish
        
        return () => clearTimeout(subscribeTimer)
      } catch (error) {
        console.error('❌ Failed to initialize bot WebSocket connection:', error)
        console.error('Error details:', {
          userId,
          apiUrl: process.env.NEXT_PUBLIC_API_URL,
          error: error instanceof Error ? error.message : error
        })
        return undefined
      }
    }
    
    const cleanupPromise = initializeConnection()

    // Cleanup on unmount
    return () => {
      isMounted = false
      cleanupPromise.then(cleanup => cleanup?.())
      disconnectWebSocket(userId)
    }
  }, [userId, wsUrl]) // Removed dependencies that cause reconnection loops

  return {
    isConnected: isWebSocketConnected(userId),
    userBots,
    isLoadingBots: isLoading
  }
}

/**
 * Hook for simulating real-time bot status updates (for demo purposes)
 * This simulates what will happen when your backend WebSocket sends status updates
 */
export function useBotStatusSimulator(userId: string, enabled = false) {
  const { updateBotStatus, getBotsByUser } = useBotStore()
  const userBots = getBotsByUser(userId)

  useEffect(() => {
    if (!enabled || userBots.length === 0) return

    const interval = setInterval(() => {
      // Simulate status updates for active bots
      userBots.forEach(bot => {
        if (!bot.isActive) return

        const now = new Date().toISOString()
        
        // Simulate realistic status transitions
        switch (bot.status.phase) {
          case 'idle':
            // Sometimes transition to extraction
            if (Math.random() < 0.3) {
              updateBotStatus(bot.config_id, {
                phase: 'extraction',
                color: 'blue',
                message: `Analyzing ${bot.crypto}/USDT signals...`,
                timestamp: now,
                showSpinner: true,
                context: {
                  symbol: `${bot.crypto}/USDT`,
                  timeframe: '1h'
                }
              })
            } else {
              // Update idle message
              const idleMessages = [
                `Monitoring ${bot.crypto} market conditions...`,
                `Scanning for ${bot.strategy} opportunities...`,
                `Waiting for high-confidence setup...`,
                `Processing market data feeds...`
              ]
              updateBotStatus(bot.config_id, {
                ...bot.status,
                message: idleMessages[Math.floor(Math.random() * idleMessages.length)],
                timestamp: now
              })
            }
            break
            
          case 'extraction':
            // Progress through extraction or move to decision
            if (Math.random() < 0.4) {
              updateBotStatus(bot.config_id, {
                phase: 'decision',
                color: 'green',
                message: 'Initializing 4-pillar validation...',
                timestamp: now,
                showSpinner: true,
                context: {
                  ...bot.status.context,
                  indicatorCount: 14
                }
              })
            } else {
              // Update extraction progress
              const extractionMessages = [
                `Fetching ${bot.crypto}/USDT price data...`,
                'Calculating RSI and MACD indicators...',
                'Analyzing support/resistance levels...',
                'Processing 14+ technical indicators...'
              ]
              updateBotStatus(bot.config_id, {
                ...bot.status,
                message: extractionMessages[Math.floor(Math.random() * extractionMessages.length)],
                timestamp: now
              })
            }
            break
            
          case 'decision':
            // Move to trading or back to idle
            if (Math.random() < 0.5) {
              const confidence = 65 + Math.random() * 25 // 65-90%
              updateBotStatus(bot.config_id, {
                phase: 'trading',
                color: 'orange',
                message: `Signal approved: ${bot.crypto}/USDT LONG (${confidence.toFixed(0)}% confidence)`,
                timestamp: now,
                showSpinner: true,
                context: {
                  ...bot.status.context,
                  confidence: confidence / 100,
                  direction: 'LONG',
                  entryPrice: 43000 + Math.random() * 5000
                }
              })
            } else {
              // Continue decision process
              const decisionMessages = [
                'Analyzing Pillar 1: Market Regime...',
                'Volume confirmation: 2.4x average',
                'RSI analysis: 68.2 on 1h timeframe',
                'Confidence scoring in progress...'
              ]
              updateBotStatus(bot.config_id, {
                ...bot.status,
                message: decisionMessages[Math.floor(Math.random() * decisionMessages.length)],
                timestamp: now
              })
            }
            break
            
          case 'trading':
            // Simulate trade execution then return to idle
            if (Math.random() < 0.3) {
              updateBotStatus(bot.config_id, {
                phase: 'idle',
                color: 'blue',
                message: `Trade completed. Monitoring for next signal...`,
                timestamp: now,
                showSpinner: false,
                context: {}
              })
            } else {
              // Update trading progress
              const pnl = -50 + Math.random() * 150 // -$50 to +$100
              updateBotStatus(bot.config_id, {
                ...bot.status,
                message: `Position monitoring: P&L $${pnl.toFixed(2)}`,
                timestamp: now,
                context: {
                  ...bot.status.context,
                  pnl
                }
              })
            }
            break
        }
      })
    }, 3000) // Update every 3 seconds

    return () => clearInterval(interval)
  }, [enabled, userBots, updateBotStatus])
}