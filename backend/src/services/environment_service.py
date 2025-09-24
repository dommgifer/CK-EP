"""
T033: EnvironmentService Kubespray 環境配置
處理 Kubernetes 環境的配置和狀態管理
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.exam_session import ExamSession, ExamSessionStatus


class EnvironmentService:
    """環境配置服務"""

    def __init__(self, db: Session):
        self.db = db

    async def get_environment_status(self, session_id: str) -> Dict[str, Any]:
        """取得環境狀態"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        # 環境狀態資訊
        status_info = {
            "session_id": session_id,
            "environment_status": db_session.environment_status,
            "vnc_container_id": db_session.vnc_container_id,
            "bastion_container_id": db_session.bastion_container_id,
            "vm_config_id": db_session.vm_config_id,
            "last_updated": datetime.utcnow().isoformat(),
            "containers": {
                "vnc": {
                    "status": "running" if db_session.vnc_container_id else "not_created",
                    "container_id": db_session.vnc_container_id
                },
                "bastion": {
                    "status": "running" if db_session.bastion_container_id else "not_created",
                    "container_id": db_session.bastion_container_id
                }
            },
            "kubernetes": {
                "status": self._get_kubernetes_status(db_session.environment_status),
                "deployment_progress": self._get_deployment_progress(db_session.environment_status)
            }
        }

        return status_info

    async def provision_environment(self, session_id: str) -> Dict[str, Any]:
        """配置考試環境"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        if db_session.status != ExamSessionStatus.CREATED:
            raise ValueError("只能為 'created' 狀態的會話配置環境")

        try:
            # 更新環境狀態為配置中
            db_session.environment_status = "provisioning"
            self.db.commit()

            # 啟動配置流程（簡化版本）
            result = await self._start_environment_provisioning(session_id, db_session)

            return result

        except Exception as e:
            db_session.environment_status = "failed"
            self.db.commit()
            raise RuntimeError(f"環境配置失敗: {str(e)}")

    async def _start_environment_provisioning(self, session_id: str, db_session: ExamSession) -> Dict[str, Any]:
        """啟動環境配置流程"""

        # 階段 1: 啟動容器
        await self._provision_containers(db_session)

        # 階段 2: 配置 Kubernetes（模擬）
        await self._provision_kubernetes(db_session)

        # 更新最終狀態
        db_session.environment_status = "ready"
        self.db.commit()

        return {
            "session_id": session_id,
            "status": "success",
            "message": "環境配置完成",
            "environment_status": "ready",
            "containers": {
                "vnc_container_id": db_session.vnc_container_id,
                "bastion_container_id": db_session.bastion_container_id
            },
            "provisioned_at": datetime.utcnow().isoformat()
        }

    async def _provision_containers(self, db_session: ExamSession):
        """配置容器（模擬）"""
        # 模擬 VNC 容器啟動
        vnc_container_id = f"vnc-{db_session.id[:8]}"
        db_session.vnc_container_id = vnc_container_id

        # 模擬 Bastion 容器啟動
        bastion_container_id = f"bastion-{db_session.id[:8]}"
        db_session.bastion_container_id = bastion_container_id

        db_session.environment_status = "containers_ready"
        self.db.commit()

        # 模擬容器啟動時間
        await asyncio.sleep(1)

    async def _provision_kubernetes(self, db_session: ExamSession):
        """配置 Kubernetes 環境（模擬）"""
        # 模擬 Kubespray 部署過程
        deployment_stages = [
            "configuring_inventory",
            "downloading_images",
            "installing_kubernetes",
            "configuring_network",
            "finalizing_setup"
        ]

        for stage in deployment_stages:
            db_session.environment_status = f"k8s_{stage}"
            self.db.commit()
            # 模擬每個階段的時間
            await asyncio.sleep(0.5)

    def _get_kubernetes_status(self, environment_status: str) -> str:
        """取得 Kubernetes 狀態"""
        if environment_status == "ready":
            return "running"
        elif environment_status.startswith("k8s_"):
            return "deploying"
        elif environment_status == "failed":
            return "failed"
        else:
            return "not_deployed"

    def _get_deployment_progress(self, environment_status: str) -> int:
        """取得部署進度百分比"""
        progress_map = {
            "not_provisioned": 0,
            "provisioning": 10,
            "containers_ready": 20,
            "k8s_configuring_inventory": 30,
            "k8s_downloading_images": 50,
            "k8s_installing_kubernetes": 70,
            "k8s_configuring_network": 85,
            "k8s_finalizing_setup": 95,
            "ready": 100,
            "failed": 0
        }
        return progress_map.get(environment_status, 0)

    async def cleanup_environment(self, session_id: str) -> Dict[str, Any]:
        """清理環境資源"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        try:
            # 清理容器（模擬）
            if db_session.vnc_container_id:
                # 模擬停止 VNC 容器
                pass

            if db_session.bastion_container_id:
                # 模擬停止 Bastion 容器
                pass

            # 重置環境狀態
            db_session.environment_status = "cleaned"
            db_session.vnc_container_id = None
            db_session.bastion_container_id = None
            self.db.commit()

            return {
                "session_id": session_id,
                "status": "success",
                "message": "環境已清理",
                "cleaned_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise RuntimeError(f"環境清理失敗: {str(e)}")