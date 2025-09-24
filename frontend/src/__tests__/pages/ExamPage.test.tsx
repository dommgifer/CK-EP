/**
 * T102: ExamPage 頁面組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import '@testing-library/jest-dom'
import ExamPage from '../../pages/ExamPage'

// Mock API clients
jest.mock('../../services/examSessionApi', () => ({
  examSessionApi: {
    get: jest.fn(),
    start: jest.fn(),
    pause: jest.fn(),
    resume: jest.fn(),
    submitAnswer: jest.fn(),
    nextQuestion: jest.fn(),
    previousQuestion: jest.fn(),
    complete: jest.fn(),
    getProgress: jest.fn(),
  },
}))

jest.mock('../../services/questionSetApi', () => ({
  questionSetApi: {
    getById: jest.fn(),
  },
}))

jest.mock('../../services/environmentApi', () => ({
  environmentApi: {
    getStatus: jest.fn(),
    getVncUrl: jest.fn(),
  },
}))

// Mock toast notifications
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
  },
}))

const examSessionApi = require('../../services/examSessionApi').examSessionApi
const questionSetApi = require('../../services/questionSetApi').questionSetApi
const environmentApi = require('../../services/environmentApi').environmentApi

// Test wrapper with providers and router
const TestWrapper: React.FC<{ children: React.ReactNode; route?: string }> = ({
  children,
  route = '/exam/test-session-001'
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const mockExamSession = {
  id: 'test-session-001',
  question_set_id: 'cka/test-001',
  vm_cluster_config_id: 'test-cluster',
  status: 'in_progress',
  created_at: '2025-09-24T08:00:00Z',
  started_at: '2025-09-24T08:05:00Z',
  time_limit_minutes: 120,
  current_question_index: 0,
  answers: {},
  progress: 25.0,
  vnc_url: 'http://localhost:6080/vnc.html',
  environment_ready: true
}

const mockQuestionSet = {
  metadata: {
    exam_type: 'CKA',
    set_id: 'test-001',
    name: '測試題組',
    description: 'CKA 模擬考試',
    time_limit_minutes: 120,
    passing_score: 70.0
  },
  questions: [
    {
      id: 1,
      content: '## 任務 1：建立 Pod\n\n建立一個名為 `test-pod` 的 Pod，使用 `nginx:1.20` 映像。',
      weight: 30.0,
      kubernetes_objects: ['Pod'],
      hints: ['使用 kubectl create 命令', '指定正確的映像版本'],
      verification_scripts: ['q1_verify.sh'],
      preparation_scripts: []
    },
    {
      id: 2,
      content: '## 任務 2：建立 Service\n\n建立一個 ClusterIP Service 將 Pod 的 80 埠暴露。',
      weight: 40.0,
      kubernetes_objects: ['Service'],
      hints: ['使用 kubectl expose 命令'],
      verification_scripts: ['q2_verify.sh'],
      preparation_scripts: []
    },
    {
      id: 3,
      content: '## 任務 3：配置 ConfigMap\n\n建立 ConfigMap 並將其掛載到 Pod 中。',
      weight: 30.0,
      kubernetes_objects: ['ConfigMap', 'Pod'],
      hints: ['使用 YAML 檔案定義'],
      verification_scripts: ['q3_verify.sh'],
      preparation_scripts: []
    }
  ]
}

const mockProgress = {
  current_question_index: 0,
  total_questions: 3,
  answered_questions: 0,
  progress_percentage: 0.0,
  time_remaining: 7200, // 2 hours in seconds
  time_elapsed: 300     // 5 minutes
}

describe('ExamPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()

    // Default API responses
    examSessionApi.get.mockResolvedValue(mockExamSession)
    questionSetApi.getById.mockResolvedValue(mockQuestionSet)
    examSessionApi.getProgress.mockResolvedValue(mockProgress)
    environmentApi.getStatus.mockResolvedValue({ ready: true })
    environmentApi.getVncUrl.mockResolvedValue({ url: 'http://localhost:6080/vnc.html' })
  })

  it('應該渲染考試介面基本元素', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('CKA 模擬考試')).toBeInTheDocument()
      expect(screen.getByText('任務 1：建立 Pod')).toBeInTheDocument()
    })

    // 檢查計時器
    expect(screen.getByText(/剩餘時間/)).toBeInTheDocument()

    // 檢查進度條
    expect(screen.getByText('進度: 0%')).toBeInTheDocument()

    // 檢查導航按鈕
    expect(screen.getByText('下一題')).toBeInTheDocument()
    expect(screen.getByText('暫停')).toBeInTheDocument()
  })

  it('應該顯示當前題目內容', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('任務 1：建立 Pod')).toBeInTheDocument()
      expect(screen.getByText(/建立一個名為.*test-pod.*的 Pod/)).toBeInTheDocument()
      expect(screen.getByText(/nginx:1.20.*映像/)).toBeInTheDocument()
    })
  })

  it('應該顯示題目提示', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      const hintsButton = screen.getByText('查看提示')
      fireEvent.click(hintsButton)
    })

    await waitFor(() => {
      expect(screen.getByText('使用 kubectl create 命令')).toBeInTheDocument()
      expect(screen.getByText('指定正確的映像版本')).toBeInTheDocument()
    })
  })

  it('應該能夠切換到下一題', async () => {
    examSessionApi.nextQuestion.mockResolvedValue({
      success: true,
      question_id: 2
    })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('任務 1：建立 Pod')).toBeInTheDocument()
    })

    const nextButton = screen.getByText('下一題')
    fireEvent.click(nextButton)

    await waitFor(() => {
      expect(examSessionApi.nextQuestion).toHaveBeenCalledWith('test-session-001')
    })
  })

  it('應該能夠切換到上一題', async () => {
    // 設定為第二題
    const sessionOnSecondQuestion = {
      ...mockExamSession,
      current_question_index: 1
    }
    examSessionApi.get.mockResolvedValue(sessionOnSecondQuestion)

    examSessionApi.previousQuestion.mockResolvedValue({
      success: true,
      question_id: 1
    })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('上一題')).toBeInTheDocument()
    })

    const prevButton = screen.getByText('上一題')
    fireEvent.click(prevButton)

    await waitFor(() => {
      expect(examSessionApi.previousQuestion).toHaveBeenCalledWith('test-session-001')
    })
  })

  it('應該能夠提交答案', async () => {
    examSessionApi.submitAnswer.mockResolvedValue({ success: true })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('任務 1：建立 Pod')).toBeInTheDocument()
    })

    // 輸入答案
    const answerTextarea = screen.getByPlaceholderText('請輸入您的解答方案...')
    fireEvent.change(answerTextarea, {
      target: { value: 'kubectl create pod test-pod --image=nginx:1.20' }
    })

    // 提交答案
    const submitButton = screen.getByText('儲存答案')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(examSessionApi.submitAnswer).toHaveBeenCalledWith(
        'test-session-001',
        1,
        { solution: 'kubectl create pod test-pod --image=nginx:1.20' }
      )
    })
  })

  it('應該能夠暫停考試', async () => {
    examSessionApi.pause.mockResolvedValue({ success: true })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      const pauseButton = screen.getByText('暫停')
      fireEvent.click(pauseButton)
    })

    await waitFor(() => {
      expect(examSessionApi.pause).toHaveBeenCalledWith('test-session-001')
    })
  })

  it('應該能夠恢復考試', async () => {
    // 設定為暫停狀態
    const pausedSession = {
      ...mockExamSession,
      status: 'paused'
    }
    examSessionApi.get.mockResolvedValue(pausedSession)
    examSessionApi.resume.mockResolvedValue({ success: true })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      const resumeButton = screen.getByText('繼續')
      fireEvent.click(resumeButton)
    })

    await waitFor(() => {
      expect(examSessionApi.resume).toHaveBeenCalledWith('test-session-001')
    })
  })

  it('應該顯示 VNC 檢視器', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      const vncFrame = screen.getByTitle('Kubernetes 叢集環境')
      expect(vncFrame).toBeInTheDocument()
      expect(vncFrame).toHaveAttribute('src', 'http://localhost:6080/vnc.html')
    })
  })

  it('應該顯示環境狀態', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('環境已就緒')).toBeInTheDocument()
    })
  })

  it('應該處理環境未就緒的情況', async () => {
    environmentApi.getStatus.mockResolvedValue({ ready: false, message: '正在準備環境...' })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('正在準備環境...')).toBeInTheDocument()
    })
  })

  it('應該顯示即時計時器', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/剩餘時間.*2:00:00/)).toBeInTheDocument()
    })
  })

  it('應該在時間不足時發出警告', async () => {
    const lowTimeProgress = {
      ...mockProgress,
      time_remaining: 600 // 10 minutes left
    }
    examSessionApi.getProgress.mockResolvedValue(lowTimeProgress)

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/時間不足警告/)).toBeInTheDocument()
    })
  })

  it('應該能夠完成考試', async () => {
    examSessionApi.complete.mockResolvedValue({
      success: true,
      result_id: 'result-001'
    })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      const completeButton = screen.getByText('完成考試')
      fireEvent.click(completeButton)
    })

    // 確認對話框
    await waitFor(() => {
      expect(screen.getByText('確認完成考試')).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: '確認完成' })
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(examSessionApi.complete).toHaveBeenCalledWith('test-session-001')
    })
  })

  it('應該顯示題目導航', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    // 點擊題目導航
    const question2Button = screen.getByText('2')
    fireEvent.click(question2Button)

    // 應該觸發題目切換
  })

  it('應該處理載入錯誤', async () => {
    examSessionApi.get.mockRejectedValue(new Error('載入失敗'))

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/載入考試時發生錯誤/)).toBeInTheDocument()
    })
  })

  it('應該支援鍵盤快捷鍵', async () => {
    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('任務 1：建立 Pod')).toBeInTheDocument()
    })

    // 模擬按下 Ctrl+S 儲存答案
    fireEvent.keyDown(document, { key: 's', ctrlKey: true })

    // 應該觸發儲存動作
  })

  it('應該自動儲存答案', async () => {
    jest.useFakeTimers()
    examSessionApi.submitAnswer.mockResolvedValue({ success: true })

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('任務 1：建立 Pod')).toBeInTheDocument()
    })

    // 輸入答案
    const answerTextarea = screen.getByPlaceholderText('請輸入您的解答方案...')
    fireEvent.change(answerTextarea, {
      target: { value: 'kubectl create pod test-pod --image=nginx:1.20' }
    })

    // 快進時間觸發自動儲存
    jest.advanceTimersByTime(30000) // 30 seconds

    await waitFor(() => {
      expect(examSessionApi.submitAnswer).toHaveBeenCalled()
    })

    jest.useRealTimers()
  })

  it('應該顯示答案狀態指示器', async () => {
    // 設定已有答案的會話
    const sessionWithAnswers = {
      ...mockExamSession,
      answers: {
        '1': { solution: 'kubectl create pod test-pod --image=nginx:1.20' },
        '2': { solution: 'kubectl expose pod test-pod --port=80' }
      }
    }
    examSessionApi.get.mockResolvedValue(sessionWithAnswers)

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      // 題目 1 和 2 應該標記為已回答
      const answeredIndicators = screen.getAllByText('✓')
      expect(answeredIndicators).toHaveLength(2)
    })
  })

  it('應該能夠全螢幕模式切換', async () => {
    // Mock requestFullscreen
    document.documentElement.requestFullscreen = jest.fn()
    document.exitFullscreen = jest.fn()

    render(
      <TestWrapper>
        <ExamPage />
      </TestWrapper>
    )

    await waitFor(() => {
      const fullscreenButton = screen.getByTitle('全螢幕模式')
      fireEvent.click(fullscreenButton)
    })

    expect(document.documentElement.requestFullscreen).toHaveBeenCalled()
  })
})