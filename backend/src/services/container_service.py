"""
T064: 容器服務中介軟體
處理 Docker 容器的管理和操作
"""
import docker
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ContainerService:
    """容器管理服務"""

    def __init__(self):
        self.docker_client = None
        self.connected = False

    def connect(self) -> bool:
        """連接到 Docker"""
        try:
            self.docker_client = docker.from_env()
            # 測試連線
            self.docker_client.ping()
            self.connected = True
            logger.info("Successfully connected to Docker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.connected = False
            return False

    async def create_vnc_container(self, session_id: str, image: str = "consol/debian-xfce-vnc:latest") -> Dict[str, Any]:
        """建立 VNC 容器"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            container_name = f"vnc-{session_id[:8]}"

            # 容器配置
            container_config = {
                "name": container_name,
                "image": image,
                "detach": True,
                "ports": {
                    "6901/tcp": None,  # noVNC web interface
                    "5901/tcp": None   # VNC port
                },
                "environment": {
                    "VNC_PW": "vncpassword",
                    "VNC_RESOLUTION": "1920x1080",
                    "VNC_COL_DEPTH": "24"
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
                    "exam.container.type": "vnc"
                }
            }

            # 建立並啟動容器
            container = self.docker_client.containers.run(**container_config)

            logger.info(f"VNC 容器已建立: {container.id}")

            return {
                "container_id": container.id,
                "container_name": container_name,
                "status": "created",
                "ports": container.attrs["NetworkSettings"]["Ports"],
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"建立 VNC 容器失敗: {e}")
            raise RuntimeError(f"建立 VNC 容器失敗: {str(e)}")

    async def create_bastion_container(self, session_id: str, image: str = "k8s-exam-bastion:latest") -> Dict[str, Any]:
        """建立 Bastion 容器"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            container_name = f"bastion-{session_id[:8]}"

            # 容器配置
            container_config = {
                "name": container_name,
                "image": image,
                "detach": True,
                "ports": {
                    "22/tcp": None  # SSH port
                },
                "volumes": {
                    "/home/ubuntu/DW-CK/data/ssh_keys": {
                        "bind": "/root/.ssh",
                        "mode": "ro"
                    },
                    "/home/ubuntu/DW-CK/data/kubespray_configs": {
                        "bind": "/workspace/kubespray-configs",
                        "mode": "ro"
                    }
                },
                "labels": {
                    "exam.session.id": session_id,
                    "exam.container.type": "bastion"
                },
                "command": ["tail", "-f", "/dev/null"]  # 保持容器運行
            }

            # 建立並啟動容器
            container = self.docker_client.containers.run(**container_config)

            logger.info(f"Bastion 容器已建立: {container.id}")

            return {
                "container_id": container.id,
                "container_name": container_name,
                "status": "created",
                "ports": container.attrs["NetworkSettings"]["Ports"],
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"建立 Bastion 容器失敗: {e}")
            raise RuntimeError(f"建立 Bastion 容器失敗: {str(e)}")

    async def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """取得容器狀態"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            container = self.docker_client.containers.get(container_id)

            return {
                "container_id": container.id,
                "name": container.name,
                "status": container.status,
                "state": container.attrs["State"],
                "ports": container.attrs["NetworkSettings"]["Ports"],
                "created": container.attrs["Created"],
                "image": container.attrs["Config"]["Image"]
            }

        except docker.errors.NotFound:
            return {
                "container_id": container_id,
                "status": "not_found",
                "error": "容器不存在"
            }
        except Exception as e:
            logger.error(f"取得容器狀態失敗: {e}")
            raise RuntimeError(f"取得容器狀態失敗: {str(e)}")

    async def stop_container(self, container_id: str) -> Dict[str, Any]:
        """停止容器"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)

            logger.info(f"容器已停止: {container_id}")

            return {
                "container_id": container_id,
                "status": "stopped",
                "stopped_at": datetime.utcnow().isoformat()
            }

        except docker.errors.NotFound:
            return {
                "container_id": container_id,
                "status": "not_found",
                "error": "容器不存在"
            }
        except Exception as e:
            logger.error(f"停止容器失敗: {e}")
            raise RuntimeError(f"停止容器失敗: {str(e)}")

    async def remove_container(self, container_id: str, force: bool = False) -> Dict[str, Any]:
        """移除容器"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            container = self.docker_client.containers.get(container_id)
            container.remove(force=force)

            logger.info(f"容器已移除: {container_id}")

            return {
                "container_id": container_id,
                "status": "removed",
                "removed_at": datetime.utcnow().isoformat()
            }

        except docker.errors.NotFound:
            return {
                "container_id": container_id,
                "status": "not_found",
                "error": "容器不存在"
            }
        except Exception as e:
            logger.error(f"移除容器失敗: {e}")
            raise RuntimeError(f"移除容器失敗: {str(e)}")

    async def list_session_containers(self, session_id: str) -> List[Dict[str, Any]]:
        """列出會話相關的容器"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            containers = self.docker_client.containers.list(
                all=True,
                filters={"label": f"exam.session.id={session_id}"}
            )

            result = []
            for container in containers:
                result.append({
                    "container_id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.attrs["Config"]["Image"],
                    "created": container.attrs["Created"],
                    "type": container.labels.get("exam.container.type", "unknown")
                })

            return result

        except Exception as e:
            logger.error(f"列出容器失敗: {e}")
            raise RuntimeError(f"列出容器失敗: {str(e)}")

    async def cleanup_session_containers(self, session_id: str) -> Dict[str, Any]:
        """清理會話相關的容器"""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("無法連接到 Docker")

        try:
            containers = await self.list_session_containers(session_id)
            removed_containers = []

            for container_info in containers:
                container_id = container_info["container_id"]
                try:
                    # 停止並移除容器
                    await self.stop_container(container_id)
                    result = await self.remove_container(container_id, force=True)
                    removed_containers.append(result)
                except Exception as e:
                    logger.error(f"清理容器失敗 {container_id}: {e}")
                    removed_containers.append({
                        "container_id": container_id,
                        "status": "cleanup_failed",
                        "error": str(e)
                    })

            return {
                "session_id": session_id,
                "cleaned_containers": removed_containers,
                "total_cleaned": len(removed_containers),
                "cleaned_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"清理會話容器失敗: {e}")
            raise RuntimeError(f"清理會話容器失敗: {str(e)}")


# 全域容器服務實例
container_service = ContainerService()


def get_container_service() -> ContainerService:
    """取得容器服務依賴注入"""
    if not container_service.connected:
        container_service.connect()
    return container_service