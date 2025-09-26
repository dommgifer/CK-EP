#!/usr/bin/env python3
"""
Kubespray API Server
為 Kubernetes 考試模擬器提供 Kubespray 配置生成和部署服務
"""

import logging
from fastapi import FastAPI

from .api import kubespray_router

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Kubespray API Server",
    description="Kubernetes 考試環境 Kubespray 配置和部署服務",
    version="1.0.0"
)

# 註冊路由
app.include_router(kubespray_router, tags=["Kubespray"])

# 根路由
@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Kubespray API Server",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)