import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { apiClient } from '@/lib/api'

// Helper functions for V2 API data transformation
function extractStrategyFromConfig(configData: any): string {
  // Try to determine strategy from decision prompt or config type
  const userPrompt = configData.decision?.user_prompt?.toLowerCase() || ''
  if (userPrompt.includes('rsi')) return 'meanrev'
  if (userPrompt.includes('macd') || userPrompt.includes('trend')) return 'trend'
  if (userPrompt.includes('momentum') || userPrompt.includes('breakout')) return 'momentum'
  return 'ai' // Default for sophisticated strategies
}

function extractCryptoFromPair(selectedPair: string): string {
  // Extract crypto from trading pair (e.g., "BTC/USDT" -> "BTC")
  return selectedPair?.split('/')[0] || 'BTC'
}

function extractRiskLevel(configData: any): string {
  // Determine risk level from trading configuration
  const leverage = configData.trading?.leverage || 1
  const accountPercent = configData.trading?.position_sizing?.account_percent || 5
  
  if (leverage <= 2 && accountPercent <= 3) return 'low'
  if (leverage <= 5 && accountPercent <= 7) return 'medium'
  return 'high'
}

// Bot interfaces aligned with backend config_instances table
export interface BotStatus {
  phase: 'inactive' | 'idle' | 'extraction' | 'decision' | 'trading'
  color: 'gray' | 'blue' | 'green' | 'orange'
  message: string
  timestamp: string
  showSpinner?: boolean
  context?: {
    symbol?: string
    timeframe?: string
    direction?: string
    progress?: string
    confidence?: number
    indicatorCount?: number
    pillarNumber?: number
    volumeRatio?: number
    entryPrice?: number
    pnl?: number
  }
}

export interface Bot {
  // Backend identifiers
  config_id: string          // Primary key from config_instances table
  instance_name: string      // From config_instances.instance_name
  config_type: 'ggshot' | 'demo' | 'production'
  
  // Configuration data
  name: string              // Display name (can differ from instance_name)
  strategy?: string         // meanrev, momentum, trend, ai
  crypto?: string          // BTC, ETH, SOL
  riskLevel?: string       // low, medium, high
  
  // Runtime state
  status: BotStatus
  isActive: boolean        // Maps to config_instances.status = 'active'
  
  // Metadata
  createdAt: Date
  lastRun?: Date
  userId: string           // For multi-user support
}

export interface WebSocketConnection {
  ws: WebSocket | null
  isConnected: boolean
  reconnectAttempts: number
  lastError?: string
}

interface BotStore {
  // State
  bots: Map<string, Bot>           // Keyed by config_id
  connections: Map<string, WebSocketConnection>  // Keyed by userId
  isLoading: boolean
  error: string | null
  
  // Bot Management Actions
  addBot: (bot: Bot) => void
  updateBot: (config_id: string, updates: Partial<Bot>) => void
  removeBot: (config_id: string) => void
  getBotById: (config_id: string) => Bot | undefined
  getBotsByUser: (userId: string) => Bot[]
  getActiveBots: (userId: string) => Bot[]
  
  // Status Management Actions
  updateBotStatus: (config_id: string, status: BotStatus) => void
  setBotActive: (config_id: string, isActive: boolean) => void
  
  // WebSocket Management Actions
  connectWebSocket: (userId: string, wsUrl: string, onDemoMessage?: (data: Record<string, unknown>) => void) => Promise<void>
  disconnectWebSocket: (userId: string) => void
  subscribeToBot: (config_id: string) => void
  isWebSocketConnected: (userId: string) => boolean
  
  // API Actions
  loadBots: (userId: string) => Promise<void>
  createBot: (botData: Omit<Bot, 'config_id' | 'createdAt' | 'status'>) => Promise<Bot>
  startBot: (config_id: string) => Promise<void>
  stopBot: (config_id: string) => Promise<void> 
  deleteBot: (config_id: string) => Promise<void>
  
  // Utility Actions
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export const useBotStore = create<BotStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial State
      bots: new Map(),
      connections: new Map(),
      isLoading: false,
      error: null,

      // Bot Management Actions
      addBot: (bot: Bot) => set((state) => {
        const newBots = new Map(state.bots)
        newBots.set(bot.config_id, bot)
        return { bots: newBots }
      }),

      updateBot: (config_id: string, updates: Partial<Bot>) => set((state) => {
        const newBots = new Map(state.bots)
        const existingBot = newBots.get(config_id)
        if (existingBot) {
          newBots.set(config_id, { ...existingBot, ...updates })
        }
        return { bots: newBots }
      }),

      removeBot: (config_id: string) => set((state) => {
        const newBots = new Map(state.bots)
        newBots.delete(config_id)
        return { bots: newBots }
      }),

      getBotById: (config_id: string) => {
        return get().bots.get(config_id)
      },

      getBotsByUser: (userId: string) => {
        return Array.from(get().bots.values()).filter(bot => bot.userId === userId)
      },

      getActiveBots: (userId: string) => {
        return Array.from(get().bots.values()).filter(
          bot => bot.userId === userId && bot.isActive
        )
      },

      // Status Management Actions  
      updateBotStatus: (config_id: string, status: BotStatus) => set((state) => {
        const newBots = new Map(state.bots)
        const bot = newBots.get(config_id)
        if (bot) {
          newBots.set(config_id, { 
            ...bot, 
            status,
            lastRun: new Date() // Update last activity timestamp
          })
        }
        return { bots: newBots }
      }),

      setBotActive: (config_id: string, isActive: boolean) => set((state) => {
        const newBots = new Map(state.bots)
        const bot = newBots.get(config_id)
        if (bot) {
          newBots.set(config_id, { 
            ...bot, 
            isActive,
            status: isActive 
              ? { ...bot.status, phase: 'idle', color: 'blue', message: 'Bot started, waiting for signals...' }
              : { ...bot.status, phase: 'inactive', color: 'gray', message: 'Bot stopped' }
          })
        }
        return { bots: newBots }
      }),

      // WebSocket Management Actions
      connectWebSocket: async (userId: string, wsUrl: string, onDemoMessage?: (data: Record<string, unknown>) => void) => {
        const state = get()
        const existing = state.connections.get(userId)
        
        // Don't reconnect if already connected
        if (existing?.isConnected) return

        try {
          const ws = new WebSocket(wsUrl)
          
          // Set up connection in connecting state
          const newConnections = new Map(state.connections)
          newConnections.set(userId, {
            ws,
            isConnected: false,
            reconnectAttempts: existing?.reconnectAttempts || 0
          })
          set({ connections: newConnections })

          ws.onopen = () => {
            console.log(`WebSocket connected for user ${userId}`)
            set((state) => {
              const newConnections = new Map(state.connections)
              const conn = newConnections.get(userId)
              if (conn) {
                newConnections.set(userId, { 
                  ...conn, 
                  isConnected: true,
                  reconnectAttempts: 0,
                  lastError: undefined
                })
              }
              return { connections: newConnections }
            })
          }

          ws.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data)
              
              // Forward demo messages to callback if provided
              if (onDemoMessage && (data.type === 'demo_position_create' || data.status === 'demo_started')) {
                onDemoMessage(data)
              }
              
              if (data.type === 'bot_status_update') {
                // Extract config_id from bot_id (format: "ggshot-e249bb49")  
                const config_id = data.config_id || data.bot_id
                
                if (config_id && data.status) {
                  get().updateBotStatus(config_id, {
                    phase: data.status.phase,
                    color: data.status.color,
                    message: data.status.message,
                    timestamp: data.status.timestamp,
                    showSpinner: ['extraction', 'decision', 'trading'].includes(data.status.phase),
                    context: data.status.context
                  })
                }
              }
            } catch (error) {
              console.error('Failed to parse WebSocket message:', error)
            }
          }

          ws.onclose = (event) => {
            console.log(`WebSocket disconnected for user ${userId}:`, event.code)
            set((state) => {
              const newConnections = new Map(state.connections)
              const conn = newConnections.get(userId)
              if (conn) {
                newConnections.set(userId, { 
                  ...conn, 
                  isConnected: false,
                  lastError: `Connection closed: ${event.code}`
                })
              }
              return { connections: newConnections }
            })

            // Auto-reconnect after delay (exponential backoff)
            const attempts = existing?.reconnectAttempts || 0
            if (attempts < 5) {
              const delay = Math.min(1000 * Math.pow(2, attempts), 30000)
              setTimeout(() => {
                get().connectWebSocket(userId, wsUrl)
              }, delay)
            }
          }

          ws.onerror = (error) => {
            console.error(`WebSocket error for user ${userId}:`, error)
            set((state) => {
              const newConnections = new Map(state.connections)
              const conn = newConnections.get(userId)
              if (conn) {
                newConnections.set(userId, { 
                  ...conn, 
                  lastError: 'Connection error',
                  reconnectAttempts: conn.reconnectAttempts + 1
                })
              }
              return { connections: newConnections }
            })
          }

        } catch (error) {
          console.error(`Failed to create WebSocket for user ${userId}:`, error)
          set((state) => {
            const newConnections = new Map(state.connections)
            newConnections.set(userId, {
              ws: null,
              isConnected: false,
              reconnectAttempts: (existing?.reconnectAttempts || 0) + 1,
              lastError: 'Connection failed'
            })
            return { connections: newConnections }
          })
        }
      },

      disconnectWebSocket: (userId: string) => {
        const state = get()
        const connection = state.connections.get(userId)
        
        if (connection?.ws) {
          connection.ws.close()
        }

        const newConnections = new Map(state.connections)
        newConnections.delete(userId)
        set({ connections: newConnections })
      },

      subscribeToBot: (config_id: string) => {
        // Send subscription message to WebSocket
        // Implementation depends on your WebSocket protocol
        const state = get()
        const bot = state.bots.get(config_id)
        if (bot) {
          const connection = state.connections.get(bot.userId)
          if (connection?.isConnected && connection.ws) {
            connection.ws.send(JSON.stringify({
              type: 'subscribe',
              bot_id: config_id
            }))
          }
        }
      },

      isWebSocketConnected: (userId: string) => {
        return get().connections.get(userId)?.isConnected || false
      },

      // API Actions
      loadBots: async (userId: string) => {
        set({ isLoading: true, error: null })
        
        try {
          // V2 API integration with authentication
          const configs = await apiClient.listConfigs()
          
          if (!configs || !Array.isArray(configs)) {
            throw new Error('Invalid response format from configs API')
          }
          
          console.log('📊 V2 API Response from /api/v2/config:', configs)
          console.log('📊 Type:', typeof configs, 'Length:', configs.length)
          
          // Transform V2 config data to frontend Bot interface
          const transformedBots: Bot[] = configs.length > 0 ? configs.map((configData: any) => ({
            config_id: configData.config_id,
            instance_name: configData.config_name || `Bot-${configData.config_id.slice(0, 8)}`,
            config_type: 'production', // V2 configs are production by default
            name: configData.config_name || `Bot-${configData.config_id.slice(0, 8)}`,
            strategy: extractStrategyFromConfig(configData.config_data),
            crypto: extractCryptoFromPair(configData.config_data.selected_pair),
            riskLevel: extractRiskLevel(configData.config_data),
            status: {
              phase: 'inactive', // Will be updated via bot status endpoint
              color: 'gray',
              message: 'Ready to start',
              timestamp: new Date().toISOString()
            },
            isActive: false, // Will be updated via bot status endpoint
            createdAt: configData.created_at ? new Date(configData.created_at) : new Date(),
            lastRun: configData.updated_at ? new Date(configData.updated_at) : undefined,
            userId: userId
          })) : []
          
          // Clear existing bots for this user and add new ones
          const newBots = new Map(get().bots)
          // Remove existing user bots
          for (const [configId, bot] of newBots) {
            if (bot.userId === userId) {
              newBots.delete(configId)
            }
          }
          // Add new bots
          transformedBots.forEach(bot => {
            newBots.set(bot.config_id, bot)
          })
          
          set({ bots: newBots, isLoading: false })
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to load bots'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      createBot: async (botData) => {
        set({ isLoading: true, error: null })
        
        try {
          // TODO: Replace with actual API call
          const newBot: Bot = {
            ...botData,
            config_id: `bot-${Date.now()}`, // Temporary ID generation
            createdAt: new Date(),
            status: {
              phase: 'idle',
              color: 'gray', 
              message: 'Ready to start...',
              timestamp: new Date().toISOString()
            }
          }

          get().addBot(newBot)
          set({ isLoading: false })
          return newBot
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to create bot'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      startBot: async (config_id: string) => {
        set({ isLoading: true, error: null })
        
        try {
          const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/api/v2/bot/${config_id}/start`, {
            method: 'POST'
          })
          
          if (!response.ok) {
            throw new Error(`Failed to start bot: ${response.status}`)
          }
          
          get().setBotActive(config_id, true)
          set({ isLoading: false })
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to start bot'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      stopBot: async (config_id: string) => {
        set({ isLoading: true, error: null })
        
        try {
          const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/api/v2/bot/${config_id}/stop`, {
            method: 'POST'
          })
          
          if (!response.ok) {
            throw new Error(`Failed to stop bot: ${response.status}`)
          }
          
          get().setBotActive(config_id, false)
          set({ isLoading: false })
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to stop bot'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      deleteBot: async (config_id: string) => {
        set({ isLoading: true, error: null })
        
        try {
          const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/api/v2/bot/${config_id}/status`, {
            method: 'DELETE'
          })
          
          if (!response.ok) {
            throw new Error(`Failed to delete bot: ${response.status}`)
          }
          
          get().removeBot(config_id)
          set({ isLoading: false })
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to delete bot'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      // Utility Actions
      clearError: () => set({ error: null }),
      setLoading: (loading: boolean) => set({ isLoading: loading })
    })),
    { name: 'bot-store' }
  )
)

// Selectors for common queries
export const selectBotsByUser = (userId: string) => (state: BotStore) => 
  Array.from(state.bots.values()).filter(bot => bot.userId === userId)

export const selectActiveBots = (userId: string) => (state: BotStore) =>
  Array.from(state.bots.values()).filter(bot => bot.userId === userId && bot.isActive)

export const selectBotById = (config_id: string) => (state: BotStore) =>
  state.bots.get(config_id)