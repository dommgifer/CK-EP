/**
 * T072: VM 配置管理頁面
 * 管理 Kubernetes 叢集 VM 配置的 CRUD 操作
 */
import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import { PlusIcon, TrashIcon, PencilIcon, PlayIcon } from '@heroicons/react/24/outline'

import { vmConfigApi } from '../services/vmConfigApi'
import VMNodeConfig from '../components/VMNodeConfig'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

interface VMConfig {
  id: string
  name: string
  master_nodes: Array<{
    ip_address: string
    hostname: string
    role: string
    ssh_port: number
  }>
  worker_nodes: Array<{
    ip_address: string
    hostname: string
    role: string
    ssh_port: number
  }>
  ssh_username: string
  connection_status: string
  last_tested_at?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export default function VMConfigPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<VMConfig | null>(null)
  const [selectedConfig, setSelectedConfig] = useState<string | null>(null)

  const queryClient = useQueryClient()

  // 查詢所有 VM 配置
  const {
    data: vmConfigs,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['vmConfigs'],
    queryFn: vmConfigApi.getAll
  })

  // 刪除 VM 配置
  const deleteMutation = useMutation({
    mutationFn: vmConfigApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vmConfigs'] })
      toast.success('VM 配置已刪除')
    },
    onError: (error) => {
      toast.error(`刪除失敗: ${error.message}`)
    }
  })

  // 測試連線
  const testConnectionMutation = useMutation({
    mutationFn: vmConfigApi.testConnection,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['vmConfigs'] })
      if (data.success) {
        toast.success('連線測試成功')
      } else {
        toast.error(`連線測試失敗: ${data.error}`)
      }
    },
    onError: (error) => {
      toast.error(`連線測試失敗: ${error.message}`)
    }
  })

  const handleDelete = async (configId: string) => {
    if (window.confirm('確定要刪除此 VM 配置？此操作無法復原。')) {
      deleteMutation.mutate(configId)
    }
  }

  const handleTestConnection = async (configId: string) => {
    if (window.confirm('確定要測試此 VM 配置的連線？')) {
      testConnectionMutation.mutate(configId)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      success: { bg: 'bg-green-100', text: 'text-green-800', label: '連線正常' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: '連線失敗' },
      untested: { bg: 'bg-gray-100', text: 'text-gray-800', label: '未測試' }
    }

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.untested

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
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
        title="載入 VM 配置失敗"
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
          <h1 className="text-2xl font-bold text-gray-900">VM 配置管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            管理 Kubernetes 叢集的虛擬機器配置
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          新增 VM 配置
        </button>
      </div>

      {/* VM 配置列表 */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {vmConfigs && vmConfigs.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {vmConfigs.map((config: VMConfig) => (
              <li key={config.id}>
                <div className="px-4 py-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-medium text-gray-900">
                        {config.name}
                      </h3>
                      {getStatusBadge(config.connection_status)}
                    </div>

                    <div className="mt-2 text-sm text-gray-500">
                      <p>
                        Master 節點: {config.master_nodes.length} 個 |
                        Worker 節點: {config.worker_nodes.length} 個
                      </p>
                      <p>SSH 使用者: {config.ssh_username}</p>
                      {config.last_tested_at && (
                        <p>最後測試: {new Date(config.last_tested_at).toLocaleString()}</p>
                      )}
                    </div>

                    {config.error_message && (
                      <div className="mt-2 text-sm text-red-600">
                        錯誤: {config.error_message}
                      </div>
                    )}

                    {/* 節點詳細資訊 */}
                    {selectedConfig === config.id && (
                      <div className="mt-4 space-y-3">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Master 節點</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {config.master_nodes.map((node, index) => (
                              <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                                {node.ip_address} ({node.hostname || 'N/A'})
                              </div>
                            ))}
                          </div>
                        </div>

                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Worker 節點</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {config.worker_nodes.map((node, index) => (
                              <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                                {node.ip_address} ({node.hostname || 'N/A'})
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedConfig(
                        selectedConfig === config.id ? null : config.id
                      )}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      {selectedConfig === config.id ? '收起' : '展開'}
                    </button>

                    <button
                      onClick={() => handleTestConnection(config.id)}
                      disabled={testConnectionMutation.isLoading}
                      className="inline-flex items-center p-1 border border-transparent rounded text-green-600 hover:text-green-800 disabled:opacity-50"
                      title="測試連線"
                    >
                      <PlayIcon className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => setEditingConfig(config)}
                      className="inline-flex items-center p-1 border border-transparent rounded text-blue-600 hover:text-blue-800"
                      title="編輯"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => handleDelete(config.id)}
                      disabled={deleteMutation.isLoading}
                      className="inline-flex items-center p-1 border border-transparent rounded text-red-600 hover:text-red-800 disabled:opacity-50"
                      title="刪除"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">沒有 VM 配置</h3>
            <p className="mt-1 text-sm text-gray-500">
              開始建立您的第一個 Kubernetes 叢集配置
            </p>
            <div className="mt-6">
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                新增 VM 配置
              </button>
            </div>
          </div>
        )}
      </div>

      {/* VM 配置表單模態 */}
      {(isCreateModalOpen || editingConfig) && (
        <VMNodeConfig
          config={editingConfig}
          isOpen={isCreateModalOpen || !!editingConfig}
          onClose={() => {
            setIsCreateModalOpen(false)
            setEditingConfig(null)
          }}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['vmConfigs'] })
            setIsCreateModalOpen(false)
            setEditingConfig(null)
          }}
        />
      )}
    </div>
  )
}