#!/usr/bin/env python3

"""
T108: 記憶體使用量最佳化
監控和最佳化系統記憶體使用
"""

import asyncio
import psutil
import json
from typing import Dict, List, Any
import logging
from datetime import datetime
import gc

class MemoryOptimizer:
    """記憶體最佳化器"""

    def __init__(self):
        self.memory_threshold = 80  # 記憶體使用率警告閾值
        self.cleanup_threshold = 90  # 自動清理閾值

    async def monitor_memory_usage(self) -> Dict[str, Any]:
        """監控記憶體使用情況"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "timestamp": datetime.now().isoformat(),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percentage": memory.percent,
                "free": memory.free
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percentage": swap.percent
            }
        }

    async def optimize_application_memory(self):
        """最佳化應用程式記憶體使用"""
        # 強制垃圾回收
        gc.collect()

        # 清理 Python 快取
        import sys
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()

    def get_memory_recommendations(self, usage: Dict[str, Any]) -> List[str]:
        """取得記憶體最佳化建議"""
        recommendations = []

        memory_percent = usage["memory"]["percentage"]

        if memory_percent > 90:
            recommendations.append("記憶體使用率過高，建議重啟服務")
            recommendations.append("檢查記憶體洩漏")
        elif memory_percent > 80:
            recommendations.append("記憶體使用率偏高，建議最佳化")
            recommendations.append("清理不必要的快取")

        return recommendations

# FastAPI 記憶體最佳化中介軟體
from fastapi import Request, Response
import time

class MemoryOptimizationMiddleware:
    """記憶體最佳化中介軟體"""

    def __init__(self):
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5分鐘清理一次

    async def __call__(self, request: Request, call_next):
        # 檢查是否需要記憶體清理
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                gc.collect()
                self.last_cleanup = current_time

        response = await call_next(request)
        return response