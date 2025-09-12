import { useEffect, useRef, useState } from 'react'
import { useBotStore } from '@/store/botStore'
import { createClient } from '@/lib/supabase'

/**
 * 🔥 NEW SSE Hook - Replaces WebSocket complexity!
 * 
 * Uses Server-Sent Events to stream unified dashboard data:
 * - Bot configurations and status
 * - Open positions and P&L  
 * - Recent decisions
 * - Account summaries
 * 
 * Updates every 5 seconds with auto-reconnect and Last-Event-ID support.
 */
export function useDashboardSSE(userId: string | undefined) {
  const eventSourceRef = useRef<EventSource | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastEventId, setLastEventId] = useState<string | null>(null)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  
  const { 
    setBotsFromSSE,
    updatePositionsFromSSE,
    updateDecisionsFromSSE,
    updateAccountsFromSSE,
    isLoading
  } = useBotStore()

  useEffect(() => {
    if (!userId) {
      console.log('⏳ SSE hook waiting for userId...')
      return
    }

    let isMounted = true
    const supabase = createClient()

    const connectSSE = async () => {
      try {
        // Get current auth token
        const { data: { session } } = await supabase.auth.getSession()
        if (!session?.access_token) {
          console.error('❌ No auth token for SSE connection')
          setConnectionError('Authentication required')
          return
        }

        // Build SSE URL with auth token
        const apiUrl = process.env.NEXT_PUBLIC_V2_API_URL || 'https://ggbots-api.nightingale.business'
        const sseUrl = `${apiUrl}/api/dashboard-stream?token=${encodeURIComponent(session.access_token)}`
        
        console.log('🚀 Connecting to SSE dashboard stream...')
        
        // Create EventSource connection  
        const eventSource = new EventSource(sseUrl)
        eventSourceRef.current = eventSource
        
        eventSource.onopen = () => {
          if (!isMounted) return
          console.log('✅ SSE dashboard stream connected')
          setIsConnected(true)
          setConnectionError(null)
        }

        eventSource.onmessage = (event) => {
          if (!isMounted) return
          
          try {
            const data = JSON.parse(event.data)
            
            // Update last event ID for resume support
            if (event.lastEventId) {
              setLastEventId(event.lastEventId)
            }
            
            // Update all dashboard data from unified stream
            if (data.bots) {
              setBotsFromSSE(data.bots, userId)
            }
            if (data.positions) {
              updatePositionsFromSSE(data.positions)
            }
            if (data.decisions) {
              updateDecisionsFromSSE(data.decisions)
            }
            if (data.accounts) {
              updateAccountsFromSSE(data.accounts)
            }
            
            console.log('📨 SSE dashboard update:', {
              bots: data.bots?.length || 0,
              positions: data.positions?.length || 0, 
              decisions: data.decisions?.length || 0,
              accounts: data.accounts?.length || 0
            })
            
          } catch (error) {
            console.error('❌ Failed to parse SSE dashboard data:', error)
          }
        }

        eventSource.addEventListener('dashboard', (event: MessageEvent) => {
          if (!isMounted) return
          
          try {
            const data = JSON.parse(event.data)
            
            // Handle specific dashboard events (same as onmessage but typed)
            if (data.bots) {
              setBotsFromSSE(data.bots, userId)
            }
            if (data.positions) {
              updatePositionsFromSSE(data.positions)
            }
            if (data.decisions) {
              updateDecisionsFromSSE(data.decisions)
            }
            if (data.accounts) {
              updateAccountsFromSSE(data.accounts)
            }
            
          } catch (error) {
            console.error('❌ Failed to parse SSE dashboard event:', error)
          }
        })

        eventSource.addEventListener('error', (event) => {
          console.log('❌ SSE error event:', event)
        })

        eventSource.onerror = (error) => {
          if (!isMounted) return
          
          console.error('❌ SSE connection error:', error)
          setIsConnected(false)
          setConnectionError('Connection lost - will retry...')
          
          // EventSource automatically reconnects, but we can handle specific cases
          if (eventSource.readyState === EventSource.CLOSED) {
            console.log('🔄 SSE connection closed, will reconnect...')
          }
        }

      } catch (error) {
        console.error('❌ Failed to initialize SSE connection:', error)
        setConnectionError(error instanceof Error ? error.message : 'Connection failed')
      }
    }

    // Connect to SSE stream
    connectSSE()

    // Cleanup on unmount
    return () => {
      isMounted = false
      if (eventSourceRef.current) {
        console.log('🛑 Closing SSE dashboard stream')
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      setIsConnected(false)
    }
  }, [userId, setBotsFromSSE, updatePositionsFromSSE, updateDecisionsFromSSE, updateAccountsFromSSE])

  return {
    isConnected,
    connectionError,
    lastEventId,
    isLoading
  }
}

// 🔥 WebSocket hook removed - now using SSE only!