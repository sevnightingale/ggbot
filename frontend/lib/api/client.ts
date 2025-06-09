import { 
  ExtractionConfig, 
  DecisionConfig, 
  TradingConfig,
  Trade,
  PerformanceData,
  SchedulerStatus,
  ApiResponse
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const USER_ID = process.env.NEXT_PUBLIC_USER_ID || '00000000-0000-0000-0000-000000000001'
const DEFAULT_CONFIG_ID = 'a93de31b-9b8a-42e3-827d-c31e580f5f36'

class ApiClient {
  private baseUrl: string
  private userId: string

  constructor() {
    this.baseUrl = API_URL
    this.userId = USER_ID
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Configuration APIs
  async getConfig(module: 'extraction' | 'decision' | 'trading'): Promise<any> {
    return this.request(`/agent/api/config/${this.userId}/${module}`)
  }

  async updateConfig(
    module: 'extraction' | 'decision' | 'trading', 
    config: ExtractionConfig | DecisionConfig | TradingConfig
  ): Promise<ApiResponse<any>> {
    return this.request(`/agent/api/config/${this.userId}/${module}`, {
      method: 'PUT',
      body: JSON.stringify({ config }),
    })
  }

  // Scheduler APIs
  async startScheduler(): Promise<ApiResponse<any>> {
    return this.request('/agent/api/scheduler/start', {
      method: 'POST',
    })
  }

  async stopScheduler(): Promise<ApiResponse<any>> {
    return this.request('/agent/api/scheduler/stop', {
      method: 'POST',
    })
  }

  async getSchedulerStatus(): Promise<SchedulerStatus> {
    return this.request('/agent/api/scheduler/status')
  }

  // Dashboard APIs
  async getTrades(): Promise<{ trades: Trade[] }> {
    return this.request(`/dashboard/api/dashboard/${this.userId}/trades`)
  }

  async getPerformance(period: string = '7d'): Promise<PerformanceData> {
    return this.request(`/dashboard/api/dashboard/${this.userId}/performance?period=${period}`)
  }

  // Test execution
  async triggerExtraction(): Promise<ApiResponse<any>> {
    return this.request('/extraction/webhooks/trigger-extraction', {
      method: 'POST',
    })
  }
}

export const api = new ApiClient()