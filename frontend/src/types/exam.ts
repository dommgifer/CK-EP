/**
 * 考試相關的型別定義
 */

export interface Question {
  id: string;
  context: string;
  tasks: string;
  notes: string;
  verification?: Array<{
    id: string;
    description: string;
    verificationScriptFile: string;
    expectedOutput: string;
    weightage: number;
  }>;
}

export interface QuestionSet {
  exam_type: string;
  set_id: string;
  name: string;
  description: string;
  time_limit: number;
  passing_score: number;
}

export interface ExamSession {
  id: string;
  question_set_id: string;
  status: 'pending' | 'deploying' | 'ready' | 'in_progress' | 'completed' | 'failed';
  time_remaining: number;
  started_at?: string;
  ended_at?: string;
  score?: number;
}

export interface ExamResult {
  session_id: string;
  total_score: number;
  passing_score: number;
  passed: boolean;
  question_results: QuestionResult[];
}

export interface QuestionResult {
  question_id: string;
  score: number;
  max_score: number;
  verification_results: VerificationResult[];
}

export interface VerificationResult {
  verification_id: string;
  description: string;
  passed: boolean;
  score: number;
  weightage: number;
}