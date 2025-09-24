/**
 * T083: VM 配置 API 客戶端
 * 處理與 VM 配置相關的 API 請求
 */

const API_BASE_URL = '/api/v1'

interface VMNode {
  ip_address: string
  hostname: string
  role: string
  ssh_port: number
}

interface VMConfigCreate {
  name: string
  master_nodes: VMNode[]
  worker_nodes: VMNode[]
  ssh_username: string
}

interface VMConfigUpdate extends Partial<VMConfigCreate> {}

interface VMConfig extends VMConfigCreate {
  id: string
  connection_status: string
  last_tested_at?: string
  error_message?: string
  created_at: string
  updated_at: string
}

interface TestConnectionResult {
  success: boolean
  message: string
  error?: string
  tested_at: string
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
    await this.request<void>(`/vm-configs/${id}`, {
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
export type { VMConfig, VMConfigCreate, VMConfigUpdate, VMNode, TestConnectionResult }