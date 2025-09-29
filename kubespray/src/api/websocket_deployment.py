"""
Kubespray 部署 WebSocket API
替代 SSE 實作，提供雙向通信能力
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import redis.asyncio as redis

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis 客戶端
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# 活躍的 WebSocket 連線管理
class ConnectionManager:
    """WebSocket 連線管理器"""
    
    def __init__(self):
        # session_id -> Set[WebSocket] 映射
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """建立新連線"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket 連線建立 - Session: {session_id}, 連線數: {len(self.active_connections[session_id])}")
        
        # 發送連線確認訊息
        await self.send_personal_message({
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket 連線已建立"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """斷開連線"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                
        logger.info(f"WebSocket 連線斷開 - Session: {session_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """發送訊息給特定連線"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"發送 WebSocket 訊息失敗: {e}")
    
    async def broadcast_to_session(self, message: dict, session_id: str):
        """廣播訊息給特定 session 的所有連線"""
        if session_id in self.active_connections:
            disconnected_connections = []
            
            for connection in self.active_connections[session_id].copy():
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"廣播訊息失敗: {e}")
                    disconnected_connections.append(connection)
            
            # 清理斷開的連線
            for connection in disconnected_connections:
                self.active_connections[session_id].discard(connection)


# 全域連線管理器
manager = ConnectionManager()


class WebSocketMessage(BaseModel):
    """WebSocket 訊息格式"""
    type: str  # 訊息類型: command, log, status, error
    session_id: str
    data: dict
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or not data['timestamp']:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)


@router.websocket("/exam-sessions/{session_id}/kubespray/deploy/logs/ws")
async def websocket_deployment_logs(websocket: WebSocket, session_id: str):
    """WebSocket 端點，提供雙向部署日誌通信"""
    
    await manager.connect(websocket, session_id)
    
    # 啟動 Redis 訂閱任務
    redis_task = asyncio.create_task(
        subscribe_redis_logs(session_id, websocket)
    )
    
    try:
        while True:
            # 接收來自前端的訊息
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                await handle_client_message(session_id, message_data, websocket)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "訊息格式錯誤"
                }, websocket)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket 客戶端斷開連線 - Session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket 錯誤: {e}")
    finally:
        # 清理資源
        redis_task.cancel()
        manager.disconnect(websocket, session_id)


async def subscribe_redis_logs(session_id: str, websocket: WebSocket):
    """訂閱 Redis 部署日誌並轉發到 WebSocket"""
    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"session:{session_id}:deploy:logs")
        
        async for message in pubsub.listen():
            if message['type'] == 'subscribe':
                continue
            elif message['type'] == 'message':
                try:
                    event_data = json.loads(message['data'])
                    
                    # 轉換 SSE 格式到 WebSocket 格式
                    ws_message = {
                        "type": event_data.get('event_type', 'log'),
                        "session_id": session_id,
                        "data": event_data.get('data', {}),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await manager.send_personal_message(ws_message, websocket)
                    
                    # 檢查是否為結束事件
                    if (event_data.get('event_type') == 'status' and 
                        event_data.get('data', {}).get('status') in ['completed', 'failed']):
                        logger.info(f"部署結束，關閉 WebSocket 訂閱 - Session: {session_id}")
                        break
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Redis 訊息解析錯誤: {e}")
                    continue
                    
    except asyncio.CancelledError:
        logger.info(f"Redis 訂閱被取消 - Session: {session_id}")
    except Exception as e:
        logger.error(f"Redis 訂閱錯誤: {e}")
    finally:
        try:
            await pubsub.unsubscribe()
            await pubsub.close()
        except:
            pass


async def handle_client_message(session_id: str, message_data: dict, websocket: WebSocket):
    """處理來自客戶端的訊息"""
    message_type = message_data.get('type')
    
    if message_type == 'ping':
        # 心跳檢測
        await manager.send_personal_message({
            "type": "pong",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
    elif message_type == 'get_status':
        # 查詢當前部署狀態
        try:
            status_json = await redis_client.get(f"session:{session_id}:deploy:status")
            if status_json:
                status_data = json.loads(status_json)
                await manager.send_personal_message({
                    "type": "status",
                    "session_id": session_id,
                    "data": status_data,
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "session_id": session_id,
                    "message": "部署狀態不存在",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
        except Exception as e:
            logger.error(f"查詢部署狀態錯誤: {e}")
            await manager.send_personal_message({
                "type": "error",
                "session_id": session_id,
                "message": f"查詢狀態失敗: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
    elif message_type == 'command':
        # 處理部署控制指令（擴展功能）
        command = message_data.get('command')
        await manager.send_personal_message({
            "type": "command_received",
            "session_id": session_id,
            "command": command,
            "message": f"已收到指令: {command}",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
    else:
        await manager.send_personal_message({
            "type": "error",
            "session_id": session_id,
            "message": f"未知的訊息類型: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)


# 廣播功能（供其他模組使用）
async def broadcast_deployment_update(session_id: str, message: dict):
    """廣播部署更新到該 session 的所有 WebSocket 連線"""
    await manager.broadcast_to_session(message, session_id)