/**
 * T078: 題目導航組件
 * 考試過程中的題目切換和進度指示
 */
import React from 'react'
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  FlagIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface Question {
  id: number
  title: string
  weight: number
  completed?: boolean
  flagged?: boolean
}

interface QuestionNavigationProps {
  questions: Question[]
  currentIndex: number
  onNavigate: (index: number) => void
  onPrevious: () => void
  onNext: () => void
  onFlag: (index: number) => void
  timeRemaining?: number
  readOnly?: boolean
}

export default function QuestionNavigation({
  questions,
  currentIndex,
  onNavigate,
  onPrevious,
  onNext,
  onFlag,
  timeRemaining,
  readOnly = false
}: QuestionNavigationProps) {
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getQuestionStatus = (index: number) => {
    const question = questions[index]
    if (question.completed) return 'completed'
    if (question.flagged) return 'flagged'
    if (index === currentIndex) return 'current'
    if (index < currentIndex) return 'visited'
    return 'pending'
  }

  const getQuestionColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'flagged':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'current':
        return 'bg-blue-600 text-white border-blue-600'
      case 'visited':
        return 'bg-gray-100 text-gray-600 border-gray-300'
      default:
        return 'bg-white text-gray-500 border-gray-200'
    }
  }

  const canNavigatePrevious = currentIndex > 0
  const canNavigateNext = currentIndex < questions.length - 1
  const completedCount = questions.filter(q => q.completed).length
  const flaggedCount = questions.filter(q => q.flagged).length

  return (
    <div className="bg-white border-t border-gray-200">
      {/* 計時器和統計資訊 */}
      {timeRemaining !== undefined && (
        <div className="px-4 py-3 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                剩餘時間: <span className="font-mono font-semibold ml-1">{formatTime(timeRemaining)}</span>
              </div>
              <div className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 mr-1 text-green-500" />
                已完成: {completedCount}/{questions.length}
              </div>
              {flaggedCount > 0 && (
                <div className="flex items-center">
                  <FlagIcon className="h-4 w-4 mr-1 text-yellow-500" />
                  已標記: {flaggedCount}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 題目格子導航 */}
      <div className="px-4 py-4">
        <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 gap-2">
          {questions.map((question, index) => {
            const status = getQuestionStatus(index)
            const isClickable = !readOnly

            return (
              <button
                key={question.id}
                onClick={() => isClickable && onNavigate(index)}
                disabled={!isClickable}
                className={`
                  relative w-10 h-10 text-sm font-medium rounded border-2 transition-colors
                  ${getQuestionColor(status)}
                  ${isClickable ? 'hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1' : 'cursor-default'}
                  ${status === 'current' ? 'shadow-md' : ''}
                `}
                title={`題目 ${index + 1}: ${question.title} (${question.weight} 分)`}
              >
                {index + 1}
                {question.flagged && (
                  <FlagIcon className="absolute -top-1 -right-1 h-3 w-3 text-yellow-500" />
                )}
                {question.completed && (
                  <CheckCircleIcon className="absolute -bottom-1 -right-1 h-3 w-3 text-green-500 bg-white rounded-full" />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* 導航控制 */}
      {!readOnly && (
        <div className="px-4 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <button
              onClick={onPrevious}
              disabled={!canNavigatePrevious}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeftIcon className="h-4 w-4 mr-1" />
              上一題
            </button>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => onFlag(currentIndex)}
                className={`
                  inline-flex items-center px-3 py-2 border text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500
                  ${questions[currentIndex]?.flagged
                    ? 'border-yellow-300 text-yellow-800 bg-yellow-100 hover:bg-yellow-200'
                    : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                  }
                `}
              >
                <FlagIcon className="h-4 w-4 mr-1" />
                {questions[currentIndex]?.flagged ? '取消標記' : '標記'}
              </button>

              <span className="text-sm text-gray-500">
                {currentIndex + 1} / {questions.length}
              </span>
            </div>

            <button
              onClick={onNext}
              disabled={!canNavigateNext}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一題
              <ChevronRightIcon className="h-4 w-4 ml-1" />
            </button>
          </div>
        </div>
      )}

      {/* 進度指示 */}
      <div className="px-4 pb-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
          />
        </div>
        <div className="mt-1 text-xs text-gray-500 text-center">
          進度: {Math.round(((currentIndex + 1) / questions.length) * 100)}%
        </div>
      </div>
    </div>
  )
}