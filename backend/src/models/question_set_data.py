"""
T028: QuestionSetData 資料類別
題組資料記憶體模型
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VerificationStep(BaseModel):
    """驗證步驟模型"""
    id: str
    description: str
    verificationScriptFile: str  # 驗證腳本檔案名稱
    expectedOutput: str  # 期望輸出
    weightage: int  # 權重分數


class QuestionData(BaseModel):
    """題目資料模型"""
    id: str  # 題目ID（字串格式）
    context: str  # 背景/情境描述
    tasks: str  # 任務描述
    notes: str  # 注意事項
    verification: List[VerificationStep]  # 驗證步驟列表


class QuestionSetMetadata(BaseModel):
    """題組元資料模型"""
    exam_type: str  # CKA, CKAD, CKS
    set_id: str
    name: str
    description: str
    time_limit: int  # 分鐘
    passing_score: int  # 及格分數百分比
    # 可選欄位
    difficulty: Optional[str] = None  # easy, medium, hard
    total_questions: Optional[int] = None
    created_date: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = []


class QuestionSetData(BaseModel):
    """題組完整資料模型"""
    set_id: str  # e.g., "cka-001"
    exam_type: str  # CKA, CKAD, CKS
    metadata: QuestionSetMetadata  # 從 metadata.json 載入
    questions: List[QuestionData]  # 從 questions.json 載入
    scripts_path: str = ""  # 腳本目錄路徑
    file_paths: Dict[str, str] = {}  # 檔案路徑記錄
    loaded_at: Optional[datetime] = None
    file_modified_at: Optional[datetime] = None

    @property
    def id(self) -> str:
        """題組唯一識別碼"""
        return f"{self.exam_type.lower()}-{self.set_id}"

    @property
    def certification_type(self) -> str:
        """認證類型（向後相容）"""
        return self.exam_type

    def get_question_by_id(self, question_id: str) -> Optional[QuestionData]:
        """根據 ID 獲取題目"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def get_question_by_index(self, index: int) -> Optional[QuestionData]:
        """根據索引獲取題目"""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    def get_total_weight(self) -> float:
        """計算總權重（所有驗證步驟的權重總和）"""
        total_weight = 0
        for question in self.questions:
            for verification in question.verification:
                total_weight += verification.weightage
        return float(total_weight)

    def validate_question_weights(self) -> bool:
        """驗證題目權重總和"""
        total_weight = self.get_total_weight()
        # 新的驗證步驟權重系統，允許總權重在合理範圍內（一般為題目數量的1.5-3倍）
        expected_min = len(self.questions) * 1.5
        expected_max = len(self.questions) * 3.5
        return expected_min <= total_weight <= expected_max


# API 回應模型

class QuestionSetSummary(BaseModel):
    """題組摘要資訊"""
    set_id: str
    exam_type: str
    name: str
    description: str
    time_limit: int
    passing_score: int
    total_questions: int  # 從實際題目數量計算


class QuestionSetListResponse(BaseModel):
    """題組列表回應"""
    question_sets: List[QuestionSetSummary]
    total_count: int
    filtered_count: int


class QuestionSetDetailResponse(BaseModel):
    """題組詳細資訊回應"""
    set_id: str
    exam_type: str
    metadata: QuestionSetMetadata
    questions: List[QuestionData]
    scripts_path: str
    total_weight: float
    loaded_at: Optional[datetime]
    file_modified_at: Optional[datetime]


class ReloadResult(BaseModel):
    """重載結果"""
    success: bool
    message: str
    loaded_count: int
    error_count: int
    loaded_sets: List[str]
    errors: List[str]
    timestamp: datetime