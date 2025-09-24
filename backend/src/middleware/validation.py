"""
T070: 輸入驗證和安全中介軟體
提供 API 請求的輸入驗證、清理和安全檢查
"""
import re
import json
import logging
from typing import Callable, Awaitable, Dict, Any, Set
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ValidationMiddleware:
    """輸入驗證中介軟體"""

    def __init__(self):
        # SQL 注入關鍵字檢測
        self.sql_injection_patterns = [
            r"('|(\\')|(;)|(\\;))",  # 引號和分號
            r"(\\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\\b)",
            r"(\\b(OR|AND)\\s+\\d+\\s*=\\s*\\d+)",  # OR 1=1, AND 1=1 等
            r"(\\b(OR|AND)\\s+\\w+\\s*=\\s*\\w+)",
        ]

        # XSS 攻擊模式
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\\w+\\s*=",  # onclick, onload 等事件
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]

        # 路徑遍歷攻擊模式
        self.path_traversal_patterns = [
            r"\\.\\./",
            r"\\.\\.\\\\",
            r"\\./",
            r"~/"
        ]

        # 允許的檔案擴展名
        self.allowed_file_extensions = {
            ".json", ".yaml", ".yml", ".sh", ".py", ".txt", ".md"
        }

        # 最大請求大小 (10MB)
        self.max_request_size = 10 * 1024 * 1024

        # 受保護的端點（需要額外驗證）
        self.protected_endpoints = {
            "POST:/api/v1/vm-configs",
            "PUT:/api/v1/vm-configs/{config_id}",
            "POST:/api/v1/exam-sessions",
            "PATCH:/api/v1/exam-sessions/{session_id}",
        }

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """中介軟體主要邏輯"""
        try:
            # 檢查請求大小
            await self._check_request_size(request)

            # 驗證路徑安全性
            self._validate_path_security(request.url.path)

            # 驗證查詢參數
            self._validate_query_parameters(dict(request.query_params))

            # 如果有請求體，驗證內容
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_body(request)

            # 繼續處理請求
            response = await call_next(request)
            return response

        except HTTPException:
            # 重新拋出 HTTP 異常
            raise
        except Exception as e:
            logger.error(f"驗證中介軟體錯誤: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "驗證失敗",
                    "message": "請求驗證過程中發生錯誤"
                }
            )

    async def _check_request_size(self, request: Request) -> None:
        """檢查請求大小"""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "error": "請求過大",
                            "message": f"請求大小 {size} 超過限制 {self.max_request_size} bytes",
                            "max_size": self.max_request_size
                        }
                    )
            except ValueError:
                # 無效的 content-length
                pass

    def _validate_path_security(self, path: str) -> None:
        """驗證路徑安全性"""
        # 檢查路徑遍歷攻擊
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "無效路徑",
                        "message": "路徑包含不安全的字符"
                    }
                )

        # 檢查路徑長度
        if len(path) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "路徑過長",
                    "message": "URL 路徑超過最大長度限制"
                }
            )

    def _validate_query_parameters(self, params: Dict[str, str]) -> None:
        """驗證查詢參數"""
        for key, value in params.items():
            # 檢查參數長度
            if len(str(key)) > 100 or len(str(value)) > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "參數過長",
                        "message": f"查詢參數 '{key}' 超過最大長度限制"
                    }
                )

            # 檢查 SQL 注入
            self._check_sql_injection(str(value), f"查詢參數 '{key}'")

            # 檢查 XSS
            self._check_xss_attack(str(value), f"查詢參數 '{key}'")

    async def _validate_request_body(self, request: Request) -> None:
        """驗證請求體內容"""
        try:
            # 讀取請求體
            body = await request.body()

            if not body:
                return

            # 嘗試解析 JSON
            try:
                body_str = body.decode('utf-8')
                if body_str.strip():
                    json_data = json.loads(body_str)
                    self._validate_json_content(json_data)
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "編碼錯誤",
                        "message": "請求內容包含無效的 UTF-8 字符"
                    }
                )
            except json.JSONDecodeError:
                # 不是 JSON，可能是其他格式（如 form data）
                # 檢查原始字符串
                self._validate_text_content(body_str)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"請求體驗證失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "請求體驗證失敗",
                    "message": "無法驗證請求內容"
                }
            )

    def _validate_json_content(self, data: Any) -> None:
        """驗證 JSON 內容"""
        def validate_value(value: Any, path: str = "root") -> None:
            if isinstance(value, str):
                # 檢查字符串長度
                if len(value) > 10000:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "字符串過長",
                            "message": f"字段 '{path}' 的值超過最大長度限制"
                        }
                    )

                # 檢查安全性
                self._check_sql_injection(value, f"字段 '{path}'")
                self._check_xss_attack(value, f"字段 '{path}'")

            elif isinstance(value, dict):
                if len(value) > 100:  # 限制對象欄位數量
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "對象過大",
                            "message": f"字段 '{path}' 包含過多屬性"
                        }
                    )

                for key, val in value.items():
                    # 檢查鍵名
                    if len(str(key)) > 100:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "error": "鍵名過長",
                                "message": f"對象鍵名 '{key}' 超過最大長度"
                            }
                        )

                    validate_value(val, f"{path}.{key}")

            elif isinstance(value, list):
                if len(value) > 1000:  # 限制陣列大小
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "陣列過大",
                            "message": f"字段 '{path}' 的陣列超過最大長度限制"
                        }
                    )

                for i, item in enumerate(value):
                    validate_value(item, f"{path}[{i}]")

        validate_value(data)

    def _validate_text_content(self, text: str) -> None:
        """驗證文本內容"""
        # 檢查文本長度
        if len(text) > 50000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "內容過長",
                    "message": "請求內容超過最大長度限制"
                }
            )

        # 檢查安全性
        self._check_sql_injection(text, "請求內容")
        self._check_xss_attack(text, "請求內容")

    def _check_sql_injection(self, text: str, field_name: str) -> None:
        """檢查 SQL 注入攻擊"""
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"偵測到疑似 SQL 注入攻擊在 {field_name}: {text[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "不安全的輸入",
                        "message": f"{field_name} 包含不允許的字符或模式"
                    }
                )

    def _check_xss_attack(self, text: str, field_name: str) -> None:
        """檢查 XSS 攻擊"""
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"偵測到疑似 XSS 攻擊在 {field_name}: {text[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "不安全的輸入",
                        "message": f"{field_name} 包含不允許的 HTML 或 JavaScript 內容"
                    }
                )

    def add_allowed_extension(self, extension: str) -> None:
        """添加允許的檔案擴展名"""
        self.allowed_file_extensions.add(extension.lower())

    def remove_allowed_extension(self, extension: str) -> None:
        """移除允許的檔案擴展名"""
        self.allowed_file_extensions.discard(extension.lower())

    def get_validation_stats(self) -> Dict[str, Any]:
        """取得驗證統計資訊"""
        return {
            "max_request_size": self.max_request_size,
            "allowed_file_extensions": list(self.allowed_file_extensions),
            "protected_endpoints_count": len(self.protected_endpoints),
            "sql_injection_patterns_count": len(self.sql_injection_patterns),
            "xss_patterns_count": len(self.xss_patterns),
            "path_traversal_patterns_count": len(self.path_traversal_patterns)
        }


# 全域驗證中介軟體實例
validation_middleware = ValidationMiddleware()


def get_validation_middleware() -> ValidationMiddleware:
    """取得驗證中介軟體"""
    return validation_middleware