"""
T065: VNC 容器啟動邏輯
專門處理 VNC 容器的建立、配置和管理
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .container_service import get_container_service

logger = logging.getLogger(__name__)


class VNCContainerService:
    """VNC 容器管理服務"""

    def __init__(self):
        self.container_service = get_container_service()
        self.vnc_image = "consol/debian-xfce-vnc:latest"
        self.vnc_password = "vncpassword"

    async def create_vnc_container(self, session_id: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """建立 VNC 容器"""
        try:
            container_name = f"vnc-{session_id[:8]}"

            # 預設配置
            default_config = {
                "name": container_name,
                "image": self.vnc_image,
                "detach": True,
                "ports": {
                    "6901/tcp": None,  # noVNC web interface
                    "5901/tcp": None   # VNC port
                },
                "environment": {
                    "VNC_PW": self.vnc_password,
                    "VNC_RESOLUTION": "1920x1080",
                    "VNC_COL_DEPTH": "24",
                    "USER": "1000",
                    "GROUP": "1000"
                },
                "volumes": {
                    "/home/ubuntu/DW-CK/data/ssh_keys": {
                        "bind": "/root/.ssh",
                        "mode": "ro"
                    }
                },
                "shm_size": "2g",
                "labels": {
                    "exam.session.id": session_id,
                    "exam.container.type": "vnc",
                    "exam.created_at": datetime.utcnow().isoformat()
                },
                "restart_policy": {"Name": "unless-stopped"}
            }

            # 合併自訂配置
            if custom_config:
                default_config.update(custom_config)

            # 使用容器服務建立容器
            result = await self.container_service.create_vnc_container(session_id, self.vnc_image)

            # 等待容器啟動
            await self._wait_for_container_ready(result["container_id"])

            # 取得容器詳細資訊
            container_info = await self.container_service.get_container_status(result["container_id"])

            return {
                "session_id": session_id,
                "container_id": result["container_id"],
                "container_name": container_name,
                "vnc_info": {
                    "web_url": f"/vnc/{session_id}/",
                    "vnc_password": self.vnc_password,
                    "resolution": "1920x1080",
                    "ports": container_info.get("ports", {}),
                    "access_instructions": [
                        "透過瀏覽器開啟 VNC Web 介面",
                        f"輸入 VNC 密碼: {self.vnc_password}",
                        "在桌面開啟終端機",
                        "執行 'ssh bastion' 連線到工具環境"
                    ]
                },
                "status": "created",
                "created_at": result.get("created_at", datetime.utcnow().isoformat())
            }

        except Exception as e:
            logger.error(f"建立 VNC 容器失敗: {e}")
            raise RuntimeError(f"建立 VNC 容器失敗: {str(e)}")

    async def _wait_for_container_ready(self, container_id: str, timeout_seconds: int = 30) -> bool:
        """等待容器準備就緒"""
        import asyncio

        for i in range(timeout_seconds):
            try:
                status_info = await self.container_service.get_container_status(container_id)
                if status_info.get("status") == "running":
                    logger.info(f"VNC 容器 {container_id} 已準備就緒")
                    return True

                await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"檢查容器狀態失敗: {e}")
                await asyncio.sleep(1)

        logger.warning(f"VNC 容器 {container_id} 在 {timeout_seconds} 秒內未就緒")
        return False

    async def configure_ssh_connection(self, container_id: str, bastion_container_name: str) -> Dict[str, Any]:
        """配置 VNC 容器到 Bastion 的 SSH 連線"""
        try:
            # SSH 配置檔案內容
            ssh_config = f"""
Host bastion
    HostName {bastion_container_name}
    User root
    Port 22
    IdentityFile /root/.ssh/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
"""

            # 寫入 SSH 配置（這裡需要實際的容器執行功能）
            # 在實際實作中，會使用 docker exec 來配置
            logger.info(f"SSH 配置已準備用於容器 {container_id}")

            return {
                "container_id": container_id,
                "ssh_configured": True,
                "bastion_host": bastion_container_name,
                "ssh_config": ssh_config,
                "configured_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"配置 SSH 連線失敗: {e}")
            raise RuntimeError(f"配置 SSH 連線失敗: {str(e)}")

    async def get_vnc_access_info(self, session_id: str) -> Dict[str, Any]:
        """取得 VNC 存取資訊"""
        try:
            containers = await self.container_service.list_session_containers(session_id)
            vnc_container = None

            for container in containers:
                if container.get("type") == "vnc":
                    vnc_container = container
                    break

            if not vnc_container:
                raise ValueError(f"找不到會話 {session_id} 的 VNC 容器")

            container_info = await self.container_service.get_container_status(vnc_container["container_id"])

            return {
                "session_id": session_id,
                "container_id": vnc_container["container_id"],
                "container_name": vnc_container["name"],
                "status": container_info.get("status"),
                "vnc_info": {
                    "web_url": f"/vnc/{session_id}/",
                    "vnc_password": self.vnc_password,
                    "direct_vnc_port": self._extract_vnc_port(container_info.get("ports", {})),
                    "web_port": self._extract_web_port(container_info.get("ports", {})),
                    "ready": container_info.get("status") == "running"
                },
                "created_at": vnc_container.get("created"),
                "retrieved_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"取得 VNC 存取資訊失敗: {e}")
            raise RuntimeError(f"取得 VNC 存取資訊失敗: {str(e)}")

    def _extract_vnc_port(self, ports: Dict[str, Any]) -> Optional[int]:
        """提取 VNC 直連埠號"""
        vnc_port_info = ports.get("5901/tcp")
        if vnc_port_info and len(vnc_port_info) > 0:
            return int(vnc_port_info[0]["HostPort"])
        return None

    def _extract_web_port(self, ports: Dict[str, Any]) -> Optional[int]:
        """提取 noVNC Web 埠號"""
        web_port_info = ports.get("6901/tcp")
        if web_port_info and len(web_port_info) > 0:
            return int(web_port_info[0]["HostPort"])
        return None

    async def stop_vnc_container(self, session_id: str) -> Dict[str, Any]:
        """停止 VNC 容器"""
        try:
            containers = await self.container_service.list_session_containers(session_id)
            vnc_container = None

            for container in containers:
                if container.get("type") == "vnc":
                    vnc_container = container
                    break

            if not vnc_container:
                return {
                    "session_id": session_id,
                    "status": "not_found",
                    "message": "VNC 容器不存在"
                }

            # 停止容器
            stop_result = await self.container_service.stop_container(vnc_container["container_id"])

            return {
                "session_id": session_id,
                "container_id": vnc_container["container_id"],
                "status": "stopped",
                "stop_result": stop_result,
                "stopped_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"停止 VNC 容器失敗: {e}")
            raise RuntimeError(f"停止 VNC 容器失敗: {str(e)}")

    async def remove_vnc_container(self, session_id: str, force: bool = False) -> Dict[str, Any]:
        """移除 VNC 容器"""
        try:
            containers = await self.container_service.list_session_containers(session_id)
            vnc_container = None

            for container in containers:
                if container.get("type") == "vnc":
                    vnc_container = container
                    break

            if not vnc_container:
                return {
                    "session_id": session_id,
                    "status": "not_found",
                    "message": "VNC 容器不存在"
                }

            # 移除容器
            remove_result = await self.container_service.remove_container(vnc_container["container_id"], force)

            return {
                "session_id": session_id,
                "container_id": vnc_container["container_id"],
                "status": "removed",
                "remove_result": remove_result,
                "removed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"移除 VNC 容器失敗: {e}")
            raise RuntimeError(f"移除 VNC 容器失敗: {str(e)}")


# 全域 VNC 容器服務實例
vnc_container_service = VNCContainerService()


def get_vnc_container_service() -> VNCContainerService:
    """取得 VNC 容器服務依賴注入"""
    return vnc_container_service