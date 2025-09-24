/**
 * T071: 主要路由設定
 * Kubernetes 考試模擬器的主要應用程式入口和路由配置
 */
import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastContainer } from 'react-toastify'

// 頁面組件
import HomePage from './pages/HomePage'
import VMConfigPage from './pages/VMConfigPage'
import QuestionSetPage from './pages/QuestionSetPage'
import CreateExamPage from './pages/CreateExamPage'
import ExamPage from './pages/ExamPage'
import ResultsPage from './pages/ResultsPage'

// 佈局組件
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'

// 樣式
import 'react-toastify/dist/ReactToastify.css'
import './index.css'

// 建立 React Query 客戶端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分鐘
      cacheTime: 10 * 60 * 1000, // 10 分鐘
      refetchOnWindowFocus: false,
      retry: 1
    },
    mutations: {
      retry: false
    }
  }
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <ErrorBoundary>
          <div className="min-h-screen bg-gray-50">
            <Layout>
              <Routes>
                {/* 首頁 */}
                <Route path="/" element={<HomePage />} />

                {/* VM 配置管理 */}
                <Route path="/vm-configs" element={<VMConfigPage />} />

                {/* 題組瀏覽 */}
                <Route path="/question-sets" element={<QuestionSetPage />} />

                {/* 考試會話建立 */}
                <Route path="/create-exam" element={<CreateExamPage />} />

                {/* 考試進行頁面 */}
                <Route path="/exam/:sessionId" element={<ExamPage />} />

                {/* 考試結果 */}
                <Route path="/results/:sessionId" element={<ResultsPage />} />

                {/* 404 重導向 */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>

            {/* 全域通知 */}
            <ToastContainer
              position="top-right"
              autoClose={5000}
              hideProgressBar={false}
              newestOnTop={false}
              closeOnClick
              rtl={false}
              pauseOnFocusLoss
              draggable
              pauseOnHover
              theme="light"
            />
          </div>
        </ErrorBoundary>
      </Router>
    </QueryClientProvider>
  )
}

export default App