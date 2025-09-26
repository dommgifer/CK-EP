#!/usr/bin/env python3
"""
Kubespray API Server
為 Kubernetes 考試模擬器提供 Kubespray 配置生成和部署服務
"""

import os
import yaml
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kubespray API Server",
    description="Kubernetes 考試環境 Kubespray 配置和部署服務",
    version="1.0.0"
)

# 配置路徑
INVENTORY_BASE_PATH = "/kubespray/inventory"
TEMPLATES_PATH = "/kubespray/templates"
QUESTION_SETS_PATH = "/kubespray/question_sets"

class VMNode(BaseModel):
    name: str
    ip: str
    role: str  # master, worker

class SSHConfig(BaseModel):
    user: str = "root"
    port: int = 22

class VMConfig(BaseModel):
    nodes: List[VMNode]
    ssh_config: SSHConfig = SSHConfig()

class GenerateInventoryRequest(BaseModel):
    session_id: str
    vm_config: VMConfig
    question_set_id: Optional[str] = None

class GenerateInventoryResponse(BaseModel):
    session_id: str
    inventory_path: str
    generated_files: List[str]
    generated_at: str

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "kubespray_ready": True,
        "ssh_keys_mounted": os.path.exists("/root/.ssh/id_rsa"),
        "inventory_writable": os.access(INVENTORY_BASE_PATH, os.W_OK),
        "uptime_seconds": 3600,  # 簡化
        "version": "1.0.0",
        "checked_at": datetime.utcnow().isoformat()
    }

@app.post("/exam-sessions/{session_id}/kubespray/inventory", response_model=GenerateInventoryResponse)
async def generate_inventory(
    session_id: str,
    request: GenerateInventoryRequest
):
    """
    為考試會話生成 Kubespray inventory 配置
    """
    try:
        logger.info(f"開始為會話 {session_id} 生成 kubespray 配置")

        # 建立會話配置目錄
        session_dir = Path(INVENTORY_BASE_PATH) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        group_vars_all_dir = session_dir / "group_vars" / "all"
        group_vars_k8s_dir = session_dir / "group_vars" / "k8s_cluster"
        group_vars_all_dir.mkdir(parents=True, exist_ok=True)
        group_vars_k8s_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # 1. 生成 inventory.ini
        inventory_content = _generate_inventory_ini(request.vm_config)
        inventory_path = session_dir / "inventory.ini"
        with open(inventory_path, 'w', encoding='utf-8') as f:
            f.write(inventory_content)
        generated_files.append(str(inventory_path))

        # 2. 生成 group_vars/all/all.yml
        all_config = _generate_all_config(request.vm_config.ssh_config)
        all_config_path = group_vars_all_dir / "all.yml"
        with open(all_config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(all_config, f, default_flow_style=False)
        generated_files.append(str(all_config_path))

        # 3. 複製 etcd 配置
        etcd_template_path = Path(QUESTION_SETS_PATH) / "templates" / "all" / "etcd.yml"
        if etcd_template_path.exists():
            etcd_target_path = group_vars_all_dir / "etcd.yml"
            shutil.copy2(etcd_template_path, etcd_target_path)
            generated_files.append(str(etcd_target_path))

        # 4. 生成 k8s-cluster.yml (基礎範本 + 題組覆蓋)
        k8s_cluster_config = await _generate_k8s_cluster_config(request.question_set_id)
        k8s_cluster_path = group_vars_k8s_dir / "k8s-cluster.yml"
        with open(k8s_cluster_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(k8s_cluster_config, f, default_flow_style=False)
        generated_files.append(str(k8s_cluster_path))

        # 5. 複製 addons.yml
        addons_template_path = Path(QUESTION_SETS_PATH) / "templates" / "addons.yml"
        if addons_template_path.exists():
            addons_target_path = group_vars_k8s_dir / "addons.yml"
            shutil.copy2(addons_template_path, addons_target_path)
            generated_files.append(str(addons_target_path))

        # 6. 複製題組特定的網路配置
        if request.question_set_id:
            await _copy_network_configs(group_vars_k8s_dir, request.question_set_id, generated_files)

        logger.info(f"成功為會話 {session_id} 生成配置，共 {len(generated_files)} 個檔案")

        return GenerateInventoryResponse(
            session_id=session_id,
            inventory_path=str(session_dir),
            generated_files=[str(Path(f).relative_to(INVENTORY_BASE_PATH)) for f in generated_files],
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"生成配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"生成 kubespray 配置失敗: {str(e)}")

def _generate_inventory_ini(vm_config: VMConfig) -> str:
    """生成 Ansible inventory.ini 內容"""
    lines = [
        "# Kubespray inventory file",
        f"# Generated at: {datetime.utcnow().isoformat()}",
        "",
        "[all]"
    ]

    # 添加所有節點
    for node in vm_config.nodes:
        node_line = f"{node.name} ansible_host={node.ip} ip={node.ip}"
        lines.append(node_line)

    lines.extend(["", "[kube_control_plane]"])
    # 添加 master 節點
    for node in vm_config.nodes:
        if node.role == "master":
            lines.append(node.name)

    lines.extend(["", "[etcd]"])
    # 添加 etcd 節點（通常是 master）
    for node in vm_config.nodes:
        if node.role == "master":
            lines.append(node.name)

    lines.extend(["", "[kube_node]"])
    # 添加所有節點作為 kube_node
    for node in vm_config.nodes:
        lines.append(node.name)

    lines.extend([
        "",
        "[calico_rr]",
        "# 通常空的，除非題組特別需要 Route Reflector",
        "",
        "[k8s_cluster:children]",
        "kube_control_plane",
        "kube_node",
        "calico_rr"
    ])

    return "\n".join(lines)

def _generate_all_config(ssh_config: SSHConfig) -> Dict[str, Any]:
    """生成 group_vars/all/all.yml 配置"""
    return {
        "ansible_user": ssh_config.user,
        "ansible_ssh_private_key_file": "/root/.ssh/id_rsa",
        "bootstrap_os": "ubuntu",
        "ansible_ssh_port": ssh_config.port,
        "ansible_ssh_common_args": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    }

async def _generate_k8s_cluster_config(question_set_id: Optional[str] = None) -> Dict[str, Any]:
    """生成 k8s-cluster.yml 配置（基礎範本 + 題組覆蓋）"""
    # 載入基礎範本
    base_template_path = Path(QUESTION_SETS_PATH) / "templates" / "base.yml"
    base_config = {}

    if base_template_path.exists():
        with open(base_template_path, 'r', encoding='utf-8') as f:
            base_config = yaml.safe_load(f) or {}
        logger.info(f"載入基礎範本: {base_template_path}")
    else:
        logger.warning(f"基礎範本不存在: {base_template_path}")

    # 如果有題組 ID，載入覆蓋配置
    if question_set_id:
        # 解析題組路徑，例如 "cks/001" -> Path("cks/001")
        question_set_parts = question_set_id.strip('/').split('/')
        if len(question_set_parts) >= 2:
            exam_type, set_id = question_set_parts[0], question_set_parts[1]
            overwrite_path = Path(QUESTION_SETS_PATH) / exam_type / set_id / "base-overwrite.yml"

            if overwrite_path.exists():
                with open(overwrite_path, 'r', encoding='utf-8') as f:
                    overwrite_config = yaml.safe_load(f) or {}

                # 深度合併配置
                merged_config = _deep_merge(base_config, overwrite_config)
                logger.info(f"應用題組覆蓋配置: {overwrite_path}")
                return merged_config
            else:
                logger.warning(f"題組覆蓋配置不存在: {overwrite_path}")

    return base_config

async def _copy_network_configs(target_dir: Path, question_set_id: str, generated_files: List[str]) -> None:
    """複製題組特定的網路配置檔案"""
    try:
        question_set_parts = question_set_id.strip('/').split('/')
        if len(question_set_parts) >= 2:
            exam_type, set_id = question_set_parts[0], question_set_parts[1]
            network_dir = Path(QUESTION_SETS_PATH) / exam_type / set_id / "network"

            if network_dir.exists() and network_dir.is_dir():
                for config_file in network_dir.glob("*.yml"):
                    target_path = target_dir / config_file.name
                    shutil.copy2(config_file, target_path)
                    generated_files.append(str(target_path))
                    logger.info(f"已複製網路配置: {config_file.name}")
            else:
                logger.info(f"題組沒有網路配置目錄: {network_dir}")
    except Exception as e:
        logger.error(f"複製網路配置失敗: {e}")

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """深度合併兩個字典"""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)