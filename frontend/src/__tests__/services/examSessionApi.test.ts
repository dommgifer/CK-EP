/**
 * T104: ExamSessionAPI 客戶端測試
 */

import { examSessionApi } from '../../services/examSessionApi'

// Mock fetch globally
global.fetch = jest.fn()

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

describe('ExamSessionAPI', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default successful response
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: jest.fn().mockResolvedValue({}),
    } as any)
  })

  describe('create', () => {
    const createData = {
      question_set_id: 'cka/test-001',
      vm_cluster_config_id: 'cluster-001'
    }

    it('應該成功建立考試會話', async () => {
      const mockResponse = {
        id: 'session-001',
        question_set_id: 'cka/test-001',
        vm_cluster_config_id: 'cluster-001',
        status: 'created',
        created_at: '2025-09-24T08:00:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.create(createData)

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/exam-sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createData),
      })

      expect(result).toEqual(mockResponse)
    })

    it('應該處理建立失敗的錯誤', async () => {
      const errorResponse = { detail: '已有活動的考試會話' }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue(errorResponse),
      } as any)

      await expect(examSessionApi.create(createData)).rejects.toThrow('已有活動的考試會話')
    })

    it('應該處理網路錯誤', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(examSessionApi.create(createData)).rejects.toThrow('Network error')
    })
  })

  describe('get', () => {
    const sessionId = 'session-001'

    it('應該成功取得考試會話', async () => {
      const mockResponse = {
        id: sessionId,
        question_set_id: 'cka/test-001',
        status: 'in_progress',
        current_question_index: 1,
        answers: { '1': { solution: 'kubectl create pod test --image=nginx' } }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.get(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(`/api/v1/exam-sessions/${sessionId}`)
      expect(result).toEqual(mockResponse)
    })

    it('應該處理會話不存在的情況', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: jest.fn().mockResolvedValue({ detail: 'Session not found' }),
      } as any)

      await expect(examSessionApi.get(sessionId)).rejects.toThrow('Session not found')
    })
  })

  describe('start', () => {
    const sessionId = 'session-001'

    it('應該成功開始考試會話', async () => {
      const mockResponse = {
        success: true,
        vnc_url: 'http://localhost:6080/vnc.html',
        environment_ready: true
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.start(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/start`,
        { method: 'POST' }
      )
      expect(result).toEqual(mockResponse)
    })

    it('應該處理啟動失敗', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ detail: '會話狀態無效' }),
      } as any)

      await expect(examSessionApi.start(sessionId)).rejects.toThrow('會話狀態無效')
    })
  })

  describe('pause', () => {
    const sessionId = 'session-001'

    it('應該成功暫停考試會話', async () => {
      const mockResponse = { success: true, message: '會話已暫停' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.pause(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/pause`,
        { method: 'POST' }
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('resume', () => {
    const sessionId = 'session-001'

    it('應該成功恢復考試會話', async () => {
      const mockResponse = { success: true, message: '會話已恢復' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.resume(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/resume`,
        { method: 'POST' }
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('submitAnswer', () => {
    const sessionId = 'session-001'
    const questionId = 1
    const answer = { solution: 'kubectl create pod test --image=nginx' }

    it('應該成功提交答案', async () => {
      const mockResponse = { success: true, message: '答案已儲存' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.submitAnswer(sessionId, questionId, answer)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/submit-answer`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question_id: questionId, answer })
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('應該處理無效答案', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ detail: '答案格式無效' }),
      } as any)

      await expect(examSessionApi.submitAnswer(sessionId, questionId, answer))
        .rejects.toThrow('答案格式無效')
    })
  })

  describe('nextQuestion', () => {
    const sessionId = 'session-001'

    it('應該成功切換到下一題', async () => {
      const mockResponse = {
        success: true,
        question_id: 2,
        current_index: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.nextQuestion(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/next-question`,
        { method: 'POST' }
      )
      expect(result).toEqual(mockResponse)
    })

    it('應該處理已是最後一題的情況', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ detail: '已是最後一題' }),
      } as any)

      await expect(examSessionApi.nextQuestion(sessionId))
        .rejects.toThrow('已是最後一題')
    })
  })

  describe('previousQuestion', () => {
    const sessionId = 'session-001'

    it('應該成功切換到上一題', async () => {
      const mockResponse = {
        success: true,
        question_id: 1,
        current_index: 0
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.previousQuestion(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/previous-question`,
        { method: 'POST' }
      )
      expect(result).toEqual(mockResponse)
    })

    it('應該處理已是第一題的情況', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ detail: '已是第一題' }),
      } as any)

      await expect(examSessionApi.previousQuestion(sessionId))
        .rejects.toThrow('已是第一題')
    })
  })

  describe('complete', () => {
    const sessionId = 'session-001'

    it('應該成功完成考試', async () => {
      const mockResponse = {
        success: true,
        result_id: 'result-001',
        total_score: 85.5,
        passed: true
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.complete(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/complete`,
        { method: 'POST' }
      )
      expect(result).toEqual(mockResponse)
    })

    it('應該處理完成失敗', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockResolvedValue({ detail: '評分系統錯誤' }),
      } as any)

      await expect(examSessionApi.complete(sessionId))
        .rejects.toThrow('評分系統錯誤')
    })
  })

  describe('getProgress', () => {
    const sessionId = 'session-001'

    it('應該成功取得進度資訊', async () => {
      const mockResponse = {
        current_question_index: 1,
        total_questions: 3,
        answered_questions: 1,
        progress_percentage: 33.33,
        time_remaining: 6600, // seconds
        time_elapsed: 1800
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.getProgress(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}/progress`
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('list', () => {
    it('應該成功取得會話列表', async () => {
      const mockResponse = [
        {
          id: 'session-001',
          question_set_id: 'cka/test-001',
          status: 'completed',
          created_at: '2025-09-24T08:00:00Z'
        },
        {
          id: 'session-002',
          question_set_id: 'ckad/test-001',
          status: 'in_progress',
          created_at: '2025-09-24T09:00:00Z'
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
      } as any)

      const result = await examSessionApi.list()

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/exam-sessions')
      expect(result).toEqual(mockResponse)
    })

    it('應該支援查詢參數', async () => {
      const params = { status: 'completed', limit: 10 }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue([]),
      } as any)

      await examSessionApi.list(params)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/exam-sessions?status=completed&limit=10'
      )
    })
  })

  describe('delete', () => {
    const sessionId = 'session-001'

    it('應該成功刪除考試會話', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: jest.fn().mockResolvedValue({}),
      } as any)

      const result = await examSessionApi.delete(sessionId)

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/v1/exam-sessions/${sessionId}`,
        { method: 'DELETE' }
      )
      expect(result).toEqual({})
    })

    it('應該處理刪除失敗', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ detail: '無法刪除進行中的會話' }),
      } as any)

      await expect(examSessionApi.delete(sessionId))
        .rejects.toThrow('無法刪除進行中的會話')
    })
  })

  describe('錯誤處理', () => {
    const sessionId = 'session-001'

    it('應該處理 JSON 解析錯誤', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockRejectedValue(new Error('Invalid JSON')),
      } as any)

      await expect(examSessionApi.get(sessionId))
        .rejects.toThrow('HTTP 500')
    })

    it('應該處理空回應', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(null),
      } as any)

      const result = await examSessionApi.get(sessionId)
      expect(result).toBe(null)
    })

    it('應該處理超時錯誤', async () => {
      jest.useFakeTimers()

      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), 5000)
      })

      mockFetch.mockReturnValueOnce(timeoutPromise as any)

      const requestPromise = examSessionApi.get(sessionId)

      jest.advanceTimersByTime(5000)

      await expect(requestPromise).rejects.toThrow('Request timeout')

      jest.useRealTimers()
    })

    it('應該處理未授權錯誤', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ detail: 'Unauthorized' }),
      } as any)

      await expect(examSessionApi.get(sessionId))
        .rejects.toThrow('Unauthorized')
    })

    it('應該處理伺服器內部錯誤', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockResolvedValue({ detail: 'Internal server error' }),
      } as any)

      await expect(examSessionApi.get(sessionId))
        .rejects.toThrow('Internal server error')
    })
  })

  describe('請求攔截和重試', () => {
    it('應該在網路錯誤時重試請求', async () => {
      const sessionId = 'session-001'

      // 前兩次失敗，第三次成功
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: jest.fn().mockResolvedValue({ id: sessionId }),
        } as any)

      const result = await examSessionApi.get(sessionId, { retries: 2 })

      expect(mockFetch).toHaveBeenCalledTimes(3)
      expect(result).toEqual({ id: sessionId })
    })

    it('應該在重試次數用盡後拋出錯誤', async () => {
      const sessionId = 'session-001'

      mockFetch.mockRejectedValue(new Error('Persistent network error'))

      await expect(examSessionApi.get(sessionId, { retries: 2 }))
        .rejects.toThrow('Persistent network error')

      expect(mockFetch).toHaveBeenCalledTimes(3) // 1 original + 2 retries
    })
  })

  describe('請求取消', () => {
    it('應該支援請求取消', async () => {
      const sessionId = 'session-001'
      const controller = new AbortController()

      // 模擬長時間運行的請求
      mockFetch.mockImplementationOnce(() =>
        new Promise((resolve, reject) => {
          setTimeout(() => {
            if (controller.signal.aborted) {
              reject(new Error('Request cancelled'))
            } else {
              resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ id: sessionId })
              } as any)
            }
          }, 1000)
        })
      )

      const requestPromise = examSessionApi.get(sessionId, {
        signal: controller.signal
      })

      // 500ms 後取消請求
      setTimeout(() => controller.abort(), 500)

      await expect(requestPromise).rejects.toThrow('Request cancelled')
    })
  })
})