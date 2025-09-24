"""
T042-T044: 題組管理 API 端點
處理題組的查詢、詳細資訊和重載操作
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...services.question_set_file_manager import QuestionSetFileManager
from ...services.question_set_service import QuestionSetService
from ...models.question_set_data import (
    QuestionSetListResponse,
    QuestionSetDetailResponse,
    ReloadResult
)

router = APIRouter()

# 全域檔案管理器實例（將在應用啟動時初始化）
_file_manager: Optional[QuestionSetFileManager] = None


def get_file_manager() -> QuestionSetFileManager:
    """取得檔案管理器實例"""
    if _file_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="題組檔案管理器尚未初始化"
        )
    return _file_manager


def get_question_set_service(
    file_manager: QuestionSetFileManager = Depends(get_file_manager)
) -> QuestionSetService:
    """取得題組服務依賴注入"""
    return QuestionSetService(file_manager)


@router.get("", response_model=QuestionSetListResponse)
async def list_question_sets(
    exam_type: Optional[str] = Query(None, description="認證類型篩選 (CKA/CKAD/CKS)"),
    difficulty: Optional[str] = Query(None, description="難度篩選 (easy/medium/hard)"),
    tags: Optional[str] = Query(None, description="標籤篩選，多個標籤用逗號分隔"),
    service: QuestionSetService = Depends(get_question_set_service)
):
    """
    T042: GET /api/v1/question-sets 端點
    取得所有題組列表，支援篩選
    """
    try:
        # 解析標籤參數
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        response = await service.list_question_sets(
            exam_type=exam_type,
            difficulty=difficulty,
            tags=tag_list
        )
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得題組列表失敗: {str(e)}"
        )


@router.get("/{set_id}", response_model=QuestionSetDetailResponse)
async def get_question_set(
    set_id: str,
    service: QuestionSetService = Depends(get_question_set_service)
):
    """
    T043: GET /api/v1/question-sets/{set_id} 端點
    取得指定題組的詳細資訊
    """
    try:
        question_set = await service.get_question_set(set_id)
        if not question_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"題組 '{set_id}' 不存在"
            )
        return question_set

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得題組詳細資訊失敗: {str(e)}"
        )


@router.post("/reload", response_model=ReloadResult)
async def reload_question_sets(
    service: QuestionSetService = Depends(get_question_set_service)
):
    """
    T044: POST /api/v1/question-sets/reload 端點
    重新載入所有題組檔案
    """
    try:
        result = await service.reload_question_sets()

        # 根據結果設定適當的狀態碼
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重載題組檔案失敗: {str(e)}"
        )


@router.get("/{set_id}/validate")
async def validate_question_set(
    set_id: str,
    service: QuestionSetService = Depends(get_question_set_service)
):
    """
    驗證題組資料完整性（額外端點）
    """
    try:
        validation_result = await service.validate_question_set(set_id)
        return validation_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"驗證題組失敗: {str(e)}"
        )


@router.get("/statistics/summary")
async def get_question_set_statistics(
    service: QuestionSetService = Depends(get_question_set_service)
):
    """
    取得題組統計資訊（額外端點）
    """
    try:
        stats = service.get_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得統計資訊失敗: {str(e)}"
        )


# 初始化函數，將在應用啟動時呼叫
async def initialize_question_set_manager(base_dir: str = "data/question_sets"):
    """初始化題組檔案管理器"""
    global _file_manager

    if _file_manager is None:
        _file_manager = QuestionSetFileManager(base_dir)
        await _file_manager.initialize()


# 清理函數，將在應用關閉時呼叫
async def shutdown_question_set_manager():
    """關閉題組檔案管理器"""
    global _file_manager

    if _file_manager is not None:
        await _file_manager.shutdown()
        _file_manager = None