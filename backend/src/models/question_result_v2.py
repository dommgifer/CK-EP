"""
T025: QuestionResult 模型 v2
與 ScoringService 相容的題目結果資料模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnswerValidationResult(BaseModel):
    """答題資料驗證結果"""
    is_valid: bool
    error_message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class QuestionResult(BaseModel):
    """題目評分結果"""
    question_id: str
    session_id: str
    answer_data: Dict[str, Any]
    score: int
    max_score: int
    is_correct: bool
    feedback: str
    validation_details: Dict[str, Any] = Field(default_factory=dict)
    execution_logs: List[str] = Field(default_factory=list)
    submitted_at: datetime

    @property
    def percentage(self) -> float:
        """計算得分百分比"""
        if self.max_score == 0:
            return 0.0
        return round((self.score / self.max_score) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "question_id": self.question_id,
            "session_id": self.session_id,
            "answer_data": self.answer_data,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "is_correct": self.is_correct,
            "feedback": self.feedback,
            "validation_details": self.validation_details,
            "execution_logs": self.execution_logs,
            "submitted_at": self.submitted_at.isoformat()
        }


class BatchScoreResult(BaseModel):
    """批次評分結果"""
    session_id: str
    question_results: List[QuestionResult]
    total_score: int
    max_possible_score: int
    percentage: float
    correct_questions: int
    total_questions: int
    accuracy: float
    completed_at: datetime

    @classmethod
    def from_questions(cls, session_id: str, question_results: List[QuestionResult]):
        """從題目結果列表建立批次結果"""
        total_score = sum(result.score for result in question_results)
        max_possible_score = sum(result.max_score for result in question_results)
        correct_questions = sum(1 for result in question_results if result.is_correct)
        total_questions = len(question_results)

        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        accuracy = (correct_questions / total_questions * 100) if total_questions > 0 else 0

        return cls(
            session_id=session_id,
            question_results=question_results,
            total_score=total_score,
            max_possible_score=max_possible_score,
            percentage=round(percentage, 2),
            correct_questions=correct_questions,
            total_questions=total_questions,
            accuracy=round(accuracy, 2),
            completed_at=datetime.utcnow()
        )