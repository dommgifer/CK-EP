/**
 * 題目面板組件（左側）
 * 整合題目導航和內容顯示
 */
import React from 'react';
import { QuestionNavigation } from './QuestionNavigation';
import { QuestionContent } from './QuestionContent';
import type { Question } from '../../types/exam';

interface QuestionPanelProps {
  questions: Question[];
  currentIndex: number;
  markedQuestions: Set<string>;
  timeRemaining: number;
  onQuestionChange: (index: number) => void;
  onToggleMark: (questionId: string) => void;
}

export const QuestionPanel: React.FC<QuestionPanelProps> = ({
  questions,
  currentIndex,
  markedQuestions,
  timeRemaining,
  onQuestionChange,
  onToggleMark,
}) => {
  const currentQuestion = questions[currentIndex];

  if (!currentQuestion) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500 dark:text-gray-400">沒有可顯示的題目</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* 題目導航 */}
      <QuestionNavigation
        questions={questions}
        currentIndex={currentIndex}
        markedQuestions={markedQuestions}
        timeRemaining={timeRemaining}
        onQuestionChange={onQuestionChange}
      />

      {/* 題目內容 */}
      <QuestionContent
        question={currentQuestion}
        isMarked={markedQuestions.has(currentQuestion.id)}
        onToggleMark={() => onToggleMark(currentQuestion.id)}
      />
    </div>
  );
};