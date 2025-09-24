/**
 * T084: 題組 API 客戶端
 * 處理與題組相關的 API 請求
 */

const API_BASE_URL = '/api/v1'

interface QuestionSetFilters {
  certification_type?: string
  difficulty?: string
}

interface QuestionSet {
  set_id: string
  certification_type: string
  metadata: {
    exam_type: string
    set_id: string
    name: string
    description: string
    difficulty: string
    time_limit: number
    total_questions: number
    passing_score: number
    created_date: string
    version: string
    tags: string[]
    topics: Array<{
      name: string
      weight: number
    }>
    exam_domains: Array<{
      name: string
      percentage: number
    }>
  }
  questions: Array<{
    id: number
    content: string
    weight: number
    kubernetes_objects: string[]
    hints: string[]
    verification_scripts: string[]
    preparation_scripts: string[]
  }>
  scripts_path: string
  file_paths: {
    metadata: string
    questions: string
    scripts: string
  }
  loaded_at: string
  file_modified_at: string
}

interface ReloadResult {
  loaded: string[]
  errors: string[]
  total_loaded: number
  total_errors: number
  reloaded_at: string
}

class QuestionSetAPI {
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

  async getAll(filters: QuestionSetFilters = {}): Promise<QuestionSet[]> {
    const params = new URLSearchParams()

    if (filters.certification_type) {
      params.append('certification_type', filters.certification_type)
    }

    if (filters.difficulty) {
      params.append('difficulty', filters.difficulty)
    }

    const query = params.toString()
    const endpoint = query ? `/question-sets?${query}` : '/question-sets'

    return this.request<QuestionSet[]>(endpoint)
  }

  async getById(setId: string): Promise<QuestionSet> {
    return this.request<QuestionSet>(`/question-sets/${setId}`)
  }

  async reload(): Promise<ReloadResult> {
    return this.request<ReloadResult>('/question-sets/reload', {
      method: 'POST',
    })
  }
}

export const questionSetApi = new QuestionSetAPI()
export type { QuestionSet, QuestionSetFilters, ReloadResult }