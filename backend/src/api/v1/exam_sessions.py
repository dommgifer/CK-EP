"""
T045-T052: 考試會話管理 API 端點
處理考試會話的生命週期管理
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...database.connection import get_database
from ...cache.redis_client import get_redis, RedisClient
from ...services.exam_session_service import ExamSessionService
from ...api.v1.question_sets import get_file_manager
from ...services.question_set_file_manager import QuestionSetFileManager
from ...models.exam_session import (
    ExamSessionCreate,
    ExamSessionUpdate,
    ExamSessionResponse,
    ExamSessionDetailed
)

router = APIRouter()


def get_exam_session_service(
    db: Session = Depends(get_database),
    redis_client: RedisClient = Depends(get_redis),
    question_set_manager: QuestionSetFileManager = Depends(get_file_manager)
) -> ExamSessionService:
    """取得考試會話服務依賴注入"""
    return ExamSessionService(db, redis_client, question_set_manager)


@router.get("", response_model=List[ExamSessionResponse])
async def list_exam_sessions(
    status: Optional[str] = Query(None, description="篩選會話狀態"),
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T045: GET /api/v1/exam-sessions 端點
    列出所有考試會話
    """
    try:
        sessions = await service.list_sessions(status_filter=status)
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得考試會話列表失敗: {str(e)}"
        )


@router.post("", response_model=ExamSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_session(
    session_request: ExamSessionCreate,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T046: POST /api/v1/exam-sessions 端點
    建立新的考試會話
    """
    try:
        session = await service.create_session(session_request)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立考試會話失敗: {str(e)}"
        )


@router.get("/{session_id}", response_model=ExamSessionDetailed)
async def get_exam_session(
    session_id: str,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T047: GET /api/v1/exam-sessions/{session_id} 端點
    取得考試會話詳細資訊
    """
    try:
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"考試會話 '{session_id}' 不存在"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得考試會話失敗: {str(e)}"
        )


@router.patch("/{session_id}", response_model=ExamSessionResponse)
async def update_exam_session(
    session_id: str,
    update_request: ExamSessionUpdate,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T048: PATCH /api/v1/exam-sessions/{session_id} 端點
    更新考試會話資訊
    """
    try:
        session = await service.update_session(session_id, update_request)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"考試會話 '{session_id}' 不存在"
            )
        return session
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新考試會話失敗: {str(e)}"
        )


@router.post("/{session_id}/start", response_model=ExamSessionResponse)
async def start_exam_session(
    session_id: str,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T049: POST /api/v1/exam-sessions/{session_id}/start 端點
    開始考試會話
    """
    try:
        session = await service.start_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"開始考試會話失敗: {str(e)}"
        )


@router.post("/{session_id}/pause", response_model=ExamSessionResponse)
async def pause_exam_session(
    session_id: str,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T050: POST /api/v1/exam-sessions/{session_id}/pause 端點
    暫停考試會話
    """
    try:
        session = await service.pause_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暫停考試會話失敗: {str(e)}"
        )


@router.post("/{session_id}/resume", response_model=ExamSessionResponse)
async def resume_exam_session(
    session_id: str,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T051: POST /api/v1/exam-sessions/{session_id}/resume 端點
    恢復考試會話
    """
    try:
        session = await service.resume_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢復考試會話失敗: {str(e)}"
        )


@router.post("/{session_id}/complete", response_model=ExamSessionResponse)
async def complete_exam_session(
    session_id: str,
    service: ExamSessionService = Depends(get_exam_session_service)
):
    """
    T052: POST /api/v1/exam-sessions/{session_id}/complete 端點
    完成考試會話
    """
    try:
        session = await service.complete_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成考試會話失敗: {str(e)}"
        )