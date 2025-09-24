"""
測試配置和共用 fixtures
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from typing import AsyncGenerator, Generator

# 這裡先建立基本框架，實際實作會在後續任務中完成


@pytest.fixture(scope="session")
def event_loop():
    """建立事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """建立測試客戶端"""
    # TODO: 在實作 main.py 後匯入
    # from src.main import app
    # with TestClient(app) as client:
    #     yield client
    raise NotImplementedError("等待 main.py 實作")


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """建立異步測試客戶端"""
    # TODO: 在實作 main.py 後匯入
    # from src.main import app
    # async with AsyncClient(app=app, base_url="http://test") as client:
    #     yield client
    raise NotImplementedError("等待 main.py 實作")


@pytest.fixture
def mock_vm_config():
    """模擬 VM 配置資料"""
    return {
        "id": "test-cluster",
        "name": "測試叢集",
        "description": "用於測試的 VM 配置",
        "nodes": [
            {
                "name": "k8s-master",
                "ip": "192.168.1.10",
                "role": "master",
                "specs": {
                    "cpu_cores": 2,
                    "memory_gb": 4,
                    "disk_gb": 50
                }
            }
        ],
        "ssh_config": {
            "user": "ubuntu",
            "port": 22
        },
        "network": {
            "pod_subnet": "10.244.0.0/16",
            "service_subnet": "10.96.0.0/12"
        }
    }


@pytest.fixture
def mock_question_set():
    """模擬題組資料"""
    return {
        "id": "test-ckad",
        "title": "測試 CKAD 題組",
        "certification_type": "CKAD",
        "difficulty": "intermediate",
        "duration_minutes": 120,
        "total_questions": 2,
        "total_points": 100
    }


@pytest.fixture
def mock_exam_session():
    """模擬考試會話資料"""
    return {
        "id": "test-session-001",
        "question_set_id": "test-ckad",
        "vm_config_id": "test-cluster",
        "status": "created",
        "current_question_index": 0,
        "start_time": None,
        "end_time": None,
        "duration_minutes": 120
    }