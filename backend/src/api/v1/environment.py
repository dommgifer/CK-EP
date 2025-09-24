"""
T053-T054: 環境管理 API 端點
處理 Kubernetes 環境的狀態查詢和配置
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.connection import get_database
from ...services.environment_service import EnvironmentService

router = APIRouter()


def get_environment_service(db: Session = Depends(get_database)) -> EnvironmentService:
    """取得環境服務依賴注入"""
    return EnvironmentService(db)


@router.get("/{session_id}/environment/status")
async def get_environment_status(
    session_id: str,
    service: EnvironmentService = Depends(get_environment_service)
) -> Dict[str, Any]:
    """
    T053: GET /api/v1/exam-sessions/{session_id}/environment/status 端點
    取得考試環境狀態
    """
    try:
        status_info = await service.get_environment_status(session_id)
        return status_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得環境狀態失敗: {str(e)}"
        )


@router.post("/{session_id}/environment/provision")
async def provision_environment(
    session_id: str,
    service: EnvironmentService = Depends(get_environment_service)
) -> Dict[str, Any]:
    """
    T054: POST /api/v1/exam-sessions/{session_id}/environment/provision 端點
    配置考試環境
    """
    try:
        result = await service.provision_environment(session_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置環境失敗: {str(e)}"
        )


@router.delete("/{session_id}/environment/cleanup")
async def cleanup_environment(
    session_id: str,
    service: EnvironmentService = Depends(get_environment_service)
) -> Dict[str, Any]:
    """
    清理考試環境（額外端點）
    """
    try:
        result = await service.cleanup_environment(session_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理環境失敗: {str(e)}"
        )