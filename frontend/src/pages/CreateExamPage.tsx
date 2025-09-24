/**
 * T074: 考試會話建立頁面
 * 建立新的考試會話，配置 VM 叢集和題組
 */
import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import {
  ClockIcon,
  AcademicCapIcon,
  DocumentTextIcon,
  PlayIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

import { examSessionApi } from '../services/examSessionApi'
import { vmConfigApi } from '../services/vmConfigApi'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

interface QuestionSet {
  set_id: string
  certification_type: string
  metadata: {
    name: string
    description: string
    difficulty: string
    time_limit: number
    total_questions: number
    passing_score: number
    exam_type: string
  }
}

interface VMConfig {
  id: string
  name: string
  connection_status: string
  master_nodes: any[]
  worker_nodes: any[]
}

export default function CreateExamPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [selectedVMConfig, setSelectedVMConfig] = useState<string>('')
  const [selectedQuestionSet, setSelectedQuestionSet] = useState<QuestionSet | null>(null)
  const [customDuration, setCustomDuration] = useState<number | null>(null)

  // 從路由狀態取得預選的題組
  useEffect(() => {
    if (location.state?.selectedQuestionSet) {
      setSelectedQuestionSet(location.state.selectedQuestionSet)
    }
  }, [location.state])

  // 查詢可用的 VM 配置
  const {
    data: vmConfigs,
    isLoading: isLoadingVMs,
    error: vmError
  } = useQuery({
    queryKey: ['vmConfigs'],
    queryFn: vmConfigApi.getAll
  })

  // 建立考試會話
  const createExamMutation = useMutation({
    mutationFn: examSessionApi.create,
    onSuccess: (data) => {
      toast.success('考試會話已建立')
      navigate(`/exam/${data.id}`)
    },
    onError: (error) => {
      toast.error(`建立考試會話失敗: ${error.message}`)
    }
  })

  const handleCreateExam = async () => {
    if (!selectedQuestionSet) {
      toast.error('請選擇題組')
      return
    }

    if (!selectedVMConfig) {
      toast.error('請選擇 VM 配置')
      return
    }

    // 準備考試會話資料
    const examData = {
      question_set_id: selectedQuestionSet.set_id,
      vm_config_id: selectedVMConfig,
      duration_minutes: customDuration || selectedQuestionSet.metadata.time_limit,
      exam_type: selectedQuestionSet.metadata.exam_type
    }

    createExamMutation.mutate(examData)
  }

  const getAvailableVMConfigs = () => {
    if (!vmConfigs) return []
    return vmConfigs.filter((config: VMConfig) => config.connection_status === 'success')
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'hard':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getCertTypeColor = (certType: string) => {
    switch (certType.toUpperCase()) {
      case 'CKA':
        return 'bg-blue-100 text-blue-800'
      case 'CKAD':
        return 'bg-purple-100 text-purple-800'
      case 'CKS':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center text-gray-500 hover:text-gray-700"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          返回
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">建立考試會話</h1>
          <p className="mt-1 text-sm text-gray-500">
            配置您的 Kubernetes 考試環境
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 主要設定 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 題組選擇 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">選擇題組</h2>

            {selectedQuestionSet ? (
              <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {selectedQuestionSet.metadata.name}
                  </h3>
                  <div className="flex space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCertTypeColor(selectedQuestionSet.metadata.exam_type)}`}>
                      {selectedQuestionSet.metadata.exam_type}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(selectedQuestionSet.metadata.difficulty)}`}>
                      {selectedQuestionSet.metadata.difficulty}
                    </span>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-3">
                  {selectedQuestionSet.metadata.description}
                </p>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-4 w-4 mr-2 text-gray-400" />
                    {selectedQuestionSet.metadata.total_questions} 題
                  </div>
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-2 text-gray-400" />
                    {selectedQuestionSet.metadata.time_limit} 分鐘
                  </div>
                  <div className="flex items-center">
                    <AcademicCapIcon className="h-4 w-4 mr-2 text-gray-400" />
                    及格: {selectedQuestionSet.metadata.passing_score}%
                  </div>
                </div>

                <div className="mt-4">
                  <button
                    onClick={() => navigate('/question-sets')}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    更換題組
                  </button>
                </div>
              </div>
            ) : (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">未選擇題組</h3>
                <p className="mt-1 text-sm text-gray-500">
                  請選擇一個考試題組來開始
                </p>
                <div className="mt-4">
                  <button
                    onClick={() => navigate('/question-sets')}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    選擇題組
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* VM 配置選擇 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">選擇 VM 配置</h2>

            {isLoadingVMs ? (
              <div className="flex justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : vmError ? (
              <ErrorAlert
                title="載入 VM 配置失敗"
                message={vmError.message}
              />
            ) : (
              <div className="space-y-3">
                {getAvailableVMConfigs().map((config: VMConfig) => (
                  <label
                    key={config.id}
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedVMConfig === config.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="vmConfig"
                      value={config.id}
                      checked={selectedVMConfig === config.id}
                      onChange={(e) => setSelectedVMConfig(e.target.value)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <div className="ml-3 flex-1">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-medium text-gray-900">
                          {config.name}
                        </h3>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          連線正常
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        Master: {config.master_nodes.length} 個 |
                        Worker: {config.worker_nodes.length} 個
                      </p>
                    </div>
                  </label>
                ))}

                {getAvailableVMConfigs().length === 0 && (
                  <div className="text-center py-6">
                    <p className="text-sm text-gray-500">
                      沒有可用的 VM 配置，請先建立並測試 VM 配置
                    </p>
                    <button
                      onClick={() => navigate('/vm-configs')}
                      className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      管理 VM 配置
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 高級設定 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">高級設定</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  考試時間 (分鐘)
                </label>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="duration"
                      checked={customDuration === null}
                      onChange={() => setCustomDuration(null)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      使用預設時間
                      {selectedQuestionSet && ` (${selectedQuestionSet.metadata.time_limit} 分鐘)`}
                    </span>
                  </label>
                </div>
                <div className="mt-2 flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="duration"
                      checked={customDuration !== null}
                      onChange={() => setCustomDuration(60)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">自訂時間</span>
                  </label>
                  {customDuration !== null && (
                    <input
                      type="number"
                      min="30"
                      max="480"
                      value={customDuration}
                      onChange={(e) => setCustomDuration(parseInt(e.target.value))}
                      className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 側邊欄摘要 */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">考試摘要</h2>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">題組</label>
                <p className="text-sm text-gray-900">
                  {selectedQuestionSet?.metadata.name || '未選擇'}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">VM 配置</label>
                <p className="text-sm text-gray-900">
                  {selectedVMConfig
                    ? vmConfigs?.find((c: VMConfig) => c.id === selectedVMConfig)?.name
                    : '未選擇'
                  }
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">考試時間</label>
                <p className="text-sm text-gray-900">
                  {customDuration || selectedQuestionSet?.metadata.time_limit || 0} 分鐘
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">題目數量</label>
                <p className="text-sm text-gray-900">
                  {selectedQuestionSet?.metadata.total_questions || 0} 題
                </p>
              </div>
            </div>

            <div className="mt-6">
              <button
                onClick={handleCreateExam}
                disabled={!selectedQuestionSet || !selectedVMConfig || createExamMutation.isLoading}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createExamMutation.isLoading ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <PlayIcon className="h-4 w-4 mr-2" />
                    開始考試
                  </>
                )}
              </button>
            </div>
          </div>

          {/* 注意事項 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-yellow-800 mb-2">注意事項</h3>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>• 考試開始後無法暫停或更改配置</li>
              <li>• 請確保網路連線穩定</li>
              <li>• 系統同時只能有一個活動會話</li>
              <li>• 建議使用 Chrome 或 Firefox 瀏覽器</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}