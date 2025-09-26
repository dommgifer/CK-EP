from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExamType(str, Enum):
    """考試類型枚舉"""
    CKA = "CKA"
    CKAD = "CKAD" 
    CKS = "CKS"


class SessionStatus(str, Enum):
    """會話狀態枚舉"""
    PREPARING = "preparing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class EnvironmentStatus(str, Enum):
    """環境狀態枚舉"""
    CONFIGURING = "configuring"
    READY = "ready"
    ERROR = "error"


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