"""
T100: VMClusterService 單元測試
測試 VM 叢集服務的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json
import tempfile
from pathlib import Path

import sys
sys.path.append("../../src")

from src.services.vm_cluster_service import VMClusterService
from src.models.vm_cluster_config import VMClusterConfig
from src.services.vnc_container_service import VNCContainerService
from src.services.bastion_container_service import BastionContainerService


class TestVMClusterService:
    """VMClusterService 測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫會話"""
        mock_session = Mock()
        mock_session.query.return_value = mock_session
        mock_session.filter.return_value = mock_session
        mock_session.first.return_value = None
        mock_session.all.return_value = []
        return mock_session

    @pytest.fixture
    def mock_vnc_service(self):
        """模擬 VNC 容器服務"""
        service = Mock(spec=VNCContainerService)
        service.create_vnc_container = AsyncMock()
        service.stop_vnc_container = AsyncMock()
        service.get_vnc_url = AsyncMock()
        return service

    @pytest.fixture
    def mock_bastion_service(self):
        """模擬 Bastion 容器服務"""
        service = Mock(spec=BastionContainerService)
        service.create_bastion_container = AsyncMock()
        service.stop_bastion_container = AsyncMock()
        service.execute_command = AsyncMock()
        return service

    @pytest.fixture
    def vm_cluster_service(self, mock_db_session, mock_vnc_service, mock_bastion_service):
        """VM 叢集服務實例"""
        service = VMClusterService(
            db_session=mock_db_session,
            vnc_service=mock_vnc_service,
            bastion_service=mock_bastion_service
        )
        return service

    @pytest.fixture
    def sample_vm_config(self) -> VMClusterConfig:
        """範例 VM 配置"""
        return VMClusterConfig(
            id="test-cluster-001",
            name="測試叢集",
            description="用於測試的 Kubernetes 叢集",
            nodes=[
                {
                    "name": "master-1",
                    "ip": "192.168.1.10",
                    "roles": ["master", "etcd"],
                    "specs": {"cpu": 2, "memory": "4Gi", "disk": "20Gi"}
                },
                {
                    "name": "worker-1",
                    "ip": "192.168.1.11",
                    "roles": ["worker"],
                    "specs": {"cpu": 2, "memory": "4Gi", "disk": "20Gi"}
                }
            ],
            ssh_user="ubuntu",
            created_by="test_user"
        )

    @pytest.fixture
    def sample_question_set_config(self) -> Dict[str, Any]:
        """範例題組配置"""
        return {
            "kubernetes_version": "v1.29.1",
            "network_plugin": "calico",
            "base_overwrite": {
                "kube_version": "v1.29.1",
                "calico_version": "v3.27.0"
            },
            "addons_overwrite": {
                "metrics_server_enabled": True,
                "ingress_nginx_enabled": True
            }
        }

    async def test_setup_kubernetes_cluster_success(self, vm_cluster_service, mock_db_session,
                                                   sample_vm_config, sample_question_set_config,
                                                   mock_vnc_service, mock_bastion_service):
        """測試成功設定 Kubernetes 叢集"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_vm_config
        mock_vnc_service.create_vnc_container.return_value = {
            "container_id": "vnc-container-123",
            "vnc_url": "http://localhost:6080/vnc.html"
        }
        mock_bastion_service.create_bastion_container.return_value = {
            "container_id": "bastion-container-123"
        }

        # 模擬 Kubespray 執行成功
        with patch.object(vm_cluster_service, '_run_kubespray_playbook', new_callable=AsyncMock) as mock_kubespray:
            mock_kubespray.return_value = {"success": True, "message": "叢集部署成功"}

            # 執行測試
            result = await vm_cluster_service.setup_kubernetes_cluster(
                session_id="test-session-001",
                vm_cluster_config_id="test-cluster-001",
                question_set_config=sample_question_set_config
            )

            # 驗證結果
            assert result["success"] is True
            assert result["vnc_url"] == "http://localhost:6080/vnc.html"
            assert result["cluster_ready"] is True

            # 驗證呼叫
            mock_vnc_service.create_vnc_container.assert_called_once()
            mock_bastion_service.create_bastion_container.assert_called_once()
            mock_kubespray.assert_called_once()

    async def test_setup_kubernetes_cluster_vm_config_not_found(self, vm_cluster_service,
                                                              mock_db_session):
        """測試 VM 配置不存在時設定失敗"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # 執行測試並驗證異常
        with pytest.raises(ValueError, match="VM 叢集配置不存在"):
            await vm_cluster_service.setup_kubernetes_cluster(
                session_id="test-session-001",
                vm_cluster_config_id="nonexistent-cluster",
                question_set_config={}
            )

    async def test_setup_kubernetes_cluster_container_creation_failure(self, vm_cluster_service,
                                                                     mock_db_session,
                                                                     sample_vm_config,
                                                                     mock_vnc_service):
        """測試容器建立失敗"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_vm_config
        mock_vnc_service.create_vnc_container.side_effect = Exception("容器建立失敗")

        # 執行測試
        result = await vm_cluster_service.setup_kubernetes_cluster(
            session_id="test-session-001",
            vm_cluster_config_id="test-cluster-001",
            question_set_config={}
        )

        # 驗證結果
        assert result["success"] is False
        assert "容器建立失敗" in result["error"]

    @patch('subprocess.run')
    async def test_run_kubespray_playbook_success(self, mock_subprocess, vm_cluster_service,
                                                sample_vm_config):
        """測試成功執行 Kubespray playbook"""
        # 設定模擬
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "PLAY RECAP: All tasks completed successfully"

        with tempfile.TemporaryDirectory() as temp_dir:
            # 執行測試
            result = await vm_cluster_service._run_kubespray_playbook(
                session_id="test-session",
                vm_config=sample_vm_config,
                config_overrides={},
                working_dir=temp_dir
            )

            # 驗證結果
            assert result["success"] is True
            assert "successfully" in result["message"]

    @patch('subprocess.run')
    async def test_run_kubespray_playbook_failure(self, mock_subprocess, vm_cluster_service,
                                                sample_vm_config):
        """測試 Kubespray playbook 執行失敗"""
        # 設定模擬
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Ansible playbook failed"

        with tempfile.TemporaryDirectory() as temp_dir:
            # 執行測試
            result = await vm_cluster_service._run_kubespray_playbook(
                session_id="test-session",
                vm_config=sample_vm_config,
                config_overrides={},
                working_dir=temp_dir
            )

            # 驗證結果
            assert result["success"] is False
            assert "failed" in result["message"]

    async def test_generate_kubespray_inventory(self, vm_cluster_service, sample_vm_config):
        """測試生成 Kubespray inventory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            inventory_path = await vm_cluster_service._generate_kubespray_inventory(
                vm_config=sample_vm_config,
                working_dir=temp_dir
            )

            # 驗證檔案存在
            assert inventory_path.exists()

            # 驗證檔案內容
            content = inventory_path.read_text()
            assert "master-1" in content
            assert "worker-1" in content
            assert "192.168.1.10" in content
            assert "192.168.1.11" in content

    async def test_generate_kubespray_config(self, vm_cluster_service, sample_question_set_config):
        """測試生成 Kubespray 配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_files = await vm_cluster_service._generate_kubespray_config(
                question_set_config=sample_question_set_config,
                working_dir=temp_dir
            )

            # 驗證配置檔案生成
            assert len(config_files) > 0
            for config_file in config_files:
                assert config_file.exists()

    async def test_get_cluster_status_healthy(self, vm_cluster_service, mock_bastion_service):
        """測試取得健康叢集狀態"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": True,
            "output": "Ready",
            "exit_code": 0
        }

        # 執行測試
        status = await vm_cluster_service.get_cluster_status("test-session")

        # 驗證結果
        assert status["healthy"] is True
        assert status["nodes_ready"] is True

    async def test_get_cluster_status_unhealthy(self, vm_cluster_service, mock_bastion_service):
        """測試取得不健康叢集狀態"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": False,
            "output": "Connection refused",
            "exit_code": 1
        }

        # 執行測試
        status = await vm_cluster_service.get_cluster_status("test-session")

        # 驗證結果
        assert status["healthy"] is False

    async def test_cleanup_cluster(self, vm_cluster_service, mock_vnc_service, mock_bastion_service):
        """測試清理叢集"""
        # 設定模擬
        mock_vnc_service.stop_vnc_container.return_value = {"success": True}
        mock_bastion_service.stop_bastion_container.return_value = {"success": True}

        # 執行測試
        result = await vm_cluster_service.cleanup_cluster("test-session")

        # 驗證結果
        assert result["success"] is True

        # 驗證呼叫
        mock_vnc_service.stop_vnc_container.assert_called_once_with("test-session")
        mock_bastion_service.stop_bastion_container.assert_called_once_with("test-session")

    async def test_execute_verification_script(self, vm_cluster_service, mock_bastion_service):
        """測試執行驗證腳本"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": True,
            "output": "Verification completed successfully",
            "exit_code": 0
        }

        # 執行測試
        result = await vm_cluster_service.execute_verification_script(
            session_id="test-session",
            script_path="/path/to/verify.sh"
        )

        # 驗證結果
        assert result["success"] is True
        assert "successfully" in result["output"]

        # 驗證呼叫
        expected_command = f"bash /path/to/verify.sh"
        mock_bastion_service.execute_command.assert_called_with("test-session", expected_command)

    async def test_copy_files_to_bastion(self, vm_cluster_service, mock_bastion_service):
        """測試複製檔案到 Bastion 容器"""
        # 設定模擬
        mock_bastion_service.copy_files.return_value = {"success": True}

        # 執行測試
        result = await vm_cluster_service.copy_files_to_bastion(
            session_id="test-session",
            source_path="/local/path",
            dest_path="/remote/path"
        )

        # 驗證結果
        assert result["success"] is True

        # 驗證呼叫
        mock_bastion_service.copy_files.assert_called_once()

    async def test_install_exam_tools(self, vm_cluster_service, mock_bastion_service):
        """測試安裝考試工具"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": True,
            "output": "Tools installed successfully",
            "exit_code": 0
        }

        # 執行測試
        result = await vm_cluster_service.install_exam_tools("test-session")

        # 驗證結果
        assert result["success"] is True

    async def test_configure_kubeconfig(self, vm_cluster_service, mock_bastion_service):
        """測試配置 kubeconfig"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": True,
            "output": "kubeconfig configured",
            "exit_code": 0
        }

        # 執行測試
        result = await vm_cluster_service.configure_kubeconfig(
            session_id="test-session",
            master_ip="192.168.1.10"
        )

        # 驗證結果
        assert result["success"] is True

    async def test_error_handling_network_timeout(self, vm_cluster_service, mock_bastion_service):
        """測試網路逾時錯誤處理"""
        # 設定模擬
        mock_bastion_service.execute_command.side_effect = asyncio.TimeoutError("Command timeout")

        # 執行測試
        result = await vm_cluster_service.get_cluster_status("test-session")

        # 驗證錯誤處理
        assert result["healthy"] is False
        assert "timeout" in result["error"].lower()

    async def test_concurrent_cluster_operations(self, vm_cluster_service, mock_bastion_service):
        """測試並發叢集操作"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": True,
            "output": "Success",
            "exit_code": 0
        }

        # 同時執行多個操作
        tasks = [
            vm_cluster_service.get_cluster_status("session1"),
            vm_cluster_service.get_cluster_status("session2"),
            vm_cluster_service.install_exam_tools("session1")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 驗證沒有異常
        for result in results:
            assert not isinstance(result, Exception)

    async def test_resource_cleanup_on_failure(self, vm_cluster_service, mock_db_session,
                                             sample_vm_config, mock_vnc_service,
                                             mock_bastion_service):
        """測試失敗時的資源清理"""
        # 設定模擬：VNC 容器建立成功，但 Bastion 容器失敗
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_vm_config
        mock_vnc_service.create_vnc_container.return_value = {
            "container_id": "vnc-123",
            "vnc_url": "http://localhost:6080"
        }
        mock_bastion_service.create_bastion_container.side_effect = Exception("Bastion failed")

        # 執行測試
        result = await vm_cluster_service.setup_kubernetes_cluster(
            session_id="test-session",
            vm_cluster_config_id="test-cluster",
            question_set_config={}
        )

        # 驗證結果和清理
        assert result["success"] is False
        # 驗證清理被呼叫（VNC 容器應該被停止）
        mock_vnc_service.stop_vnc_container.assert_called()

    async def test_configuration_validation(self, vm_cluster_service):
        """測試配置驗證"""
        # 測試無效的 VM 配置
        invalid_vm_config = VMClusterConfig(
            id="invalid",
            name="Invalid Config",
            description="Missing required fields",
            nodes=[],  # 空節點列表
            ssh_user="",  # 空 SSH 使用者
            created_by="test"
        )

        with pytest.raises(ValueError, match="節點列表不能為空"):
            await vm_cluster_service._validate_vm_config(invalid_vm_config)

    async def test_ssh_connectivity_check(self, vm_cluster_service, sample_vm_config):
        """測試 SSH 連線檢查"""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # 設定模擬：SSH 連線成功
            mock_process = Mock()
            mock_process.wait.return_value = 0
            mock_subprocess.return_value = mock_process

            # 執行測試
            result = await vm_cluster_service._check_ssh_connectivity(sample_vm_config)

            # 驗證結果
            assert result["all_nodes_accessible"] is True

    async def test_performance_monitoring(self, vm_cluster_service, mock_bastion_service):
        """測試效能監控"""
        # 設定模擬
        mock_bastion_service.execute_command.return_value = {
            "success": True,
            "output": "CPU: 25%, Memory: 60%, Disk: 40%",
            "exit_code": 0
        }

        # 執行測試
        metrics = await vm_cluster_service.get_cluster_metrics("test-session")

        # 驗證結果
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])