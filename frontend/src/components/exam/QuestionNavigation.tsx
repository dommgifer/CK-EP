/**
 * 題目導航組件
 * 包含計時器、前後按鈕、題目選擇下拉選單
 */
import React from 'react';
import type { Question } from '../../types/exam';

interface QuestionNavigationProps {
  questions: Question[];
  currentIndex: number;
  markedQuestions: Set<string>;
  timeRemaining: number;
  onQuestionChange: (index: number) => void;
}

export const QuestionNavigation: React.FC<QuestionNavigationProps> = ({
  questions,
  currentIndex,
  markedQuestions,
  timeRemaining,
  onQuestionChange,
}) => {
  const canGoPrev = currentIndex > 0;
  const canGoNext = currentIndex < questions.length - 1;

  const handlePrev = () => {
    if (canGoPrev) {
      onQuestionChange(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (canGoNext) {
      onQuestionChange(currentIndex + 1);
    }
  };

  // 格式化時間顯示
  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}:${mins.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col border-b border-gray-200 dark:border-gray-700">
      {/* 計時器進度條 */}
      <div className="bg-green-600 text-white h-10 flex items-center justify-center text-sm font-medium">
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        {formatTime(timeRemaining)} minutes
      </div>

      {/* 題目導航控制 */}
      <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-900">
        {/* 上一題按鈕 */}
        <button
          onClick={handlePrev}
          disabled={!canGoPrev}
          className={`
            p-2 rounded-lg transition-colors
            ${
              canGoPrev
                ? 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                : 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
            }
          `}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* 題目下拉選單 */}
        <select
          value={currentIndex}
          onChange={(e) => onQuestionChange(Number(e.target.value))}
          className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {questions.map((question, index) => (
            <option key={question.id} value={index}>
              {markedQuestions.has(question.id) && '● '}
              Question {parseInt(question.id)}
            </option>
          ))}
        </select>

        {/* 下一題按鈕 */}
        <button
          onClick={handleNext}
          disabled={!canGoNext}
          className={`
            p-2 rounded-lg transition-colors
            ${
              canGoNext
                ? 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                : 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
            }
          `}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
};