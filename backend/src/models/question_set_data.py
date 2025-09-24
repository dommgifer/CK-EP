"""
T028: QuestionSetData 資料類別
題組資料記憶體模型
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QuestionData(BaseModel):
    """題目資料模型"""
    id: int
    content: str  # Markdown 格式的題目內容
    weight: float  # 題目權重
    kubernetes_objects: List[str]  # 涉及的 K8s 物件
    hints: List[str] = []
    verification_scripts: List[str] = []  # 腳本檔案路徑
    preparation_scripts: List[str] = []  # 準備腳本路徑


class TopicInfo(BaseModel):
    """主題資訊"""
    name: str
    weight: float
    questions: int
    description: str


class DomainInfo(BaseModel):
    """考試領域資訊"""
    name: str
    weight: float
    description: str


class QuestionSetMetadata(BaseModel):
    """題組元資料模型"""
    exam_type: str  # CKA, CKAD, CKS
    set_id: str
    name: str
    description: str
    difficulty: str  # easy, medium, hard
    time_limit: int  # 分鐘
    total_questions: int
    passing_score: int  # 及格分數百分比
    created_date: str
    version: str
    tags: List[str] = []
    topics: List[TopicInfo] = []
    exam_domains: List[DomainInfo] = []


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

    def get_question_by_id(self, question_id: int) -> Optional[QuestionData]:
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
        """計算總權重"""
        return sum(q.weight for q in self.questions)

    def validate_question_weights(self) -> bool:
        """驗證題目權重總和"""
        total_weight = self.get_total_weight()
        # 允許權重總和在 95-105 之間（考慮浮點數精度）
        return 95.0 <= total_weight <= 105.0


# API 回應模型

class QuestionSetSummary(BaseModel):
    """題組摘要資訊"""
    set_id: str
    exam_type: str
    name: str
    description: str
    difficulty: str
    time_limit: int
    total_questions: int
    passing_score: int
    version: str
    tags: List[str]


class QuestionSetListResponse(BaseModel):
    """題組列表回應"""
    question_sets: List[QuestionSetSummary]
    total_count: int
    filtered_count: int
    exam_types: List[str]
    difficulties: List[str]


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