/**
 * T080: 環境狀態組件
 * 顯示 Kubernetes 叢集和考試環境的狀態
 */
import React from 'react'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  XCircleIcon,
  ArrowPathIcon,
  ServerIcon,
  ComputerDesktopIcon,
  CloudIcon
} from '@heroicons/react/24/outline'

interface EnvironmentStatusProps {
  sessionId?: string
  environment?: {
    cluster_status: 'not_ready' | 'deploying' | 'ready' | 'error'
    cluster_progress?: number
    cluster_message?: string
    vnc_status: 'not_ready' | 'starting' | 'ready' | 'error'
    vnc_url?: string
    bastion_status: 'not_ready' | 'starting' | 'ready' | 'error'
    ssh_status: 'not_ready' | 'ready' | 'error'
    deployment_log?: string[]
  }
  onRefresh?: () => void
  onStartEnvironment?: () => void
  onStopEnvironment?: () => void
  isLoading?: boolean
  className?: string
}

interface StatusItemProps {
  title: string
  status: 'not_ready' | 'deploying' | 'starting' | 'ready' | 'error'
  icon: React.ComponentType<any>
  message?: string
  progress?: number
  details?: string[]
  url?: string
}

const StatusItem: React.FC<StatusItemProps> = ({
  title,
  status,
  icon: Icon,
  message,
  progress,
  details,
  url
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'ready':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          borderColor: 'border-green-200',
          statusText: '就緒',
          statusIcon: CheckCircleIcon
        }
      case 'deploying':
      case 'starting':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          borderColor: 'border-yellow-200',
          statusText: status === 'deploying' ? '部署中' : '啟動中',
          statusIcon: ClockIcon
        }
      case 'error':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          borderColor: 'border-red-200',
          statusText: '錯誤',
          statusIcon: XCircleIcon
        }
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          borderColor: 'border-gray-200',
          statusText: '未就緒',
          statusIcon: ClockIcon
        }
    }
  }

  const config = getStatusConfig()
  const StatusIcon = config.statusIcon

  return (
    <div className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className={`h-5 w-5 ${config.color}`} />
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        <div className="flex items-center space-x-1">
          <StatusIcon className={`h-4 w-4 ${config.color}`} />
          <span className={`text-sm font-medium ${config.color}`}>
            {config.statusText}
          </span>
        </div>
      </div>

      {message && (
        <p className="text-sm text-gray-600 mb-2">{message}</p>
      )}

      {progress !== undefined && progress >= 0 && (
        <div className="mb-2">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>進度</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {url && status === 'ready' && (
        <div className="mt-2">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            開啟連結
          </a>
        </div>
      )}

      {details && details.length > 0 && (
        <details className="mt-2">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
            查看詳細資訊
          </summary>
          <div className="mt-2 p-2 bg-white rounded border text-xs">
            {details.map((detail, index) => (
              <div key={index} className="mb-1 font-mono text-gray-700">
                {detail}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

export default function EnvironmentStatus({
  sessionId,
  environment,
  onRefresh,
  onStartEnvironment,
  onStopEnvironment,
  isLoading = false,
  className = ''
}: EnvironmentStatusProps) {
  const hasEnvironment = !!environment

  // 計算整體狀態
  const getOverallStatus = () => {
    if (!environment) return 'not_ready'

    const statuses = [
      environment.cluster_status,
      environment.vnc_status,
      environment.bastion_status,
      environment.ssh_status
    ]

    if (statuses.some(s => s === 'error')) return 'error'
    if (statuses.some(s => s === 'deploying' || s === 'starting')) return 'starting'
    if (statuses.every(s => s === 'ready')) return 'ready'
    return 'not_ready'
  }

  const overallStatus = getOverallStatus()
  const canStart = !hasEnvironment || overallStatus === 'not_ready' || overallStatus === 'error'
  const canStop = hasEnvironment && overallStatus !== 'not_ready'

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 整體狀態標題 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <CloudIcon className="h-6 w-6 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-900">環境狀態</h3>
          {sessionId && (
            <span className="text-sm text-gray-500">會話: {sessionId}</span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
              title="重新整理狀態"
            >
              <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}

          {onStartEnvironment && canStart && (
            <button
              onClick={onStartEnvironment}
              disabled={isLoading}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
            >
              啟動環境
            </button>
          )}

          {onStopEnvironment && canStop && (
            <button
              onClick={onStopEnvironment}
              disabled={isLoading}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
            >
              停止環境
            </button>
          )}
        </div>
      </div>

      {!hasEnvironment ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <CloudIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">環境尚未建立</h4>
          <p className="text-gray-600 mb-4">
            點擊「啟動環境」開始部署 Kubernetes 叢集和考試環境
          </p>
          {onStartEnvironment && (
            <button
              onClick={onStartEnvironment}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              啟動環境
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Kubernetes 叢集狀態 */}
          <StatusItem
            title="Kubernetes 叢集"
            status={environment.cluster_status}
            icon={ServerIcon}
            message={environment.cluster_message}
            progress={environment.cluster_progress}
            details={environment.deployment_log?.slice(-5)}
          />

          {/* VNC 桌面狀態 */}
          <StatusItem
            title="VNC 桌面"
            status={environment.vnc_status}
            icon={ComputerDesktopIcon}
            message="遠端桌面環境"
            url={environment.vnc_url}
          />

          {/* Bastion 容器狀態 */}
          <StatusItem
            title="Bastion 容器"
            status={environment.bastion_status}
            icon={ServerIcon}
            message="kubectl 工具容器"
          />

          {/* SSH 連線狀態 */}
          <StatusItem
            title="SSH 連線"
            status={environment.ssh_status}
            icon={CloudIcon}
            message="叢集 SSH 存取"
          />
        </div>
      )}

      {/* 部署日誌 */}
      {environment?.deployment_log && environment.deployment_log.length > 0 && (
        <div className="mt-6">
          <details className="bg-gray-50 rounded-lg">
            <summary className="px-4 py-3 cursor-pointer font-medium text-gray-900 hover:bg-gray-100 rounded-lg">
              部署日誌 ({environment.deployment_log.length} 行)
            </summary>
            <div className="px-4 pb-4 max-h-64 overflow-y-auto">
              <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                {environment.deployment_log.join('\n')}
              </pre>
            </div>
          </details>
        </div>
      )}

      {/* 整體狀態摘要 */}
      <div className={`p-4 rounded-lg border-2 ${
        overallStatus === 'ready' ? 'border-green-200 bg-green-50' :
        overallStatus === 'error' ? 'border-red-200 bg-red-50' :
        overallStatus === 'starting' ? 'border-yellow-200 bg-yellow-50' :
        'border-gray-200 bg-gray-50'
      }`}>
        <div className="flex items-center space-x-2">
          {overallStatus === 'ready' && <CheckCircleIcon className="h-5 w-5 text-green-600" />}
          {overallStatus === 'error' && <XCircleIcon className="h-5 w-5 text-red-600" />}
          {overallStatus === 'starting' && <ClockIcon className="h-5 w-5 text-yellow-600" />}
          {overallStatus === 'not_ready' && <ClockIcon className="h-5 w-5 text-gray-600" />}

          <span className="font-medium">
            {overallStatus === 'ready' && '環境已就緒，可以開始考試'}
            {overallStatus === 'error' && '環境發生錯誤，請檢查組態或重新啟動'}
            {overallStatus === 'starting' && '環境正在初始化，請稍候...'}
            {overallStatus === 'not_ready' && '環境尚未準備，請先啟動環境'}
          </span>
        </div>
      </div>
    </div>
  )
}