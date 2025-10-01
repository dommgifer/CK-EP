/**
 * T075: 考試進行頁面
 * 主要的考試界面，包含題目、VNC 檢視器和導航
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ExamHeader } from '../components/exam/ExamHeader';
import { QuestionPanel } from '../components/exam/QuestionPanel';
import { VNCPanel } from '../components/exam/VNCPanel';
import { apiClient } from '../services/api';
import type { Question, ExamSession } from '../types/exam';

export default function ExamPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [markedQuestions, setMarkedQuestions] = useState<Set<string>>(new Set());
  const [timeRemaining, setTimeRemaining] = useState(120);
  const [vncUrl, setVncUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadExamSession = async () => {
      if (!sessionId) {
        navigate('/');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const sessionResponse = await apiClient.get<ExamSession>(`/exam-sessions/${sessionId}`);
        const session = sessionResponse.data;

        // 允許的狀態：created (剛建立), ready (準備就緒), in_progress (進行中)
        const allowedStatuses = ['created', 'ready', 'in_progress'];
        if (!allowedStatuses.includes(session.status)) {
          navigate('/');
          return;
        }

        // 使用 duration_minutes 作為初始剩餘時間
        const remainingTime = (session as any).duration_minutes || session.time_remaining || 120;
        setTimeRemaining(remainingTime);

        const questionSetResponse = await apiClient.get(`/question-sets/${session.question_set_id}`);
        const questionSetData = questionSetResponse.data;

        if (questionSetData.questions && Array.isArray(questionSetData.questions)) {
          setQuestions(questionSetData.questions);
        }

        // 嘗試載入 VNC URL，如果環境尚未部署則跳過
        try {
          const vncResponse = await apiClient.get<{ url: string }>(`/exam-sessions/${sessionId}/vnc`);
          setVncUrl(vncResponse.data.url);
        } catch (vncError) {
          console.warn('VNC URL not available yet:', vncError);
          // 環境尚未部署完成，VNC URL 稍後才會可用
        }

      } catch (err) {
        console.error('Failed to load exam session:', err);
        setError('載入考試會話失敗，請重新整理頁面或聯絡管理員');
      } finally {
        setLoading(false);
      }
    };

    loadExamSession();
  }, [sessionId, navigate]);

  useEffect(() => {
    if (timeRemaining <= 0 || loading) return;

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          handleEndExam();
          return 0;
        }
        return prev - 1;
      });
    }, 60000);

    return () => clearInterval(timer);
  }, [timeRemaining, loading]);

  const handleQuestionChange = (index: number) => {
    setCurrentQuestionIndex(index);
  };

  const handleToggleMark = (questionId: string) => {
    setMarkedQuestions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const handleEndExam = async () => {
    if (!sessionId) return;

    try {
      await apiClient.post(`/exam-sessions/${sessionId}/end`);
      navigate(`/exam/${sessionId}/results`);
    } catch (err) {
      console.error('Failed to end exam:', err);
      alert('結束考試失敗，請稍後再試');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <div className="text-white">載入考試中...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center text-red-400">
          <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            重新整理
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      <ExamHeader sessionId={sessionId || ''} onEndExam={handleEndExam} />
      <div className="flex flex-1 overflow-hidden">
        <div className="w-[40%] border-r border-gray-700 overflow-hidden">
          <QuestionPanel
            questions={questions}
            currentIndex={currentQuestionIndex}
            markedQuestions={markedQuestions}
            timeRemaining={timeRemaining}
            onQuestionChange={handleQuestionChange}
            onToggleMark={handleToggleMark}
          />
        </div>
        <div className="flex-1 overflow-hidden">
          <VNCPanel vncUrl={vncUrl} sessionId={sessionId || ''} timeRemaining={timeRemaining} />
        </div>
      </div>
    </div>
  );
}
