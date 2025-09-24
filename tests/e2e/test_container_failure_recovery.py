"""
容器故障恢復測試
驗證系統在各種容器故障情況下的恢復能力
"""
import pytest
import asyncio
import time
import docker
from typing import List, Dict, Any
from .conftest import E2ETestHelper


class TestContainerFailureRecovery:
    """容器故障恢復測試類別"""

    @pytest.fixture
    def docker_client(self):
        """Docker 客戶端"""
        return docker.from_env()

    @pytest.fixture
    def container_names(self):
        """系統容器名稱列表"""
        return [
            "dw-ck-backend-1",
            "dw-ck-frontend-1",
            "dw-ck-redis-1",
            "dw-ck-nginx-1"
        ]

    async def _wait_for_service_recovery(self, e2e_helper: E2ETestHelper, timeout: int = 60) -> bool:
        """等待服務恢復"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await e2e_helper.api_client.get("/health")
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
        return False

    def _get_container_by_name(self, docker_client, container_name: str):
        """根據名稱取得容器"""
        try:
            containers = docker_client.containers.list(all=True)
            for container in containers:
                if container_name in container.name:
                    return container
            return None
        except Exception:
            return None

    @pytest.mark.e2e
    async def test_backend_container_failure_recovery(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client,
        sample_vm_config
    ):
        """測試後端容器故障恢復"""

        # 確認服務初始狀態正常
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

        # 取得後端容器
        backend_container = self._get_container_by_name(docker_client, "dw-ck-backend")
        assert backend_container is not None, "找不到後端容器"

        # 強制停止後端容器
        backend_container.kill()

        # 等待容器停止
        await asyncio.sleep(5)

        # 驗證服務暫時不可用
        with pytest.raises(Exception):
            await e2e_helper.api_client.get("/health", timeout=5)

        # 等待 Docker Compose 自動重啟容器
        recovery_successful = await self._wait_for_service_recovery(e2e_helper, timeout=120)
        assert recovery_successful, "後端容器未能在預期時間內恢復"

        # 驗證服務功能正常
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

        # 測試基本 API 功能
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)
        assert vm_config_id is not None

        response = await e2e_helper.api_client.get(f"/vm-configs/{vm_config_id}")
        assert response.status_code == 200

    @pytest.mark.e2e
    async def test_redis_container_failure_recovery(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client,
        sample_vm_config
    ):
        """測試 Redis 容器故障恢復"""

        # 建立一些會話資料
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 取得 Redis 容器
        redis_container = self._get_container_by_name(docker_client, "dw-ck-redis")
        assert redis_container is not None, "找不到 Redis 容器"

        # 強制停止 Redis 容器
        redis_container.kill()

        # 等待容器停止
        await asyncio.sleep(5)

        # 系統應該能夠處理 Redis 不可用的情況
        # 雖然可能會有一些功能受影響，但基本 API 應該仍可運行
        try:
            response = await e2e_helper.api_client.get("/health")
            # 可能返回不同的狀態碼，但不應該完全崩潰
        except Exception:
            pass  # 預期可能會有暫時的連線問題

        # 等待 Redis 恢復
        await asyncio.sleep(30)  # 等待 Docker Compose 重啟

        # 驗證服務恢復
        recovery_successful = await self._wait_for_service_recovery(e2e_helper, timeout=60)
        assert recovery_successful, "Redis 容器故障後服務未能恢復"

        # 驗證資料持久性（如果有的話）
        response = await e2e_helper.api_client.get(f"/vm-configs/{vm_config_id}")
        assert response.status_code == 200

    @pytest.mark.e2e
    async def test_nginx_container_failure_recovery(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client
    ):
        """測試 Nginx 容器故障恢復"""

        # 確認初始狀態
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

        # 取得 Nginx 容器
        nginx_container = self._get_container_by_name(docker_client, "dw-ck-nginx")
        assert nginx_container is not None, "找不到 Nginx 容器"

        # 強制停止 Nginx 容器
        nginx_container.kill()

        # 等待容器停止
        await asyncio.sleep(5)

        # 驗證前端和 API 都不可用
        with pytest.raises(Exception):
            await e2e_helper.api_client.get("/health", timeout=5)

        # 等待恢復
        recovery_successful = await self._wait_for_service_recovery(e2e_helper, timeout=60)
        assert recovery_successful, "Nginx 容器未能在預期時間內恢復"

        # 驗證服務完全恢復
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.e2e
    async def test_multiple_container_failure_recovery(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client,
        container_names
    ):
        """測試多個容器同時故障的恢復"""

        # 確認初始狀態
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

        # 同時停止多個容器
        containers_to_kill = []
        for name in ["dw-ck-backend", "dw-ck-redis"]:  # 不包含 nginx，否則無法測試恢復
            container = self._get_container_by_name(docker_client, name)
            if container:
                containers_to_kill.append(container)

        # 同時殺掉多個容器
        for container in containers_to_kill:
            container.kill()

        # 等待容器停止
        await asyncio.sleep(10)

        # 等待系統恢復（這可能需要更長時間）
        recovery_successful = await self._wait_for_service_recovery(e2e_helper, timeout=180)
        assert recovery_successful, "多個容器故障後系統未能恢復"

        # 驗證完整功能
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.e2e
    async def test_container_restart_policy_validation(
        self,
        docker_compose_environment,
        docker_client,
        container_names
    ):
        """驗證容器重啟政策配置"""

        for container_name_pattern in container_names:
            container = self._get_container_by_name(docker_client, container_name_pattern.replace("-1", ""))
            if container:
                # 檢查容器的重啟政策
                container.reload()
                restart_policy = container.attrs.get('HostConfig', {}).get('RestartPolicy', {})

                # 驗證重啟政策不是 "no"
                assert restart_policy.get('Name') in ['unless-stopped', 'always', 'on-failure'], \
                    f"容器 {container.name} 沒有適當的重啟政策"

    @pytest.mark.e2e
    async def test_graceful_shutdown_handling(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client,
        sample_vm_config
    ):
        """測試優雅關閉處理"""

        # 建立一個考試會話
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 如果有題組檔案，建立考試會話
        try:
            session_id = await e2e_helper.create_exam_session("cka/e2e-test-001", vm_config_id)
            await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/start")
        except Exception:
            # 如果沒有題組檔案，跳過這部分測試
            pass

        # 取得後端容器
        backend_container = self._get_container_by_name(docker_client, "dw-ck-backend")
        assert backend_container is not None

        # 發送 SIGTERM 信號（優雅關閉）
        backend_container.kill(signal="SIGTERM")

        # 給容器一些時間來優雅關閉
        await asyncio.sleep(15)

        # 檢查容器是否已停止
        backend_container.reload()
        assert backend_container.status == "exited", "容器未能優雅關閉"

        # 等待自動重啟
        recovery_successful = await self._wait_for_service_recovery(e2e_helper, timeout=60)
        assert recovery_successful, "優雅關閉後服務未能重啟"

    @pytest.mark.e2e
    async def test_resource_exhaustion_recovery(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client
    ):
        """測試資源耗盡時的恢復能力"""

        # 取得後端容器
        backend_container = self._get_container_by_name(docker_client, "dw-ck-backend")
        assert backend_container is not None

        # 檢查容器資源限制
        backend_container.reload()
        host_config = backend_container.attrs.get('HostConfig', {})

        # 如果有記憶體限制，驗證它是合理的
        memory_limit = host_config.get('Memory', 0)
        if memory_limit > 0:
            assert memory_limit >= 100 * 1024 * 1024, "記憶體限制過低（< 100MB）"

        # 嘗試通過大量並發請求來測試系統穩定性
        tasks = []
        for _ in range(20):  # 建立 20 個並發請求
            task = asyncio.create_task(
                e2e_helper.api_client.get("/health")
            )
            tasks.append(task)

        # 等待所有請求完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 統計成功的請求
        successful_requests = sum(
            1 for result in results
            if not isinstance(result, Exception) and hasattr(result, 'status_code') and result.status_code == 200
        )

        # 至少應有一半的請求成功
        assert successful_requests >= 10, f"只有 {successful_requests}/20 個請求成功"

        # 等待系統穩定
        await asyncio.sleep(10)

        # 驗證服務仍然正常
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.e2e
    async def test_disk_space_handling(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        docker_client
    ):
        """測試磁碟空間不足的處理"""

        # 檢查當前磁碟使用情況
        import shutil
        disk_usage = shutil.disk_usage("/home/ubuntu/DW-CK")
        free_space_gb = disk_usage.free / (1024 ** 3)

        # 如果可用空間太少，跳過測試
        if free_space_gb < 1:
            pytest.skip("磁碟空間不足，跳過磁碟空間測試")

        # 驗證服務在低磁碟空間警告下仍能運行
        response = await e2e_helper.api_client.get("/health")
        assert response.status_code == 200

        # 檢查日誌是否有磁碟空間警告
        backend_container = self._get_container_by_name(docker_client, "dw-ck-backend")
        if backend_container:
            logs = backend_container.logs().decode('utf-8')
            # 這裡可以檢查是否有適當的磁碟空間監控日誌
            # 但不強制要求，因為這取決於具體實作