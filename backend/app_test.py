#!/usr/bin/env python3
"""
簡化的 FastAPI 測試應用程式
用於驗證基本系統功能
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import os
from datetime import datetime

# 建立 FastAPI 應用
app = FastAPI(
    title="DW-CK Test API",
    description="Kubernetes 考試模擬器測試 API",
    version="1.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 連接
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    redis_connected = True
except Exception as e:
    print(f"Redis 連接失敗: {e}")
    redis_connected = False

@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "DW-CK Test API is running",
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "ok",
            "redis": "ok" if redis_connected else "error"
        }
    }

    # 測試 Redis 連接
    if redis_connected:
        try:
            redis_client.ping()
            health_status["services"]["redis"] = "ok"
        except Exception:
            health_status["services"]["redis"] = "error"
            health_status["status"] = "degraded"

    return health_status

@app.get("/api/v1/health")
async def api_health():
    """API 健康檢查（完整路徑）"""
    return await health_check()

@app.get("/api/v1/test")
async def test_endpoint():
    """測試端點"""
    return {
        "message": "Test endpoint working",
        "data": {
            "environment": os.getenv("ENVIRONMENT", "test"),
            "redis_connected": redis_connected
        }
    }

@app.post("/api/v1/test")
async def test_post():
    """測試 POST 端點"""
    return {
        "message": "POST endpoint working",
        "method": "POST"
    }

@app.get("/api/v1/vm-configs")
async def list_vm_configs():
    """模擬 VM 配置列表"""
    return {
        "configs": [
            {
                "id": "test-config-1",
                "name": "測試配置 1",
                "description": "用於測試的 VM 配置",
                "status": "active"
            }
        ],
        "total": 1
    }

@app.get("/api/v1/question-sets")
async def list_question_sets():
    """模擬題組列表"""
    return {
        "question_sets": [
            {
                "id": "cka/test-001",
                "title": "CKA 測試題組",
                "description": "用於測試的 CKA 題組",
                "exam_type": "cka",
                "question_count": 5
            },
            {
                "id": "ckad/test-001",
                "title": "CKAD 測試題組",
                "description": "用於測試的 CKAD 題組",
                "exam_type": "ckad",
                "question_count": 8
            }
        ],
        "total": 2
    }

@app.post("/api/v1/question-sets/reload")
async def reload_question_sets():
    """模擬題組重載"""
    return {
        "message": "Question sets reloaded successfully",
        "timestamp": datetime.now().isoformat(),
        "loaded_count": 2
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )