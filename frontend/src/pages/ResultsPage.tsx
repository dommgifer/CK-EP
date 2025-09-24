/**
 * T076: 考試結果頁面
 * 顯示考試完成後的詳細結果和分析
 */
import React from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  AcademicCapIcon,
  DocumentTextIcon,
  HomeIcon
} from '@heroicons/react/24/outline'

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  // 模擬考試結果資料
  const examResult = {
    sessionId,
    totalScore: 78,
    maxScore: 100,
    passingScore: 66,
    passed: true,
    completionTime: 105, // 分鐘
    totalQuestions: 15,
    correctAnswers: 12,
    questionResults: [
      { id: 1, title: '建立 Pod', score: 8, maxScore: 10, passed: true },
      { id: 2, title: '配置 Service', score: 10, maxScore: 10, passed: true },
      { id: 3, title: '設定 ConfigMap', score: 0, maxScore: 8, passed: false },
      { id: 4, title: 'RBAC 配置', score: 6, maxScore: 8, passed: true },
      { id: 5, title: '網路策略', score: 5, maxScore: 12, passed: false },
      // ... 更多題目
    ],
    examType: 'CKA',
    completedAt: '2025-09-24T10:30:00Z'
  }

  const getScoreColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100
    if (percentage >= 80) return 'text-green-600'
    if (percentage >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100
    if (percentage >= 80) return 'bg-green-100'
    if (percentage >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 頁面標題 */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">考試結果</h1>
        <p className="mt-2 text-sm text-gray-500">會話 ID: {sessionId}</p>
      </div>

      {/* 總體結果卡片 */}
      <div className={`rounded-lg shadow-lg p-8 ${examResult.passed ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        <div className="text-center">
          <div className="flex justify-center mb-4">
            {examResult.passed ? (
              <CheckCircleIcon className="h-16 w-16 text-green-600" />
            ) : (
              <XCircleIcon className="h-16 w-16 text-red-600" />
            )}
          </div>

          <h2 className={`text-2xl font-bold mb-2 ${examResult.passed ? 'text-green-800' : 'text-red-800'}`}>
            {examResult.passed ? '恭喜通過考試！' : '考試未通過'}
          </h2>

          <div className="text-4xl font-bold mb-4">
            <span className={examResult.passed ? 'text-green-600' : 'text-red-600'}>
              {examResult.totalScore}
            </span>
            <span className="text-gray-400">/{examResult.maxScore}</span>
          </div>

          <p className="text-lg text-gray-600">
            及格分數: {examResult.passingScore} 分 | 您的分數: {examResult.totalScore} 分
          </p>
        </div>
      </div>

      {/* 統計資訊 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <AcademicCapIcon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{examResult.examType}</div>
          <div className="text-sm text-gray-500">認證類型</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <ClockIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{examResult.completionTime}m</div>
          <div className="text-sm text-gray-500">完成時間</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <DocumentTextIcon className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{examResult.correctAnswers}/{examResult.totalQuestions}</div>
          <div className="text-sm text-gray-500">正確題數</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="text-2xl font-bold text-gray-900">
            {Math.round((examResult.totalScore / examResult.maxScore) * 100)}%
          </div>
          <div className="text-sm text-gray-500">正確率</div>
        </div>
      </div>

      {/* 詳細結果 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">題目詳細結果</h3>
        </div>

        <div className="divide-y divide-gray-200">
          {examResult.questionResults.map((question, index) => (
            <div key={question.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-900">
                    {question.id}
                  </span>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{question.title}</h4>
                    <p className="text-sm text-gray-500">
                      {question.passed ? '已通過' : '未通過'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreBgColor(question.score, question.maxScore)}`}>
                    <span className={getScoreColor(question.score, question.maxScore)}>
                      {question.score}/{question.maxScore}
                    </span>
                  </div>

                  {question.passed ? (
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircleIcon className="h-5 w-5 text-red-500" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 建議和下一步 */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-4">學習建議</h3>

        {examResult.passed ? (
          <div className="space-y-3">
            <p className="text-blue-800">
              🎉 恭喜您通過了 {examResult.examType} 模擬考試！您的表現非常出色。
            </p>
            <p className="text-blue-800">
              建議繼續練習其他難度的題組，或嘗試其他認證類型來提升技能。
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-blue-800">
              不要氣餒！每次練習都是學習的機會。根據結果分析，建議重點複習以下領域：
            </p>
            <ul className="list-disc list-inside space-y-1 text-blue-700">
              <li>Pod 和 Container 管理</li>
              <li>Service 和網路配置</li>
              <li>安全性和 RBAC</li>
            </ul>
          </div>
        )}
      </div>

      {/* 操作按鈕 */}
      <div className="flex justify-center space-x-4">
        <Link
          to="/question-sets"
          className="inline-flex items-center px-6 py-3 border border-gray-300 shadow-sm text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <DocumentTextIcon className="h-5 w-5 mr-2" />
          再次練習
        </Link>

        <Link
          to="/"
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <HomeIcon className="h-5 w-5 mr-2" />
          返回首頁
        </Link>
      </div>

      {/* 考試資訊 */}
      <div className="text-center text-sm text-gray-500">
        <p>考試完成時間: {new Date(examResult.completedAt).toLocaleString()}</p>
      </div>
    </div>
  )
}