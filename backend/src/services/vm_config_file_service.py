"""
T066: VM 配置檔案管理服務
處理 VM 配置檔案的讀取、驗證和管理
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..models.vm_cluster_config import VMClusterConfig, VMClusterConfigCreate

logger = logging.getLogger(__name__)


class VMConfigFileService:
    """VM 配置檔案管理服務"""

    def __init__(self, base_dir: str = "data/vm_configs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def list_config_files(self) -> List[Dict[str, Any]]:
        """列出所有配置檔案"""
        config_files = []

        if not self.base_dir.exists():
            return config_files

        # 掃描 JSON 和 YAML 檔案
        for ext in ["*.json", "*.yaml", "*.yml"]:
            for config_file in self.base_dir.glob(ext):
                if config_file.is_file():
                    try:
                        file_info = {
                            "filename": config_file.name,
                            "path": str(config_file),
                            "size": config_file.stat().st_size,
                            "modified_at": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat(),
                            "extension": config_file.suffix.lower()
                        }

                        # 嘗試讀取檔案內容以驗證格式
                        try:
                            content = self._read_config_file(config_file)
                            file_info["valid"] = True
                            file_info["config_name"] = content.get("name", config_file.stem)
                            file_info["node_count"] = len(content.get("nodes", []))
                        except Exception as e:
                            file_info["valid"] = False
                            file_info["error"] = str(e)

                        config_files.append(file_info)

                    except Exception as e:
                        logger.error(f"無法讀取檔案資訊 {config_file}: {e}")

        return sorted(config_files, key=lambda x: x["filename"])

    def read_config_file(self, filename: str) -> Dict[str, Any]:
        """讀取配置檔案"""
        config_path = self.base_dir / filename

        if not config_path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {filename}")

        try:
            return self._read_config_file(config_path)
        except Exception as e:
            raise ValueError(f"讀取配置檔案失敗: {str(e)}")

    def _read_config_file(self, config_path: Path) -> Dict[str, Any]:
        """內部方法：讀取配置檔案"""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                return json.load(f)
            else:  # YAML
                return yaml.safe_load(f)

    def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證配置檔案格式"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 必需欄位檢查
        required_fields = ["name", "description", "nodes"]
        for field in required_fields:
            if field not in config_data:
                validation_result["errors"].append(f"缺少必需欄位: {field}")

        # 節點配置檢查
        if "nodes" in config_data:
            nodes = config_data["nodes"]
            if not isinstance(nodes, list) or len(nodes) == 0:
                validation_result["errors"].append("至少需要一個節點配置")
            else:
                for i, node in enumerate(nodes):
                    node_errors = self._validate_node_config(node, i)
                    validation_result["errors"].extend(node_errors)

        # SSH 配置檢查
        if "ssh_config" in config_data:
            ssh_errors = self._validate_ssh_config(config_data["ssh_config"])
            validation_result["errors"].extend(ssh_errors)

        validation_result["valid"] = len(validation_result["errors"]) == 0
        return validation_result

    def _validate_node_config(self, node: Dict[str, Any], index: int) -> List[str]:
        """驗證節點配置"""
        errors = []
        required_node_fields = ["name", "ip", "role"]

        for field in required_node_fields:
            if field not in node:
                errors.append(f"節點 {index}: 缺少必需欄位 '{field}'")

        # IP 地址格式簡單檢查
        if "ip" in node:
            ip = node["ip"]
            if not isinstance(ip, str) or not self._is_valid_ip_format(ip):
                errors.append(f"節點 {index}: IP 地址格式無效: {ip}")

        # 角色檢查
        if "role" in node:
            valid_roles = ["master", "worker", "etcd"]
            if node["role"] not in valid_roles:
                errors.append(f"節點 {index}: 無效的角色 '{node['role']}'，有效值: {valid_roles}")

        return errors

    def _validate_ssh_config(self, ssh_config: Dict[str, Any]) -> List[str]:
        """驗證 SSH 配置"""
        errors = []
        required_ssh_fields = ["username"]

        for field in required_ssh_fields:
            if field not in ssh_config:
                errors.append(f"SSH 配置: 缺少必需欄位 '{field}'")

        return errors

    def _is_valid_ip_format(self, ip: str) -> bool:
        """簡單的 IP 地址格式檢查"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False

        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False

    def save_config_file(self, filename: str, config_data: Dict[str, Any], format: str = "json") -> Dict[str, Any]:
        """儲存配置檔案"""
        # 驗證配置
        validation = self.validate_config(config_data)
        if not validation["valid"]:
            raise ValueError(f"配置檔案驗證失敗: {', '.join(validation['errors'])}")

        # 確定檔案路徑
        if format.lower() == "yaml":
            if not filename.endswith(('.yaml', '.yml')):
                filename += '.yaml'
        else:
            if not filename.endswith('.json'):
                filename += '.json'

        config_path = self.base_dir / filename

        try:
            # 備份現有檔案
            if config_path.exists():
                backup_path = config_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
                config_path.rename(backup_path)
                logger.info(f"現有配置檔案已備份到: {backup_path}")

            # 寫入新檔案
            with open(config_path, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"配置檔案已儲存: {config_path}")

            return {
                "filename": filename,
                "path": str(config_path),
                "format": format,
                "saved_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"儲存配置檔案失敗: {e}")
            raise RuntimeError(f"儲存配置檔案失敗: {str(e)}")

    def delete_config_file(self, filename: str) -> Dict[str, Any]:
        """刪除配置檔案"""
        config_path = self.base_dir / filename

        if not config_path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {filename}")

        try:
            # 建立備份
            backup_path = config_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.deleted")
            config_path.rename(backup_path)

            logger.info(f"配置檔案已刪除並備份到: {backup_path}")

            return {
                "filename": filename,
                "deleted_at": datetime.utcnow().isoformat(),
                "backup_path": str(backup_path)
            }

        except Exception as e:
            logger.error(f"刪除配置檔案失敗: {e}")
            raise RuntimeError(f"刪除配置檔案失敗: {str(e)}")

    def get_file_stats(self) -> Dict[str, Any]:
        """取得檔案統計資訊"""
        config_files = self.list_config_files()

        stats = {
            "total_files": len(config_files),
            "valid_files": len([f for f in config_files if f.get("valid", False)]),
            "invalid_files": len([f for f in config_files if not f.get("valid", True)]),
            "total_nodes": sum(f.get("node_count", 0) for f in config_files if f.get("valid", False)),
            "file_formats": {},
            "last_updated": datetime.utcnow().isoformat()
        }

        # 統計檔案格式
        for config_file in config_files:
            ext = config_file["extension"]
            stats["file_formats"][ext] = stats["file_formats"].get(ext, 0) + 1

        return stats


# 全域 VM 配置檔案服務實例
vm_config_file_service = VMConfigFileService()


def get_vm_config_file_service() -> VMConfigFileService:
    """取得 VM 配置檔案服務依賴注入"""
    return vm_config_file_service