"""
T026: VerificationResult 模型
驗證結果資料模型
"""
from pydantic import BaseModel
from typing import Any, Dict


class VerificationResult(BaseModel):
    """驗證結果模型"""
    rule_type: str
    passed: bool
    points_awarded: int
    max_points: int
    message: str
    details: Dict[str, Any] = {}

    class Config:
        from_attributes = True