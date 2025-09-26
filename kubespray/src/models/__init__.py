"""模型套件初始化"""

from .schemas import (
    ExamType,
    SessionStatus, 
    EnvironmentStatus,
    VMNode,
    SSHConfig,
    VMClusterConfig,
    GenerateInventoryRequest,
    GenerateInventoryResponse,
    HealthCheckResponse
)

__all__ = [
    "ExamType",
    "SessionStatus", 
    "EnvironmentStatus",
    "VMNode",
    "SSHConfig", 
    "VMClusterConfig",
    "GenerateInventoryRequest",
    "GenerateInventoryResponse",
    "HealthCheckResponse"
]