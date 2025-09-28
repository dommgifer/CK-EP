"""VM 連線測試 API 端點"""
import asyncio
import paramiko
import socket
import time
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import httpx

logger = logging.getLogger(__name__)

class VMConnectionTestResult(BaseModel):
    success: bool
    message: str
    tested_at: datetime
    nodes: List[Dict[str, Any]]
    total_nodes: int
    successful_nodes: int
    failed_nodes: int

router = APIRouter()

@router.post("/{config_id}/test-connection", response_model=VMConnectionTestResult)
async def test_vm_connection(config_id: str):
    """使用 paramiko 直接測試 VM SSH 連線"""
    logger.info(f"開始測試 VM 配置 {config_id} 的 SSH 連線")

    try:
        # 1. 從 backend 獲取 VM 配置
        vm_config = await _get_vm_config_from_backend(config_id)

        # 2. 並行測試所有節點的 SSH 連線
        test_results = await _test_all_nodes_ssh(vm_config["nodes"], vm_config["ssh_config"])

        # 3. 計算統計資訊
        successful_nodes = sum(1 for result in test_results if result["success"])
        failed_nodes = len(test_results) - successful_nodes

        # 4. 建立測試結果
        overall_success = successful_nodes > 0 and failed_nodes == 0
        message = f"測試完成：{successful_nodes} 成功，{failed_nodes} 失敗"

        result = VMConnectionTestResult(
            success=overall_success,
            message=message,
            tested_at=datetime.utcnow(),
            nodes=test_results,
            total_nodes=len(test_results),
            successful_nodes=successful_nodes,
            failed_nodes=failed_nodes
        )

        logger.info(f"SSH 連線測試完成: {message}")
        return result

    except Exception as e:
        logger.error(f"SSH 連線測試失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"SSH 連線測試執行失敗: {str(e)}"
        )

async def _get_vm_config_from_backend(config_id: str) -> Dict[str, Any]:
    """從 backend 獲取 VM 配置"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://k8s-exam-backend:8000/api/v1/vm-configs/{config_id}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise RuntimeError(f"無法獲取 VM 配置: {str(e)}")

async def _test_all_nodes_ssh(nodes: List[Dict[str, Any]], ssh_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """並行測試所有節點的 SSH 連線"""
    tasks = []
    for node in nodes:
        task = _test_single_node_ssh(node, ssh_config)
        tasks.append(task)

    # 並行執行所有 SSH 測試
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 處理結果和異常
    test_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            test_results.append({
                "name": nodes[i]["name"],
                "ip": nodes[i]["ip"],
                "role": nodes[i]["role"],
                "success": False,
                "error": str(result),
                "response_time": None
            })
        else:
            test_results.append(result)

    return test_results

async def _test_single_node_ssh(node: Dict[str, Any], ssh_config: Dict[str, Any]) -> Dict[str, Any]:
    """使用 paramiko 測試單一節點 SSH 連線"""

    def ssh_test():
        """同步 SSH 測試函數"""
        start_time = time.time()
        client = None

        try:
            # 建立 SSH 客戶端
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 載入私鑰
            try:
                private_key = paramiko.RSAKey.from_private_key_file("/root/.ssh/id_rsa")
            except Exception as e:
                raise RuntimeError(f"無法載入 SSH 私鑰: {str(e)}")

            # 嘗試連線
            client.connect(
                hostname=node["ip"],
                port=ssh_config.get("port", 22),
                username=ssh_config["user"],
                pkey=private_key,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
                look_for_keys=False,
                allow_agent=False
            )

            # 執行簡單命令確認連線
            stdin, stdout, stderr = client.exec_command("echo 'connection_test_ok'", timeout=5)
            stdout_data = stdout.read().decode().strip()
            stderr_data = stderr.read().decode().strip()

            response_time = time.time() - start_time

            if "connection_test_ok" in stdout_data:
                return {
                    "name": node["name"],
                    "ip": node["ip"],
                    "role": node["role"],
                    "success": True,
                    "error": None,
                    "response_time": round(response_time, 3)
                }
            else:
                return {
                    "name": node["name"],
                    "ip": node["ip"],
                    "role": node["role"],
                    "success": False,
                    "error": stderr_data or "命令執行失敗",
                    "response_time": round(response_time, 3)
                }

        except paramiko.AuthenticationException:
            response_time = time.time() - start_time
            return {
                "name": node["name"],
                "ip": node["ip"],
                "role": node["role"],
                "success": False,
                "error": "SSH 認證失敗",
                "response_time": round(response_time, 3)
            }
        except paramiko.SSHException as e:
            response_time = time.time() - start_time
            return {
                "name": node["name"],
                "ip": node["ip"],
                "role": node["role"],
                "success": False,
                "error": f"SSH 連線錯誤: {str(e)}",
                "response_time": round(response_time, 3)
            }
        except socket.timeout:
            response_time = time.time() - start_time
            return {
                "name": node["name"],
                "ip": node["ip"],
                "role": node["role"],
                "success": False,
                "error": "連線逾時",
                "response_time": round(response_time, 3)
            }
        except socket.error as e:
            response_time = time.time() - start_time
            return {
                "name": node["name"],
                "ip": node["ip"],
                "role": node["role"],
                "success": False,
                "error": f"網路連線錯誤: {str(e)}",
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
        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

    # 在執行緒池中運行同步 SSH 測試
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ssh_test)

    return result