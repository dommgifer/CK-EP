/**
 * T102: VMConfigPage 頁面組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import '@testing-library/jest-dom'
import VMConfigPage from '../../pages/VMConfigPage'

// Mock API client
jest.mock('../../services/vmConfigApi', () => ({
  vmConfigApi: {
    getAll: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  },
}))

// Mock toast notifications
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const vmConfigApi = require('../../services/vmConfigApi').vmConfigApi

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

const mockVMConfigs = [
  {
    id: 'config-1',
    name: '測試叢集 1',
    description: '用於 CKA 考試的測試叢集',
    nodes: [
      {
        name: 'master-1',
        ip: '192.168.1.10',
        roles: ['master', 'etcd'],
        specs: { cpu: 2, memory: '4Gi', disk: '20Gi' }
      },
      {
        name: 'worker-1',
        ip: '192.168.1.11',
        roles: ['worker'],
        specs: { cpu: 2, memory: '4Gi', disk: '20Gi' }
      }
    ],
    ssh_user: 'ubuntu',
    created_by: 'test_user',
    created_at: '2025-09-24T08:00:00Z',
    updated_at: '2025-09-24T08:00:00Z'
  },
  {
    id: 'config-2',
    name: '測試叢集 2',
    description: '用於 CKAD 考試的測試叢集',
    nodes: [
      {
        name: 'master-1',
        ip: '192.168.1.20',
        roles: ['master', 'etcd'],
        specs: { cpu: 2, memory: '4Gi', disk: '20Gi' }
      }
    ],
    ssh_user: 'ubuntu',
    created_by: 'test_user',
    created_at: '2025-09-24T08:00:00Z',
    updated_at: '2025-09-24T08:00:00Z'
  }
]

describe('VMConfigPage', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()
    // Default API responses
    vmConfigApi.getAll.mockResolvedValue(mockVMConfigs)
  })

  it('應該渲染頁面標題和基本元素', async () => {
    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    expect(screen.getByText('VM 叢集配置管理')).toBeInTheDocument()
    expect(screen.getByText('建立新配置')).toBeInTheDocument()

    // 等待資料載入
    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })
  })

  it('應該顯示 VM 配置列表', async () => {
    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
      expect(screen.getByText('測試叢集 2')).toBeInTheDocument()
      expect(screen.getByText('用於 CKA 考試的測試叢集')).toBeInTheDocument()
      expect(screen.getByText('用於 CKAD 考試的測試叢集')).toBeInTheDocument()
    })

    // 檢查節點資訊
    expect(screen.getByText('2 個節點')).toBeInTheDocument()
    expect(screen.getByText('1 個節點')).toBeInTheDocument()
  })

  it('應該顯示載入狀態', () => {
    vmConfigApi.getAll.mockReturnValue(new Promise(() => {})) // Never resolves

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    expect(screen.getByText('載入中...')).toBeInTheDocument()
  })

  it('應該顯示錯誤狀態', async () => {
    vmConfigApi.getAll.mockRejectedValue(new Error('API 錯誤'))

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/載入 VM 配置時發生錯誤/)).toBeInTheDocument()
    })
  })

  it('應該能夠打開新增配置對話框', async () => {
    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    const createButton = screen.getByText('建立新配置')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('建立 VM 叢集配置')).toBeInTheDocument()
    })
  })

  it('應該能夠編輯現有配置', async () => {
    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByText('編輯')
    fireEvent.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('編輯 VM 叢集配置')).toBeInTheDocument()
    })
  })

  it('應該能夠刪除配置', async () => {
    vmConfigApi.delete.mockResolvedValue({})

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByText('刪除')
    fireEvent.click(deleteButtons[0])

    // 確認刪除對話框
    await waitFor(() => {
      expect(screen.getByText('確認刪除')).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: '刪除' })
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(vmConfigApi.delete).toHaveBeenCalledWith('config-1')
    })
  })

  it('應該能夠搜尋和過濾配置', async () => {
    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
      expect(screen.getByText('測試叢集 2')).toBeInTheDocument()
    })

    // 輸入搜尋條件
    const searchInput = screen.getByPlaceholderText('搜尋配置...')
    fireEvent.change(searchInput, { target: { value: 'CKA' } })

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
      expect(screen.queryByText('測試叢集 2')).not.toBeInTheDocument()
    })
  })

  it('應該能夠複製配置', async () => {
    vmConfigApi.create.mockResolvedValue({
      id: 'config-3',
      name: '測試叢集 1 (複本)',
      ...mockVMConfigs[0]
    })

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })

    const copyButtons = screen.getAllByText('複製')
    fireEvent.click(copyButtons[0])

    await waitFor(() => {
      expect(vmConfigApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: '測試叢集 1 (複本)',
          description: '用於 CKA 考試的測試叢集'
        })
      )
    })
  })

  it('應該顯示配置詳細資訊', async () => {
    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })

    const viewButtons = screen.getAllByText('檢視')
    fireEvent.click(viewButtons[0])

    await waitFor(() => {
      expect(screen.getByText('配置詳細資訊')).toBeInTheDocument()
      expect(screen.getByText('master-1')).toBeInTheDocument()
      expect(screen.getByText('worker-1')).toBeInTheDocument()
      expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
      expect(screen.getByText('192.168.1.11')).toBeInTheDocument()
    })
  })

  it('應該處理表單提交錯誤', async () => {
    vmConfigApi.create.mockRejectedValue(new Error('建立失敗'))

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    const createButton = screen.getByText('建立新配置')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('建立 VM 叢集配置')).toBeInTheDocument()
    })

    // 填寫表單
    const nameInput = screen.getByLabelText('配置名稱')
    fireEvent.change(nameInput, { target: { value: '新配置' } })

    const submitButton = screen.getByRole('button', { name: '建立' })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/建立失敗/)).toBeInTheDocument()
    })
  })

  it('應該支援響應式設計', async () => {
    // 模擬手機螢幕
    global.innerWidth = 375
    global.innerHeight = 812
    global.dispatchEvent(new Event('resize'))

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })

    // 在小螢幕上，某些元素可能會隱藏或改變佈局
    // 這裡可以測試響應式行為
  })

  it('應該能夠匯出配置', async () => {
    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'blob:url')
    global.URL.revokeObjectURL = jest.fn()

    // Mock createElement to return a link element
    const mockLink = {
      click: jest.fn(),
      setAttribute: jest.fn(),
      style: {}
    }
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
    jest.spyOn(document.body, 'appendChild').mockImplementation()
    jest.spyOn(document.body, 'removeChild').mockImplementation()

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('測試叢集 1')).toBeInTheDocument()
    })

    const exportButtons = screen.getAllByText('匯出')
    fireEvent.click(exportButtons[0])

    expect(global.URL.createObjectURL).toHaveBeenCalled()
    expect(mockLink.click).toHaveBeenCalled()
  })

  it('應該能夠匯入配置', async () => {
    vmConfigApi.create.mockResolvedValue(mockVMConfigs[0])

    render(
      <TestWrapper>
        <VMConfigPage />
      </TestWrapper>
    )

    const importButton = screen.getByText('匯入配置')
    fireEvent.click(importButton)

    // 模擬檔案選擇
    const fileInput = screen.getByLabelText('選擇配置檔案')
    const file = new File(
      [JSON.stringify(mockVMConfigs[0])],
      'config.json',
      { type: 'application/json' }
    )

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(vmConfigApi.create).toHaveBeenCalled()
    })
  })
})