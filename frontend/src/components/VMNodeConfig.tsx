/**
 * T077: VM 節點配置組件
 * 用於建立和編輯 VM 配置的表單組件
 */
import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline'

import { vmConfigApi, type VMConfig, type VMConfigCreate, type VMNode } from '../services/vmConfigApi'
import LoadingSpinner from './LoadingSpinner'

interface VMNodeConfigProps {
  config?: VMConfig | null
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function VMNodeConfig({ config, isOpen, onClose, onSuccess }: VMNodeConfigProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<VMConfigCreate>({
    name: '',
    master_nodes: [{ ip_address: '', hostname: '', role: 'master', ssh_port: 22 }],
    worker_nodes: [{ ip_address: '', hostname: '', role: 'worker', ssh_port: 22 }],
    ssh_username: 'root'
  })

  // 編輯模式時載入現有資料
  useEffect(() => {
    if (config) {
      setFormData({
        name: config.name,
        master_nodes: config.master_nodes,
        worker_nodes: config.worker_nodes,
        ssh_username: config.ssh_username
      })
    } else {
      // 重置表單
      setFormData({
        name: '',
        master_nodes: [{ ip_address: '', hostname: '', role: 'master', ssh_port: 22 }],
        worker_nodes: [{ ip_address: '', hostname: '', role: 'worker', ssh_port: 22 }],
        ssh_username: 'root'
      })
    }
  }, [config])

  // 建立 VM 配置
  const createMutation = useMutation({
    mutationFn: vmConfigApi.create,
    onSuccess: () => {
      toast.success('VM 配置已建立')
      onSuccess()
    },
    onError: (error) => {
      toast.error(`建立失敗: ${error.message}`)
    }
  })

  // 更新 VM 配置
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: VMConfigCreate }) =>
      vmConfigApi.update(id, data),
    onSuccess: () => {
      toast.success('VM 配置已更新')
      onSuccess()
    },
    onError: (error) => {
      toast.error(`更新失敗: ${error.message}`)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // 驗證表單
    if (!formData.name.trim()) {
      toast.error('請輸入配置名稱')
      return
    }

    if (formData.master_nodes.length === 0) {
      toast.error('至少需要一個 Master 節點')
      return
    }

    if (formData.master_nodes.some(node => !node.ip_address.trim())) {
      toast.error('請填寫所有 Master 節點的 IP 地址')
      return
    }

    if (config) {
      updateMutation.mutate({ id: config.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const addNode = (type: 'master' | 'worker') => {
    const newNode: VMNode = {
      ip_address: '',
      hostname: '',
      role: type,
      ssh_port: 22
    }

    if (type === 'master') {
      setFormData(prev => ({
        ...prev,
        master_nodes: [...prev.master_nodes, newNode]
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        worker_nodes: [...prev.worker_nodes, newNode]
      }))
    }
  }

  const removeNode = (type: 'master' | 'worker', index: number) => {
    if (type === 'master') {
      if (formData.master_nodes.length <= 1) {
        toast.error('至少需要一個 Master 節點')
        return
      }
      setFormData(prev => ({
        ...prev,
        master_nodes: prev.master_nodes.filter((_, i) => i !== index)
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        worker_nodes: prev.worker_nodes.filter((_, i) => i !== index)
      }))
    }
  }

  const updateNode = (type: 'master' | 'worker', index: number, field: keyof VMNode, value: string | number) => {
    if (type === 'master') {
      setFormData(prev => ({
        ...prev,
        master_nodes: prev.master_nodes.map((node, i) =>
          i === index ? { ...node, [field]: value } : node
        )
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        worker_nodes: prev.worker_nodes.map((node, i) =>
          i === index ? { ...node, [field]: value } : node
        )
      }))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* 標題 */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium text-gray-900">
            {config ? '編輯 VM 配置' : '建立 VM 配置'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本資訊 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                配置名稱 *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="例如：Production Cluster"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                SSH 使用者名稱 *
              </label>
              <input
                type="text"
                value={formData.ssh_username}
                onChange={(e) => setFormData(prev => ({ ...prev, ssh_username: e.target.value }))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="root"
              />
            </div>
          </div>

          {/* Master 節點 */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-md font-medium text-gray-900">Master 節點</h4>
              <button
                type="button"
                onClick={() => addNode('master')}
                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded text-blue-600 hover:text-blue-800"
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                新增
              </button>
            </div>

            <div className="space-y-3">
              {formData.master_nodes.map((node, index) => (
                <div key={index} className="grid grid-cols-12 gap-3 items-end">
                  <div className="col-span-4">
                    <label className="block text-xs font-medium text-gray-700">IP 地址 *</label>
                    <input
                      type="text"
                      value={node.ip_address}
                      onChange={(e) => updateNode('master', index, 'ip_address', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                      placeholder="192.168.1.100"
                    />
                  </div>
                  <div className="col-span-3">
                    <label className="block text-xs font-medium text-gray-700">主機名稱</label>
                    <input
                      type="text"
                      value={node.hostname}
                      onChange={(e) => updateNode('master', index, 'hostname', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                      placeholder="master-1"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-medium text-gray-700">SSH 埠</label>
                    <input
                      type="number"
                      value={node.ssh_port}
                      onChange={(e) => updateNode('master', index, 'ssh_port', parseInt(e.target.value))}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                      min="1"
                      max="65535"
                    />
                  </div>
                  <div className="col-span-2">
                    <span className="block text-xs font-medium text-gray-700">角色</span>
                    <span className="mt-1 block px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded text-center">
                      Master
                    </span>
                  </div>
                  <div className="col-span-1">
                    {formData.master_nodes.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeNode('master', index)}
                        className="p-1 text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Worker 節點 */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-md font-medium text-gray-900">Worker 節點</h4>
              <button
                type="button"
                onClick={() => addNode('worker')}
                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded text-blue-600 hover:text-blue-800"
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                新增
              </button>
            </div>

            <div className="space-y-3">
              {formData.worker_nodes.map((node, index) => (
                <div key={index} className="grid grid-cols-12 gap-3 items-end">
                  <div className="col-span-4">
                    <label className="block text-xs font-medium text-gray-700">IP 地址</label>
                    <input
                      type="text"
                      value={node.ip_address}
                      onChange={(e) => updateNode('worker', index, 'ip_address', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                      placeholder="192.168.1.101"
                    />
                  </div>
                  <div className="col-span-3">
                    <label className="block text-xs font-medium text-gray-700">主機名稱</label>
                    <input
                      type="text"
                      value={node.hostname}
                      onChange={(e) => updateNode('worker', index, 'hostname', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                      placeholder="worker-1"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-medium text-gray-700">SSH 埠</label>
                    <input
                      type="number"
                      value={node.ssh_port}
                      onChange={(e) => updateNode('worker', index, 'ssh_port', parseInt(e.target.value))}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                      min="1"
                      max="65535"
                    />
                  </div>
                  <div className="col-span-2">
                    <span className="block text-xs font-medium text-gray-700">角色</span>
                    <span className="mt-1 block px-2 py-1 bg-green-100 text-green-800 text-sm rounded text-center">
                      Worker
                    </span>
                  </div>
                  <div className="col-span-1">
                    <button
                      type="button"
                      onClick={() => removeNode('worker', index)}
                      className="p-1 text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createMutation.isLoading || updateMutation.isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {(createMutation.isLoading || updateMutation.isLoading) && (
                <LoadingSpinner size="sm" className="mr-2" />
              )}
              {config ? '更新' : '建立'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}