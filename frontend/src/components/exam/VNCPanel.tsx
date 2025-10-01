/**
 * VNC 面板組件（右側）
 * 嵌入 noVNC iframe
 */
import React, { useState, useEffect } from 'react';

interface VNCPanelProps {
  vncUrl: string;
  sessionId: string;
  timeRemaining: number;
}

export const VNCPanel: React.FC<VNCPanelProps> = ({ vncUrl, sessionId, timeRemaining }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (vncUrl) {
      setIsLoading(false);
      // 模擬連線檢查
      setTimeout(() => setIsConnected(true), 1000);
    }
  }, [vncUrl]);

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  if (!vncUrl) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900">
        <div className="text-center text-gray-400">
          <svg
            className="w-16 h-16 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <p>VNC 環境準備中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* noVNC iframe */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
            <div className="text-center text-gray-400">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p>載入 VNC 桌面環境...</p>
            </div>
          </div>
        )}
        <iframe
          src={vncUrl}
          className="w-full h-full border-0"
          title="noVNC Desktop"
          allow="clipboard-read; clipboard-write"
          onLoad={() => setIsLoading(false)}
        />
      </div>

      {/* 狀態列 */}
      <div className="bg-gray-800 px-4 py-3 border-t border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            {/* 連線狀態 */}
            <div className="flex items-center gap-2">
              <span
                className={`
                  inline-block w-2 h-2 rounded-full
                  ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}
                `}
              ></span>
              <span
                className={`
                  ${isConnected ? 'text-green-400' : 'text-gray-400'}
                `}
              >
                {isConnected ? '連線正常' : '連線中...'}
              </span>
            </div>

            {/* 叢集名稱 */}
            <span className="text-gray-400">
              Cluster: <span className="text-gray-300">exam-cluster</span>
            </span>
          </div>

          {/* 剩餘時間 */}
          <div className="text-gray-400">
            Session: <span className="text-gray-300">{formatTime(timeRemaining)} remaining</span>
          </div>
        </div>
      </div>
    </div>
  );
};