/**
 * T083: VM 配置 API 客戶端
 * 處理與 VM 配置相關的 API 請求
 */

const API_BASE_URL = '/api/v1'

interface VMNode {
  name: string
  ip: string
  role: 'master' | 'worker'
}

interface SSHConfig {
  user: string
  port: number
  private_key_path: string
}

interface VMConfigCreate {
  name: string
  description?: string
  nodes: VMNode[]
  ssh_config: SSHConfig
}

interface VMConfigUpdate {
  name?: string
  description?: string
  nodes?: VMNode[]
  ssh_config?: SSHConfig
}

interface VMConfig {
  id: string
  name: string
  description?: string
  nodes: VMNode[]
  ssh_config: SSHConfig
  created_at: string
  updated_at: string
  is_active: boolean
  last_tested_at?: string
}

interface TestConnectionResult {
  success: boolean
  message: string
  tested_at: string
  nodes: Array<{
    name: string
    ip: string
    role: string
    success: boolean
    error?: string
    response_time?: number
  }>
  total_nodes: number
  successful_nodes: number
  failed_nodes: number
}

class VMConfigAPI {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`)
    }

    // 處理 204 No Content 回應（如 DELETE 操作）
    if (response.status === 204) {
      return null as T
    }

    return response.json()
  }

  async getAll(): Promise<VMConfig[]> {
    return this.request<VMConfig[]>('/vm-configs')
  }

  async getById(id: string): Promise<VMConfig> {
    return this.request<VMConfig>(`/vm-configs/${id}`)
  }

  async create(config: VMConfigCreate): Promise<VMConfig> {
    return this.request<VMConfig>('/vm-configs', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  async update(id: string, config: VMConfigUpdate): Promise<VMConfig> {
    return this.request<VMConfig>(`/vm-configs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    })
  }

  async delete(id: string): Promise<void> {
    await this.request<null>(`/vm-configs/${id}`, {
      method: 'DELETE',
    })
  }

  async testConnection(id: string): Promise<TestConnectionResult> {
    return this.request<TestConnectionResult>(`/vm-configs/${id}/test-connection`, {
      method: 'POST',
    })
  }
}

export const vmConfigApi = new VMConfigAPI()
export type { VMConfig, VMConfigCreate, VMConfigUpdate, VMNode, SSHConfig, TestConnectionResult }