import { 
  UnifiedConfig,
  Trade,
  PerformanceData,
  SchedulerStatus,
  ApiResponse
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const DEFAULT_USER_ID = process.env.NEXT_PUBLIC_USER_ID || '00000000-0000-0000-0000-000000000001'

class ApiClient {
  private baseUrl: string
  private userId: string
  private readonly timeout: number = 5000 // 5 second timeout for faster fallback

  constructor() {
    this.baseUrl = API_URL
    // Check for demo user ID in localStorage first, fallback to default
    if (typeof window !== 'undefined') {
      this.userId = localStorage.getItem('demo_user_id') || DEFAULT_USER_ID
    } else {
      this.userId = DEFAULT_USER_ID
    }
    console.log('ApiClient initialized with baseUrl:', this.baseUrl, 'userId:', this.userId)
  }

  // Method to update user ID after demo signup
  setUserId(userId: string) {
    this.userId = userId
    console.log('ApiClient userId updated to:', userId)
  }

  // Getter for userId
  get currentUserId(): string {
    return this.userId
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`
    console.log('Making API request to:', url)
    
    // Create AbortController for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        console.error(`API Error: ${response.status} ${response.statusText}`)
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      console.log('API request successful:', path)
      return data
    } catch (error) {
      clearTimeout(timeoutId)
      
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('API request timed out:', path)
        throw new Error(`Request timeout: ${path}`)
      }
      
      console.error('API request failed:', path, error)
      throw error
    }
  }

  // Test API connection
  async testConnection(): Promise<boolean> {
    try {
      console.log('Testing API connection...')
      // Try a simple request with shorter timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000) // 3 second timeout for connection test
      
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      clearTimeout(timeoutId)
      console.log('API connection test result:', response.ok)
      return response.ok
    } catch (error) {
      console.error('API connection test failed:', error)
      return false
    }
  }

  // Configuration APIs
  async getUnifiedConfig(configId: string): Promise<UnifiedConfig> {
    return this.request(`/api/configs/${configId}`)
  }

  async getUserConfigs(userId?: string): Promise<UnifiedConfig[]> {
    const userIdToUse = userId || this.userId
    return this.request(`/api/configs/user/${userIdToUse}`)
  }

  async updateUnifiedConfig(configId: string, configData: Record<string, unknown>): Promise<ApiResponse<{ status: string, message: string }>> {
    return this.request(`/api/configs/${configId}`, {
      method: 'PUT',
      body: JSON.stringify(configData),
    })
  }

  async createConfigFromTemplate(template: string, symbol?: string, configName?: string, userId?: string): Promise<UnifiedConfig> {
    const userIdToUse = userId || this.userId
    return this.request(`/api/configs/create-from-template`, {
      method: 'POST',
      body: JSON.stringify({
        template,
        symbol: symbol || 'BTC/USDT',
        config_name: configName,
        user_id: userIdToUse,
        risk_level: 'medium'
      }),
    })
  }

  async deleteConfig(configId: string): Promise<ApiResponse<{ status: string, message: string }>> {
    return this.request(`/api/configs/${configId}`, {
      method: 'DELETE',
    })
  }

  // Scheduler APIs
  async startScheduler(): Promise<ApiResponse<{ message: string }>> {
    return this.request('/agent/api/scheduler/start', {
      method: 'POST',
    })
  }

  async stopScheduler(): Promise<ApiResponse<{ message: string }>> {
    return this.request('/agent/api/scheduler/stop', {
      method: 'POST',
    })
  }

  async getSchedulerStatus(): Promise<SchedulerStatus> {
    return this.request('/agent/api/scheduler/status')
  }

  // Dashboard APIs
  async getTrades(configId?: string): Promise<{ trades: Trade[] }> {
    if (configId) {
      return this.request(`/dashboard/api/dashboard/trades/${configId}`)
    }
    return this.request(`/dashboard/api/dashboard/${this.userId}/trades`)
  }

  async getPerformance(period: string = '7d', configId?: string): Promise<PerformanceData> {
    if (configId) {
      return this.request(`/dashboard/api/dashboard/performance/${configId}?period=${period}`)
    }
    return this.request(`/dashboard/api/dashboard/${this.userId}/performance?period=${period}`)
  }

  // Test execution
  async triggerExtraction(): Promise<ApiResponse<{ message: string }>> {
    return this.request('/extraction/webhooks/trigger-extraction', {
      method: 'POST',
    })
  }
}

export const api = new ApiClient()