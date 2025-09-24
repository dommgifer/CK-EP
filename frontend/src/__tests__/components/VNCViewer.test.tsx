/**
 * T103: VNCViewer UI 組件單元測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import VNCViewer from '../../components/VNCViewer'

// Mock environment API
jest.mock('../../services/environmentApi', () => ({
  environmentApi: {
    getVncUrl: jest.fn(),
    getStatus: jest.fn(),
  },
}))

const environmentApi = require('../../services/environmentApi').environmentApi

describe('VNCViewer', () => {
  const defaultProps = {
    sessionId: 'test-session-001',
    width: '100%',
    height: '600px'
  }

  beforeEach(() => {
    jest.clearAllMocks()
    environmentApi.getVncUrl.mockResolvedValue({
      url: 'http://localhost:6080/vnc.html?path=websockify&token=test-session-001'
    })
    environmentApi.getStatus.mockResolvedValue({ ready: true })
  })

  it('應該渲染 VNC 檢視器基本結構', async () => {
    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()
      expect(iframe).toHaveAttribute('width', '100%')
      expect(iframe).toHaveAttribute('height', '600px')
    })
  })

  it('應該顯示載入狀態', () => {
    environmentApi.getVncUrl.mockReturnValue(new Promise(() => {})) // Never resolves

    render(<VNCViewer {...defaultProps} />)

    expect(screen.getByText('正在載入 VNC 連線...')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('應該顯示連線錯誤', async () => {
    environmentApi.getVncUrl.mockRejectedValue(new Error('VNC 連線失敗'))

    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('VNC 連線失敗')).toBeInTheDocument()
      expect(screen.getByText('重新連線')).toBeInTheDocument()
    })
  })

  it('應該能夠重新連線', async () => {
    environmentApi.getVncUrl
      .mockRejectedValueOnce(new Error('連線失敗'))
      .mockResolvedValueOnce({
        url: 'http://localhost:6080/vnc.html?path=websockify&token=test-session-001'
      })

    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('重新連線')).toBeInTheDocument()
    })

    const retryButton = screen.getByText('重新連線')
    fireEvent.click(retryButton)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()
    })

    expect(environmentApi.getVncUrl).toHaveBeenCalledTimes(2)
  })

  it('應該處理環境未就緒狀態', async () => {
    environmentApi.getStatus.mockResolvedValue({
      ready: false,
      message: '正在準備 Kubernetes 環境...'
    })

    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('環境準備中')).toBeInTheDocument()
      expect(screen.getByText('正在準備 Kubernetes 環境...')).toBeInTheDocument()
    })
  })

  it('應該支援全螢幕切換', async () => {
    // Mock fullscreen API
    const mockRequestFullscreen = jest.fn()
    const mockExitFullscreen = jest.fn()

    Object.defineProperty(document, 'fullscreenElement', {
      value: null,
      writable: true
    })

    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      iframe.requestFullscreen = mockRequestFullscreen
    })

    const fullscreenButton = screen.getByTitle('全螢幕')
    fireEvent.click(fullscreenButton)

    expect(mockRequestFullscreen).toHaveBeenCalled()
  })

  it('應該支援縮放功能', async () => {
    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByTitle('放大')).toBeInTheDocument()
      expect(screen.getByTitle('縮小')).toBeInTheDocument()
      expect(screen.getByTitle('適應視窗')).toBeInTheDocument()
    })

    // 測試放大
    const zoomInButton = screen.getByTitle('放大')
    fireEvent.click(zoomInButton)

    // 測試縮小
    const zoomOutButton = screen.getByTitle('縮小')
    fireEvent.click(zoomOutButton)

    // 測試適應視窗
    const fitButton = screen.getByTitle('適應視窗')
    fireEvent.click(fitButton)
  })

  it('應該顯示連線狀態', async () => {
    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      expect(screen.getByText('已連線')).toBeInTheDocument()
      expect(screen.getByTestId('connection-indicator')).toHaveClass('connected')
    })
  })

  it('應該處理 iframe 載入事件', async () => {
    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()

      // 模擬 iframe 載入完成
      fireEvent.load(iframe)
    })

    expect(screen.getByText('已連線')).toBeInTheDocument()
  })

  it('應該處理 iframe 錯誤事件', async () => {
    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()

      // 模擬 iframe 載入錯誤
      fireEvent.error(iframe)
    })

    expect(screen.getByText('VNC 連線中斷')).toBeInTheDocument()
    expect(screen.getByText('重新連線')).toBeInTheDocument()
  })

  it('應該支援鍵盤快捷鍵', async () => {
    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()
    })

    // 測試快捷鍵
    fireEvent.keyDown(document, { key: 'f', ctrlKey: true, altKey: true })
    // 應該觸發全螢幕切換

    fireEvent.keyDown(document, { key: '=', ctrlKey: true })
    // 應該觸發放大

    fireEvent.keyDown(document, { key: '-', ctrlKey: true })
    // 應該觸發縮小
  })

  it('應該定期檢查連線狀態', async () => {
    jest.useFakeTimers()

    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()
    })

    // 清除之前的呼叫記錄
    environmentApi.getStatus.mockClear()

    // 快進時間觸發狀態檢查
    jest.advanceTimersByTime(5000) // 5 seconds

    await waitFor(() => {
      expect(environmentApi.getStatus).toHaveBeenCalledWith('test-session-001')
    })

    jest.useRealTimers()
  })

  it('應該處理會話 ID 變更', async () => {
    const { rerender } = render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()
    })

    // 變更 sessionId
    rerender(<VNCViewer {...defaultProps} sessionId="new-session-002" />)

    await waitFor(() => {
      expect(environmentApi.getVncUrl).toHaveBeenCalledWith('new-session-002')
    })
  })

  it('應該支援自訂樣式', () => {
    const customProps = {
      ...defaultProps,
      width: '800px',
      height: '600px',
      className: 'custom-vnc-viewer'
    }

    render(<VNCViewer {...customProps} />)

    const container = screen.getByTestId('vnc-viewer-container')
    expect(container).toHaveClass('custom-vnc-viewer')
  })

  it('應該處理網路中斷情況', async () => {
    // 模擬網路中斷
    environmentApi.getStatus
      .mockResolvedValueOnce({ ready: true })
      .mockRejectedValue(new Error('Network error'))

    render(<VNCViewer {...defaultProps} />)

    await waitFor(() => {
      const iframe = screen.getByTitle('VNC 遠端桌面')
      expect(iframe).toBeInTheDocument()
    })

    // 觸發網路檢查
    jest.advanceTimersByTime(5000)

    await waitFor(() => {
      expect(screen.getByText('網路連線中斷')).toBeInTheDocument()
    })
  })

  it('應該顯示工具列', async () => {
    render(<VNCViewer {...defaultProps} showToolbar={true} />)

    await waitFor(() => {
      expect(screen.getByRole('toolbar')).toBeInTheDocument()
      expect(screen.getByTitle('全螢幕')).toBeInTheDocument()
      expect(screen.getByTitle('放大')).toBeInTheDocument()
      expect(screen.getByTitle('縮小')).toBeInTheDocument()
      expect(screen.getByTitle('適應視窗')).toBeInTheDocument()
      expect(screen.getByTitle('發送 Ctrl+Alt+Del')).toBeInTheDocument()
    })
  })

  it('應該支援發送特殊按鍵', async () => {
    render(<VNCViewer {...defaultProps} showToolbar={true} />)

    await waitFor(() => {
      const ctrlAltDelButton = screen.getByTitle('發送 Ctrl+Alt+Del')
      expect(ctrlAltDelButton).toBeInTheDocument()
    })

    const ctrlAltDelButton = screen.getByTitle('發送 Ctrl+Alt+Del')
    fireEvent.click(ctrlAltDelButton)

    // 應該發送特殊按鍵組合到 VNC 連線
  })

  it('應該處理剪貼簿功能', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(),
        readText: jest.fn().mockResolvedValue('test clipboard content')
      }
    })

    render(<VNCViewer {...defaultProps} showToolbar={true} />)

    await waitFor(() => {
      const clipboardButton = screen.getByTitle('剪貼簿')
      expect(clipboardButton).toBeInTheDocument()
    })

    const clipboardButton = screen.getByTitle('剪貼簿')
    fireEvent.click(clipboardButton)

    await waitFor(() => {
      expect(screen.getByText('剪貼簿內容')).toBeInTheDocument()
    })
  })

  it('應該支援質量設定調整', async () => {
    render(<VNCViewer {...defaultProps} showToolbar={true} />)

    await waitFor(() => {
      const settingsButton = screen.getByTitle('設定')
      expect(settingsButton).toBeInTheDocument()
    })

    const settingsButton = screen.getByTitle('設定')
    fireEvent.click(settingsButton)

    await waitFor(() => {
      expect(screen.getByText('畫質設定')).toBeInTheDocument()
      expect(screen.getByLabelText('高畫質')).toBeInTheDocument()
      expect(screen.getByLabelText('平衡')).toBeInTheDocument()
      expect(screen.getByLabelText('高效能')).toBeInTheDocument()
    })
  })
})