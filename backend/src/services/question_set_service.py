"""
T032: QuestionSetService 題組管理服務
處理題組的查詢、篩選和管理操作
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from .question_set_file_manager import QuestionSetFileManager
from ..models.question_set_data import (
    QuestionSetData,
    QuestionSetSummary,
    QuestionSetListResponse,
    QuestionSetDetailResponse,
    ReloadResult
)


class QuestionSetService:
    """題組管理服務"""

    def __init__(self, file_manager: QuestionSetFileManager):
        self.file_manager = file_manager

    async def list_question_sets(
        self,
        exam_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> QuestionSetListResponse:
        """取得題組列表，支援篩選"""
        question_sets = self.file_manager.list_question_sets(
            certification_type=exam_type,
            difficulty=difficulty
        )

        # 額外的標籤篩選
        if tags:
            filtered_sets = []
            for qs in question_sets:
                qs_tags = [tag.lower() for tag in qs.metadata.tags]
                if any(tag.lower() in qs_tags for tag in tags):
                    filtered_sets.append(qs)
            question_sets = filtered_sets

        # 轉換為摘要格式
        summaries = [
            QuestionSetSummary(
                set_id=qs.set_id,
                exam_type=qs.exam_type,
                name=qs.metadata.name,
                description=qs.metadata.description,
                difficulty=qs.metadata.difficulty,
                time_limit=qs.metadata.time_limit,
                total_questions=qs.metadata.total_questions,
                passing_score=qs.metadata.passing_score,
                version=qs.metadata.version,
                tags=qs.metadata.tags
            )
            for qs in question_sets
        ]

        # 收集統計資訊
        all_sets = self.file_manager.get_all_question_sets()
        exam_types = list(set(qs.exam_type for qs in all_sets.values()))
        difficulties = list(set(qs.metadata.difficulty for qs in all_sets.values()))

        return QuestionSetListResponse(
            question_sets=summaries,
            total_count=len(all_sets),
            filtered_count=len(summaries),
            exam_types=exam_types,
            difficulties=difficulties
        )

    async def get_question_set(self, set_id: str) -> Optional[QuestionSetDetailResponse]:
        """取得特定題組的詳細資訊"""
        question_set = self.file_manager.get_question_set(set_id)
        if not question_set:
            return None

        return QuestionSetDetailResponse(
            set_id=question_set.set_id,
            exam_type=question_set.exam_type,
            metadata=question_set.metadata,
            questions=question_set.questions,
            scripts_path=question_set.scripts_path,
            total_weight=question_set.get_total_weight(),
            loaded_at=question_set.loaded_at,
            file_modified_at=question_set.file_modified_at
        )

    async def reload_question_sets(self) -> ReloadResult:
        """重新載入所有題組檔案"""
        try:
            results = await self.file_manager.reload_question_sets()

            return ReloadResult(
                success=True,
                message="題組重載完成",
                loaded_count=len(results["loaded"]),
                error_count=len(results["errors"]),
                loaded_sets=results["loaded"],
                errors=results["errors"],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            return ReloadResult(
                success=False,
                message=f"題組重載失敗: {str(e)}",
                loaded_count=0,
                error_count=1,
                loaded_sets=[],
                errors=[str(e)],
                timestamp=datetime.utcnow()
            )

    def get_statistics(self) -> Dict[str, Any]:
        """取得題組統計資訊"""
        return self.file_manager.get_stats()

    async def validate_question_set(self, set_id: str) -> Dict[str, Any]:
        """驗證題組資料完整性"""
        question_set = self.file_manager.get_question_set(set_id)
        if not question_set:
            return {
                "valid": False,
                "errors": [f"題組 '{set_id}' 不存在"]
            }

        errors = []
        warnings = []

        # 驗證題目權重
        if not question_set.validate_question_weights():
            total_weight = question_set.get_total_weight()
            errors.append(f"題目權重總和異常: {total_weight} (應該接近 100)")

        # 驗證題目數量
        if len(question_set.questions) != question_set.metadata.total_questions:
            warnings.append(
                f"題目數量不一致: 實際 {len(question_set.questions)}, "
                f"metadata 記錄 {question_set.metadata.total_questions}"
            )

        # 驗證腳本檔案
        if question_set.scripts_path:
            import os
            for question in question_set.questions:
                for script in question.verification_scripts:
                    script_path = os.path.join(question_set.scripts_path, "verify", script)
                    if not os.path.exists(script_path):
                        warnings.append(f"驗證腳本不存在: {script}")

                for script in question.preparation_scripts:
                    script_path = os.path.join(question_set.scripts_path, "prepare", script)
                    if not os.path.exists(script_path):
                        warnings.append(f"準備腳本不存在: {script}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "question_count": len(question_set.questions),
            "total_weight": question_set.get_total_weight(),
            "validation_time": datetime.utcnow().isoformat()
        }