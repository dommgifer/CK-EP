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
import redis
from contextlib import asynccontextmanager

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

    VM_CONFIG_CACHE_KEY = "vm_cluster_config"
    CACHE_TIMEOUT = 3600  # 1小時

    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        try:
            self.redis = redis_client or redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
            # 測試連線
            self.redis.ping()
            self.cache_enabled = True
        except Exception:
            self.redis = None
            self.cache_enabled = False

    async def create_vm_config(self, config_request: CreateVMConfigRequest) -> VMClusterConfigResponse:
        """建立 VM 配置（覆蓋更新模式）"""
        try:
            # 檢查是否已有配置，如有則刪除既有的
            existing_configs = await self.list_vm_configs()
            if existing_configs:
                # 覆蓋更新：刪除所有現有配置
                for config in existing_configs:
                    await self.delete_vm_config(config.id)

            # 生成 ID（如果未提供）
            config_id = config_request.id or str(uuid.uuid4())

            # 建立配置 JSON
            config_data = {
                "nodes": [node.dict() for node in config_request.nodes],
                "ssh_config": config_request.ssh_config.dict()
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

            # 更新快取
            await self._update_cache(db_config)

            return self._to_response_model(db_config)

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
        # 嘗試從快取讀取
        if self.cache_enabled:
            try:
                cached_data = self.redis.get(f"{self.VM_CONFIG_CACHE_KEY}:list")
                if cached_data:
                    configs_data = json.loads(cached_data)
                    return [VMClusterConfigResponse(**config) for config in configs_data]
            except Exception:
                pass  # 快取失敗，繼續從資料庫讀取

        db_configs = self.db.query(VMClusterConfig).filter(
            VMClusterConfig.is_active == "true"
        ).all()

        responses = [self._to_response_model(config) for config in db_configs]

        # 更新列表快取
        if self.cache_enabled and responses:
            try:
                cache_data = [config.dict() for config in responses]
                self.redis.setex(
                    f"{self.VM_CONFIG_CACHE_KEY}:list",
                    self.CACHE_TIMEOUT,
                    json.dumps(cache_data, default=str)
                )
            except Exception:
                pass  # 快取更新失敗不影響主流程

        return responses

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
            if any([update_request.nodes, update_request.ssh_config]):
                current_config = json.loads(db_config.config_json)

                if update_request.nodes is not None:
                    current_config["nodes"] = [node.dict() for node in update_request.nodes]
                if update_request.ssh_config is not None:
                    current_config["ssh_config"] = update_request.ssh_config.dict()

                db_config.config_json = json.dumps(current_config)

            db_config.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_config)

            # 更新快取
            await self._update_cache(db_config)

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
            # 硬刪除而不是軟刪除（用於覆蓋更新）
            self.db.delete(db_config)
            self.db.commit()

            # 清除快取
            await self._clear_cache()

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

    async def _update_cache(self, db_config: VMClusterConfig):
        """更新快取"""
        if not self.cache_enabled:
            return

        try:
            response = self._to_response_model(db_config)
            # 更新單一配置快取
            self.redis.setex(
                f"{self.VM_CONFIG_CACHE_KEY}:{db_config.id}",
                self.CACHE_TIMEOUT,
                json.dumps(response.dict(), default=str)
            )
            # 清除列表快取讓它重新載入
            self.redis.delete(f"{self.VM_CONFIG_CACHE_KEY}:list")
        except Exception:
            pass

    async def _clear_cache(self):
        """清除所有快取"""
        if not self.cache_enabled:
            return

        try:
            # 清除所有 VM 配置相關快取
            keys = self.redis.keys(f"{self.VM_CONFIG_CACHE_KEY}:*")
            if keys:
                self.redis.delete(*keys)
        except Exception:
            pass

    def _to_response_model(self, db_config: VMClusterConfig) -> VMClusterConfigResponse:
        """轉換資料庫模型為回應模型"""
        config_data = json.loads(db_config.config_json)

        return VMClusterConfigResponse(
            id=db_config.id,
            name=db_config.name,
            description=db_config.description,
            nodes=config_data["nodes"],
            ssh_config=config_data["ssh_config"],
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            is_active=db_config.is_active == "true",
            last_tested_at=db_config.last_tested_at
        )