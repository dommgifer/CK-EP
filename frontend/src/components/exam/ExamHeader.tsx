/**
 * 考試頂部導航列
 * 包含 View Results、Exam Interface、Exam Controls、Exam Information 四個下拉選單
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ExamHeaderProps {
  sessionId: string;
  onEndExam: () => void;
}

export const ExamHeader: React.FC<ExamHeaderProps> = ({ sessionId, onEndExam }) => {
  const navigate = useNavigate();
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const toggleDropdown = (name: string) => {
    setOpenDropdown(openDropdown === name ? null : name);
  };

  const closeAllDropdowns = () => {
    setOpenDropdown(null);
  };

  const handleViewResults = () => {
    navigate(`/exam/${sessionId}/results`);
    closeAllDropdowns();
  };

  const handleEndExam = () => {
    if (confirm('確定要結束考試嗎？結束後將無法繼續答題。')) {
      onEndExam();
      closeAllDropdowns();
    }
  };

  return (
    <header className="bg-gray-900 text-white border-b border-gray-700">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Logo/Title */}
        <div className="text-lg font-bold">DW-CK Simulator</div>

        {/* 導航選單 */}
        <nav className="flex items-center gap-2">
          {/* View Results */}
          <button
            onClick={handleViewResults}
            className="px-4 py-2 text-sm hover:bg-gray-800 rounded transition-colors"
          >
            View Results
          </button>

          {/* Exam Interface ▼ */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('interface')}
              className="px-4 py-2 text-sm hover:bg-gray-800 rounded transition-colors flex items-center gap-1"
            >
              Exam Interface
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            {openDropdown === 'interface' && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-2 z-50">
                <button
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={closeAllDropdowns}
                >
                  全螢幕模式
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={closeAllDropdowns}
                >
                  調整面板大小
                </button>
              </div>
            )}
          </div>

          {/* Exam Controls ▼ */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('controls')}
              className="px-4 py-2 text-sm hover:bg-gray-800 rounded transition-colors flex items-center gap-1"
            >
              Exam Controls
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            {openDropdown === 'controls' && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-2 z-50">
                <button
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={closeAllDropdowns}
                >
                  暫停考試
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={handleEndExam}
                >
                  結束考試
                </button>
              </div>
            )}
          </div>

          {/* Exam Information ▼ */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('information')}
              className="px-4 py-2 text-sm hover:bg-gray-800 rounded transition-colors flex items-center gap-1"
            >
              Exam Information
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            {openDropdown === 'information' && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 z-50">
                <div className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
                  <div>
                    <span className="font-medium">會話 ID:</span> {sessionId}
                  </div>
                  <div>
                    <span className="font-medium">考試類型:</span> CKS
                  </div>
                  <div>
                    <span className="font-medium">通過分數:</span> 66
                  </div>
                </div>
              </div>
            )}
          </div>
        </nav>
      </div>

      {/* 點擊外部關閉下拉選單 */}
      {openDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={closeAllDropdowns}
        />
      )}
    </header>
  );
};