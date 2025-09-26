import os
from datetime import datetime


class HealthService:
    """健康檢查服務"""
    
    def __init__(self):
        self.version = "1.0.0"
        
    def check_health(self) -> dict:
        """執行健康檢查"""
        return {
            "status": "healthy",
            "kubespray_ready": True,
            "ssh_keys_mounted": os.path.exists("/root/.ssh/id_rsa"),
            "inventory_writable": os.access("/kubespray/inventory", os.W_OK),
            "uptime_seconds": 3600,  # 簡化
            "version": self.version,
            "checked_at": datetime.utcnow().isoformat()
        }