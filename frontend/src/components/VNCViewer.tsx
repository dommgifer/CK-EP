/**
 * T079: VNC 檢視器組件
 * 嵌入式 noVNC 連線介面
 */
import React, { useEffect, useRef, useState } from 'react'
import {
  ComputerDesktopIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline'

interface VNCViewerProps {
  sessionId: string
  host?: string
  port?: number
  path?: string
  password?: string
  autoConnect?: boolean
  onConnected?: () => void
  onDisconnected?: () => void
  onError?: (error: string) => void
  className?: string
}

interface VNCSettings {
  viewOnly: boolean
  shared: boolean
  scaleViewport: boolean
  resizeSession: boolean
  showDotCursor: boolean
  clipViewport: boolean
}

export default function VNCViewer({
  sessionId,
  host = window.location.hostname,
  port = 80,
  path = `/api/v1/exam-sessions/${sessionId}/vnc`,
  password,
  autoConnect = true,
  onConnected,
  onDisconnected,
  onError,
  className = ''
}: VNCViewerProps) {
  const vncContainerRef = useRef<HTMLDivElement>(null)
  const rfbRef = useRef<any>(null)

  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [settings, setSettings] = useState<VNCSettings>({
    viewOnly: false,
    shared: true,
    scaleViewport: true,
    resizeSession: false,
    showDotCursor: false,
    clipViewport: true
  })

  // 載入 noVNC 腳本
  useEffect(() => {
    const loadNoVNC = async () => {
      // 檢查 noVNC 是否已載入
      if (window.RFB) {
        return true
      }

      try {
        // 動態載入 noVNC 腳本
        const script = document.createElement('script')
        script.src = '/novnc/app.js'
        script.async = true

        return new Promise((resolve, reject) => {
          script.onload = () => {
            if (window.RFB) {
              resolve(true)
            } else {
              reject(new Error('noVNC 載入失敗'))
            }
          }
          script.onerror = () => reject(new Error('無法載入 noVNC 腳本'))
          document.head.appendChild(script)
        })
      } catch (err) {
        throw new Error('載入 noVNC 時發生錯誤')
      }
    }

    loadNoVNC().catch(err => {
      setError(err.message)
      onError?.(err.message)
    })
  }, [onError])

  // 連線函數
  const connect = async () => {
    if (!window.RFB || !vncContainerRef.current) {
      setError('VNC 環境尚未準備就緒')
      return
    }

    if (rfbRef.current) {
      rfbRef.current.disconnect()
    }

    setIsConnecting(true)
    setError(null)

    try {
      // 建構 WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${host}:${port}${path}`

      // 建立 RFB 連線
      const rfb = new window.RFB(vncContainerRef.current, wsUrl, {
        credentials: { password: password || '' },
        shared: settings.shared,
        repeaterID: '',
        wsProtocols: ['binary']
      })

      // 設定事件監聽器
      rfb.addEventListener('connect', () => {
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        onConnected?.()
      })

      rfb.addEventListener('disconnect', (e: any) => {
        setIsConnected(false)
        setIsConnecting(false)
        rfbRef.current = null

        if (e.detail.clean) {
          console.log('VNC 連線正常斷開')
        } else {
          const errorMsg = `VNC 連線異常斷開: ${e.detail.reason}`
          setError(errorMsg)
          onError?.(errorMsg)
        }
        onDisconnected?.()
      })

      rfb.addEventListener('credentialsrequired', () => {
        const pwd = prompt('請輸入 VNC 密碼:')
        if (pwd) {
          rfb.sendCredentials({ password: pwd })
        } else {
          rfb.disconnect()
        }
      })

      rfb.addEventListener('securityfailure', (e: any) => {
        const errorMsg = `VNC 安全驗證失敗: ${e.detail.reason}`
        setError(errorMsg)
        onError?.(errorMsg)
      })

      // 應用設定
      rfb.viewOnly = settings.viewOnly
      rfb.scaleViewport = settings.scaleViewport
      rfb.resizeSession = settings.resizeSession
      rfb.showDotCursor = settings.showDotCursor
      rfb.clipViewport = settings.clipViewport

      rfbRef.current = rfb

    } catch (err: any) {
      setIsConnecting(false)
      const errorMsg = `VNC 連線錯誤: ${err.message}`
      setError(errorMsg)
      onError?.(errorMsg)
    }
  }

  // 斷線函數
  const disconnect = () => {
    if (rfbRef.current) {
      rfbRef.current.disconnect()
      rfbRef.current = null
    }
  }

  // 自動連線
  useEffect(() => {
    if (autoConnect && window.RFB) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, sessionId])

  // 設定變更處理
  const handleSettingChange = (key: keyof VNCSettings, value: boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }))

    // 如果已連線，立即應用設定
    if (rfbRef.current) {
      switch (key) {
        case 'viewOnly':
          rfbRef.current.viewOnly = value
          break
        case 'scaleViewport':
          rfbRef.current.scaleViewport = value
          break
        case 'resizeSession':
          rfbRef.current.resizeSession = value
          break
        case 'showDotCursor':
          rfbRef.current.showDotCursor = value
          break
        case 'clipViewport':
          rfbRef.current.clipViewport = value
          break
      }
    }
  }

  return (
    <div className={`flex flex-col h-full bg-black ${className}`}>
      {/* 工具欄 */}
      <div className="flex items-center justify-between bg-gray-800 text-white px-4 py-2">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <ComputerDesktopIcon className="h-5 w-5" />
            <span className="text-sm font-medium">VNC 桌面</span>
          </div>

          <div className={`text-xs px-2 py-1 rounded ${
            isConnected ? 'bg-green-600' : isConnecting ? 'bg-yellow-600' : 'bg-red-600'
          }`}>
            {isConnected ? '已連線' : isConnecting ? '連線中...' : '未連線'}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSettings(prev => ({ ...prev, viewOnly: !prev.viewOnly }))}
            className={`p-1 rounded hover:bg-gray-700 ${
              settings.viewOnly ? 'text-yellow-400' : 'text-gray-300'
            }`}
            title={settings.viewOnly ? '檢視模式 (點擊切換為控制模式)' : '控制模式 (點擊切換為檢視模式)'}
          >
            {settings.viewOnly ? <EyeIcon className="h-4 w-4" /> : <EyeSlashIcon className="h-4 w-4" />}
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1 rounded hover:bg-gray-700 text-gray-300"
            title="設定"
          >
            <Cog6ToothIcon className="h-4 w-4" />
          </button>

          <button
            onClick={isConnected ? disconnect : connect}
            disabled={isConnecting}
            className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            {isConnected ? '斷線' : isConnecting ? '連線中...' : '連線'}
          </button>
        </div>
      </div>

      {/* 設定面板 */}
      {showSettings && (
        <div className="bg-gray-700 text-white p-4 border-b border-gray-600">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.scaleViewport}
                onChange={(e) => handleSettingChange('scaleViewport', e.target.checked)}
                className="rounded"
              />
              <span>縮放檢視區</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.clipViewport}
                onChange={(e) => handleSettingChange('clipViewport', e.target.checked)}
                className="rounded"
              />
              <span>裁剪檢視區</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.resizeSession}
                onChange={(e) => handleSettingChange('resizeSession', e.target.checked)}
                className="rounded"
              />
              <span>調整會話大小</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.showDotCursor}
                onChange={(e) => handleSettingChange('showDotCursor', e.target.checked)}
                className="rounded"
              />
              <span>顯示點狀游標</span>
            </label>
          </div>
        </div>
      )}

      {/* VNC 容器 */}
      <div className="flex-1 relative">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 z-10">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded max-w-md text-center">
              <div className="flex items-center justify-center mb-2">
                <ExclamationTriangleIcon className="h-6 w-6 mr-2" />
                <span className="font-semibold">連線錯誤</span>
              </div>
              <p className="text-sm mb-3">{error}</p>
              <button
                onClick={() => {
                  setError(null)
                  connect()
                }}
                className="inline-flex items-center px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
              >
                <ArrowPathIcon className="h-4 w-4 mr-1" />
                重試
              </button>
            </div>
          </div>
        )}

        {isConnecting && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 z-10">
            <div className="text-center text-white">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p>正在連線到遠端桌面...</p>
            </div>
          </div>
        )}

        {!isConnected && !isConnecting && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black text-white">
            <div className="text-center">
              <ComputerDesktopIcon className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium mb-2">VNC 桌面環境</h3>
              <p className="text-sm text-gray-400 mb-4">點擊連線按鈕開始存取遠端桌面</p>
              <button
                onClick={connect}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                連線到桌面
              </button>
            </div>
          </div>
        )}

        <div
          ref={vncContainerRef}
          className="w-full h-full"
          style={{
            display: isConnected ? 'block' : 'none',
            minHeight: '400px'
          }}
        />
      </div>
    </div>
  )
}

// 擴展全域 Window 型別以包含 RFB
declare global {
  interface Window {
    RFB: any
  }
}