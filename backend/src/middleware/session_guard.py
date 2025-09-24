"""
T069: 單一會話限制中介軟體
確保系統同時只能有一個活動的考試會話
"""
import logging
from typing import Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database.connection import get_database
from ..models.exam_session import ExamSession, ExamSessionStatus

logger = logging.getLogger(__name__)


class SessionGuardMiddleware:
    """會話保護中介軟體"""

    def __init__(self):
        self.protected_endpoints = {
            # 會話建立端點
            "POST:/api/v1/exam-sessions",
            # 會話啟動端點
            "POST:/api/v1/exam-sessions/{session_id}/start",
            # 會話恢復端點
            "POST:/api/v1/exam-sessions/{session_id}/resume",
            # 環境配置端點
            "POST:/api/v1/exam-sessions/{session_id}/environment/provision"
        }

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """中介軟體主要邏輯"""
        try:
            # 檢查是否為受保護的端點
            endpoint_key = f"{request.method}:{request.url.path}"

            # 對於帶參數的路徑，使用模式匹配
            is_protected = self._is_protected_endpoint(request.method, request.url.path)

            if is_protected:
                # 執行會話限制檢查
                await self._check_session_limit(request)

            # 繼續處理請求
            response = await call_next(request)
            return response

        except HTTPException:
            # 重新拋出 HTTP 異常
            raise
        except Exception as e:
            logger.error(f"會話保護中介軟體錯誤: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "會話檢查失敗",
                    "message": "系統內部錯誤，請稍後再試"
                }
            )

    def _is_protected_endpoint(self, method: str, path: str) -> bool:
        """檢查是否為受保護的端點"""
        # 精確匹配
        exact_key = f"{method}:{path}"
        if exact_key in self.protected_endpoints:
            return True

        # 模式匹配（帶參數的路徑）
        for protected_pattern in self.protected_endpoints:
            if self._path_matches_pattern(method, path, protected_pattern):
                return True

        return False

    def _path_matches_pattern(self, method: str, path: str, pattern: str) -> bool:
        """檢查路徑是否匹配保護模式"""
        try:
            pattern_method, pattern_path = pattern.split(":", 1)

            if method != pattern_method:
                return False

            # 簡單的參數替換匹配
            if "{" in pattern_path and "}" in pattern_path:
                # 將 {session_id} 等參數替換為通配符進行匹配
                import re
                pattern_regex = re.sub(r'\{[^}]+\}', r'[^/]+', pattern_path)
                pattern_regex = f"^{pattern_regex}$"
                return bool(re.match(pattern_regex, path))

            return path == pattern_path

        except ValueError:
            return False

    async def _check_session_limit(self, request: Request) -> None:
        """檢查會話限制"""
        try:
            # 取得資料庫會話
            db_gen = get_database()
            db: Session = next(db_gen)

            try:
                # 檢查是否有活動的會話
                active_session = db.query(ExamSession).filter(
                    ExamSession.status.in_([
                        ExamSessionStatus.IN_PROGRESS,
                        ExamSessionStatus.PAUSED
                    ])
                ).first()

                # 如果是建立新會話的請求
                if request.method == "POST" and "/exam-sessions" in request.url.path and "{" not in request.url.path:
                    if active_session:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail={
                                "error": "會話衝突",
                                "message": "系統已有進行中的考試會話，請先完成或取消現有會話",
                                "active_session_id": active_session.id,
                                "active_session_status": active_session.status.value
                            }
                        )

                # 如果是操作特定會話的請求
                elif "{session_id}" in str(request.url.path):
                    # 從路徑中提取 session_id
                    session_id = self._extract_session_id_from_path(request.url.path)

                    if session_id and active_session and active_session.id != session_id:
                        # 嘗試操作非活動會話
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail={
                                "error": "會話衝突",
                                "message": f"無法操作會話 {session_id}，系統已有其他進行中的會話",
                                "active_session_id": active_session.id,
                                "requested_session_id": session_id
                            }
                        )

            finally:
                db.close()

        except HTTPException:
            # 重新拋出 HTTP 異常
            raise
        except Exception as e:
            logger.error(f"會話限制檢查失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "會話檢查失敗",
                    "message": "無法驗證會話狀態"
                }
            )

    def _extract_session_id_from_path(self, path: str) -> str:
        """從路徑中提取 session_id"""
        try:
            # 例如：/api/v1/exam-sessions/abc-123/start
            # 分割路徑並找到 exam-sessions 後的部分
            parts = path.split("/")

            if "exam-sessions" in parts:
                session_index = parts.index("exam-sessions")
                if len(parts) > session_index + 1:
                    return parts[session_index + 1]

            return None

        except Exception as e:
            logger.warning(f"無法從路徑提取 session_id: {e}")
            return None

    def add_protected_endpoint(self, method: str, path: str) -> None:
        """添加受保護的端點"""
        endpoint_key = f"{method}:{path}"
        self.protected_endpoints.add(endpoint_key)
        logger.info(f"添加受保護端點: {endpoint_key}")

    def remove_protected_endpoint(self, method: str, path: str) -> None:
        """移除受保護的端點"""
        endpoint_key = f"{method}:{path}"
        self.protected_endpoints.discard(endpoint_key)
        logger.info(f"移除受保護端點: {endpoint_key}")

    def get_protected_endpoints(self) -> set:
        """取得所有受保護的端點"""
        return self.protected_endpoints.copy()


# 全域會話保護中介軟體實例
session_guard_middleware = SessionGuardMiddleware()


def get_session_guard_middleware() -> SessionGuardMiddleware:
    """取得會話保護中介軟體"""
    return session_guard_middleware