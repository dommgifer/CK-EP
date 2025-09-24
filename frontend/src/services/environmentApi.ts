/**
 * T086: 環境管理 API 客戶端
 * 處理考試環境的生命週期管理
 */

const API_BASE_URL = '/api/v1'

export interface EnvironmentStatus {
  cluster_status: 'not_ready' | 'deploying' | 'ready' | 'error'
  cluster_progress?: number
  cluster_message?: string
  vnc_status: 'not_ready' | 'starting' | 'ready' | 'error'
  vnc_url?: string
  bastion_status: 'not_ready' | 'starting' | 'ready' | 'error'
  ssh_status: 'not_ready' | 'ready' | 'error'
  deployment_log?: string[]
  created_at?: string
  updated_at?: string
}

export interface VNCConnectionInfo {
  url: string
  port: number
  password?: string
  host?: string
  path?: string
}

export interface EnvironmentConfig {
  auto_start?: boolean
  timeout_minutes?: number
  preserve_on_error?: boolean
  custom_kubespray_config?: Record<string, any>
  custom_vnc_config?: Record<string, any>
  custom_bastion_config?: Record<string, any>
}

class EnvironmentAPI {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      let errorData: any = {}
      try {
        errorData = await response.json()
      } catch {
        errorData = { detail: `HTTP ${response.status}` }
      }
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * 獲取考試環境狀態
   */
  async getStatus(sessionId: string): Promise<EnvironmentStatus> {
    return this.request<EnvironmentStatus>(`/exam-sessions/${sessionId}/environment`)
  }

  /**
   * 啟動考試環境
   */
  async start(sessionId: string, config?: EnvironmentConfig): Promise<EnvironmentStatus> {
    return this.request<EnvironmentStatus>(`/exam-sessions/${sessionId}/environment`, {
      method: 'POST',
      body: JSON.stringify(config || {}),
    })
  }

  /**
   * 停止考試環境
   */
  async stop(sessionId: string, force: boolean = false): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/exam-sessions/${sessionId}/environment`, {
      method: 'DELETE',
      body: JSON.stringify({ force }),
    })
  }

  /**
   * 重啟考試環境
   */
  async restart(sessionId: string, config?: EnvironmentConfig): Promise<EnvironmentStatus> {
    return this.request<EnvironmentStatus>(`/exam-sessions/${sessionId}/environment/restart`, {
      method: 'POST',
      body: JSON.stringify(config || {}),
    })
  }

  /**
   * 獲取 VNC 連線資訊
   */
  async getVNCConnection(sessionId: string): Promise<VNCConnectionInfo> {
    return this.request<VNCConnectionInfo>(`/exam-sessions/${sessionId}/vnc`)
  }

  /**
   * 測試 VNC 連線
   */
  async testVNCConnection(sessionId: string): Promise<{ accessible: boolean; message: string }> {
    return this.request<{ accessible: boolean; message: string }>(`/exam-sessions/${sessionId}/vnc/test`)
  }

  /**
   * 獲取部署日誌
   */
  async getDeploymentLogs(sessionId: string, lines: number = 100): Promise<{ logs: string[] }> {
    return this.request<{ logs: string[] }>(`/exam-sessions/${sessionId}/environment/logs?lines=${lines}`)
  }

  /**
   * 獲取 Kubernetes 叢集資訊
   */
  async getClusterInfo(sessionId: string): Promise<{
    nodes: Array<{
      name: string
      status: string
      roles: string[]
      version: string
      ready: boolean
    }>
    version: string
    ready: boolean
  }> {
    return this.request(`/exam-sessions/${sessionId}/environment/cluster-info`)
  }

  /**
   * 執行健康檢查
   */
  async healthCheck(sessionId: string): Promise<{
    overall_healthy: boolean
    checks: Array<{
      name: string
      status: 'pass' | 'fail' | 'warning'
      message: string
      details?: any
    }>
  }> {
    return this.request(`/exam-sessions/${sessionId}/environment/health`)
  }

  /**
   * 重置 Kubernetes 叢集
   */
  async resetCluster(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/exam-sessions/${sessionId}/environment/reset-cluster`, {
      method: 'POST',
    })
  }

  /**
   * 取得環境資源使用情況
   */
  async getResourceUsage(sessionId: string): Promise<{
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_usage: number
    container_count: number
    pod_count: number
  }> {
    return this.request(`/exam-sessions/${sessionId}/environment/resources`)
  }

  /**
   * 匯出環境配置
   */
  async exportConfig(sessionId: string): Promise<{
    kubespray_config: any
    vnc_config: any
    bastion_config: any
    generated_at: string
  }> {
    return this.request(`/exam-sessions/${sessionId}/environment/export-config`)
  }

  /**
   * 匯入環境配置
   */
  async importConfig(sessionId: string, config: {
    kubespray_config?: any
    vnc_config?: any
    bastion_config?: any
  }): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/exam-sessions/${sessionId}/environment/import-config`, {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  /**
   * 取得可用的預設配置模板
   */
  async getConfigTemplates(): Promise<{
    templates: Array<{
      id: string
      name: string
      description: string
      kubespray_config: any
      vnc_config: any
      bastion_config: any
    }>
  }> {
    return this.request(`/exam-sessions/environment/templates`)
  }

  /**
   * 應用配置模板
   */
  async applyTemplate(sessionId: string, templateId: string, overrides?: any): Promise<EnvironmentStatus> {
    return this.request<EnvironmentStatus>(`/exam-sessions/${sessionId}/environment/apply-template`, {
      method: 'POST',
      body: JSON.stringify({
        template_id: templateId,
        overrides: overrides || {}
      }),
    })
  }

  /**
   * 取得環境事件日誌
   */
  async getEventLogs(sessionId: string, since?: string): Promise<{
    events: Array<{
      timestamp: string
      level: 'info' | 'warning' | 'error'
      component: string
      message: string
      details?: any
    }>
  }> {
    const params = since ? `?since=${encodeURIComponent(since)}` : ''
    return this.request(`/exam-sessions/${sessionId}/environment/events${params}`)
  }

  /**
   * 清理環境資源
   */
  async cleanup(sessionId: string, options?: {
    remove_containers?: boolean
    remove_networks?: boolean
    remove_volumes?: boolean
    remove_images?: boolean
  }): Promise<{ message: string; cleaned_resources: string[] }> {
    return this.request<{ message: string; cleaned_resources: string[] }>(`/exam-sessions/${sessionId}/environment/cleanup`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    })
  }
}

// 建立並匯出 API 實例
export const environmentApi = new EnvironmentAPI()
export default environmentApi