"""
T022: VMClusterConfig 模型
VM 叢集配置資料模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator, model_validator
from ..database.connection import Base


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

class VMNode(BaseModel):
    """VM 節點配置"""
    name: str = Field(..., description="節點名稱")
    ip: str = Field(..., description="IP 位址")
    role: str = Field(..., description="節點角色 (master/worker)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['master', 'worker']:
            raise ValueError('角色必須是 master 或 worker')
        return v


class SSHConfig(BaseModel):
    """SSH 連線配置"""
    user: str = Field(..., description="SSH 使用者名稱")
    port: int = Field(22, description="SSH 埠號")
    private_key_path: str = Field(default="/root/.ssh/id_rsa", description="SSH 私鑰路徑")


class VMClusterConfigBase(BaseModel):
    """VM 叢集配置基礎模型"""
    name: str = Field(..., description="叢集名稱")
    description: Optional[str] = Field(None, description="叢集描述")
    nodes: List[VMNode] = Field(..., min_items=2, max_items=2, description="節點列表(固定2個:1 master + 1 worker)")
    ssh_config: SSHConfig = Field(..., description="SSH 配置")

    @model_validator(mode='after')
    def validate_nodes(self):
        """驗證必須有1個master和1個worker節點"""
        roles = [node.role for node in self.nodes]
        master_count = roles.count('master')
        worker_count = roles.count('worker')

        if master_count != 1:
            raise ValueError(f'必須恰好有1個master節點，當前有{master_count}個')
        if worker_count != 1:
            raise ValueError(f'必須恰好有1個worker節點，當前有{worker_count}個')

        return self


class CreateVMConfigRequest(VMClusterConfigBase):
    """建立 VM 配置請求模型"""
    id: Optional[str] = Field(None, description="配置 ID，若未提供則自動生成")


class UpdateVMConfigRequest(BaseModel):
    """更新 VM 配置請求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[VMNode]] = Field(None, min_items=2, max_items=2, description="節點列表(固定2個:1 master + 1 worker)")
    ssh_config: Optional[SSHConfig] = None

    @model_validator(mode='after')
    def validate_nodes(self):
        """驗證必須有1個master和1個worker節點"""
        if self.nodes is not None:
            roles = [node.role for node in self.nodes]
            master_count = roles.count('master')
            worker_count = roles.count('worker')

            if master_count != 1:
                raise ValueError(f'必須恰好有1個master節點，當前有{master_count}個')
            if worker_count != 1:
                raise ValueError(f'必須恰好有1個worker節點，當前有{worker_count}個')

        return self


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
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            is_active=db_model.is_active == "true",
            last_tested_at=db_model.last_tested_at,
            test_result=test_result
        )