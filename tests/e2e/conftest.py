"""
E2E 測試配置檔案
提供完整考試流程的端對端測試支援
"""
import asyncio
import json
import pytest
import time
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient
from pathlib import Path
import docker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 測試配置
BASE_URL = "http://localhost"
API_BASE_URL = f"{BASE_URL}/api/v1"
DOCKER_COMPOSE_FILE = Path(__file__).parent.parent.parent / "docker-compose.yml"
TEST_TIMEOUT = 300  # 5 分鐘超時

@pytest.fixture(scope="session")
def docker_compose_environment():
    """啟動完整的 Docker Compose 環境用於 E2E 測試"""
    client = docker.from_env()

    # 確保環境乾淨
    try:
        containers = client.containers.list(
            filters={"label": "com.docker.compose.project=dw-ck"}
        )
        for container in containers:
            container.stop()
            container.remove()
    except Exception:
        pass

    # 啟動服務
    import subprocess
    compose_process = subprocess.Popen([
        "docker-compose", "-f", str(DOCKER_COMPOSE_FILE),
        "up", "-d", "--build"
    ])
    compose_process.wait()

    # 等待服務就緒
    max_retries = 30
    for _ in range(max_retries):
        try:
            import requests
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(2)
    else:
        raise Exception("服務未能在預期時間內啟動")

    yield

    # 清理
    subprocess.run([
        "docker-compose", "-f", str(DOCKER_COMPOSE_FILE),
        "down", "-v"
    ])

@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """API 客戶端用於後端測試"""
    async with AsyncClient(base_url=API_BASE_URL) as client:
        yield client

@pytest.fixture
def web_driver():
    """Selenium WebDriver 用於前端 UI 測試"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture
def sample_vm_config() -> Dict[str, Any]:
    """測試用 VM 配置"""
    return {
        "name": "E2E 測試叢集",
        "description": "用於端對端測試的 Kubernetes 叢集",
        "nodes": [
            {
                "name": "master-1",
                "ip": "192.168.1.10",
                "roles": ["master", "etcd"]
            },
            {
                "name": "worker-1",
                "ip": "192.168.1.11",
                "roles": ["worker"]
            }
        ],
        "ssh_user": "ubuntu"
    }

@pytest.fixture
def sample_question_set() -> Dict[str, Any]:
    """測試用題組資料"""
    return {
        "exam_type": "cka",
        "set_id": "e2e-test-001",
        "metadata": {
            "title": "E2E 測試題組",
            "description": "用於端對端測試的題組",
            "time_limit_minutes": 30,
            "passing_score": 70
        },
        "questions": [
            {
                "id": 1,
                "title": "建立 Pod",
                "description": "建立一個名為 test-pod 的 Pod",
                "scenario": "在預設命名空間建立 Pod",
                "scoring": {
                    "max_points": 10,
                    "validation_commands": [
                        "kubectl get pod test-pod -o json"
                    ],
                    "expected_conditions": [
                        {"field": "status.phase", "value": "Running"}
                    ]
                }
            }
        ]
    }

class E2ETestHelper:
    """E2E 測試輔助類"""

    def __init__(self, api_client: AsyncClient, web_driver: webdriver.Chrome):
        self.api_client = api_client
        self.web_driver = web_driver
        self.wait = WebDriverWait(web_driver, TEST_TIMEOUT)

    async def create_vm_config(self, config: Dict[str, Any]) -> str:
        """建立 VM 配置並返回 ID"""
        response = await self.api_client.post("/vm-configs", json=config)
        assert response.status_code == 201
        return response.json()["id"]

    async def create_exam_session(self, question_set_id: str, vm_config_id: str) -> str:
        """建立考試會話並返回 ID"""
        response = await self.api_client.post("/exam-sessions", json={
            "question_set_id": question_set_id,
            "vm_cluster_config_id": vm_config_id
        })
        assert response.status_code == 201
        return response.json()["id"]

    async def wait_for_environment_ready(self, session_id: str) -> None:
        """等待考試環境準備完成"""
        max_retries = 60  # 10 分鐘
        for _ in range(max_retries):
            response = await self.api_client.get(f"/exam-sessions/{session_id}")
            session_data = response.json()

            if session_data["environment_status"] == "ready":
                return
            elif session_data["environment_status"] == "failed":
                raise Exception("考試環境準備失敗")

            await asyncio.sleep(10)

        raise TimeoutError("考試環境準備超時")

    def navigate_to_exam(self, session_id: str) -> None:
        """導航到考試頁面"""
        self.web_driver.get(f"{BASE_URL}/exam/{session_id}")

        # 等待頁面載入
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "exam-container"))
        )

    def submit_answer(self, question_id: int, answer: str) -> None:
        """在 UI 中提交答案"""
        # 找到答案文字區域
        answer_textarea = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"[data-question-id='{question_id}'] textarea")
            )
        )
        answer_textarea.clear()
        answer_textarea.send_keys(answer)

        # 點擊提交按鈕
        submit_btn = self.web_driver.find_element(
            By.CSS_SELECTOR, f"[data-question-id='{question_id}'] .submit-answer-btn"
        )
        submit_btn.click()

        # 等待提交確認
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"[data-question-id='{question_id}'] .answer-submitted")
            )
        )

@pytest.fixture
def e2e_helper(api_client, web_driver):
    """E2E 測試輔助工具"""
    return E2ETestHelper(api_client, web_driver)