/**
 * T073: 題組選擇頁面
 * 瀏覽和選擇考試題組，支援篩選和預覽功能
 */
import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import {
  AcademicCapIcon,
  ClockIcon,
  DocumentTextIcon,
  ArrowRightIcon,
  FunnelIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

import { questionSetApi } from '../services/questionSetApi'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

interface QuestionSet {
  set_id: string
  certification_type: string
  metadata: {
    exam_type: string
    name: string
    description: string
    difficulty: string
    time_limit: number
    total_questions: number
    passing_score: number
    version: string
    tags: string[]
    topics: Array<{
      name: string
      weight: number
    }>
  }
  questions: Array<{
    id: number
    content: string
    weight: number
    kubernetes_objects: string[]
  }>
  loaded_at: string
  file_modified_at: string
}

export default function QuestionSetPage() {
  const navigate = useNavigate()
  const [selectedCertType, setSelectedCertType] = useState<string>('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [expandedSet, setExpandedSet] = useState<string | null>(null)

  // 查詢所有題組
  const {
    data: questionSets,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['questionSets', selectedCertType, selectedDifficulty],
    queryFn: () => questionSetApi.getAll({
      certification_type: selectedCertType === 'all' ? undefined : selectedCertType,
      difficulty: selectedDifficulty === 'all' ? undefined : selectedDifficulty
    })
  })

  // 重載題組
  const { mutate: reloadQuestionSets, isLoading: isReloading } = useQuery({
    queryKey: ['reloadQuestionSets'],
    queryFn: questionSetApi.reload,
    enabled: false,
    onSuccess: () => {
      toast.success('題組已重新載入')
      refetch()
    },
    onError: (error) => {
      toast.error(`重載失敗: ${error.message}`)
    }
  })

  const handleSelectQuestionSet = (questionSet: QuestionSet) => {
    navigate('/create-exam', {
      state: { selectedQuestionSet: questionSet }
    })
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

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <ErrorAlert
        title="載入題組失敗"
        message={error.message}
        onRetry={refetch}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* 頁面標題和操作 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">題組選擇</h1>
          <p className="mt-1 text-sm text-gray-500">
            選擇適合的考試題組開始練習
          </p>
        </div>
        <button
          onClick={() => reloadQuestionSets()}
          disabled={isReloading}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-4 w-4 mr-2 ${isReloading ? 'animate-spin' : ''}`} />
          重新載入
        </button>
      </div>

      {/* 篩選器 */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex items-center space-x-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <div className="flex items-center space-x-4">
            <div>
              <label className="text-sm font-medium text-gray-700">認證類型</label>
              <select
                value={selectedCertType}
                onChange={(e) => setSelectedCertType(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="all">全部</option>
                <option value="CKA">CKA</option>
                <option value="CKAD">CKAD</option>
                <option value="CKS">CKS</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">難度</label>
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="all">全部</option>
                <option value="easy">簡單</option>
                <option value="medium">中等</option>
                <option value="hard">困難</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 題組列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {questionSets && questionSets.length > 0 ? (
          questionSets.map((questionSet: QuestionSet) => (
            <div
              key={questionSet.set_id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200"
            >
              <div className="p-6">
                {/* 標題和標籤 */}
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                    {questionSet.metadata.name}
                  </h3>
                  <div className="flex flex-col space-y-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCertTypeColor(questionSet.metadata.exam_type)}`}>
                      {questionSet.metadata.exam_type}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(questionSet.metadata.difficulty)}`}>
                      {questionSet.metadata.difficulty}
                    </span>
                  </div>
                </div>

                {/* 描述 */}
                <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                  {questionSet.metadata.description}
                </p>

                {/* 統計資訊 */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-sm text-gray-500">
                    <DocumentTextIcon className="h-4 w-4 mr-2" />
                    {questionSet.metadata.total_questions} 題
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <ClockIcon className="h-4 w-4 mr-2" />
                    {questionSet.metadata.time_limit} 分鐘
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <AcademicCapIcon className="h-4 w-4 mr-2" />
                    及格分數: {questionSet.metadata.passing_score}%
                  </div>
                </div>

                {/* 標籤 */}
                {questionSet.metadata.tags && questionSet.metadata.tags.length > 0 && (
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-1">
                      {questionSet.metadata.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800"
                        >
                          {tag}
                        </span>
                      ))}
                      {questionSet.metadata.tags.length > 3 && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          +{questionSet.metadata.tags.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* 展開詳細資訊 */}
                {expandedSet === questionSet.set_id && (
                  <div className="mb-4 p-3 bg-gray-50 rounded">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">考試主題</h4>
                    <div className="space-y-1">
                      {questionSet.metadata.topics?.map((topic, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span className="text-gray-600">{topic.name}</span>
                          <span className="text-gray-400">{topic.weight}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 操作按鈕 */}
                <div className="flex justify-between items-center">
                  <button
                    onClick={() => setExpandedSet(
                      expandedSet === questionSet.set_id ? null : questionSet.set_id
                    )}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    {expandedSet === questionSet.set_id ? '收起' : '查看詳情'}
                  </button>

                  <button
                    onClick={() => handleSelectQuestionSet(questionSet)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    選擇題組
                    <ArrowRightIcon className="ml-2 h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* 底部資訊 */}
              <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
                <div className="text-xs text-gray-500">
                  版本: {questionSet.metadata.version} |
                  更新: {new Date(questionSet.file_modified_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">沒有找到題組</h3>
            <p className="mt-1 text-sm text-gray-500">
              請調整篩選條件或重新載入題組
            </p>
          </div>
        )}
      </div>
    </div>
  )
}