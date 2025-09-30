import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'automatic',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // Docker 環境配置
    host: '0.0.0.0',  // 允許容器外部訪問
    port: 5173,       // Vite 標準 port
    strictPort: true, // port 被佔用時直接失敗

    // HMR 配置 (透過 nginx 代理時必須)
    hmr: {
      clientPort: 80,     // 瀏覽器透過 nginx (port 80) 連線
      protocol: 'ws',
    },

    // Docker 環境檔案監聽
    watch: {
      usePolling: true,   // Docker volume 需要 polling
      interval: 1000,     // 每秒檢查一次
    },

    // 開發模式不需要代理 (nginx 處理)
    proxy: undefined,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // 🚀 關鍵修改：使用 ESBuild 而非 Terser (快 10-100 倍)
    minify: 'esbuild',
    // 🚀 關鍵修改：關閉壓縮大小報告 (節省時間)
    reportCompressedSize: false,
    rollupOptions: {
      output: {
        // 🚀 關鍵修改：簡化檔案命名 (減少處理開銷)
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
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
      '@radix-ui/react-dialog',
      '@radix-ui/react-select',
      '@radix-ui/react-label',
      '@radix-ui/react-slot',
      '@radix-ui/react-radio-group',
    ],
  },
})