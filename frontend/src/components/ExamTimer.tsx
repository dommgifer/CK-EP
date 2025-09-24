/**
 * T081: 計時器組件
 * 考試倒數計時和時間管理
 */
import React, { useState, useEffect, useCallback } from 'react'
import {
  ClockIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

interface ExamTimerProps {
  totalSeconds: number
  isPaused?: boolean
  autoStart?: boolean
  onTimeUpdate?: (remainingSeconds: number) => void
  onTimeExpired?: () => void
  onWarning?: (remainingSeconds: number) => void
  warningThresholds?: number[] // 警告閾值（秒），例如 [1800, 600, 300] 表示剩餘30分鐘、10分鐘、5分鐘時警告
  showControls?: boolean
  onStart?: () => void
  onPause?: () => void
  onStop?: () => void
  className?: string
}

export default function ExamTimer({
  totalSeconds,
  isPaused = false,
  autoStart = true,
  onTimeUpdate,
  onTimeExpired,
  onWarning,
  warningThresholds = [1800, 600, 300], // 30分鐘、10分鐘、5分鐘
  showControls = false,
  onStart,
  onPause,
  onStop,
  className = ''
}: ExamTimerProps) {
  const [remainingSeconds, setRemainingSeconds] = useState(totalSeconds)
  const [isRunning, setIsRunning] = useState(autoStart && !isPaused)
  const [hasExpired, setHasExpired] = useState(false)
  const [warningsTriggered, setWarningsTriggered] = useState<Set<number>>(new Set())

  // 格式化時間顯示
  const formatTime = useCallback((seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }, [])

  // 獲取時間狀態樣式
  const getTimeStyle = useCallback(() => {
    if (hasExpired) {
      return 'text-red-600 font-bold animate-pulse'
    }
    if (remainingSeconds <= 300) { // 5分鐘
      return 'text-red-600 font-bold'
    }
    if (remainingSeconds <= 600) { // 10分鐘
      return 'text-orange-600 font-semibold'
    }
    if (remainingSeconds <= 1800) { // 30分鐘
      return 'text-yellow-600'
    }
    return 'text-gray-900'
  }, [remainingSeconds, hasExpired])

  // 獲取進度條顏色
  const getProgressColor = useCallback(() => {
    const percentage = (remainingSeconds / totalSeconds) * 100
    if (percentage <= 8.33) return 'bg-red-600' // 5分鐘 (5/60 * 100)
    if (percentage <= 16.67) return 'bg-orange-500' // 10分鐘
    if (percentage <= 50) return 'bg-yellow-500' // 30分鐘
    return 'bg-green-600'
  }, [remainingSeconds, totalSeconds])

  // 計時器邏輯
  useEffect(() => {
    let interval: NodeJS.Timeout

    if (isRunning && remainingSeconds > 0 && !hasExpired) {
      interval = setInterval(() => {
        setRemainingSeconds(prev => {
          const newTime = prev - 1

          // 檢查是否需要觸發警告
          warningThresholds.forEach(threshold => {
            if (newTime === threshold && !warningsTriggered.has(threshold)) {
              setWarningsTriggered(prev => new Set(prev).add(threshold))
              onWarning?.(newTime)
            }
          })

          // 時間更新回調
          onTimeUpdate?.(newTime)

          // 檢查是否時間到期
          if (newTime <= 0) {
            setHasExpired(true)
            setIsRunning(false)
            onTimeExpired?.()
            return 0
          }

          return newTime
        })
      }, 1000)
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [isRunning, remainingSeconds, hasExpired, onTimeUpdate, onTimeExpired, onWarning, warningThresholds, warningsTriggered])

  // 暫停狀態同步
  useEffect(() => {
    setIsRunning(!isPaused && remainingSeconds > 0 && !hasExpired)
  }, [isPaused, remainingSeconds, hasExpired])

  // 控制函數
  const handleStart = () => {
    if (!hasExpired && remainingSeconds > 0) {
      setIsRunning(true)
      onStart?.()
    }
  }

  const handlePause = () => {
    setIsRunning(false)
    onPause?.()
  }

  const handleStop = () => {
    setIsRunning(false)
    setRemainingSeconds(0)
    setHasExpired(true)
    onStop?.()
  }

  const handleReset = () => {
    setRemainingSeconds(totalSeconds)
    setIsRunning(autoStart)
    setHasExpired(false)
    setWarningsTriggered(new Set())
  }

  // 計算進度百分比
  const progressPercentage = ((totalSeconds - remainingSeconds) / totalSeconds) * 100

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center space-x-4">
        {/* 時鐘圖示 */}
        <div className="flex-shrink-0">
          <ClockIcon className={`h-6 w-6 ${hasExpired ? 'text-red-600' : 'text-gray-600'}`} />
        </div>

        {/* 時間顯示 */}
        <div className="flex-1">
          <div className="flex items-baseline space-x-2">
            <span className={`text-2xl font-mono ${getTimeStyle()}`}>
              {formatTime(remainingSeconds)}
            </span>
            {hasExpired && (
              <span className="text-sm text-red-600 font-medium">時間到期</span>
            )}
            {isPaused && !hasExpired && (
              <span className="text-sm text-yellow-600 font-medium">已暫停</span>
            )}
          </div>

          {/* 進度條 */}
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>已用時: {formatTime(totalSeconds - remainingSeconds)}</span>
              <span>總時長: {formatTime(totalSeconds)}</span>
            </div>
          </div>
        </div>

        {/* 控制按鈕 */}
        {showControls && (
          <div className="flex items-center space-x-2">
            {!isRunning && !hasExpired ? (
              <button
                onClick={handleStart}
                className="p-2 text-green-600 hover:bg-green-50 rounded"
                title="開始"
              >
                <PlayIcon className="h-5 w-5" />
              </button>
            ) : (
              <button
                onClick={handlePause}
                disabled={hasExpired}
                className="p-2 text-yellow-600 hover:bg-yellow-50 rounded disabled:opacity-50"
                title="暫停"
              >
                <PauseIcon className="h-5 w-5" />
              </button>
            )}

            <button
              onClick={handleStop}
              disabled={hasExpired}
              className="p-2 text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
              title="停止"
            >
              <StopIcon className="h-5 w-5" />
            </button>

            <button
              onClick={handleReset}
              className="px-3 py-1 text-xs text-gray-600 hover:bg-gray-50 rounded border"
              title="重置"
            >
              重置
            </button>
          </div>
        )}

        {/* 警告指示器 */}
        {remainingSeconds <= 600 && remainingSeconds > 0 && !hasExpired && (
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 animate-pulse" />
          </div>
        )}
      </div>

      {/* 時間警告訊息 */}
      {remainingSeconds <= 300 && remainingSeconds > 0 && !hasExpired && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
            <span className="text-red-800 font-medium">
              考試即將結束！剩餘時間不足 5 分鐘
            </span>
          </div>
        </div>
      )}

      {hasExpired && (
        <div className="mt-3 p-3 bg-red-100 border border-red-300 rounded">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            <div>
              <p className="text-red-800 font-medium">考試時間已結束</p>
              <p className="text-red-700 text-sm">系統將自動提交您的答案</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}