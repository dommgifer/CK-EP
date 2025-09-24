"""
完整考試流程 E2E 測試
驗證從 VM 配置到考試完成的完整使用者流程
"""
import pytest
import asyncio
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .conftest import E2ETestHelper


class TestCompleteExamFlow:
    """完整考試流程測試"""

    @pytest.mark.e2e
    async def test_complete_cka_exam_flow(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        sample_question_set
    ):
        """測試完整的 CKA 考試流程"""

        # Step 1: 確保題組檔案存在
        question_set_dir = Path("/home/ubuntu/DW-CK/data/question_sets/cka/e2e-test-001")
        question_set_dir.mkdir(parents=True, exist_ok=True)

        # 寫入題組檔案
        with open(question_set_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(sample_question_set["metadata"], f, ensure_ascii=False, indent=2)

        with open(question_set_dir / "questions.json", "w", encoding="utf-8") as f:
            json.dump(sample_question_set["questions"], f, ensure_ascii=False, indent=2)

        # 觸發題組重載
        response = await e2e_helper.api_client.post("/question-sets/reload")
        assert response.status_code == 200

        # Step 2: 建立 VM 配置
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)
        assert vm_config_id is not None

        # 驗證 VM 配置建立成功
        response = await e2e_helper.api_client.get(f"/vm-configs/{vm_config_id}")
        assert response.status_code == 200
        config_data = response.json()
        assert config_data["name"] == sample_vm_config["name"]

        # Step 3: 驗證題組可用
        response = await e2e_helper.api_client.get("/question-sets/cka/e2e-test-001")
        assert response.status_code == 200
        question_set_data = response.json()
        assert question_set_data["metadata"]["title"] == "E2E 測試題組"

        # Step 4: 建立考試會話
        session_id = await e2e_helper.create_exam_session(
            "cka/e2e-test-001",
            vm_config_id
        )
        assert session_id is not None

        # 驗證會話建立成功
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["status"] == "created"
        assert session_data["question_set_id"] == "cka/e2e-test-001"

        # Step 5: 開始考試
        response = await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/start")
        assert response.status_code == 200

        # 等待環境準備完成（這在實際環境中可能需要較長時間）
        # 在測試環境中，我們模擬環境準備過程
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
        session_data = response.json()
        assert session_data["status"] in ["starting", "ready"]

        # Step 6: 導航到考試頁面並進行 UI 測試
        e2e_helper.navigate_to_exam(session_id)

        # 驗證考試頁面元素存在
        exam_container = e2e_helper.web_driver.find_element(By.CLASS_NAME, "exam-container")
        assert exam_container is not None

        # 驗證題目顯示
        question_element = e2e_helper.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "question"))
        )
        assert "建立 Pod" in question_element.text

        # 驗證 VNC 檢視器存在
        vnc_viewer = e2e_helper.web_driver.find_element(By.CLASS_NAME, "vnc-viewer")
        assert vnc_viewer is not None

        # Step 7: 提交答案
        sample_answer = "kubectl run test-pod --image=nginx"
        e2e_helper.submit_answer(1, sample_answer)

        # 驗證答案提交成功
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
        session_data = response.json()
        assert len(session_data.get("answers", [])) > 0

        # Step 8: 完成考試
        response = await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/finish")
        assert response.status_code == 200

        # 驗證考試結果
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}/results")
        assert response.status_code == 200
        results = response.json()
        assert "total_score" in results
        assert "question_results" in results

    @pytest.mark.e2e
    async def test_exam_session_timeout_handling(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config
    ):
        """測試考試會話超時處理"""

        # 建立短時限的題組
        timeout_question_set = {
            "metadata": {
                "title": "超時測試題組",
                "description": "用於測試超時的題組",
                "time_limit_minutes": 1,  # 1 分鐘時限
                "passing_score": 70
            },
            "questions": [
                {
                    "id": 1,
                    "title": "簡單任務",
                    "description": "建立一個 Pod",
                    "scoring": {"max_points": 10}
                }
            ]
        }

        # 建立題組檔案
        question_set_dir = Path("/home/ubuntu/DW-CK/data/question_sets/cka/timeout-test")
        question_set_dir.mkdir(parents=True, exist_ok=True)

        with open(question_set_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(timeout_question_set["metadata"], f, ensure_ascii=False, indent=2)

        with open(question_set_dir / "questions.json", "w", encoding="utf-8") as f:
            json.dump(timeout_question_set["questions"], f, ensure_ascii=False, indent=2)

        # 重載題組
        await e2e_helper.api_client.post("/question-sets/reload")

        # 建立 VM 配置和考試會話
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)
        session_id = await e2e_helper.create_exam_session(
            "cka/timeout-test",
            vm_config_id
        )

        # 開始考試
        await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/start")

        # 等待超過時限
        await asyncio.sleep(70)  # 等待超過 1 分鐘

        # 檢查會話是否自動結束
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
        session_data = response.json()
        assert session_data["status"] in ["finished", "timeout"]

    @pytest.mark.e2e
    async def test_concurrent_exam_prevention(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        sample_question_set
    ):
        """測試並行考試會話防護機制"""

        # 準備題組
        question_set_dir = Path("/home/ubuntu/DW-CK/data/question_sets/cka/concurrent-test")
        question_set_dir.mkdir(parents=True, exist_ok=True)

        with open(question_set_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(sample_question_set["metadata"], f, ensure_ascii=False, indent=2)

        with open(question_set_dir / "questions.json", "w", encoding="utf-8") as f:
            json.dump(sample_question_set["questions"], f, ensure_ascii=False, indent=2)

        await e2e_helper.api_client.post("/question-sets/reload")

        # 建立 VM 配置
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 建立第一個考試會話並開始
        session1_id = await e2e_helper.create_exam_session(
            "cka/concurrent-test",
            vm_config_id
        )
        await e2e_helper.api_client.post(f"/exam-sessions/{session1_id}/start")

        # 嘗試建立第二個考試會話（應該失敗）
        response = await e2e_helper.api_client.post("/exam-sessions", json={
            "question_set_id": "cka/concurrent-test",
            "vm_cluster_config_id": vm_config_id
        })
        assert response.status_code == 400
        error_data = response.json()
        assert "活動會話" in error_data["detail"]

    @pytest.mark.e2e
    async def test_vm_connection_validation(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper
    ):
        """測試 VM 連線驗證"""

        # 建立包含無效 IP 的 VM 配置
        invalid_vm_config = {
            "name": "無效 IP 測試",
            "description": "用於測試無效 IP 的配置",
            "nodes": [
                {
                    "name": "invalid-node",
                    "ip": "192.168.999.999",  # 無效 IP
                    "roles": ["master"]
                }
            ],
            "ssh_user": "ubuntu"
        }

        # 建立配置（應該成功，因為只是保存配置）
        vm_config_id = await e2e_helper.create_vm_config(invalid_vm_config)
        assert vm_config_id is not None

        # 嘗試建立考試會話（可能成功，取決於驗證時機）
        try:
            session_id = await e2e_helper.create_exam_session(
                "cka/e2e-test-001",  # 假設這個題組存在
                vm_config_id
            )

            # 嘗試開始考試（應該在環境準備時失敗）
            response = await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/start")

            if response.status_code == 200:
                # 如果開始成功，等待環境狀態變為失敗
                for _ in range(10):
                    response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
                    session_data = response.json()
                    if session_data["environment_status"] == "failed":
                        break
                    await asyncio.sleep(2)
                else:
                    pytest.fail("預期環境準備失敗，但未發生")

        except Exception:
            # 如果在更早階段失敗也是可接受的
            pass