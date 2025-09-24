"""
T030: VMClusterService CRUD 操作
VM 叢集配置服務
"""
import json
import uuid
import asyncio
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.vm_cluster_config import (
    VMClusterConfig,
    VMClusterConfigResponse,
    VMClusterConfigDetailed,
    VMConnectionTestResult,
    CreateVMConfigRequest,
    UpdateVMConfigRequest
)


class VMClusterService:
    """VM 叢集配置服務"""

    def __init__(self, db: Session):
        self.db = db

    async def create_vm_config(self, config_request: CreateVMConfigRequest) -> VMClusterConfigResponse:
        """建立 VM 配置"""
        try:
            # 生成 ID（如果未提供）
            config_id = config_request.id or str(uuid.uuid4())

            # 建立配置 JSON
            config_data = {
                "nodes": [node.dict() for node in config_request.nodes],
                "ssh_config": config_request.ssh_config.dict(),
                "network": config_request.network.dict()
            }

            # 建立資料庫記錄
            db_config = VMClusterConfig(
                id=config_id,
                name=config_request.name,
                description=config_request.description,
                config_json=json.dumps(config_data),
                is_active="true"
            )

            self.db.add(db_config)
            self.db.commit()
            self.db.refresh(db_config)

            return self._to_response_model(db_config)

        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"VM 配置 ID '{config_id}' 已存在")
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"建立 VM 配置失敗: {str(e)}")

    async def get_vm_config(self, config_id: str) -> Optional[VMClusterConfigDetailed]:
        """獲取 VM 配置詳細資訊"""
        db_config = self.db.query(VMClusterConfig).filter(
            VMClusterConfig.id == config_id,
            VMClusterConfig.is_active == "true"
        ).first()

        if not db_config:
            return None

        return VMClusterConfigDetailed.from_db_model(db_config)

    async def list_vm_configs(self) -> List[VMClusterConfigResponse]:
        """列出所有 VM 配置"""
        db_configs = self.db.query(VMClusterConfig).filter(
            VMClusterConfig.is_active == "true"
        ).all()

        return [self._to_response_model(config) for config in db_configs]

    async def update_vm_config(self, config_id: str, update_request: UpdateVMConfigRequest) -> Optional[VMClusterConfigResponse]:
        """更新 VM 配置"""
        db_config = self.db.query(VMClusterConfig).filter(
            VMClusterConfig.id == config_id,
            VMClusterConfig.is_active == "true"
        ).first()

        if not db_config:
            return None

        try:
            # 更新欄位
            if update_request.name is not None:
                db_config.name = update_request.name
            if update_request.description is not None:
                db_config.description = update_request.description

            # 更新配置 JSON
            if any([update_request.nodes, update_request.ssh_config, update_request.network]):
                current_config = json.loads(db_config.config_json)

                if update_request.nodes is not None:
                    current_config["nodes"] = [node.dict() for node in update_request.nodes]
                if update_request.ssh_config is not None:
                    current_config["ssh_config"] = update_request.ssh_config.dict()
                if update_request.network is not None:
                    current_config["network"] = update_request.network.dict()

                db_config.config_json = json.dumps(current_config)

            db_config.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_config)

            return self._to_response_model(db_config)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"更新 VM 配置失敗: {str(e)}")

    async def delete_vm_config(self, config_id: str) -> bool:
        """刪除 VM 配置（軟刪除）"""
        db_config = self.db.query(VMClusterConfig).filter(
            VMClusterConfig.id == config_id,
            VMClusterConfig.is_active == "true"
        ).first()

        if not db_config:
            return False

        try:
            db_config.is_active = "false"
            db_config.updated_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"刪除 VM 配置失敗: {str(e)}")

    async def test_vm_connection(self, config_id: str) -> VMConnectionTestResult:
        """測試 VM 連線"""
        db_config = self.db.query(VMClusterConfig).filter(
            VMClusterConfig.id == config_id,
            VMClusterConfig.is_active == "true"
        ).first()

        if not db_config:
            raise ValueError(f"VM 配置 '{config_id}' 不存在")

        config_data = json.loads(db_config.config_json)
        nodes = config_data["nodes"]
        ssh_config = config_data["ssh_config"]

        test_results = []
        successful_nodes = 0
        failed_nodes = 0

        # 並行測試所有節點
        tasks = []
        for node in nodes:
            task = self._test_single_node(node, ssh_config)
            tasks.append(task)

        node_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(node_results):
            if isinstance(result, Exception):
                test_results.append({
                    "name": nodes[i]["name"],
                    "ip": nodes[i]["ip"],
                    "role": nodes[i]["role"],
                    "success": False,
                    "error": str(result),
                    "response_time": None
                })
                failed_nodes += 1
            else:
                test_results.append(result)
                if result["success"]:
                    successful_nodes += 1
                else:
                    failed_nodes += 1

        # 建立測試結果
        test_result = VMConnectionTestResult(
            success=successful_nodes > 0 and failed_nodes == 0,
            message=f"測試完成：{successful_nodes} 成功，{failed_nodes} 失敗",
            tested_at=datetime.utcnow(),
            nodes=test_results,
            total_nodes=len(nodes),
            successful_nodes=successful_nodes,
            failed_nodes=failed_nodes
        )

        # 儲存測試結果到資料庫
        try:
            db_config.last_tested_at = test_result.tested_at
            db_config.test_result_json = json.dumps(test_result.dict())
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # 不中斷測試流程，只記錄錯誤
            print(f"Warning: Failed to save test result: {e}")

        return test_result

    async def _test_single_node(self, node: Dict[str, Any], ssh_config: Dict[str, Any]) -> Dict[str, Any]:
        """測試單一節點連線"""
        import time
        start_time = time.time()

        try:
            # 構建 SSH 測試命令
            ssh_cmd = [
                "ssh",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "BatchMode=yes",
                "-p", str(ssh_config.get("port", 22)),
                "-i", "/root/.ssh/id_rsa",  # 固定路徑
                f"{ssh_config['user']}@{node['ip']}",
                "echo 'connection_test_ok'"
            ]

            # 執行 SSH 測試
            result = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()
            response_time = time.time() - start_time

            if result.returncode == 0 and b"connection_test_ok" in stdout:
                return {
                    "name": node["name"],
                    "ip": node["ip"],
                    "role": node["role"],
                    "success": True,
                    "error": None,
                    "response_time": round(response_time, 3)
                }
            else:
                error_msg = stderr.decode().strip() or "SSH 連線失敗"
                return {
                    "name": node["name"],
                    "ip": node["ip"],
                    "role": node["role"],
                    "success": False,
                    "error": error_msg,
                    "response_time": round(response_time, 3)
                }

        except Exception as e:
            response_time = time.time() - start_time
            return {
                "name": node["name"],
                "ip": node["ip"],
                "role": node["role"],
                "success": False,
                "error": str(e),
                "response_time": round(response_time, 3)
            }

    def _to_response_model(self, db_config: VMClusterConfig) -> VMClusterConfigResponse:
        """轉換資料庫模型為回應模型"""
        config_data = json.loads(db_config.config_json)

        return VMClusterConfigResponse(
            id=db_config.id,
            name=db_config.name,
            description=db_config.description,
            nodes=config_data["nodes"],
            ssh_config=config_data["ssh_config"],
            network=config_data["network"],
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            is_active=db_config.is_active == "true",
            last_tested_at=db_config.last_tested_at
        )