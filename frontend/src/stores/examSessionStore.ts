/**
 * T087: 考試會話狀態管理
 * 使用 Zustand 管理考試會話的全域狀態
 */
import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { examSessionApi, type ExamSession, type ExamSessionCreate } from '../services/examSessionApi'
import { environmentApi, type EnvironmentStatus } from '../services/environmentApi'

export interface Question {
  id: number
  title: string
  description: string
  weight: number
  time_limit?: number
  completed?: boolean
  flagged?: boolean
  answer?: string
  score?: number
  max_score?: number
  feedback?: string
  last_modified?: string
}

export interface ExamProgress {
  current_question_index: number
  total_questions: number
  completed_questions: number
  flagged_questions: number
  time_spent: number
  answers: Record<number, string>
  question_scores: Record<number, number>
}

export interface ExamSessionState {
  // 當前考試會話
  currentSession: ExamSession | null

  // 環境狀態
  environment: EnvironmentStatus | null

  // 題目和進度
  questions: Question[]
  progress: ExamProgress

  // 計時器狀態
  timeRemaining: number
  isPaused: boolean
  hasExpired: boolean

  // UI 狀態
  isLoading: boolean
  error: string | null

  // 操作
  createSession: (data: ExamSessionCreate) => Promise<void>
  loadSession: (sessionId: string) => Promise<void>
  startSession: (sessionId: string) => Promise<void>
  pauseSession: (sessionId: string) => Promise<void>
  resumeSession: (sessionId: string) => Promise<void>
  endSession: (sessionId: string) => Promise<void>

  // 環境管理
  startEnvironment: (sessionId: string) => Promise<void>
  stopEnvironment: (sessionId: string) => Promise<void>
  refreshEnvironment: (sessionId: string) => Promise<void>

  // 題目導航
  navigateToQuestion: (index: number) => void
  nextQuestion: () => void
  previousQuestion: () => void
  flagQuestion: (index: number) => void
  unflagQuestion: (index: number) => void

  // 答案管理
  saveAnswer: (questionId: number, answer: string) => Promise<void>
  submitAnswer: (questionId: number) => Promise<void>

  // 計時器
  updateTimer: (seconds: number) => void
  pauseTimer: () => void
  resumeTimer: () => void
  expireTimer: () => void

  // 狀態重置
  reset: () => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
}

const initialProgress: ExamProgress = {
  current_question_index: 0,
  total_questions: 0,
  completed_questions: 0,
  flagged_questions: 0,
  time_spent: 0,
  answers: {},
  question_scores: {}
}

export const useExamSessionStore = create<ExamSessionState>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // 初始狀態
        currentSession: null,
        environment: null,
        questions: [],
        progress: initialProgress,
        timeRemaining: 0,
        isPaused: false,
        hasExpired: false,
        isLoading: false,
        error: null,

        // 考試會話操作
        createSession: async (data: ExamSessionCreate) => {
          set(state => {
            state.isLoading = true
            state.error = null
          })

          try {
            const session = await examSessionApi.create(data)
            set(state => {
              state.currentSession = session
              state.timeRemaining = session.time_limit * 60 // 轉換為秒
              state.isLoading = false
            })
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isLoading = false
            })
            throw error
          }
        },

        loadSession: async (sessionId: string) => {
          set(state => {
            state.isLoading = true
            state.error = null
          })

          try {
            const session = await examSessionApi.getById(sessionId)
            const questions = await examSessionApi.getQuestions(sessionId)

            set(state => {
              state.currentSession = session
              state.questions = questions
              state.progress = {
                current_question_index: session.current_question_index || 0,
                total_questions: questions.length,
                completed_questions: questions.filter(q => q.completed).length,
                flagged_questions: questions.filter(q => q.flagged).length,
                time_spent: session.time_spent || 0,
                answers: questions.reduce((acc, q) => {
                  if (q.answer) acc[q.id] = q.answer
                  return acc
                }, {} as Record<number, string>),
                question_scores: questions.reduce((acc, q) => {
                  if (q.score !== undefined) acc[q.id] = q.score
                  return acc
                }, {} as Record<number, number>)
              }

              const elapsed = session.time_spent || 0
              state.timeRemaining = Math.max(0, (session.time_limit * 60) - elapsed)
              state.isPaused = session.status === 'paused'
              state.hasExpired = session.status === 'completed' && state.timeRemaining === 0
              state.isLoading = false
            })

            // 同時載入環境狀態
            get().refreshEnvironment(sessionId)
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isLoading = false
            })
            throw error
          }
        },

        startSession: async (sessionId: string) => {
          try {
            await examSessionApi.start(sessionId)
            set(state => {
              if (state.currentSession) {
                state.currentSession.status = 'in_progress'
                state.isPaused = false
              }
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        pauseSession: async (sessionId: string) => {
          try {
            await examSessionApi.pause(sessionId)
            set(state => {
              if (state.currentSession) {
                state.currentSession.status = 'paused'
                state.isPaused = true
              }
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        resumeSession: async (sessionId: string) => {
          try {
            await examSessionApi.resume(sessionId)
            set(state => {
              if (state.currentSession) {
                state.currentSession.status = 'in_progress'
                state.isPaused = false
              }
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        endSession: async (sessionId: string) => {
          try {
            const result = await examSessionApi.end(sessionId)
            set(state => {
              if (state.currentSession) {
                state.currentSession.status = 'completed'
                state.currentSession.final_score = result.final_score
                state.isPaused = false
                state.hasExpired = true
              }
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        // 環境管理
        startEnvironment: async (sessionId: string) => {
          try {
            const environment = await environmentApi.start(sessionId)
            set(state => {
              state.environment = environment
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        stopEnvironment: async (sessionId: string) => {
          try {
            await environmentApi.stop(sessionId)
            set(state => {
              state.environment = null
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        refreshEnvironment: async (sessionId: string) => {
          try {
            const environment = await environmentApi.getStatus(sessionId)
            set(state => {
              state.environment = environment
            })
          } catch (error: any) {
            // 環境不存在時不視為錯誤
            set(state => {
              state.environment = null
            })
          }
        },

        // 題目導航
        navigateToQuestion: (index: number) => {
          set(state => {
            if (index >= 0 && index < state.questions.length) {
              state.progress.current_question_index = index

              // 更新後端狀態
              if (state.currentSession) {
                examSessionApi.updateProgress(state.currentSession.id, {
                  current_question_index: index
                }).catch(console.error)
              }
            }
          })
        },

        nextQuestion: () => {
          const { progress, questions } = get()
          if (progress.current_question_index < questions.length - 1) {
            get().navigateToQuestion(progress.current_question_index + 1)
          }
        },

        previousQuestion: () => {
          const { progress } = get()
          if (progress.current_question_index > 0) {
            get().navigateToQuestion(progress.current_question_index - 1)
          }
        },

        flagQuestion: (index: number) => {
          set(state => {
            if (state.questions[index]) {
              state.questions[index].flagged = true
              state.progress.flagged_questions += 1
            }
          })
        },

        unflagQuestion: (index: number) => {
          set(state => {
            if (state.questions[index] && state.questions[index].flagged) {
              state.questions[index].flagged = false
              state.progress.flagged_questions -= 1
            }
          })
        },

        // 答案管理
        saveAnswer: async (questionId: number, answer: string) => {
          set(state => {
            state.progress.answers[questionId] = answer

            const questionIndex = state.questions.findIndex(q => q.id === questionId)
            if (questionIndex !== -1) {
              state.questions[questionIndex].answer = answer
              state.questions[questionIndex].last_modified = new Date().toISOString()
            }
          })

          // 自動儲存到後端
          const { currentSession } = get()
          if (currentSession) {
            try {
              await examSessionApi.saveAnswer(currentSession.id, questionId, answer)
            } catch (error) {
              console.error('Failed to save answer:', error)
            }
          }
        },

        submitAnswer: async (questionId: number) => {
          const { currentSession, progress } = get()
          if (!currentSession) return

          try {
            const result = await examSessionApi.submitAnswer(currentSession.id, questionId, progress.answers[questionId])

            set(state => {
              const questionIndex = state.questions.findIndex(q => q.id === questionId)
              if (questionIndex !== -1) {
                state.questions[questionIndex].completed = true
                state.questions[questionIndex].score = result.score
                state.questions[questionIndex].feedback = result.feedback
                state.progress.completed_questions += 1
                state.progress.question_scores[questionId] = result.score
              }
            })
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        // 計時器
        updateTimer: (seconds: number) => {
          set(state => {
            state.timeRemaining = seconds
            if (state.currentSession) {
              state.progress.time_spent = (state.currentSession.time_limit * 60) - seconds
            }
          })
        },

        pauseTimer: () => {
          set(state => {
            state.isPaused = true
          })
        },

        resumeTimer: () => {
          set(state => {
            state.isPaused = false
          })
        },

        expireTimer: () => {
          set(state => {
            state.hasExpired = true
            state.isPaused = false
            state.timeRemaining = 0
          })

          // 自動結束考試
          const { currentSession } = get()
          if (currentSession && currentSession.status === 'in_progress') {
            get().endSession(currentSession.id).catch(console.error)
          }
        },

        // 狀態重置
        reset: () => {
          set(state => {
            state.currentSession = null
            state.environment = null
            state.questions = []
            state.progress = initialProgress
            state.timeRemaining = 0
            state.isPaused = false
            state.hasExpired = false
            state.isLoading = false
            state.error = null
          })
        },

        setError: (error: string | null) => {
          set(state => {
            state.error = error
          })
        },

        setLoading: (loading: boolean) => {
          set(state => {
            state.isLoading = loading
          })
        }
      })),
      {
        name: 'exam-session-store',
      }
    )
  )
)

// 訂閱器：自動儲存進度
useExamSessionStore.subscribe(
  (state) => state.progress,
  (progress, previousProgress) => {
    const currentSession = useExamSessionStore.getState().currentSession
    if (currentSession && progress !== previousProgress) {
      // 防抖儲存
      const timeoutId = setTimeout(() => {
        examSessionApi.updateProgress(currentSession.id, {
          current_question_index: progress.current_question_index,
          time_spent: progress.time_spent
        }).catch(console.error)
      }, 1000)

      return () => clearTimeout(timeoutId)
    }
  },
  {
    equalityFn: (a, b) => JSON.stringify(a) === JSON.stringify(b)
  }
)