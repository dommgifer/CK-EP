"""
T024: ExamResult 模型
考試結果資料模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()


class ExamResult(Base):
    """考試結果 SQLAlchemy 模型"""
    __tablename__ = "exam_results"

    id = Column(String(36), primary_key=True)
    exam_session_id = Column(String(36), nullable=False)
    question_set_id = Column(String(100), nullable=False)
    certification_type = Column(String(20), nullable=False)

    # 分數資訊
    final_score = Column(Integer, nullable=False)
    max_possible_score = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    passed = Column(String(10), nullable=False)  # "true" or "false"

    # 時間資訊
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    time_used_minutes = Column(Integer, nullable=False)

    # 詳細結果 JSON
    question_results_json = Column(Text, nullable=False)  # 各題結果
    summary_json = Column(Text, nullable=False)  # 總結資訊

    # 元資料
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ExamResult(id={self.id}, score={self.final_score}/{self.max_possible_score})>"


# Pydantic 模型

class QuestionResultSummary(BaseModel):
    """題目結果摘要"""
    question_id: str
    title: str
    score: int
    max_score: int
    percentage: float
    time_taken_seconds: int
    answered: bool


class ExamResultSummary(BaseModel):
    """考試結果摘要"""
    total_questions: int
    answered_questions: int
    unanswered_questions: int
    total_score: int
    max_possible_score: int
    percentage: float
    passed: bool
    time_used_minutes: int
    time_limit_minutes: int
    efficiency_rating: str  # "excellent", "good", "fair", "poor"


class ExamResultBase(BaseModel):
    """考試結果基礎模型"""
    exam_session_id: str
    question_set_id: str
    certification_type: str
    final_score: int
    max_possible_score: int
    percentage: float
    passed: bool
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    time_used_minutes: int


class ExamResultResponse(ExamResultBase):
    """考試結果回應模型"""
    id: str
    created_at: datetime
    summary: ExamResultSummary

    class Config:
        from_attributes = True


class ExamResultDetailed(ExamResultResponse):
    """考試結果詳細資訊"""
    question_results: List[QuestionResultSummary]
    performance_analysis: Dict[str, Any]
    recommendations: List[str]

    @classmethod
    def from_db_model(cls, db_model: ExamResult):
        """從資料庫模型建立詳細結果"""
        import json

        # 解析 JSON 資料
        question_results_data = json.loads(db_model.question_results_json)
        summary_data = json.loads(db_model.summary_json)

        # 建立題目結果列表
        question_results = [
            QuestionResultSummary(**result) for result in question_results_data
        ]

        # 建立摘要
        summary = ExamResultSummary(**summary_data)

        # 效能分析
        performance_analysis = cls._analyze_performance(
            db_model.percentage,
            db_model.time_used_minutes,
            db_model.duration_minutes,
            question_results
        )

        # 建議
        recommendations = cls._generate_recommendations(
            db_model.certification_type,
            db_model.percentage,
            question_results
        )

        return cls(
            id=db_model.id,
            exam_session_id=db_model.exam_session_id,
            question_set_id=db_model.question_set_id,
            certification_type=db_model.certification_type,
            final_score=db_model.final_score,
            max_possible_score=db_model.max_possible_score,
            percentage=db_model.percentage,
            passed=db_model.passed == "true",
            start_time=db_model.start_time,
            end_time=db_model.end_time,
            duration_minutes=db_model.duration_minutes,
            time_used_minutes=db_model.time_used_minutes,
            created_at=db_model.created_at,
            summary=summary,
            question_results=question_results,
            performance_analysis=performance_analysis,
            recommendations=recommendations
        )

    @staticmethod
    def _analyze_performance(percentage: float, time_used: int, time_limit: int,
                           question_results: List[QuestionResultSummary]) -> Dict[str, Any]:
        """分析考試表現"""
        time_efficiency = (time_limit - time_used) / time_limit if time_limit > 0 else 0

        # 各類題目表現
        topic_performance = {}
        for result in question_results:
            # 這裡可以根據題目 ID 或標籤分析不同主題的表現
            pass

        return {
            "overall_score": percentage,
            "time_efficiency": round(time_efficiency * 100, 1),
            "strengths": [],  # TODO: 根據高分題目分析
            "weaknesses": [],  # TODO: 根據低分題目分析
            "topic_performance": topic_performance
        }

    @staticmethod
    def _generate_recommendations(cert_type: str, percentage: float,
                                question_results: List[QuestionResultSummary]) -> List[str]:
        """生成學習建議"""
        recommendations = []

        if percentage < 66:
            recommendations.append(f"建議加強 {cert_type} 相關知識的學習")
            recommendations.append("重點練習低分題目涉及的技術領域")

        if percentage >= 66:
            recommendations.append("恭喜通過考試！")
            if percentage < 80:
                recommendations.append("可以進一步鞏固知識以達到更高水準")

        # TODO: 根據具體錯誤模式提供更詳細建議

        return recommendations