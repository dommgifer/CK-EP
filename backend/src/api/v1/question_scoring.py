"""
T056-T057: 題目評分 API 端點
處理題目提交和導航
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database.connection import get_database
from ...cache.redis_client import get_redis, RedisClient
from ...services.exam_session_service import ExamSessionService
from ...api.v1.question_sets import get_file_manager
from ...services.question_set_file_manager import QuestionSetFileManager

router = APIRouter()


class AnswerSubmission(BaseModel):
    """答案提交模型"""
    answer_data: Dict[str, Any]
    completed: bool = True


class NavigationUpdate(BaseModel):
    """導航更新模型"""
    question_index: int


def get_exam_session_service(
    db: Session = Depends(get_database),
    redis_client: RedisClient = Depends(get_redis),
    question_set_manager: QuestionSetFileManager = Depends(get_file_manager)
) -> ExamSessionService:
    """取得考試會話服務依賴注入"""
    return ExamSessionService(db, redis_client, question_set_manager)


@router.post("/{session_id}/questions/{question_id}/submit")
async def submit_question_answer(
    session_id: str,
    question_id: int,
    submission: AnswerSubmission,
    service: ExamSessionService = Depends(get_exam_session_service)
) -> Dict[str, Any]:
    """
    T056: POST /api/v1/exam-sessions/{session_id}/questions/{question_id}/submit 端點
    提交題目答案
    """
    try:
        result = await service.submit_answer(
            session_id=session_id,
            question_id=question_id,
            answer_data=submission.answer_data
        )

        # 簡化的評分邏輯（實際應該執行驗證腳本）
        score_result = await _evaluate_answer(session_id, question_id, submission.answer_data)

        return {
            "submission_result": result,
            "score_result": score_result,
            "submitted_at": result.get("submitted_at"),
            "next_actions": [
                "前往下一題" if score_result["passed"] else "檢查答案並重新提交",
                "查看詳細評分結果",
                "繼續考試"
            ]
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交答案失敗: {str(e)}"
        )


@router.patch("/{session_id}/navigation")
async def update_navigation(
    session_id: str,
    navigation: NavigationUpdate,
    service: ExamSessionService = Depends(get_exam_session_service)
) -> Dict[str, Any]:
    """
    T057: PATCH /api/v1/exam-sessions/{session_id}/navigation 端點
    更新考試導航（切換題目）
    """
    try:
        from ...models.exam_session import ExamSessionUpdate

        # 更新當前題目索引
        update_request = ExamSessionUpdate(
            current_question_index=navigation.question_index
        )

        updated_session = await service.update_session(session_id, update_request)

        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"考試會話 '{session_id}' 不存在"
            )

        return {
            "session_id": session_id,
            "current_question_index": updated_session.current_question_index,
            "total_questions": updated_session.total_questions,
            "navigation_updated_at": updated_session.updated_at.isoformat() if hasattr(updated_session, 'updated_at') else None,
            "progress": {
                "current": navigation.question_index + 1,
                "total": updated_session.total_questions,
                "percentage": round((navigation.question_index / updated_session.total_questions) * 100, 1)
            }
        }

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
            detail=f"更新導航失敗: {str(e)}"
        )


async def _evaluate_answer(session_id: str, question_id: int, answer_data: Dict[str, Any]) -> Dict[str, Any]:
    """評估答案（簡化版本）"""
    # 這裡應該執行實際的驗證腳本
    # 目前返回模擬結果

    # 簡單的評分邏輯
    has_required_fields = bool(answer_data.get("kubectl_commands") or answer_data.get("yaml_content"))

    return {
        "question_id": question_id,
        "passed": has_required_fields,
        "score": 10 if has_required_fields else 0,
        "max_score": 10,
        "feedback": "答案已提交並評分" if has_required_fields else "答案格式不完整",
        "verification_results": [
            {
                "check": "格式驗證",
                "passed": has_required_fields,
                "message": "答案包含所需欄位" if has_required_fields else "缺少必要的答案內容"
            }
        ],
        "evaluated_at": "2025-09-23T22:30:00Z"
    }