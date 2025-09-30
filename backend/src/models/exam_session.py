"""
T021: ExamSession 模型
考試會話資料模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SqlEnum
from pydantic import BaseModel
from ..database.connection import Base


class ExamSessionStatus(str, Enum):
    """考試會話狀態"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExamSession(Base):
    """考試會話 SQLAlchemy 模型"""
    __tablename__ = "exam_sessions"

    id = Column(String(36), primary_key=True)
    question_set_id = Column(String(100), nullable=False)
    vm_config_id = Column(String(100), nullable=False)
    status = Column(SqlEnum(ExamSessionStatus), default=ExamSessionStatus.CREATED)
    current_question_index = Column(Integer, default=0)

    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    paused_time = Column(DateTime, nullable=True)
    resumed_time = Column(DateTime, nullable=True)

    # 考試配置
    duration_minutes = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)

    # 進度和結果
    answers_json = Column(Text, default="{}")  # JSON 格式的答題記錄
    scores_json = Column(Text, default="{}")   # JSON 格式的評分記錄
    final_score = Column(Integer, nullable=True)
    max_possible_score = Column(Integer, nullable=True)

    # 環境相關
    environment_status = Column(String(50), default="not_provisioned")
    vnc_container_id = Column(String(100), nullable=True)
    bastion_container_id = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<ExamSession(id={self.id}, status={self.status})>"


# Pydantic 模型用於 API 序列化

class ExamSessionBase(BaseModel):
    """考試會話基礎模型"""
    question_set_id: str
    vm_config_id: str
    duration_minutes: int = 120


class ExamSessionCreate(ExamSessionBase):
    """建立考試會話請求模型"""
    pass


class ExamSessionUpdate(BaseModel):
    """更新考試會話請求模型"""
    current_question_index: Optional[int] = None
    status: Optional[ExamSessionStatus] = None


class ExamSessionResponse(ExamSessionBase):
    """考試會話回應模型"""
    id: str
    status: ExamSessionStatus
    current_question_index: int
    total_questions: int
    created_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_score: Optional[int] = None
    max_possible_score: Optional[int] = None
    environment_status: str

    class Config:
        from_attributes = True


class ExamSessionDetailed(ExamSessionResponse):
    """考試會話詳細資訊模型"""
    current_question: Optional[dict] = None
    progress: dict
    environment: dict
    answers: dict
    scores: dict

    @classmethod
    def from_session(cls, session: ExamSession, **kwargs):
        """從 SQLAlchemy 模型建立詳細回應"""
        import json

        # 解析 JSON 欄位
        answers = json.loads(session.answers_json) if session.answers_json else {}
        scores = json.loads(session.scores_json) if session.scores_json else {}

        # 計算進度
        progress = {
            "current_question": session.current_question_index + 1,
            "total_questions": session.total_questions,
            "percentage": round((session.current_question_index / session.total_questions) * 100, 1) if session.total_questions > 0 else 0,
            "answered_questions": len(answers),
            "time_elapsed_minutes": kwargs.get("time_elapsed_minutes", 0)
        }

        return cls(
            **session.__dict__,
            progress=progress,
            environment=kwargs.get("environment", {}),
            answers=answers,
            scores=scores,
            current_question=kwargs.get("current_question")
        )