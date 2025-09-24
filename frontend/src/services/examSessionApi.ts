/**
 * T085: 考試會話 API 客戶端
 * 處理與考試會話相關的 API 請求
 */

const API_BASE_URL = '/api/v1'

interface ExamSessionCreate {
  question_set_id: string
  vm_config_id: string
  duration_minutes: number
  exam_type: string
}

interface ExamSessionUpdate {
  current_question_index?: number
}

interface ExamSession {
  id: string
  question_set_id: string
  vm_config_id: string
  status: string
  start_time?: string
  end_time?: string
  duration_minutes: number
  current_question_index: number
  total_questions: number
  environment_status: string
  vnc_container_id?: string
  bastion_container_id?: string
  created_at: string
  updated_at: string
}

interface ExamSessionDetailed extends ExamSession {
  question_set: {
    set_id: string
    metadata: {
      name: string
      exam_type: string
      difficulty: string
      total_questions: number
    }
  }
  vm_config: {
    id: string
    name: string
    connection_status: string
  }
  current_question?: {
    id: number
    content: string
    weight: number
    kubernetes_objects: string[]
  }
  progress: {
    current: number
    total: number
    percentage: number
  }
  time_remaining?: {
    minutes: number
    seconds: number
    total_seconds: number
  }
}

interface AnswerSubmission {
  answer_data: Record<string, any>
  completed?: boolean
}

interface SubmissionResult {
  submission_result: {
    session_id: string
    question_id: number
    submitted_at: string
  }
  score_result: {
    question_id: number
    passed: boolean
    score: number
    max_score: number
    feedback: string
    verification_results: Array<{
      check: string
      passed: boolean
      message: string
    }>
    evaluated_at: string
  }
  next_actions: string[]
}

interface NavigationUpdate {
  question_index: number
}

class ExamSessionAPI {
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

  async getAll(statusFilter?: string): Promise<ExamSession[]> {
    const params = statusFilter ? `?status=${statusFilter}` : ''
    return this.request<ExamSession[]>(`/exam-sessions${params}`)
  }

  async getById(sessionId: string): Promise<ExamSessionDetailed> {
    return this.request<ExamSessionDetailed>(`/exam-sessions/${sessionId}`)
  }

  async create(session: ExamSessionCreate): Promise<ExamSession> {
    return this.request<ExamSession>('/exam-sessions', {
      method: 'POST',
      body: JSON.stringify(session),
    })
  }

  async update(sessionId: string, update: ExamSessionUpdate): Promise<ExamSession> {
    return this.request<ExamSession>(`/exam-sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    })
  }

  async start(sessionId: string): Promise<ExamSession> {
    return this.request<ExamSession>(`/exam-sessions/${sessionId}/start`, {
      method: 'POST',
    })
  }

  async pause(sessionId: string): Promise<ExamSession> {
    return this.request<ExamSession>(`/exam-sessions/${sessionId}/pause`, {
      method: 'POST',
    })
  }

  async resume(sessionId: string): Promise<ExamSession> {
    return this.request<ExamSession>(`/exam-sessions/${sessionId}/resume`, {
      method: 'POST',
    })
  }

  async complete(sessionId: string): Promise<ExamSession> {
    return this.request<ExamSession>(`/exam-sessions/${sessionId}/complete`, {
      method: 'POST',
    })
  }

  async submitAnswer(
    sessionId: string,
    questionId: number,
    submission: AnswerSubmission
  ): Promise<SubmissionResult> {
    return this.request<SubmissionResult>(
      `/exam-sessions/${sessionId}/questions/${questionId}/submit`,
      {
        method: 'POST',
        body: JSON.stringify(submission),
      }
    )
  }

  async updateNavigation(
    sessionId: string,
    navigation: NavigationUpdate
  ): Promise<{
    session_id: string
    current_question_index: number
    total_questions: number
    navigation_updated_at: string
    progress: {
      current: number
      total: number
      percentage: number
    }
  }> {
    return this.request(`/exam-sessions/${sessionId}/navigation`, {
      method: 'PATCH',
      body: JSON.stringify(navigation),
    })
  }
}

export const examSessionApi = new ExamSessionAPI()
export type {
  ExamSession,
  ExamSessionCreate,
  ExamSessionUpdate,
  ExamSessionDetailed,
  AnswerSubmission,
  SubmissionResult,
  NavigationUpdate
}