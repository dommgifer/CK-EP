/**
 * T089: 題組狀態管理
 * 使用 Zustand 管理題組的全域狀態
 */
import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { questionSetApi, type QuestionSet, type QuestionSetMetadata } from '../services/questionSetApi'

export interface QuestionSetFilter {
  examType?: string[]
  difficulty?: string[]
  tags?: string[]
  searchQuery?: string
  minQuestions?: number
  maxQuestions?: number
}

export interface QuestionSetState {
  // 題組資料
  questionSets: QuestionSet[]
  metadata: QuestionSetMetadata[]
  selectedQuestionSet: QuestionSet | null

  // 篩選和搜尋
  filter: QuestionSetFilter
  filteredQuestionSets: QuestionSet[]

  // 快取管理
  lastReloaded: string | null
  cacheExpiry: number // 毫秒

  // UI 狀態
  isLoading: boolean
  isReloading: boolean
  error: string | null

  // 操作
  loadQuestionSets: () => Promise<void>
  reloadQuestionSets: () => Promise<void>
  getQuestionSet: (id: string) => Promise<QuestionSet>
  selectQuestionSet: (id: string | null) => void

  // 篩選和搜尋
  setFilter: (filter: Partial<QuestionSetFilter>) => void
  clearFilter: () => void
  applyFilter: () => void

  // 快取管理
  isCacheExpired: () => boolean
  clearCache: () => void

  // 狀態重置
  reset: () => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
}

const initialFilter: QuestionSetFilter = {
  examType: [],
  difficulty: [],
  tags: [],
  searchQuery: '',
  minQuestions: undefined,
  maxQuestions: undefined
}

const CACHE_DURATION = 5 * 60 * 1000 // 5 分鐘

export const useQuestionSetStore = create<QuestionSetState>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // 初始狀態
        questionSets: [],
        metadata: [],
        selectedQuestionSet: null,
        filter: initialFilter,
        filteredQuestionSets: [],
        lastReloaded: null,
        cacheExpiry: CACHE_DURATION,
        isLoading: false,
        isReloading: false,
        error: null,

        // 載入題組列表
        loadQuestionSets: async () => {
          const state = get()

          // 檢查快取是否有效
          if (state.metadata.length > 0 && !state.isCacheExpired()) {
            return
          }

          set(state => {
            state.isLoading = true
            state.error = null
          })

          try {
            const metadata = await questionSetApi.getAll()

            set(state => {
              state.metadata = metadata
              // 如果有完整的題組資料，更新它們，否則保留現有資料
              metadata.forEach(meta => {
                const existingIndex = state.questionSets.findIndex(qs => qs.id === meta.id)
                if (existingIndex === -1) {
                  // 創建部分題組物件（只有 metadata）
                  state.questionSets.push({
                    id: meta.id,
                    name: meta.name,
                    description: meta.description,
                    exam_type: meta.exam_type,
                    difficulty: meta.difficulty,
                    estimated_duration: meta.estimated_duration,
                    question_count: meta.question_count,
                    tags: meta.tags,
                    created_at: meta.created_at,
                    updated_at: meta.updated_at,
                    questions: [] // 延遲載入
                  })
                } else {
                  // 更新 metadata，保留 questions
                  const existing = state.questionSets[existingIndex]
                  state.questionSets[existingIndex] = {
                    ...existing,
                    ...meta
                  }
                }
              })

              state.lastReloaded = new Date().toISOString()
              state.isLoading = false
            })

            // 自動應用篩選器
            get().applyFilter()
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isLoading = false
            })
            throw error
          }
        },

        // 重新載入題組列表
        reloadQuestionSets: async () => {
          set(state => {
            state.isReloading = true
            state.error = null
          })

          try {
            await questionSetApi.reload()
            await get().loadQuestionSets()

            set(state => {
              state.isReloading = false
            })
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isReloading = false
            })
            throw error
          }
        },

        // 取得完整題組資料
        getQuestionSet: async (id: string) => {
          try {
            const questionSet = await questionSetApi.getById(id)

            set(state => {
              const index = state.questionSets.findIndex(qs => qs.id === id)
              if (index !== -1) {
                state.questionSets[index] = questionSet
              } else {
                state.questionSets.push(questionSet)
              }
            })

            return questionSet
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        // 選擇題組
        selectQuestionSet: (id: string | null) => {
          set(state => {
            if (id) {
              const questionSet = state.questionSets.find(qs => qs.id === id)
              state.selectedQuestionSet = questionSet || null

              // 如果題組沒有載入問題，自動載入
              if (questionSet && questionSet.questions.length === 0) {
                get().getQuestionSet(id).catch(console.error)
              }
            } else {
              state.selectedQuestionSet = null
            }
          })
        },

        // 設定篩選器
        setFilter: (newFilter: Partial<QuestionSetFilter>) => {
          set(state => {
            state.filter = { ...state.filter, ...newFilter }
          })

          // 自動應用篩選器
          get().applyFilter()
        },

        // 清除篩選器
        clearFilter: () => {
          set(state => {
            state.filter = initialFilter
          })

          get().applyFilter()
        },

        // 應用篩選器
        applyFilter: () => {
          set(state => {
            const { filter, questionSets } = state

            let filtered = [...questionSets]

            // 考試類型篩選
            if (filter.examType && filter.examType.length > 0) {
              filtered = filtered.filter(qs =>
                filter.examType!.includes(qs.exam_type)
              )
            }

            // 難度篩選
            if (filter.difficulty && filter.difficulty.length > 0) {
              filtered = filtered.filter(qs =>
                filter.difficulty!.includes(qs.difficulty)
              )
            }

            // 標籤篩選
            if (filter.tags && filter.tags.length > 0) {
              filtered = filtered.filter(qs =>
                filter.tags!.some(tag => qs.tags.includes(tag))
              )
            }

            // 搜尋查詢
            if (filter.searchQuery && filter.searchQuery.trim()) {
              const query = filter.searchQuery.toLowerCase()
              filtered = filtered.filter(qs =>
                qs.name.toLowerCase().includes(query) ||
                qs.description.toLowerCase().includes(query) ||
                qs.tags.some(tag => tag.toLowerCase().includes(query))
              )
            }

            // 題目數量範圍
            if (filter.minQuestions !== undefined) {
              filtered = filtered.filter(qs => qs.question_count >= filter.minQuestions!)
            }
            if (filter.maxQuestions !== undefined) {
              filtered = filtered.filter(qs => qs.question_count <= filter.maxQuestions!)
            }

            state.filteredQuestionSets = filtered
          })
        },

        // 檢查快取是否過期
        isCacheExpired: () => {
          const { lastReloaded, cacheExpiry } = get()
          if (!lastReloaded) return true

          const lastReloadTime = new Date(lastReloaded).getTime()
          const now = new Date().getTime()
          return (now - lastReloadTime) > cacheExpiry
        },

        // 清除快取
        clearCache: () => {
          set(state => {
            state.questionSets = []
            state.metadata = []
            state.filteredQuestionSets = []
            state.selectedQuestionSet = null
            state.lastReloaded = null
          })
        },

        // 狀態重置
        reset: () => {
          set(state => {
            state.questionSets = []
            state.metadata = []
            state.selectedQuestionSet = null
            state.filter = initialFilter
            state.filteredQuestionSets = []
            state.lastReloaded = null
            state.isLoading = false
            state.isReloading = false
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
        name: 'question-set-store'
      }
    )
  )
)

// 選擇器 - 取得可用的考試類型
export const useAvailableExamTypes = () => {
  return useQuestionSetStore(state => {
    const examTypes = new Set(state.questionSets.map(qs => qs.exam_type))
    return Array.from(examTypes).sort()
  })
}

// 選擇器 - 取得可用的難度等級
export const useAvailableDifficulties = () => {
  return useQuestionSetStore(state => {
    const difficulties = new Set(state.questionSets.map(qs => qs.difficulty))
    return Array.from(difficulties).sort()
  })
}

// 選擇器 - 取得所有標籤
export const useAvailableTags = () => {
  return useQuestionSetStore(state => {
    const allTags = state.questionSets.flatMap(qs => qs.tags)
    const uniqueTags = new Set(allTags)
    return Array.from(uniqueTags).sort()
  })
}

// 選擇器 - 取得題目數量統計
export const useQuestionCountStats = () => {
  return useQuestionSetStore(state => {
    const counts = state.questionSets.map(qs => qs.question_count)
    if (counts.length === 0) {
      return { min: 0, max: 0, average: 0 }
    }

    return {
      min: Math.min(...counts),
      max: Math.max(...counts),
      average: Math.round(counts.reduce((sum, count) => sum + count, 0) / counts.length)
    }
  })
}

// 自動載入題組 - 在 store 初始化時觸發
if (typeof window !== 'undefined') {
  // 只在瀏覽器環境中執行
  const store = useQuestionSetStore.getState()
  store.loadQuestionSets().catch(console.error)
}