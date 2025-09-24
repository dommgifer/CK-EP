"""
T067: 錯誤處理中介軟體
統一的 API 錯誤處理和回應格式
"""
import logging
from typing import Callable, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """標準錯誤回應格式"""
    error: str
    message: str
    detail: Any = None
    timestamp: str
    path: str


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """錯誤處理中介軟體"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求並捕獲異常"""
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # FastAPI HTTP 異常
            return await self._handle_http_exception(request, e)
        except ValueError as e:
            # 值錯誤（通常是輸入驗證錯誤）
            return await self._handle_validation_error(request, e)
        except PermissionError as e:
            # 權限錯誤
            return await self._handle_permission_error(request, e)
        except FileNotFoundError as e:
            # 檔案不存在錯誤
            return await self._handle_not_found_error(request, e)
        except ConnectionError as e:
            # 連線錯誤（資料庫、Redis 等）
            return await self._handle_connection_error(request, e)
        except Exception as e:
            # 未預期的錯誤
            return await self._handle_internal_error(request, e)

    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """處理 HTTP 異常"""
        error_response = ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail or "HTTP error occurred",
            detail=getattr(exc, 'detail', None),
            timestamp=self._get_timestamp(),
            path=str(request.url.path)
        )

        logger.warning(f"HTTP error {exc.status_code}: {exc.detail} - Path: {request.url.path}")

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )

    async def _handle_validation_error(self, request: Request, exc: ValueError) -> JSONResponse:
        """處理驗證錯誤"""
        error_response = ErrorResponse(
            error="VALIDATION_ERROR",
            message="輸入資料驗證失敗",
            detail=str(exc),
            timestamp=self._get_timestamp(),
            path=str(request.url.path)
        )

        logger.warning(f"Validation error: {exc} - Path: {request.url.path}")

        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )

    async def _handle_permission_error(self, request: Request, exc: PermissionError) -> JSONResponse:
        """處理權限錯誤"""
        error_response = ErrorResponse(
            error="PERMISSION_ERROR",
            message="權限不足",
            detail=str(exc),
            timestamp=self._get_timestamp(),
            path=str(request.url.path)
        )

        logger.warning(f"Permission error: {exc} - Path: {request.url.path}")

        return JSONResponse(
            status_code=403,
            content=error_response.dict()
        )

    async def _handle_not_found_error(self, request: Request, exc: FileNotFoundError) -> JSONResponse:
        """處理檔案不存在錯誤"""
        error_response = ErrorResponse(
            error="NOT_FOUND",
            message="請求的資源不存在",
            detail=str(exc),
            timestamp=self._get_timestamp(),
            path=str(request.url.path)
        )

        logger.warning(f"Not found error: {exc} - Path: {request.url.path}")

        return JSONResponse(
            status_code=404,
            content=error_response.dict()
        )

    async def _handle_connection_error(self, request: Request, exc: ConnectionError) -> JSONResponse:
        """處理連線錯誤"""
        error_response = ErrorResponse(
            error="CONNECTION_ERROR",
            message="外部服務連線失敗",
            detail=str(exc),
            timestamp=self._get_timestamp(),
            path=str(request.url.path)
        )

        logger.error(f"Connection error: {exc} - Path: {request.url.path}")

        return JSONResponse(
            status_code=503,
            content=error_response.dict()
        )

    async def _handle_internal_error(self, request: Request, exc: Exception) -> JSONResponse:
        """處理內部伺服器錯誤"""
        error_response = ErrorResponse(
            error="INTERNAL_ERROR",
            message="內部伺服器錯誤",
            detail=str(exc) if logger.level <= logging.DEBUG else None,
            timestamp=self._get_timestamp(),
            path=str(request.url.path)
        )

        logger.error(f"Internal error: {exc} - Path: {request.url.path}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )

    def _get_timestamp(self) -> str:
        """取得當前時間戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"