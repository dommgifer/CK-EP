"""
Kubespray API 代理路由
提供前端統一的 API 端點，一對一映射到 Kubespray API Server
"""
import json
import logging
import asyncio
from datetime import datetime
import httpx
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Kubespray Proxy"])

# Kubespray API Server 容器名稱和端口
KUBESPRAY_API_URL = "http://k8s-exam-kubespray-api:8080"


# ============================================================================
# 請求和回應模型定義 (與 kubespray API 一致)
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class VMNode(BaseModel):
    """VM 節點模型"""
    name: str
    ip: str
    role: str = Field(description="角色: master, worker")


class SSHConfig(BaseModel):
    """SSH 配置模型"""
    user: str = "root"
    port: int = 22


class VMClusterConfig(BaseModel):
    """VM 叢集配置模型"""
    id: Optional[str] = None
    name: str
    nodes: List[VMNode]
    ssh_config: SSHConfig = SSHConfig()
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GenerateInventoryRequest(BaseModel):
    """生成 inventory 請求模型"""
    session_id: str
    vm_config: VMClusterConfig
    question_set_id: Optional[str] = None


class GenerateInventoryResponse(BaseModel):
    """生成 inventory 回應模型"""
    session_id: str
    inventory_path: str
    generated_files: List[str]
    generated_at: str


class HealthCheckResponse(BaseModel):
    """健康檢查回應模型"""
    status: str
    kubespray_ready: bool
    ssh_keys_mounted: bool
    inventory_writable: bool
    uptime_seconds: int
    version: str
    checked_at: str


class KubesprayRootResponse(BaseModel):
    """Kubespray API 根端點回應"""
    message: str
    version: str
    status: str


class VMConnectionTestResult(BaseModel):
    """VM 連線測試結果模型"""
    success: bool
    message: str
    tested_at: datetime
    nodes: List[Dict[str, Any]]
    total_nodes: int
    successful_nodes: int
    failed_nodes: int


class DeployRequest(BaseModel):
    """部署請求模型"""
    playbook: str = "cluster.yml"


class DeploymentResponse(BaseModel):
    """部署回應模型"""
    session_id: str
    status: str
    playbook: str
    log_stream_url: str
    started_at: str


class DeploymentStatusResponse(BaseModel):
    """部署狀態回應模型"""
    session_id: str
    status: str  # pending, running, completed, failed
    playbook: str
    started_at: str
    completed_at: Optional[str] = None
    exit_code: Optional[int] = None


# ============================================================================
# 代理端點定義 (一對一映射)
# ============================================================================

@router.get("/kubespray/health", response_model=HealthCheckResponse)
async def kubespray_health_check():
    """
    Kubespray API 健康檢查
    代理到: GET /health
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{KUBESPRAY_API_URL}/health")
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error(f"無法連接到 Kubespray API Server: {KUBESPRAY_API_URL}")
        raise HTTPException(
            status_code=503,
            detail="Kubespray API Server 無法連接"
        )
    except httpx.TimeoutException:
        logger.error(f"Kubespray API 健康檢查逾時")
        raise HTTPException(
            status_code=504,
            detail="Kubespray API 健康檢查逾時"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Kubespray API 健康檢查失敗: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Kubespray API 健康檢查失敗: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"代理 Kubespray 健康檢查失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理請求失敗: {str(e)}"
        )


@router.post(
    "/exam-sessions/{session_id}/kubespray/inventory",
    response_model=GenerateInventoryResponse
)
async def generate_kubespray_inventory(
    session_id: str,
    request: GenerateInventoryRequest
):
    """
    生成 Kubespray inventory 配置
    代理到: POST /exam-sessions/{session_id}/kubespray/inventory
    """
    try:
        # 更新請求中的 session_id 以確保一致性
        request.session_id = session_id

        # 序列化請求資料，處理 datetime 欄位
        request_data = request.model_dump()
        # 移除可能造成序列化問題的 datetime 欄位
        if 'vm_config' in request_data and isinstance(request_data['vm_config'], dict):
            vm_config = request_data['vm_config']
            # 移除所有 datetime 欄位
            vm_config.pop('created_at', None)
            vm_config.pop('updated_at', None)
            vm_config.pop('last_tested_at', None)

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{KUBESPRAY_API_URL}/exam-sessions/{session_id}/kubespray/inventory",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error(f"無法連接到 Kubespray API Server: {KUBESPRAY_API_URL}")
        raise HTTPException(
            status_code=503,
            detail="Kubespray API Server 無法連接"
        )
    except httpx.TimeoutException:
        logger.error(f"生成 Kubespray inventory 逾時")
        raise HTTPException(
            status_code=504,
            detail="生成 Kubespray inventory 逾時"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"生成 Kubespray inventory 失敗: {e.response.status_code}")
        error_detail = "生成 Kubespray inventory 失敗"
        try:
            error_data = e.response.json()
            if "detail" in error_data:
                error_detail = error_data["detail"]
        except:
            error_detail = e.response.text or error_detail

        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"代理生成 Kubespray inventory 失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理請求失敗: {str(e)}"
        )


@router.get("/kubespray/info", response_model=KubesprayRootResponse)
async def kubespray_info():
    """
    Kubespray API 基本資訊
    代理到: GET /
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{KUBESPRAY_API_URL}/")
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error(f"無法連接到 Kubespray API Server: {KUBESPRAY_API_URL}")
        raise HTTPException(
            status_code=503,
            detail="Kubespray API Server 無法連接"
        )
    except httpx.TimeoutException:
        logger.error(f"取得 Kubespray 資訊逾時")
        raise HTTPException(
            status_code=504,
            detail="取得 Kubespray 資訊逾時"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"取得 Kubespray 資訊失敗: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"取得 Kubespray 資訊失敗: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"代理取得 Kubespray 資訊失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理請求失敗: {str(e)}"
        )


@router.post("/vm-configs/{config_id}/test-connection", response_model=VMConnectionTestResult)
async def test_vm_connection_proxy(config_id: str):
    """
    VM 連線測試代理
    代理到: POST /vm-configs/{config_id}/test-connection
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{KUBESPRAY_API_URL}/vm-configs/{config_id}/test-connection"
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error(f"無法連接到 Kubespray API Server: {KUBESPRAY_API_URL}")
        raise HTTPException(
            status_code=503,
            detail="Kubespray API Server 無法連接"
        )
    except httpx.TimeoutException:
        logger.error(f"VM 連線測試逾時")
        raise HTTPException(
            status_code=504,
            detail="VM 連線測試逾時"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"VM 連線測試失敗: {e.response.status_code}")
        error_detail = "VM 連線測試失敗"
        try:
            error_data = e.response.json()
            if "detail" in error_data:
                error_detail = error_data["detail"]
        except:
            error_detail = e.response.text or error_detail

        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"代理 VM 連線測試失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理請求失敗: {str(e)}"
        )


# ============================================================================
# 部署相關端點 (根據 kubespray-deployment-design.md)
# ============================================================================

@router.post(
    "/exam-sessions/{session_id}/kubespray/deploy",
    response_model=DeploymentResponse
)
async def start_kubespray_deployment(
    session_id: str,
    request: DeployRequest
):
    """
    啟動 Kubespray 部署
    代理到: POST /exam-sessions/{session_id}/kubespray/deploy
    """
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{KUBESPRAY_API_URL}/exam-sessions/{session_id}/kubespray/deploy",
                json=request.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error(f"無法連接到 Kubespray API Server: {KUBESPRAY_API_URL}")
        raise HTTPException(
            status_code=503,
            detail="Kubespray API Server 無法連接"
        )
    except httpx.TimeoutException:
        logger.error(f"啟動 Kubespray 部署逾時")
        raise HTTPException(
            status_code=504,
            detail="啟動 Kubespray 部署逾時"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"啟動 Kubespray 部署失敗: {e.response.status_code}")
        error_detail = "啟動 Kubespray 部署失敗"
        try:
            error_data = e.response.json()
            if "detail" in error_data:
                error_detail = error_data["detail"]
        except:
            error_detail = e.response.text or error_detail

        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"代理啟動 Kubespray 部署失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理請求失敗: {str(e)}"
        )


@router.websocket("/exam-sessions/{session_id}/kubespray/deploy/logs/ws")
async def websocket_deployment_logs_proxy(websocket: WebSocket, session_id: str):
    """
    即時部署 Log WebSocket 代理
    直接代理到 Kubespray API 的 WebSocket 端點
    """
    await websocket.accept()
    
    try:
        # 建立到 Kubespray API 的 WebSocket 連線
        import websockets
        
        kubespray_ws_url = f"ws://k8s-exam-kubespray-api:8080/exam-sessions/{session_id}/kubespray/deploy/logs/ws"
        
        logger.info(f"正在建立 WebSocket 代理連線: {kubespray_ws_url}")
        
        async with websockets.connect(kubespray_ws_url) as kubespray_ws:
            logger.info(f"WebSocket 代理連線建立成功 - Session: {session_id}")
            
            # 創建雙向代理任務
            async def client_to_server():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await kubespray_ws.send(data)
                except WebSocketDisconnect:
                    logger.info(f"客戶端 WebSocket 斷開 - Session: {session_id}")
                except Exception as e:
                    logger.error(f"客戶端到伺服器代理錯誤: {e}")
            
            async def server_to_client():
                try:
                    async for message in kubespray_ws:
                        await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"伺服器到客戶端代理錯誤: {e}")
            
            # 並行執行雙向代理
            await asyncio.gather(
                client_to_server(),
                server_to_client(),
                return_exceptions=True
            )
                
    except Exception as e:
        logger.error(f"WebSocket 代理錯誤: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "session_id": session_id,
                "message": f"代理連線失敗: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }))
        except:
            pass
    finally:
        logger.info(f"WebSocket 代理連線關閉 - Session: {session_id}")





@router.get(
    "/exam-sessions/{session_id}/kubespray/deploy/status",
    response_model=DeploymentStatusResponse
)
async def get_deployment_status(session_id: str):
    """
    查詢部署狀態
    代理到: GET /exam-sessions/{session_id}/kubespray/deploy/status
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{KUBESPRAY_API_URL}/exam-sessions/{session_id}/kubespray/deploy/status"
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.error(f"無法連接到 Kubespray API Server: {KUBESPRAY_API_URL}")
        raise HTTPException(
            status_code=503,
            detail="Kubespray API Server 無法連接"
        )
    except httpx.TimeoutException:
        logger.error(f"查詢部署狀態逾時")
        raise HTTPException(
            status_code=504,
            detail="查詢部署狀態逾時"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"查詢部署狀態失敗: {e.response.status_code}")
        error_detail = "查詢部署狀態失敗"
        try:
            error_data = e.response.json()
            if "detail" in error_data:
                error_detail = error_data["detail"]
        except:
            error_detail = e.response.text or error_detail

        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"代理查詢部署狀態失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理請求失敗: {str(e)}"
        )