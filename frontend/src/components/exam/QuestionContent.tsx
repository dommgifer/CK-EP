/**
 * 題目內容顯示組件
 * 顯示 Context、Tasks、Notes
 */
import React from 'react';
import type { Question } from '../../types/exam';

interface QuestionContentProps {
  question: Question;
  isMarked: boolean;
  onToggleMark: () => void;
}

export const QuestionContent: React.FC<QuestionContentProps> = ({
  question,
  isMarked,
  onToggleMark,
}) => {
  // 檢查 context 是否需要顯示
  const shouldShowContext = question.context && question.context !== '無';

  // 檢查 notes 是否需要顯示
  const shouldShowNotes = question.notes && question.notes !== '無';

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl space-y-6">
        {/* Context 區塊 */}
        {shouldShowContext && (
          <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">
              Context:
            </div>
            <div className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
              {question.context}
            </div>
          </div>
        )}

        {/* Tasks 區塊 */}
        <div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">
            Tasks:
          </div>
          <div className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed">
            {question.tasks}
          </div>
        </div>

        {/* Notes 區塊 */}
        {shouldShowNotes && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <div className="text-sm text-yellow-800 dark:text-yellow-300 mb-2 font-medium">
              Notes:
            </div>
            <div className="text-yellow-900 dark:text-yellow-100 whitespace-pre-wrap">
              {question.notes}
            </div>
          </div>
        )}

        {/* 標記按鈕 */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onToggleMark}
            className={`
              inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
              transition-colors duration-200
              ${
                isMarked
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
              }
            `}
          >
            <svg
              className="w-4 h-4"
              fill={isMarked ? 'currentColor' : 'none'}
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
            {isMarked ? '已標記題目' : '標記題目'}
          </button>
        </div>
      </div>
    </div>
  );
};