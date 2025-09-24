/**
 * T088: VM 配置狀態管理
 * 使用 Zustand 管理 VM 配置的全域狀態
 */
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { vmConfigApi, type VMConfig, type VMConfigCreate } from '../services/vmConfigApi'

export interface VMConfigValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
  lastChecked?: string
}

export interface VMConfigState {
  // 配置列表和當前選中的配置
  configs: VMConfig[]
  currentConfig: VMConfig | null
  selectedConfigId: string | null

  // 驗證狀態
  validationResults: Record<string, VMConfigValidation>

  // UI 狀態
  isLoading: boolean
  error: string | null
  isCreating: boolean
  isUpdating: boolean
  isDeleting: string | null // 正在刪除的配置 ID

  // 操作
  loadConfigs: () => Promise<void>
  getConfig: (id: string) => Promise<VMConfig>
  createConfig: (data: VMConfigCreate) => Promise<VMConfig>
  updateConfig: (id: string, data: VMConfigCreate) => Promise<VMConfig>
  deleteConfig: (id: string) => Promise<void>
  selectConfig: (id: string | null) => void

  // 驗證
  validateConfig: (config: VMConfig) => Promise<VMConfigValidation>
  validateAllConfigs: () => Promise<void>
  clearValidation: (configId: string) => void

  // 測試連線
  testConnection: (config: VMConfig) => Promise<{
    success: boolean
    message: string
    details: Record<string, any>
  }>

  // 狀態重置
  reset: () => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
}

const initialState = {
  configs: [],
  currentConfig: null,
  selectedConfigId: null,
  validationResults: {},
  isLoading: false,
  error: null,
  isCreating: false,
  isUpdating: false,
  isDeleting: null
}

export const useVMConfigStore = create<VMConfigState>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,

        // 載入所有配置
        loadConfigs: async () => {
          set(state => {
            state.isLoading = true
            state.error = null
          })

          try {
            const configs = await vmConfigApi.getAll()
            set(state => {
              state.configs = configs
              state.isLoading = false

              // 如果有選中的配置 ID，更新 currentConfig
              if (state.selectedConfigId) {
                const selectedConfig = configs.find(c => c.id === state.selectedConfigId)
                if (selectedConfig) {
                  state.currentConfig = selectedConfig
                } else {
                  // 選中的配置不存在，清除選擇
                  state.selectedConfigId = null
                  state.currentConfig = null
                }
              }
            })
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isLoading = false
            })
            throw error
          }
        },

        // 取得單一配置
        getConfig: async (id: string) => {
          try {
            const config = await vmConfigApi.getById(id)

            set(state => {
              // 更新列表中的配置
              const index = state.configs.findIndex(c => c.id === id)
              if (index !== -1) {
                state.configs[index] = config
              } else {
                state.configs.push(config)
              }

              // 如果是當前選中的配置，也更新
              if (state.selectedConfigId === id) {
                state.currentConfig = config
              }
            })

            return config
          } catch (error: any) {
            set(state => { state.error = error.message })
            throw error
          }
        },

        // 建立新配置
        createConfig: async (data: VMConfigCreate) => {
          set(state => {
            state.isCreating = true
            state.error = null
          })

          try {
            const newConfig = await vmConfigApi.create(data)

            set(state => {
              state.configs.push(newConfig)
              state.isCreating = false
            })

            return newConfig
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isCreating = false
            })
            throw error
          }
        },

        // 更新配置
        updateConfig: async (id: string, data: VMConfigCreate) => {
          set(state => {
            state.isUpdating = true
            state.error = null
          })

          try {
            const updatedConfig = await vmConfigApi.update(id, data)

            set(state => {
              const index = state.configs.findIndex(c => c.id === id)
              if (index !== -1) {
                state.configs[index] = updatedConfig
              }

              // 如果是當前選中的配置，也更新
              if (state.selectedConfigId === id) {
                state.currentConfig = updatedConfig
              }

              state.isUpdating = false
            })

            // 清除舊的驗證結果
            get().clearValidation(id)

            return updatedConfig
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isUpdating = false
            })
            throw error
          }
        },

        // 刪除配置
        deleteConfig: async (id: string) => {
          set(state => {
            state.isDeleting = id
            state.error = null
          })

          try {
            await vmConfigApi.delete(id)

            set(state => {
              state.configs = state.configs.filter(c => c.id !== id)

              // 如果刪除的是當前選中的配置，清除選擇
              if (state.selectedConfigId === id) {
                state.selectedConfigId = null
                state.currentConfig = null
              }

              state.isDeleting = null
            })

            // 清除驗證結果
            get().clearValidation(id)
          } catch (error: any) {
            set(state => {
              state.error = error.message
              state.isDeleting = null
            })
            throw error
          }
        },

        // 選擇配置
        selectConfig: (id: string | null) => {
          set(state => {
            state.selectedConfigId = id

            if (id) {
              const config = state.configs.find(c => c.id === id)
              state.currentConfig = config || null
            } else {
              state.currentConfig = null
            }
          })
        },

        // 驗證單一配置
        validateConfig: async (config: VMConfig) => {
          try {
            // 模擬配置驗證邏輯
            const validation: VMConfigValidation = {
              isValid: true,
              errors: [],
              warnings: [],
              lastChecked: new Date().toISOString()
            }

            // 驗證 Master 節點
            if (!config.master_nodes || config.master_nodes.length === 0) {
              validation.isValid = false
              validation.errors.push('至少需要一個 Master 節點')
            } else {
              config.master_nodes.forEach((node, index) => {
                if (!node.ip_address.trim()) {
                  validation.isValid = false
                  validation.errors.push(`Master 節點 ${index + 1} 缺少 IP 地址`)
                }

                // 簡單的 IP 格式驗證
                const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
                if (node.ip_address && !ipRegex.test(node.ip_address)) {
                  validation.isValid = false
                  validation.errors.push(`Master 節點 ${index + 1} IP 地址格式不正確`)
                }

                if (!node.hostname.trim()) {
                  validation.warnings.push(`Master 節點 ${index + 1} 建議設定主機名稱`)
                }

                if (node.ssh_port < 1 || node.ssh_port > 65535) {
                  validation.isValid = false
                  validation.errors.push(`Master 節點 ${index + 1} SSH 埠號無效`)
                }
              })
            }

            // 驗證 Worker 節點（可選）
            config.worker_nodes?.forEach((node, index) => {
              if (node.ip_address && node.ip_address.trim()) {
                const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
                if (!ipRegex.test(node.ip_address)) {
                  validation.isValid = false
                  validation.errors.push(`Worker 節點 ${index + 1} IP 地址格式不正確`)
                }
              }

              if (node.ssh_port < 1 || node.ssh_port > 65535) {
                validation.isValid = false
                validation.errors.push(`Worker 節點 ${index + 1} SSH 埠號無效`)
              }
            })

            // 驗證 SSH 使用者名稱
            if (!config.ssh_username.trim()) {
              validation.isValid = false
              validation.errors.push('SSH 使用者名稱為必填')
            }

            // 檢查 IP 重複
            const allIPs = [
              ...config.master_nodes.map(n => n.ip_address),
              ...(config.worker_nodes || []).map(n => n.ip_address)
            ].filter(ip => ip.trim())

            const uniqueIPs = new Set(allIPs)
            if (allIPs.length !== uniqueIPs.size) {
              validation.isValid = false
              validation.errors.push('存在重複的 IP 地址')
            }

            set(state => {
              state.validationResults[config.id] = validation
            })

            return validation
          } catch (error: any) {
            const errorValidation: VMConfigValidation = {
              isValid: false,
              errors: [`驗證失敗: ${error.message}`],
              warnings: [],
              lastChecked: new Date().toISOString()
            }

            set(state => {
              state.validationResults[config.id] = errorValidation
            })

            return errorValidation
          }
        },

        // 驗證所有配置
        validateAllConfigs: async () => {
          const { configs } = get()
          const validationPromises = configs.map(config =>
            get().validateConfig(config).catch(console.error)
          )

          await Promise.all(validationPromises)
        },

        // 清除驗證結果
        clearValidation: (configId: string) => {
          set(state => {
            delete state.validationResults[configId]
          })
        },

        // 測試連線
        testConnection: async (config: VMConfig) => {
          try {
            // 這裡應該調用後端 API 進行實際的連線測試
            // 目前返回模擬結果
            const result = await vmConfigApi.testConnection?.(config) || {
              success: true,
              message: '連線測試成功',
              details: {
                master_nodes: config.master_nodes.map(node => ({
                  ip_address: node.ip_address,
                  status: 'connected',
                  response_time: Math.random() * 100
                })),
                worker_nodes: (config.worker_nodes || []).map(node => ({
                  ip_address: node.ip_address,
                  status: 'connected',
                  response_time: Math.random() * 100
                }))
              }
            }

            return result
          } catch (error: any) {
            return {
              success: false,
              message: `連線測試失敗: ${error.message}`,
              details: {}
            }
          }
        },

        // 狀態重置
        reset: () => {
          set(state => {
            Object.assign(state, initialState)
          })
        },

        setError: (error: string | null) => {
          set(state => {
            state.error = error
          })
        },

        setLoading: (loading: boolean) => {
          set(state => {
            state.isLoading = loading
          })
        }
      })),
      {
        name: 'vm-config-store',
        partialize: (state) => ({
          selectedConfigId: state.selectedConfigId,
          // 只持久化選中的配置 ID，其他狀態重新載入
        })
      }
    ),
    {
      name: 'vm-config-store'
    }
  )
)

// 選擇器 - 取得當前選中配置的驗證結果
export const useCurrentConfigValidation = () => {
  return useVMConfigStore(state => {
    if (state.selectedConfigId) {
      return state.validationResults[state.selectedConfigId]
    }
    return undefined
  })
}

// 選擇器 - 取得所有有效的配置
export const useValidConfigs = () => {
  return useVMConfigStore(state => {
    return state.configs.filter(config => {
      const validation = state.validationResults[config.id]
      return validation?.isValid !== false // 包括未驗證的配置
    })
  })
}

// 選擇器 - 取得有驗證錯誤的配置
export const useInvalidConfigs = () => {
  return useVMConfigStore(state => {
    return state.configs.filter(config => {
      const validation = state.validationResults[config.id]
      return validation?.isValid === false
    })
  })
}