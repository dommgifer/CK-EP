/**
 * T084: 題組 API 客戶端
 * 處理與題組相關的 API 請求
 */

const API_BASE_URL = '/api/v1'

interface QuestionSetFilters {
  exam_type?: string
}

interface QuestionSetSummary {
  set_id: string
  exam_type: string
  name: string
  description: string
  time_limit: number
  passing_score: number
  total_questions: number
}

interface QuestionSetListResponse {
  question_sets: QuestionSetSummary[]
  total_count: number
  filtered_count: number
}

interface VerificationStep {
  id: string
  description: string
  verificationScriptFile: string
  expectedOutput: string
  weightage: number
}

interface Question {
  id: string
  context: string
  tasks: string
  notes: string
  verification: VerificationStep[]
}

interface QuestionSetDetail {
  set_id: string
  exam_type: string
  metadata: {
    exam_type: string
    set_id: string
    name: string
    description: string
    time_limit: number
    passing_score: number
  }
  questions: Question[]
  scripts_path: string
  total_weight: number
  loaded_at: string | null
  file_modified_at: string | null
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

  async getAll(filters: QuestionSetFilters = {}): Promise<QuestionSetListResponse> {
    const params = new URLSearchParams()

    if (filters.exam_type) {
      params.append('exam_type', filters.exam_type)
    }

    const query = params.toString()
    const endpoint = query ? `/question-sets?${query}` : '/question-sets'

    return this.request<QuestionSetListResponse>(endpoint)
  }

  async getById(setId: string): Promise<QuestionSetDetail> {
    return this.request<QuestionSetDetail>(`/question-sets/${setId}`)
  }

  async reload(): Promise<ReloadResult> {
    return this.request<ReloadResult>('/question-sets/reload', {
      method: 'POST',
    })
  }
}

export const questionSetApi = new QuestionSetAPI()
export type {
  QuestionSetSummary,
  QuestionSetListResponse,
  QuestionSetDetail,
  QuestionSetFilters,
  Question,
  VerificationStep,
  ReloadResult
}