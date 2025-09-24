"""
T068: 請求日誌中介軟體
記錄 API 請求和回應資訊
"""
import time
import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """請求日誌中介軟體"""

    def __init__(self, app, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """記錄請求和回應"""
        start_time = time.time()

        # 記錄請求開始
        if logger.isEnabledFor(self.log_level):
            client_ip = self._get_client_ip(request)
            logger.log(
                self.log_level,
                f"Request started: {request.method} {request.url.path} - IP: {client_ip}"
            )

        # 處理請求
        response = await call_next(request)

        # 計算處理時間
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # 記錄請求完成
        if logger.isEnabledFor(self.log_level):
            client_ip = self._get_client_ip(request)
            status_code = response.status_code

            log_message = (
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {status_code} - Time: {process_time:.3f}s - IP: {client_ip}"
            )

            # 根據狀態碼選擇日誌級別
            if status_code >= 500:
                logger.error(log_message)
            elif status_code >= 400:
                logger.warning(log_message)
            else:
                logger.log(self.log_level, log_message)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """取得客戶端 IP 地址"""
        # 檢查 X-Forwarded-For 標頭（來自代理伺服器）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一個 IP（原始客戶端）
            return forwarded_for.split(",")[0].strip()

        # 檢查 X-Real-IP 標頭
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 回退到直接連線 IP
        client_host = request.client.host if request.client else "unknown"
        return client_host