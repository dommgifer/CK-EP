"""
T034: VNCService VNC 存取服務
提供 VNC 連線的 Token 管理和存取控制
"""
import json
import uuid
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..cache.redis_client import get_redis
from ..models.exam_session import ExamSession

logger = logging.getLogger(__name__)


class VNCService:
    """VNC 存取服務"""

    def __init__(self):
        self.redis_client = get_redis()
        self.token_timeout = 3600  # 1小時
        self.max_connections_per_session = 1  # 單一會話限制

    async def create_vnc_token(self, session_id: str, vnc_container_id: str) -> Dict[str, Any]:
        """
        建立 VNC 存取 Token

        Args:
            session_id: 考試會話 ID
            vnc_container_id: VNC 容器 ID

        Returns:
            Dict: 包含 Token 和存取資訊的字典
        """
        try:
            # 檢查現有 Token
            existing_token = await self._get_existing_token(session_id)
            if existing_token:
                logger.info(f"會話 {session_id} 已有有效的 VNC Token")
                return existing_token

            # 生成新的 Token
            token = self._generate_token()
            vnc_url = f"/vnc/{token}"

            # Token 資料
            token_data = {
                "token": token,
                "session_id": session_id,
                "vnc_container_id": vnc_container_id,
                "vnc_url": vnc_url,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=self.token_timeout)).isoformat(),
                "active_connections": 0,
                "max_connections": self.max_connections_per_session
            }

            # 儲存 Token 到 Redis
            await self._store_token(token, token_data)
            await self._index_session_token(session_id, token)

            logger.info(f"為會話 {session_id} 建立 VNC Token: {token}")

            return {
                "token": token,
                "vnc_url": vnc_url,
                "expires_at": token_data["expires_at"],
                "max_connections": self.max_connections_per_session
            }

        except Exception as e:
            logger.error(f"建立 VNC Token 失敗 (會話: {session_id}): {e}")
            raise RuntimeError(f"建立 VNC Token 失敗: {str(e)}")

    async def validate_vnc_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        驗證 VNC Token

        Args:
            token: VNC Token

        Returns:
            Optional[Dict]: Token 資料，如果無效則返回 None
        """
        try:
            token_data = await self._get_token_data(token)
            if not token_data:
                return None

            # 檢查是否過期
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.utcnow() > expires_at:
                await self._invalidate_token(token)
                logger.info(f"VNC Token {token} 已過期")
                return None

            # 檢查連線數限制
            if token_data["active_connections"] >= token_data["max_connections"]:
                logger.warning(f"VNC Token {token} 已達連線數限制")
                return None

            logger.info(f"VNC Token {token} 驗證成功")
            return token_data

        except Exception as e:
            logger.error(f"驗證 VNC Token 失敗 ({token}): {e}")
            return None

    async def increment_connection(self, token: str) -> bool:
        """
        增加連線計數

        Args:
            token: VNC Token

        Returns:
            bool: 是否成功增加連線
        """
        try:
            token_data = await self._get_token_data(token)
            if not token_data:
                return False

            # 檢查連線數限制
            if token_data["active_connections"] >= token_data["max_connections"]:
                return False

            # 增加連線計數
            token_data["active_connections"] += 1
            await self._store_token(token, token_data)

            logger.info(f"VNC Token {token} 連線數增加至 {token_data['active_connections']}")
            return True

        except Exception as e:
            logger.error(f"增加 VNC 連線計數失敗 ({token}): {e}")
            return False

    async def decrement_connection(self, token: str) -> bool:
        """
        減少連線計數

        Args:
            token: VNC Token

        Returns:
            bool: 是否成功減少連線
        """
        try:
            token_data = await self._get_token_data(token)
            if not token_data:
                return False

            # 減少連線計數
            token_data["active_connections"] = max(0, token_data["active_connections"] - 1)
            await self._store_token(token, token_data)

            logger.info(f"VNC Token {token} 連線數減少至 {token_data['active_connections']}")
            return True

        except Exception as e:
            logger.error(f"減少 VNC 連線計數失敗 ({token}): {e}")
            return False

    async def revoke_session_tokens(self, session_id: str) -> bool:
        """
        撤銷會話的所有 VNC Token

        Args:
            session_id: 考試會話 ID

        Returns:
            bool: 是否成功撤銷
        """
        try:
            # 取得會話的 Token
            token = await self._get_session_token(session_id)
            if not token:
                logger.info(f"會話 {session_id} 沒有 VNC Token")
                return True

            # 撤銷 Token
            await self._invalidate_token(token)
            await self._remove_session_token_index(session_id)

            logger.info(f"已撤銷會話 {session_id} 的 VNC Token")
            return True

        except Exception as e:
            logger.error(f"撤銷會話 VNC Token 失敗 (會話: {session_id}): {e}")
            return False

    def _generate_token(self) -> str:
        """生成安全的 VNC Token"""
        return secrets.token_urlsafe(32)

    async def _store_token(self, token: str, token_data: Dict[str, Any]) -> None:
        """儲存 Token 到 Redis"""
        if self.redis_client.connected:
            key = f"vnc_token:{token}"
            self.redis_client.set(key, token_data, self.token_timeout)

    async def _get_token_data(self, token: str) -> Optional[Dict[str, Any]]:
        """從 Redis 獲取 Token 資料"""
        if not self.redis_client.connected:
            return None

        key = f"vnc_token:{token}"
        return self.redis_client.get(key)

    async def _invalidate_token(self, token: str) -> None:
        """使 Token 失效"""
        if self.redis_client.connected:
            key = f"vnc_token:{token}"
            self.redis_client.delete(key)

    async def _index_session_token(self, session_id: str, token: str) -> None:
        """建立會話到 Token 的索引"""
        if self.redis_client.connected:
            key = f"session_vnc_token:{session_id}"
            self.redis_client.set(key, {"token": token}, self.token_timeout)

    async def _get_session_token(self, session_id: str) -> Optional[str]:
        """獲取會話的 Token"""
        if not self.redis_client.connected:
            return None

        key = f"session_vnc_token:{session_id}"
        data = self.redis_client.get(key)
        return data.get("token") if data else None

    async def _remove_session_token_index(self, session_id: str) -> None:
        """移除會話 Token 索引"""
        if self.redis_client.connected:
            key = f"session_vnc_token:{session_id}"
            self.redis_client.delete(key)

    async def _get_existing_token(self, session_id: str) -> Optional[Dict[str, Any]]:
        """檢查會話是否已有有效的 Token"""
        token = await self._get_session_token(session_id)
        if not token:
            return None

        token_data = await self._get_token_data(token)
        if not token_data:
            # 清理失效的索引
            await self._remove_session_token_index(session_id)
            return None

        # 檢查是否過期
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() > expires_at:
            await self._invalidate_token(token)
            await self._remove_session_token_index(session_id)
            return None

        return {
            "token": token,
            "vnc_url": token_data["vnc_url"],
            "expires_at": token_data["expires_at"],
            "max_connections": token_data["max_connections"]
        }

    async def get_token_stats(self, token: str) -> Optional[Dict[str, Any]]:
        """獲取 Token 統計資訊"""
        token_data = await self._get_token_data(token)
        if not token_data:
            return None

        return {
            "active_connections": token_data["active_connections"],
            "max_connections": token_data["max_connections"],
            "created_at": token_data["created_at"],
            "expires_at": token_data["expires_at"],
            "session_id": token_data["session_id"]
        }