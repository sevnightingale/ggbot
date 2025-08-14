import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'

// Bot interfaces aligned with backend config_instances table
export interface BotStatus {
  phase: 'idle' | 'extraction' | 'decision' | 'trading'
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
  connectWebSocket: (userId: string, wsUrl: string) => Promise<void>
  disconnectWebSocket: (userId: string) => void
  subscribeToBot: (config_id: string) => void
  isWebSocketConnected: (userId: string) => boolean
  
  // API Actions (for future backend integration)
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
              ? { ...bot.status, phase: 'idle', message: 'Bot started, waiting for signals...' }
              : { ...bot.status, phase: 'idle', message: 'Bot stopped' }
          })
        }
        return { bots: newBots }
      }),

      // WebSocket Management Actions
      connectWebSocket: async (userId: string, wsUrl: string) => {
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

      // API Actions (placeholder for future backend integration)
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
          // TODO: Replace with actual API call to update config_instances.status = 'active'
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
          // TODO: Replace with actual API call to update config_instances.status = 'inactive'
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
          // TODO: Replace with actual API call to delete from config_instances
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