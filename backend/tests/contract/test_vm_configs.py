"""
T010: VM 配置 API 契約測試
測試所有 VM 配置相關的 API 端點契約
"""
import pytest
from fastapi.testclient import TestClient


class TestVMConfigsContract:
    """VM 配置 API 契約測試"""

    def test_get_vm_configs_contract(self, test_client: TestClient):
        """測試 GET /api/v1/vm-configs 契約"""
        # 這個測試目前會失敗，因為 API 尚未實作
        with pytest.raises(NotImplementedError):
            response = test_client.get("/api/v1/vm-configs")
            # 預期回應格式
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:
                vm_config = data[0]
                assert "id" in vm_config
                assert "name" in vm_config
                assert "description" in vm_config
                assert "nodes" in vm_config
                assert "ssh_config" in vm_config
                assert "network" in vm_config

    def test_post_vm_configs_contract(self, test_client: TestClient, mock_vm_config):
        """測試 POST /api/v1/vm-configs 契約"""
        with pytest.raises(NotImplementedError):
            response = test_client.post("/api/v1/vm-configs", json=mock_vm_config)
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == mock_vm_config["id"]
            assert data["name"] == mock_vm_config["name"]

    def test_get_vm_config_by_id_contract(self, test_client: TestClient):
        """測試 GET /api/v1/vm-configs/{config_id} 契約"""
        with pytest.raises(NotImplementedError):
            config_id = "test-cluster"
            response = test_client.get(f"/api/v1/vm-configs/{config_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == config_id

    def test_put_vm_config_contract(self, test_client: TestClient, mock_vm_config):
        """測試 PUT /api/v1/vm-configs/{config_id} 契約"""
        with pytest.raises(NotImplementedError):
            config_id = "test-cluster"
            updated_config = mock_vm_config.copy()
            updated_config["name"] = "更新的測試叢集"

            response = test_client.put(f"/api/v1/vm-configs/{config_id}", json=updated_config)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "更新的測試叢集"

    def test_delete_vm_config_contract(self, test_client: TestClient):
        """測試 DELETE /api/v1/vm-configs/{config_id} 契約"""
        with pytest.raises(NotImplementedError):
            config_id = "test-cluster"
            response = test_client.delete(f"/api/v1/vm-configs/{config_id}")
            assert response.status_code == 204

    def test_test_vm_connection_contract(self, test_client: TestClient):
        """測試 POST /api/v1/vm-configs/{config_id}/test-connection 契約"""
        with pytest.raises(NotImplementedError):
            config_id = "test-cluster"
            response = test_client.post(f"/api/v1/vm-configs/{config_id}/test-connection")
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "nodes" in data
            assert isinstance(data["nodes"], list)

    def test_error_responses_contract(self, test_client: TestClient):
        """測試錯誤回應契約"""
        with pytest.raises(NotImplementedError):
            # 404 錯誤
            response = test_client.get("/api/v1/vm-configs/non-existent")
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "message" in data

            # 400 錯誤 - 無效請求
            invalid_config = {"invalid": "data"}
            response = test_client.post("/api/v1/vm-configs", json=invalid_config)
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "details" in data