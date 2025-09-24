"""
T055: VNC 存取 API 端點
處理 VNC 連線存取令牌
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.connection import get_database
from ...models.exam_session import ExamSession, ExamSessionStatus

router = APIRouter()


@router.post("/{session_id}/vnc/token")
async def generate_vnc_token(
    session_id: str,
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    T055: POST /api/v1/exam-sessions/{session_id}/vnc/token 端點
    生成 VNC 存取令牌
    """
    try:
        # 檢查會話存在性
        db_session = db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"考試會話 '{session_id}' 不存在"
            )

        # 檢查會話狀態
        if db_session.status not in [ExamSessionStatus.IN_PROGRESS, ExamSessionStatus.PAUSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能為進行中或已暫停的會話生成 VNC 令牌"
            )

        # 檢查環境是否準備就緒
        if db_session.environment_status != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="環境尚未準備就緒，無法生成 VNC 令牌"
            )

        # 生成存取令牌
        access_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=4)

        # VNC 連線資訊
        vnc_info = {
            "session_id": session_id,
            "access_token": access_token,
            "vnc_url": f"/vnc/{session_id}",
            "container_id": db_session.vnc_container_id,
            "expires_at": expires_at.isoformat(),
            "connection_info": {
                "host": "localhost",  # 透過 nginx 代理
                "port": 6901,
                "path": f"/vnc/{session_id}/",
                "password_required": False
            },
            "usage_instructions": [
                "點擊連結開啟 VNC 桌面環境",
                "在桌面開啟終端機",
                "執行 'ssh bastion' 連線到工具環境",
                "使用 kubectl 等工具完成題目"
            ]
        }

        return vnc_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成 VNC 令牌失敗: {str(e)}"
        )