/**
 * T075: 考試進行頁面
 * 主要的考試界面，包含題目、VNC 檢視器和導航
 */
import React from 'react'
import { useParams } from 'react-router-dom'

export default function ExamPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <div className="h-screen flex flex-col">
      {/* 考試工具欄 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">考試進行中</h1>
            <p className="text-sm text-gray-500">會話 ID: {sessionId}</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              剩餘時間: <span className="font-mono font-semibold">02:30:45</span>
            </div>
            <div className="text-sm text-gray-600">
              進度: <span className="font-semibold">3/15</span>
            </div>
          </div>
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="flex-1 flex">
        {/* 左側: 題目和導航 */}
        <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
          {/* 題目內容 */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="mb-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                題目 3
              </span>
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                權重: 5 分
              </span>
            </div>

            <div className="prose prose-sm max-w-none">
              <h3>建立 Pod 和 Service</h3>
              <p>
                在 <code>default</code> namespace 中建立一個名為 <code>web-app</code> 的 Pod，
                使用 <code>nginx:latest</code> 映像，並暴露在 port 80。
              </p>
              <p>
                然後建立一個名為 <code>web-service</code> 的 Service，
                將流量導向該 Pod。
              </p>

              <h4>要求：</h4>
              <ul>
                <li>Pod 名稱: web-app</li>
                <li>Container 映像: nginx:latest</li>
                <li>Service 名稱: web-service</li>
                <li>Service 類型: ClusterIP</li>
              </ul>
            </div>
          </div>

          {/* 題目導航 */}
          <div className="border-t border-gray-200 p-4">
            <div className="grid grid-cols-5 gap-2">
              {Array.from({ length: 15 }, (_, i) => (
                <button
                  key={i}
                  className={`w-8 h-8 text-xs rounded ${
                    i === 2
                      ? 'bg-blue-600 text-white'
                      : i < 2
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
            <div className="mt-4 flex justify-between">
              <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                上一題
              </button>
              <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                下一題
              </button>
            </div>
          </div>
        </div>

        {/* 右側: VNC 檢視器 */}
        <div className="flex-1 bg-black">
          <div className="h-full flex items-center justify-center text-white">
            <div className="text-center">
              <div className="mb-4">
                <svg className="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-300 mb-2">VNC 桌面環境</h3>
              <p className="text-sm text-gray-400 mb-4">正在載入遠端桌面...</p>
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                連線到桌面
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 底部操作欄 */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button className="px-4 py-2 text-sm bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">
              暫停考試
            </button>
            <button className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
              提交答案
            </button>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">自動儲存已啟用</span>
            <button className="px-4 py-2 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200">
              結束考試
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}