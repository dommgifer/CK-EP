/**
 * T103: ExamTimer UI 組件單元測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ExamTimer from '../../components/ExamTimer'

// Mock toast notifications
jest.mock('react-hot-toast', () => ({
  toast: {
    warning: jest.fn(),
    error: jest.fn(),
  },
}))

const toast = require('react-hot-toast').toast

describe('ExamTimer', () => {
  const defaultProps = {
    totalTimeMinutes: 120,
    startTime: new Date('2025-09-24T08:00:00Z'),
    isPaused: false,
    onTimeUp: jest.fn(),
    onWarning: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2025-09-24T08:30:00Z')) // 30 minutes after start
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('應該渲染計時器基本結構', () => {
    render(<ExamTimer {...defaultProps} />)

    expect(screen.getByTestId('exam-timer')).toBeInTheDocument()
    expect(screen.getByText(/剩餘時間/)).toBeInTheDocument()
    expect(screen.getByText('01:30:00')).toBeInTheDocument() // 120 - 30 = 90 minutes
  })

  it('應該正確計算剩餘時間', () => {
    render(<ExamTimer {...defaultProps} />)

    expect(screen.getByText('01:30:00')).toBeInTheDocument()
  })

  it('應該在時間流逝時更新顯示', () => {
    render(<ExamTimer {...defaultProps} />)

    expect(screen.getByText('01:30:00')).toBeInTheDocument()

    // 快進 1 分鐘
    jest.advanceTimersByTime(60000)

    expect(screen.getByText('01:29:00')).toBeInTheDocument()
  })

  it('應該在暫停時停止計時', () => {
    const { rerender } = render(<ExamTimer {...defaultProps} />)

    expect(screen.getByText('01:30:00')).toBeInTheDocument()

    // 暫停計時器
    rerender(<ExamTimer {...defaultProps} isPaused={true} />)

    // 快進時間
    jest.advanceTimersByTime(60000)

    // 時間應該保持不變
    expect(screen.getByText('01:30:00')).toBeInTheDocument()
  })

  it('應該在恢復時重新開始計時', () => {
    const { rerender } = render(<ExamTimer {...defaultProps} isPaused={true} />)

    expect(screen.getByText('01:30:00')).toBeInTheDocument()

    // 恢復計時器
    rerender(<ExamTimer {...defaultProps} isPaused={false} />)

    // 快進時間
    jest.advanceTimersByTime(60000)

    expect(screen.getByText('01:29:00')).toBeInTheDocument()
  })

  it('應該在時間不足時顯示警告', () => {
    // 設定開始時間為 115 分鐘前（剩餘 5 分鐘）
    const warningProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:25:00Z')
    }

    render(<ExamTimer {...warningProps} />)

    expect(screen.getByTestId('exam-timer')).toHaveClass('warning')
    expect(screen.getByText('00:05:00')).toBeInTheDocument()
  })

  it('應該在時間緊急時顯示危險狀態', () => {
    // 設定開始時間為 119 分鐘前（剩餘 1 分鐘）
    const dangerProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:29:00Z')
    }

    render(<ExamTimer {...dangerProps} />)

    expect(screen.getByTestId('exam-timer')).toHaveClass('danger')
    expect(screen.getByText('00:01:00')).toBeInTheDocument()
  })

  it('應該在時間用完時觸發回調', () => {
    // 設定開始時間為 120 分鐘前
    const timeUpProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:00:00Z')
    }

    render(<ExamTimer {...timeUpProps} />)

    expect(screen.getByText('00:00:00')).toBeInTheDocument()
    expect(defaultProps.onTimeUp).toHaveBeenCalled()
  })

  it('應該在警告時間點觸發警告回調', () => {
    const warningProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:25:00Z'),
      warningMinutes: 15
    }

    render(<ExamTimer {...warningProps} />)

    // 快進到警告時間點
    jest.advanceTimersByTime(60000 * 10) // 10 minutes

    expect(defaultProps.onWarning).toHaveBeenCalledWith(5) // 5 minutes remaining
  })

  it('應該顯示進度條', () => {
    render(<ExamTimer {...defaultProps} showProgress={true} />)

    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toBeInTheDocument()

    // 30 分鐘已過去，進度應該是 25%
    expect(progressBar).toHaveAttribute('aria-valuenow', '25')
  })

  it('應該支援不同的顯示格式', () => {
    render(<ExamTimer {...defaultProps} format="short" />)

    expect(screen.getByText('90m')).toBeInTheDocument()
  })

  it('應該支援自訂樣式', () => {
    render(<ExamTimer {...defaultProps} className="custom-timer" />)

    const timer = screen.getByTestId('exam-timer')
    expect(timer).toHaveClass('custom-timer')
  })

  it('應該在時間為負數時顯示超時', () => {
    // 設定開始時間為 125 分鐘前（超時 5 分鐘）
    const overtimeProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T05:55:00Z')
    }

    render(<ExamTimer {...overtimeProps} />)

    expect(screen.getByText('超時 00:05:00')).toBeInTheDocument()
    expect(screen.getByTestId('exam-timer')).toHaveClass('overtime')
  })

  it('應該發送通知提醒', () => {
    // Mock Notification API
    global.Notification = {
      requestPermission: jest.fn().mockResolvedValue('granted'),
      permission: 'granted'
    } as any

    const notificationProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:25:00Z'),
      showNotifications: true
    }

    render(<ExamTimer {...notificationProps} />)

    expect(toast.warning).toHaveBeenCalledWith('考試時間剩餘 5 分鐘！', {
      duration: 5000
    })
  })

  it('應該支援手動調整時間', () => {
    render(<ExamTimer {...defaultProps} allowAdjust={true} />)

    const adjustButton = screen.getByTitle('調整時間')
    fireEvent.click(adjustButton)

    expect(screen.getByText('調整考試時間')).toBeInTheDocument()

    const addTimeButton = screen.getByText('+5分鐘')
    fireEvent.click(addTimeButton)

    expect(screen.getByText('01:35:00')).toBeInTheDocument()
  })

  it('應該顯示暫停指示器', () => {
    render(<ExamTimer {...defaultProps} isPaused={true} />)

    expect(screen.getByText('已暫停')).toBeInTheDocument()
    expect(screen.getByTestId('pause-indicator')).toBeInTheDocument()
  })

  it('應該支援多種警告級別', () => {
    const multiWarningProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:25:00Z'),
      warningThresholds: [30, 15, 5, 1] // minutes
    }

    render(<ExamTimer {...multiWarningProps} />)

    // 在 5 分鐘剩餘時，應該顯示最高警告級別
    expect(screen.getByTestId('exam-timer')).toHaveClass('danger')
  })

  it('應該記錄時間統計', () => {
    const statsProps = {
      ...defaultProps,
      trackStats: true,
      onStatsUpdate: jest.fn()
    }

    render(<ExamTimer {...statsProps} />)

    // 快進 5 分鐘
    jest.advanceTimersByTime(300000)

    expect(statsProps.onStatsUpdate).toHaveBeenCalledWith({
      elapsedMinutes: 35,
      remainingMinutes: 85,
      progressPercentage: 29.17
    })
  })

  it('應該處理時間格式化邊界情況', () => {
    // 測試 0 分鐘
    const zeroTimeProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:00:00Z')
    }

    render(<ExamTimer {...zeroTimeProps} />)
    expect(screen.getByText('00:00:00')).toBeInTheDocument()
  })

  it('應該支援響應式字體大小', () => {
    // Mock window size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })

    render(<ExamTimer {...defaultProps} responsive={true} />)

    const timer = screen.getByTestId('exam-timer')
    expect(timer).toHaveStyle('font-size: 1.2rem') // Small screen size
  })

  it('應該支援可訪問性功能', () => {
    render(<ExamTimer {...defaultProps} />)

    const timer = screen.getByTestId('exam-timer')
    expect(timer).toHaveAttribute('role', 'timer')
    expect(timer).toHaveAttribute('aria-live', 'polite')
    expect(timer).toHaveAttribute('aria-label', '考試剩餘時間')
  })

  it('應該處理組件卸載時的清理', () => {
    const { unmount } = render(<ExamTimer {...defaultProps} />)

    // 確保計時器正在運行
    expect(screen.getByText('01:30:00')).toBeInTheDocument()

    // 卸載組件
    unmount()

    // 快進時間，不應該有任何副作用
    jest.advanceTimersByTime(60000)
  })

  it('應該支援自訂時間警告音效', () => {
    // Mock Audio API
    global.Audio = jest.fn().mockImplementation(() => ({
      play: jest.fn(),
      pause: jest.fn(),
    }))

    const audioProps = {
      ...defaultProps,
      startTime: new Date('2025-09-24T06:25:00Z'),
      playWarningSound: true,
      warningSound: '/sounds/warning.mp3'
    }

    render(<ExamTimer {...audioProps} />)

    expect(global.Audio).toHaveBeenCalledWith('/sounds/warning.mp3')
  })
})