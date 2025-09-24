import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { splitVendorChunkPlugin } from 'vite'

export default defineConfig({
  plugins: [
    react({
      // 最佳化 React 重新整理
      fastRefresh: true,
      // 生產環境最佳化
      jsxRuntime: 'automatic',
    }),
    // 自動分離第三方程式庫
    splitVendorChunkPlugin(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // 啟用 sourcemap 用於除錯
    sourcemap: false,
    // 最小化設定
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除 console.log
        drop_console: true,
        drop_debugger: true,
      },
    },
    // 設定資產大小警告限制
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // 最佳化程式碼分割
        manualChunks: (id) => {
          // React 相關
          if (id.includes('react') || id.includes('react-dom')) {
            return 'react-vendor'
          }

          // 路由相關
          if (id.includes('react-router')) {
            return 'router'
          }

          // React Query
          if (id.includes('@tanstack/react-query')) {
            return 'react-query'
          }

          // UI 程式庫
          if (id.includes('lucide-react')) {
            return 'icons'
          }

          // 測試程式庫 (不應該包含在生產版本中)
          if (id.includes('test') || id.includes('@testing-library')) {
            return 'test'
          }

          // 工具程式庫
          if (id.includes('lodash') || id.includes('date-fns') || id.includes('axios')) {
            return 'utils'
          }

          // 其他第三方程式庫
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
        // 檔案命名策略
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          if (facadeModuleId) {
            const fileName = path.basename(facadeModuleId, path.extname(facadeModuleId))
            return `js/${fileName}-[hash].js`
          }
          return 'js/[name]-[hash].js'
        },
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          let extType = info[info.length - 1]

          // 根據檔案類型分目錄
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'media'
          } else if (/\.(png|jpe?g|gif|svg|webp)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'images'
          } else if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name)) {
            extType = 'fonts'
          }

          return `${extType}/[name]-[hash][extname]`
        },
      },
      // 外部依賴 (CDN)
      external: [],
    },
    // 啟用 CSS 程式碼分離
    cssCodeSplit: true,
    // 報告壓縮後大小
    reportCompressedSize: true,
    // 啟用 rollup 監視選項
    watch: {
      buildDelay: 100,
    },
  },
  // CSS 最佳化
  css: {
    devSourcemap: true,
    preprocessorOptions: {
      css: {
        charset: false,
      },
    },
  },
  // 最佳化依賴項
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'lucide-react',
    ],
    exclude: [
      '@testing-library/react',
      '@testing-library/jest-dom',
      'vitest',
    ],
  },
  // 定義全域常數
  define: {
    __DEV__: JSON.stringify(!process.env.NODE_ENV || process.env.NODE_ENV === 'development'),
    __PROD__: JSON.stringify(process.env.NODE_ENV === 'production'),
    __VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
  },
})