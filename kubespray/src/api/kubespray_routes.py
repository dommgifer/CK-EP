from fastapi import APIRouter, HTTPException
from datetime import datetime
from pathlib import Path
import logging

from ..models import (
    GenerateInventoryRequest,
    GenerateInventoryResponse,
    HealthCheckResponse
)
from ..services import KubesprayInventoryService, HealthService

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter()

# 初始化服務
kubespray_service = KubesprayInventoryService()
health_service = HealthService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康檢查端點"""
    health_data = health_service.check_health()
    return HealthCheckResponse(**health_data)


@router.post(
    "/exam-sessions/{session_id}/kubespray/inventory", 
    response_model=GenerateInventoryResponse
)
async def generate_inventory(
    session_id: str,
    request: GenerateInventoryRequest
):
    """
    為考試會話生成 Kubespray inventory 配置
    """
    try:
        # 生成 inventory 配置
        inventory_path, generated_files = await kubespray_service.generate_inventory(
            session_id=session_id,
            vm_config=request.vm_config,
            question_set_id=request.question_set_id
        )

        # 轉換檔案路徑為相對路徑
        relative_files = []
        base_path = kubespray_service.inventory_base_path
        for file_path in generated_files:
            try:
                relative_path = str(Path(file_path).relative_to(base_path))
                relative_files.append(relative_path)
            except ValueError:
                # 如果無法取得相對路徑，使用原始路徑
                relative_files.append(file_path)

        return GenerateInventoryResponse(
            session_id=session_id,
            inventory_path=inventory_path,
            generated_files=relative_files,
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"生成配置失敗: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"生成 kubespray 配置失敗: {str(e)}"
        )