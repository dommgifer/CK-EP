/**
 * 主要應用程式組件
 * 簡化版本，移除重複的 Router 和 QueryClient 設定
 */
import React from 'react'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ExamPage from './pages/ExamPage'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/exam/:sessionId" element={<ExamPage />} />
      </Routes>
    </div>
  )
}

export default App