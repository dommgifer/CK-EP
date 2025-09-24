"""
T022: VMClusterConfig 模型
VM 叢集配置資料模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class VMClusterConfig(Base):
    """VM 叢集配置 SQLAlchemy 模型"""
    __tablename__ = "vm_cluster_configs"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 配置 JSON（包含節點、SSH、網路等資訊）
    config_json = Column(Text, nullable=False)

    # 元資料
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 使用狀態
    is_active = Column(String(10), default="true")  # 使用字串避免 SQLite 的 Boolean 問題
    last_tested_at = Column(DateTime, nullable=True)
    test_result_json = Column(Text, nullable=True)  # 最後一次連線測試結果

    def __repr__(self):
        return f"<VMClusterConfig(id={self.id}, name={self.name})>"


# Pydantic 模型

class VMNodeSpecs(BaseModel):
    """VM 節點規格"""
    cpu_cores: int = Field(..., ge=1, description="CPU 核心數")
    memory_gb: int = Field(..., ge=1, description="記憶體 GB")
    disk_gb: int = Field(..., ge=10, description="磁碟空間 GB")


class VMNode(BaseModel):
    """VM 節點配置"""
    name: str = Field(..., description="節點名稱")
    ip: str = Field(..., description="IP 位址")
    role: str = Field(..., description="節點角色 (master/worker)")
    specs: VMNodeSpecs = Field(..., description="硬體規格")


class SSHConfig(BaseModel):
    """SSH 連線配置"""
    user: str = Field(..., description="SSH 使用者名稱")
    port: int = Field(22, description="SSH 埠號")


class NetworkConfig(BaseModel):
    """網路配置"""
    pod_subnet: str = Field(..., description="Pod 子網路")
    service_subnet: str = Field(..., description="Service 子網路")


class VMClusterConfigBase(BaseModel):
    """VM 叢集配置基礎模型"""
    name: str = Field(..., description="叢集名稱")
    description: Optional[str] = Field(None, description="叢集描述")
    nodes: List[VMNode] = Field(..., min_items=1, description="節點列表")
    ssh_config: SSHConfig = Field(..., description="SSH 配置")
    network: NetworkConfig = Field(..., description="網路配置")


class CreateVMConfigRequest(VMClusterConfigBase):
    """建立 VM 配置請求模型"""
    id: Optional[str] = Field(None, description="配置 ID，若未提供則自動生成")


class UpdateVMConfigRequest(BaseModel):
    """更新 VM 配置請求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[VMNode]] = None
    ssh_config: Optional[SSHConfig] = None
    network: Optional[NetworkConfig] = None


class VMClusterConfigResponse(VMClusterConfigBase):
    """VM 叢集配置回應模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    last_tested_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VMConnectionTestResult(BaseModel):
    """VM 連線測試結果"""
    success: bool
    message: str
    tested_at: datetime
    nodes: List[Dict[str, Any]]  # 每個節點的測試結果
    total_nodes: int
    successful_nodes: int
    failed_nodes: int


class VMClusterConfigDetailed(VMClusterConfigResponse):
    """VM 叢集配置詳細資訊"""
    test_result: Optional[VMConnectionTestResult] = None
    usage_stats: Optional[Dict[str, Any]] = None  # 使用統計

    @classmethod
    def from_db_model(cls, db_model: VMClusterConfig):
        """從資料庫模型建立詳細回應"""
        import json

        # 解析配置 JSON
        config_data = json.loads(db_model.config_json)

        # 解析測試結果
        test_result = None
        if db_model.test_result_json:
            test_data = json.loads(db_model.test_result_json)
            test_result = VMConnectionTestResult(**test_data)

        return cls(
            id=db_model.id,
            name=db_model.name,
            description=db_model.description,
            nodes=config_data["nodes"],
            ssh_config=config_data["ssh_config"],
            network=config_data["network"],
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            is_active=db_model.is_active == "true",
            last_tested_at=db_model.last_tested_at,
            test_result=test_result
        )