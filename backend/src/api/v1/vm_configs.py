"""
T036-T041: VM 配置管理 API 端點
處理 VM 叢集配置的 CRUD 操作和連線測試
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.connection import get_database
from ...services.vm_cluster_service import VMClusterService
from ...models.vm_cluster_config import (
    VMClusterConfigResponse,
    VMClusterConfigDetailed,
    CreateVMConfigRequest,
    UpdateVMConfigRequest,
    VMConnectionTestResult
)

router = APIRouter()


def get_vm_service(db: Session = Depends(get_database)) -> VMClusterService:
    """取得 VM 叢集服務依賴注入"""
    return VMClusterService(db)


@router.get("", response_model=List[VMClusterConfigResponse])
async def list_vm_configs(
    vm_service: VMClusterService = Depends(get_vm_service)
):
    """
    T036: GET /api/v1/vm-configs 端點
    取得所有 VM 配置列表
    """
    try:
        configs = await vm_service.list_vm_configs()
        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得 VM 配置列表失敗: {str(e)}"
        )


@router.post("", response_model=VMClusterConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_vm_config(
    config_request: CreateVMConfigRequest,
    vm_service: VMClusterService = Depends(get_vm_service)
):
    """
    T037: POST /api/v1/vm-configs 端點
    建立新的 VM 配置
    """
    try:
        config = await vm_service.create_vm_config(config_request)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立 VM 配置失敗: {str(e)}"
        )


@router.get("/{config_id}", response_model=VMClusterConfigDetailed)
async def get_vm_config(
    config_id: str,
    vm_service: VMClusterService = Depends(get_vm_service)
):
    """
    T038: GET /api/v1/vm-configs/{config_id} 端點
    取得指定 VM 配置的詳細資訊
    """
    try:
        config = await vm_service.get_vm_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VM 配置 '{config_id}' 不存在"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得 VM 配置失敗: {str(e)}"
        )


@router.put("/{config_id}", response_model=VMClusterConfigResponse)
async def update_vm_config(
    config_id: str,
    update_request: UpdateVMConfigRequest,
    vm_service: VMClusterService = Depends(get_vm_service)
):
    """
    T039: PUT /api/v1/vm-configs/{config_id} 端點
    更新 VM 配置
    """
    try:
        config = await vm_service.update_vm_config(config_id, update_request)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VM 配置 '{config_id}' 不存在"
            )
        return config
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新 VM 配置失敗: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vm_config(
    config_id: str,
    vm_service: VMClusterService = Depends(get_vm_service)
):
    """
    T040: DELETE /api/v1/vm-configs/{config_id} 端點
    刪除 VM 配置
    """
    try:
        success = await vm_service.delete_vm_config(config_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VM 配置 '{config_id}' 不存在"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除 VM 配置失敗: {str(e)}"
        )


@router.post("/{config_id}/test-connection", response_model=VMConnectionTestResult)
async def test_vm_connection(
    config_id: str,
    vm_service: VMClusterService = Depends(get_vm_service)
):
    """
    T041: POST /api/v1/vm-configs/{config_id}/test-connection 端點
    測試 VM 配置的 SSH 連線
    """
    try:
        test_result = await vm_service.test_vm_connection(config_id)
        return test_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"測試 VM 連線失敗: {str(e)}"
        )