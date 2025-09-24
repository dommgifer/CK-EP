"""
T062: SSH 金鑰管理服務
處理 SSH 金鑰的驗證和管理
"""
import os
import stat
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SSHKeyService:
    """SSH 金鑰管理服務"""

    def __init__(self, ssh_keys_dir: str = "data/ssh_keys"):
        self.ssh_keys_dir = Path(ssh_keys_dir)
        self.ssh_keys_dir.mkdir(parents=True, exist_ok=True)
        self.private_key_path = self.ssh_keys_dir / "id_rsa"
        self.public_key_path = self.ssh_keys_dir / "id_rsa.pub"

    def validate_ssh_keys(self) -> Dict[str, Any]:
        """驗證 SSH 金鑰的存在和權限"""
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "private_key_exists": False,
                "public_key_exists": False,
                "private_key_permissions": None,
                "key_info": {},
                "checked_at": datetime.utcnow().isoformat()
            }

            # 檢查私鑰存在
            if self.private_key_path.exists():
                validation_result["private_key_exists"] = True

                # 檢查私鑰權限
                key_stat = self.private_key_path.stat()
                permissions = oct(key_stat.st_mode)[-3:]
                validation_result["private_key_permissions"] = permissions

                # 建議的權限是 600 (只有擁有者可讀寫)
                if permissions != "600":
                    validation_result["warnings"].append(
                        f"私鑰權限 {permissions} 不安全，建議設為 600"
                    )

                # 嘗試讀取私鑰資訊
                try:
                    key_info = self._get_key_info(self.private_key_path)
                    validation_result["key_info"]["private"] = key_info
                except Exception as e:
                    validation_result["warnings"].append(f"無法讀取私鑰資訊: {str(e)}")

            else:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"私鑰檔案不存在: {self.private_key_path}"
                )

            # 檢查公鑰存在（可選）
            if self.public_key_path.exists():
                validation_result["public_key_exists"] = True
                try:
                    key_info = self._get_key_info(self.public_key_path)
                    validation_result["key_info"]["public"] = key_info
                except Exception as e:
                    validation_result["warnings"].append(f"無法讀取公鑰資訊: {str(e)}")
            else:
                validation_result["warnings"].append(
                    f"公鑰檔案不存在: {self.public_key_path} (可選)"
                )

            # 檢查目錄權限
            dir_stat = self.ssh_keys_dir.stat()
            dir_permissions = oct(dir_stat.st_mode)[-3:]
            if dir_permissions not in ["700", "755"]:
                validation_result["warnings"].append(
                    f"SSH 金鑰目錄權限 {dir_permissions} 可能不安全"
                )

            return validation_result

        except Exception as e:
            logger.error(f"SSH 金鑰驗證失敗: {e}")
            return {
                "valid": False,
                "errors": [f"驗證過程發生錯誤: {str(e)}"],
                "warnings": [],
                "private_key_exists": False,
                "public_key_exists": False,
                "checked_at": datetime.utcnow().isoformat()
            }

    def _get_key_info(self, key_path: Path) -> Dict[str, Any]:
        """取得 SSH 金鑰資訊"""
        key_info = {
            "file_size": key_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(key_path.stat().st_mtime).isoformat(),
            "permissions": oct(key_path.stat().st_mode)[-3:]
        }

        # 嘗試判斷金鑰類型
        try:
            with open(key_path, 'r') as f:
                first_line = f.readline().strip()

            if key_path.name.endswith('.pub'):
                # 公鑰檔案
                if first_line.startswith('ssh-rsa'):
                    key_info["type"] = "RSA"
                elif first_line.startswith('ssh-ed25519'):
                    key_info["type"] = "Ed25519"
                elif first_line.startswith('ssh-ecdsa'):
                    key_info["type"] = "ECDSA"
                else:
                    key_info["type"] = "Unknown"

                # 提取公鑰註解
                parts = first_line.split()
                if len(parts) >= 3:
                    key_info["comment"] = parts[2]

            else:
                # 私鑰檔案
                if 'BEGIN RSA PRIVATE KEY' in first_line or 'BEGIN PRIVATE KEY' in first_line:
                    key_info["type"] = "RSA" if 'RSA' in first_line else "PKCS#8"
                elif 'BEGIN OPENSSH PRIVATE KEY' in first_line:
                    key_info["type"] = "OpenSSH"
                else:
                    key_info["type"] = "Unknown"

        except Exception as e:
            key_info["read_error"] = str(e)

        return key_info

    def fix_permissions(self) -> Dict[str, Any]:
        """修正 SSH 金鑰權限"""
        try:
            fixes_applied = []
            errors = []

            # 修正私鑰權限為 600
            if self.private_key_path.exists():
                try:
                    os.chmod(self.private_key_path, stat.S_IRUSR | stat.S_IWUSR)
                    fixes_applied.append("私鑰權限已設為 600")
                except Exception as e:
                    errors.append(f"修正私鑰權限失敗: {str(e)}")

            # 修正公鑰權限為 644（如果存在）
            if self.public_key_path.exists():
                try:
                    os.chmod(self.public_key_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                    fixes_applied.append("公鑰權限已設為 644")
                except Exception as e:
                    errors.append(f"修正公鑰權限失敗: {str(e)}")

            # 修正目錄權限為 700
            try:
                os.chmod(self.ssh_keys_dir, stat.S_IRWXU)
                fixes_applied.append("SSH 金鑰目錄權限已設為 700")
            except Exception as e:
                errors.append(f"修正目錄權限失敗: {str(e)}")

            return {
                "success": len(errors) == 0,
                "fixes_applied": fixes_applied,
                "errors": errors,
                "fixed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"修正 SSH 金鑰權限失敗: {e}")
            return {
                "success": False,
                "fixes_applied": [],
                "errors": [f"修正過程發生錯誤: {str(e)}"],
                "fixed_at": datetime.utcnow().isoformat()
            }

    def get_container_key_path(self) -> str:
        """取得容器內的 SSH 金鑰路徑"""
        return "/root/.ssh/id_rsa"

    def get_host_key_path(self) -> str:
        """取得主機上的 SSH 金鑰路徑"""
        return str(self.private_key_path.absolute())

    def create_readme(self) -> Dict[str, Any]:
        """建立 SSH 金鑰使用說明"""
        readme_path = self.ssh_keys_dir / "README.md"

        readme_content = """# SSH 金鑰管理

這個目錄用於存放 Kubernetes 考試模擬器使用的 SSH 金鑰。

## 檔案說明

- `id_rsa`: SSH 私鑰檔案（必需）
- `id_rsa.pub`: SSH 公鑰檔案（可選，但建議保留）
- `README.md`: 本說明檔案

## 設定步驟

1. **準備 SSH 金鑰對**
   ```bash
   # 如果還沒有 SSH 金鑰，可以生成一對新的
   ssh-keygen -t rsa -b 4096 -f ./id_rsa -N ""
   ```

2. **複製金鑰到此目錄**
   ```bash
   # 將您的私鑰複製到這裡
   cp /path/to/your/id_rsa ./id_rsa
   cp /path/to/your/id_rsa.pub ./id_rsa.pub
   ```

3. **設定正確的權限**
   ```bash
   chmod 700 .
   chmod 600 id_rsa
   chmod 644 id_rsa.pub  # 如果存在
   ```

4. **在您的 VM 上配置公鑰**
   ```bash
   # 在每個 VM 節點上執行
   cat id_rsa.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

## 重要提醒

- **安全性**: 私鑰檔案包含敏感資訊，請確保權限設定正確
- **備份**: 建議備份您的 SSH 金鑰對
- **測試**: 在建立考試會話前，請先測試 SSH 連線是否正常

## 疑難排解

### 連線失敗
- 檢查私鑰檔案是否存在且權限為 600
- 確認公鑰已正確安裝到目標 VM
- 檢查 VM 的 SSH 服務是否啟用

### 權限問題
- 使用系統提供的權限修正功能
- 手動執行上述權限設定指令

如需更多協助，請參考系統日誌或聯繫技術支援。
"""

        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            return {
                "success": True,
                "readme_path": str(readme_path),
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"建立 README 失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "attempted_at": datetime.utcnow().isoformat()
            }

    def get_status(self) -> Dict[str, Any]:
        """取得 SSH 金鑰管理狀態"""
        validation = self.validate_ssh_keys()

        status = {
            "ssh_keys_directory": str(self.ssh_keys_dir),
            "private_key_path": str(self.private_key_path),
            "public_key_path": str(self.public_key_path),
            "container_key_path": self.get_container_key_path(),
            "validation": validation,
            "ready_for_use": validation["valid"] and validation["private_key_exists"],
            "status_checked_at": datetime.utcnow().isoformat()
        }

        return status


# 全域 SSH 金鑰服務實例
ssh_key_service = SSHKeyService()


def get_ssh_key_service() -> SSHKeyService:
    """取得 SSH 金鑰服務依賴注入"""
    return ssh_key_service