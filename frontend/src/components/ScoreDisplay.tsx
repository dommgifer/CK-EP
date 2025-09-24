/**
 * T082: 評分結果顯示組件
 * 顯示考試評分和詳細結果
 */
import React from 'react'
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  TrophyIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

interface QuestionScore {
  id: number
  title: string
  weight: number
  score: number
  max_score: number
  passed: boolean
  time_spent?: number
  feedback?: string
  error_details?: string[]
}

interface ScoreDisplayProps {
  totalScore: number
  maxScore: number
  passingScore: number
  passed: boolean
  completionTime?: number
  questionScores?: QuestionScore[]
  examType?: string
  showDetails?: boolean
  onToggleDetails?: () => void
  className?: string
}

export default function ScoreDisplay({
  totalScore,
  maxScore,
  passingScore,
  passed,
  completionTime,
  questionScores = [],
  examType,
  showDetails = false,
  onToggleDetails,
  className = ''
}: ScoreDisplayProps) {
  const percentage = Math.round((totalScore / maxScore) * 100)
  const passingPercentage = Math.round((passingScore / maxScore) * 100)

  const getScoreColor = (score: number, maxScore: number) => {
    const pct = (score / maxScore) * 100
    if (pct >= 80) return 'text-green-600'
    if (pct >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (score: number, maxScore: number) => {
    const pct = (score / maxScore) * 100
    if (pct >= 80) return 'bg-green-100'
    if (pct >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 總體結果卡片 */}
      <div className={`rounded-lg shadow-lg p-6 ${
        passed ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
      }`}>
        <div className="text-center">
          <div className="flex justify-center mb-4">
            {passed ? (
              <div className="flex items-center space-x-2">
                <TrophyIcon className="h-12 w-12 text-yellow-500" />
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
            ) : (
              <XCircleIcon className="h-12 w-12 text-red-600" />
            )}
          </div>

          <h2 className={`text-2xl font-bold mb-2 ${
            passed ? 'text-green-800' : 'text-red-800'
          }`}>
            {passed ? '恭喜通過！' : '未通過考試'}
          </h2>

          <div className="text-4xl font-bold mb-4">
            <span className={passed ? 'text-green-600' : 'text-red-600'}>
              {totalScore}
            </span>
            <span className="text-gray-400">/{maxScore}</span>
            <span className="text-lg text-gray-600 ml-2">({percentage}%)</span>
          </div>

          <div className="flex justify-center items-center space-x-6 text-sm text-gray-600">
            <div className="flex items-center">
              <ChartBarIcon className="h-4 w-4 mr-1" />
              及格分數: {passingScore} ({passingPercentage}%)
            </div>
            {completionTime && (
              <div className="flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                完成時間: {formatTime(completionTime)}
              </div>
            )}
            {examType && (
              <div className="font-medium">
                {examType} 認證
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 統計摘要 */}
      {questionScores.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {questionScores.length}
            </div>
            <div className="text-sm text-gray-500">總題數</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {questionScores.filter(q => q.passed).length}
            </div>
            <div className="text-sm text-gray-500">通過題數</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {questionScores.filter(q => !q.passed).length}
            </div>
            <div className="text-sm text-gray-500">失敗題數</div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {Math.round(questionScores.reduce((acc, q) => acc + (q.score / q.max_score), 0) / questionScores.length * 100)}%
            </div>
            <div className="text-sm text-gray-500">平均得分率</div>
          </div>
        </div>
      )}

      {/* 題目詳細結果 */}
      {questionScores.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">題目詳細結果</h3>
              {onToggleDetails && (
                <button
                  onClick={onToggleDetails}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {showDetails ? '隱藏詳情' : '顯示詳情'}
                </button>
              )}
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {questionScores.map((question, index) => (
              <div key={question.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-900">
                      {index + 1}
                    </span>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{question.title}</h4>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className={`text-xs px-2 py-1 rounded ${
                          question.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {question.passed ? '通過' : '未通過'}
                        </span>
                        <span className="text-xs text-gray-500">
                          權重: {question.weight} 分
                        </span>
                        {question.time_spent && (
                          <span className="text-xs text-gray-500">
                            用時: {formatTime(question.time_spent)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      getScoreBgColor(question.score, question.max_score)
                    }`}>
                      <span className={getScoreColor(question.score, question.max_score)}>
                        {question.score}/{question.max_score}
                      </span>
                    </div>

                    {question.passed ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircleIcon className="h-5 w-5 text-red-500" />
                    )}
                  </div>
                </div>

                {/* 詳細回饋 */}
                {showDetails && (
                  <div className="mt-4 ml-11">
                    {question.feedback && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-gray-900 mb-1">評分回饋:</h5>
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {question.feedback}
                        </p>
                      </div>
                    )}

                    {question.error_details && question.error_details.length > 0 && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-red-900 mb-1 flex items-center">
                          <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                          錯誤詳情:
                        </h5>
                        <div className="bg-red-50 border border-red-200 rounded p-3">
                          {question.error_details.map((error, errorIndex) => (
                            <div key={errorIndex} className="text-sm text-red-700 mb-1">
                              • {error}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 進度條 */}
                    <div className="mt-2">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>得分進度</span>
                        <span>{Math.round((question.score / question.max_score) * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            question.passed ? 'bg-green-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${(question.score / question.max_score) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 整體進度條 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>整體得分</span>
          <span>{totalScore}/{maxScore} ({percentage}%)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
          <div
            className={`h-4 rounded-full transition-all duration-500 ${
              passed ? 'bg-green-500' : 'bg-red-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
          {/* 及格線指示器 */}
          <div
            className="absolute h-4 w-0.5 bg-gray-600"
            style={{
              left: `${passingPercentage}%`,
              marginTop: '-16px'
            }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>0</span>
          <span className="text-gray-600">及格線: {passingScore}</span>
          <span>{maxScore}</span>
        </div>
      </div>
    </div>
  )
}