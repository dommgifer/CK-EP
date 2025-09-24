"""
T025: QuestionResult 模型
單題結果資料模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()


class QuestionResult(Base):
    """單題結果 SQLAlchemy 模型"""
    __tablename__ = "question_results"

    id = Column(String(36), primary_key=True)
    exam_session_id = Column(String(36), nullable=False)
    question_id = Column(String(100), nullable=False)

    # 評分結果
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)

    # 時間統計
    time_taken_seconds = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, nullable=False)

    # 詳細結果
    verification_results_json = Column(Text, nullable=False)
    feedback_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<QuestionResult(id={self.id}, score={self.score}/{self.max_score})>"


class VerificationResultItem(BaseModel):
    """驗證結果項目"""
    rule_type: str
    description: str
    passed: bool
    points_awarded: int
    max_points: int
    message: str


class QuestionResultResponse(BaseModel):
    """單題結果回應模型"""
    id: str
    question_id: str
    score: int
    max_score: int
    percentage: float
    time_taken_seconds: int
    submitted_at: datetime
    verification_results: List[VerificationResultItem]
    feedback: Optional[str] = None

    class Config:
        from_attributes = True