"""
Kubespray 部署 API
根據 kubespray-deployment-design.md 實作

核心功能：
1. 啟動部署 (POST /exam-sessions/{session_id}/kubespray/deploy)
2. SSE log 流 (GET /exam-sessions/{session_id}/kubespray/deploy/logs/stream)
3. 部署狀態查詢 (GET /exam-sessions/{session_id}/kubespray/deploy/status)
"""
import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as redis

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis 客戶端 (用於 pub/sub 和狀態儲存)
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# 全域變量：當前部署 (系統限制只有一個)
current_deployment_session: Optional[str] = None
current_deployment_process: Optional[asyncio.subprocess.Process] = None


# ============================================================================
# 請求和回應模型
# ============================================================================

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
    status: str  # pending, started, running, completed, failed
    playbook: str
    started_at: str
    completed_at: Optional[str] = None
    exit_code: Optional[int] = None


# ============================================================================
# API 端點實作
# ============================================================================

@router.post("/exam-sessions/{session_id}/kubespray/deploy", response_model=DeploymentResponse)
async def start_deployment(session_id: str, request: DeployRequest):
    """啟動 Kubespray 部署"""
    global current_deployment_session, current_deployment_process

    logger.info(f"收到部署請求 - Session: {session_id}, Playbook: {request.playbook}")

    # 1. 驗證 inventory 存在
    inventory_path = f"/kubespray/inventory/{session_id}"
    if not os.path.exists(f"{inventory_path}/inventory.ini"):
        logger.error(f"Inventory 配置不存在: {inventory_path}/inventory.ini")
        raise HTTPException(404, "Inventory 配置不存在，請先生成配置")

    # 2. 檢查是否已有運行中的部署
    if current_deployment_session:
        logger.warning(f"已有部署正在進行中: {current_deployment_session}")
        raise HTTPException(409, f"已有部署正在進行中 (session: {current_deployment_session})")

    # 3. 設定當前部署會話
    current_deployment_session = session_id

    # 4. 初始化狀態
    started_at = datetime.utcnow().isoformat()
    await _set_deployment_status(session_id, {
        "session_id": session_id,
        "status": "started",
        "playbook": request.playbook,
        "started_at": started_at,
        "completed_at": None,
        "exit_code": None
    })

    # 5. 在背景啟動部署
    asyncio.create_task(_execute_deployment(session_id, request))

    logger.info(f"部署已啟動 - Session: {session_id}")

    return DeploymentResponse(
        session_id=session_id,
        status="started",
        playbook=request.playbook,
        log_stream_url=f"/exam-sessions/{session_id}/kubespray/deploy/logs/stream",
        started_at=started_at
    )


@router.get("/exam-sessions/{session_id}/kubespray/deploy/logs/stream")
async def stream_deployment_logs(session_id: str):
    """SSE 端點，提供即時 log 流"""

    async def event_generator():
        try:
            logger.info(f"開始 SSE 流 - Session: {session_id}")

            # 發送初始連線確認訊息
            yield f"event: connected\ndata: {json.dumps({'session_id': session_id, 'status': 'connected'})}\n\n"

            # 監聽即時 logs
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"session:{session_id}:deploy:logs")

            async for message in pubsub.listen():
                # 跳過訂閱確認訊息
                if message['type'] == 'subscribe':
                    continue
                elif message['type'] == 'message':
                    try:
                        event_data = json.loads(message['data'])
                        event_type = event_data.get('event_type', 'log')
                        data_payload = json.dumps(event_data['data'])

                        yield f"event: {event_type}\ndata: {data_payload}\n\n"

                        # 如果是完成或失敗事件，結束流
                        if event_type == 'status' and event_data['data'].get('status') in ['completed', 'failed']:
                            logger.info(f"部署結束，關閉 SSE 流 - Session: {session_id}")
                            break

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"SSE 訊息解析錯誤: {e}")
                        continue

        except asyncio.CancelledError:
            logger.info(f"SSE 流被取消 - Session: {session_id}")
        except Exception as e:
            logger.error(f"SSE 流錯誤: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
            except:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 緩衝
        }
    )


@router.get("/exam-sessions/{session_id}/kubespray/deploy/status", response_model=DeploymentStatusResponse)
async def get_deployment_status(session_id: str):
    """查詢部署狀態"""
    status_json = await redis_client.get(f"session:{session_id}:deploy:status")

    if not status_json:
        raise HTTPException(404, "部署記錄不存在")

    try:
        status_data = json.loads(status_json)
        return DeploymentStatusResponse(**status_data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"狀態資料解析錯誤: {e}")
        raise HTTPException(500, "狀態資料格式錯誤")


# ============================================================================
# 核心部署執行邏輯
# ============================================================================

async def _execute_deployment(session_id: str, request: DeployRequest):
    """執行 Ansible 部署並流式傳輸 log"""
    global current_deployment_session, current_deployment_process

    try:
        logger.info(f"開始執行部署 - Session: {session_id}")

        # 1. 準備 Ansible 命令 (切換到 kubespray 目錄並使用相對路徑)
        ansible_cmd = [
            "ansible-playbook",
            "-i", f"inventory/{session_id}/inventory.ini",
            request.playbook,  # cluster.yml (相對路徑)
            "-b",  # --become (官方使用 -b)
            "--private-key", "/root/.ssh/id_rsa",
            "-v"  # verbose output
        ]

        logger.info(f"Ansible 命令: {' '.join(ansible_cmd)}")

        # 2. 更新狀態為運行中
        await _update_deployment_status(session_id, "running")

        # 3. 啟動 Ansible 子程序
        process = await asyncio.create_subprocess_exec(
            *ansible_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # 合併 stderr 到 stdout
            cwd="/kubespray",
            env={**os.environ, "ANSIBLE_HOST_KEY_CHECKING": "False"}
        )

        # 4. 記錄當前部署進程
        current_deployment_process = process

        # 5. 即時處理輸出
        await _stream_ansible_output(session_id, process)

        # 6. 等待完成並處理結果
        exit_code = await process.wait()

        final_status = "completed" if exit_code == 0 else "failed"
        await _update_deployment_status(session_id, final_status, exit_code)

        # 7. 發送完成事件
        await _send_log_event(session_id, "status", {
            "status": final_status,
            "session_id": session_id,
            "exit_code": exit_code,
            "completed_at": datetime.utcnow().isoformat()
        })

        logger.info(f"部署完成 - Session: {session_id}, 狀態: {final_status}, 退出碼: {exit_code}")

    except Exception as e:
        logger.error(f"部署執行錯誤: {e}")
        await _update_deployment_status(session_id, "failed", -1)
        await _send_log_event(session_id, "error", {
            "session_id": session_id,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })

    finally:
        # 8. 清理全域狀態
        current_deployment_session = None
        current_deployment_process = None


async def _stream_ansible_output(session_id: str, process: asyncio.subprocess.Process):
    """即時流式傳輸 Ansible 輸出"""
    logger.info(f"開始串流 Ansible 輸出 - Session: {session_id}")

    while True:
        try:
            line = await process.stdout.readline()
            if not line:
                break

            log_line = line.decode('utf-8').rstrip()
            if not log_line:  # 跳過空行
                continue

            # 發送原始 log (不做任何解析)
            log_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "message": log_line
            }

            await _send_log_event(session_id, "log", log_event)

        except Exception as e:
            logger.error(f"讀取 Ansible 輸出錯誤: {e}")
            break

    logger.info(f"Ansible 輸出串流結束 - Session: {session_id}")


# ============================================================================
# 輔助函數
# ============================================================================

async def _send_log_event(session_id: str, event_type: str, data: dict):
    """發送 log 事件到 Redis pub/sub"""
    try:
        event_payload = {
            "event_type": event_type,
            "data": data
        }

        # 發布到即時流 (不做任何儲存)
        await redis_client.publish(
            f"session:{session_id}:deploy:logs",
            json.dumps(event_payload)
        )
    except Exception as e:
        logger.error(f"發送 log 事件失敗: {e}")


async def _set_deployment_status(session_id: str, status_data: dict):
    """設定部署狀態"""
    try:
        await redis_client.setex(
            f"session:{session_id}:deploy:status",
            3600,  # 1 小時過期
            json.dumps(status_data)
        )
    except Exception as e:
        logger.error(f"設定部署狀態失敗: {e}")


async def _update_deployment_status(session_id: str, status: str, exit_code: Optional[int] = None):
    """更新部署狀態"""
    try:
        # 取得現有狀態
        current_status = await redis_client.get(f"session:{session_id}:deploy:status")
        if current_status:
            status_data = json.loads(current_status)
            status_data["status"] = status
            if exit_code is not None:
                status_data["exit_code"] = exit_code
            if status in ["completed", "failed"]:
                status_data["completed_at"] = datetime.utcnow().isoformat()

            await _set_deployment_status(session_id, status_data)
    except Exception as e:
        logger.error(f"更新部署狀態失敗: {e}")