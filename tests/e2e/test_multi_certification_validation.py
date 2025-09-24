"""
多認證類型驗證測試
驗證 CKA、CKAD、CKS 三種認證類型的考試流程
"""
import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from .conftest import E2ETestHelper


class TestMultiCertificationValidation:
    """多認證類型驗證測試類別"""

    @pytest.fixture
    def cka_question_set(self) -> Dict[str, Any]:
        """CKA 測試題組"""
        return {
            "metadata": {
                "title": "CKA 多認證測試",
                "description": "CKA 認證類型驗證測試",
                "time_limit_minutes": 60,
                "passing_score": 74,
                "exam_type": "cka"
            },
            "questions": [
                {
                    "id": 1,
                    "title": "叢集管理 - 建立節點",
                    "description": "在叢集中新增一個工作節點",
                    "scenario": "需要使用 kubeadm 將新節點加入叢集",
                    "scoring": {
                        "max_points": 15,
                        "validation_commands": [
                            "kubectl get nodes"
                        ],
                        "expected_conditions": [
                            {"field": "status", "contains": "Ready"}
                        ]
                    }
                },
                {
                    "id": 2,
                    "title": "網路政策配置",
                    "description": "建立網路政策限制 Pod 間通信",
                    "scenario": "配置 NetworkPolicy 實現網路隔離",
                    "scoring": {
                        "max_points": 12,
                        "validation_commands": [
                            "kubectl get networkpolicy -n test-namespace"
                        ]
                    }
                },
                {
                    "id": 3,
                    "title": "備份 ETCD",
                    "description": "建立 ETCD 資料備份",
                    "scenario": "使用 etcdctl 建立叢集資料備份",
                    "scoring": {
                        "max_points": 18,
                        "validation_commands": [
                            "ls /opt/backup/etcd-backup.db"
                        ]
                    }
                }
            ]
        }

    @pytest.fixture
    def ckad_question_set(self) -> Dict[str, Any]:
        """CKAD 測試題組"""
        return {
            "metadata": {
                "title": "CKAD 多認證測試",
                "description": "CKAD 認證類型驗證測試",
                "time_limit_minutes": 120,
                "passing_score": 66,
                "exam_type": "ckad"
            },
            "questions": [
                {
                    "id": 1,
                    "title": "應用程式部署 - Multi-container Pod",
                    "description": "建立包含多個容器的 Pod",
                    "scenario": "建立一個包含主應用容器和 sidecar 容器的 Pod",
                    "scoring": {
                        "max_points": 13,
                        "validation_commands": [
                            "kubectl get pod multi-container-pod -o json"
                        ],
                        "expected_conditions": [
                            {"field": "spec.containers", "length": 2}
                        ]
                    }
                },
                {
                    "id": 2,
                    "title": "ConfigMap 和 Secret",
                    "description": "建立並使用 ConfigMap 和 Secret",
                    "scenario": "應用程式需要從 ConfigMap 讀取配置和從 Secret 讀取密碼",
                    "scoring": {
                        "max_points": 10,
                        "validation_commands": [
                            "kubectl get configmap app-config",
                            "kubectl get secret app-secret"
                        ]
                    }
                },
                {
                    "id": 3,
                    "title": "Service 和 Ingress",
                    "description": "暴露應用程式給外部存取",
                    "scenario": "建立 Service 和 Ingress 資源",
                    "scoring": {
                        "max_points": 12,
                        "validation_commands": [
                            "kubectl get service app-service",
                            "kubectl get ingress app-ingress"
                        ]
                    }
                },
                {
                    "id": 4,
                    "title": "故障排除",
                    "description": "診斷和修復無法啟動的 Pod",
                    "scenario": "修復 Pod 啟動失敗問題",
                    "scoring": {
                        "max_points": 15,
                        "validation_commands": [
                            "kubectl get pod broken-pod -o json"
                        ],
                        "expected_conditions": [
                            {"field": "status.phase", "value": "Running"}
                        ]
                    }
                }
            ]
        }

    @pytest.fixture
    def cks_question_set(self) -> Dict[str, Any]:
        """CKS 測試題組"""
        return {
            "metadata": {
                "title": "CKS 多認證測試",
                "description": "CKS 認證類型驗證測試",
                "time_limit_minutes": 120,
                "passing_score": 67,
                "exam_type": "cks"
            },
            "questions": [
                {
                    "id": 1,
                    "title": "Pod Security Standards",
                    "description": "配置 Pod 安全標準",
                    "scenario": "實施 Pod 安全政策限制容器權限",
                    "scoring": {
                        "max_points": 20,
                        "validation_commands": [
                            "kubectl get psp restricted-psp"
                        ]
                    }
                },
                {
                    "id": 2,
                    "title": "Network Policies",
                    "description": "建立嚴格的網路政策",
                    "scenario": "實施零信任網路政策",
                    "scoring": {
                        "max_points": 16,
                        "validation_commands": [
                            "kubectl get networkpolicy deny-all -n secure-namespace"
                        ]
                    }
                },
                {
                    "id": 3,
                    "title": "RBAC 配置",
                    "description": "配置細粒度的角色權限",
                    "scenario": "建立最小權限的 RBAC 配置",
                    "scoring": {
                        "max_points": 18,
                        "validation_commands": [
                            "kubectl get role app-reader -n app-namespace",
                            "kubectl get rolebinding app-reader-binding -n app-namespace"
                        ]
                    }
                },
                {
                    "id": 4,
                    "title": "容器映像掃描",
                    "description": "掃描容器映像安全漏洞",
                    "scenario": "使用工具掃描映像並修復漏洞",
                    "scoring": {
                        "max_points": 14,
                        "validation_commands": [
                            "ls /opt/scan-results/image-scan-report.json"
                        ]
                    }
                }
            ]
        }

    async def _setup_question_set(self, exam_type: str, set_id: str, question_set: Dict[str, Any]) -> None:
        """設定題組檔案"""
        question_set_dir = Path(f"/home/ubuntu/DW-CK/data/question_sets/{exam_type}/{set_id}")
        question_set_dir.mkdir(parents=True, exist_ok=True)

        # 寫入 metadata
        with open(question_set_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(question_set["metadata"], f, ensure_ascii=False, indent=2)

        # 寫入 questions
        with open(question_set_dir / "questions.json", "w", encoding="utf-8") as f:
            json.dump(question_set["questions"], f, ensure_ascii=False, indent=2)

    @pytest.mark.e2e
    async def test_cka_certification_flow(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        cka_question_set
    ):
        """測試 CKA 認證考試流程"""

        # 設定 CKA 題組
        await self._setup_question_set("cka", "multi-cert-test", cka_question_set)

        # 重載題組
        response = await e2e_helper.api_client.post("/question-sets/reload")
        assert response.status_code == 200

        # 建立 VM 配置
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 驗證題組載入
        response = await e2e_helper.api_client.get("/question-sets/cka/multi-cert-test")
        assert response.status_code == 200
        question_set_data = response.json()

        # 驗證 CKA 特定屬性
        assert question_set_data["metadata"]["exam_type"] == "cka"
        assert question_set_data["metadata"]["passing_score"] == 74
        assert len(question_set_data["questions"]) == 3

        # 驗證題目包含 CKA 相關內容
        question_titles = [q["title"] for q in question_set_data["questions"]]
        assert any("叢集管理" in title for title in question_titles)
        assert any("ETCD" in title for title in question_titles)

        # 建立和執行考試會話
        session_id = await e2e_helper.create_exam_session("cka/multi-cert-test", vm_config_id)
        response = await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/start")
        assert response.status_code == 200

        # 驗證考試會話屬性
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
        session_data = response.json()
        assert "cka" in session_data["question_set_id"]

    @pytest.mark.e2e
    async def test_ckad_certification_flow(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        ckad_question_set
    ):
        """測試 CKAD 認證考試流程"""

        # 設定 CKAD 題組
        await self._setup_question_set("ckad", "multi-cert-test", ckad_question_set)

        # 重載題組
        await e2e_helper.api_client.post("/question-sets/reload")

        # 建立 VM 配置
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 驗證題組載入
        response = await e2e_helper.api_client.get("/question-sets/ckad/multi-cert-test")
        assert response.status_code == 200
        question_set_data = response.json()

        # 驗證 CKAD 特定屬性
        assert question_set_data["metadata"]["exam_type"] == "ckad"
        assert question_set_data["metadata"]["passing_score"] == 66
        assert question_set_data["metadata"]["time_limit_minutes"] == 120
        assert len(question_set_data["questions"]) == 4

        # 驗證題目包含 CKAD 相關內容
        question_titles = [q["title"] for q in question_set_data["questions"]]
        assert any("Multi-container" in title for title in question_titles)
        assert any("ConfigMap" in title for title in question_titles)
        assert any("故障排除" in title for title in question_titles)

        # 建立考試會話
        session_id = await e2e_helper.create_exam_session("ckad/multi-cert-test", vm_config_id)

        # 驗證會話建立成功
        response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}")
        session_data = response.json()
        assert "ckad" in session_data["question_set_id"]

    @pytest.mark.e2e
    async def test_cks_certification_flow(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        cks_question_set
    ):
        """測試 CKS 認證考試流程"""

        # 設定 CKS 題組
        await self._setup_question_set("cks", "multi-cert-test", cks_question_set)

        # 重載題組
        await e2e_helper.api_client.post("/question-sets/reload")

        # 建立 VM 配置
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 驗證題組載入
        response = await e2e_helper.api_client.get("/question-sets/cks/multi-cert-test")
        assert response.status_code == 200
        question_set_data = response.json()

        # 驗證 CKS 特定屬性
        assert question_set_data["metadata"]["exam_type"] == "cks"
        assert question_set_data["metadata"]["passing_score"] == 67
        assert len(question_set_data["questions"]) == 4

        # 驗證題目包含 CKS 安全相關內容
        question_titles = [q["title"] for q in question_set_data["questions"]]
        assert any("Security" in title for title in question_titles)
        assert any("RBAC" in title for title in question_titles)
        assert any("掃描" in title for title in question_titles)

        # 建立考試會話
        session_id = await e2e_helper.create_exam_session("cks/multi-cert-test", vm_config_id)

    @pytest.mark.e2e
    async def test_cross_certification_isolation(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        cka_question_set,
        ckad_question_set,
        cks_question_set
    ):
        """測試不同認證類型之間的隔離性"""

        # 設定所有三種類型的題組
        await self._setup_question_set("cka", "isolation-test", cka_question_set)
        await self._setup_question_set("ckad", "isolation-test", ckad_question_set)
        await self._setup_question_set("cks", "isolation-test", cks_question_set)

        # 重載題組
        await e2e_helper.api_client.post("/question-sets/reload")

        # 建立 VM 配置
        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        # 驗證各類型題組都可以獨立存取
        for exam_type in ["cka", "ckad", "cks"]:
            response = await e2e_helper.api_client.get(f"/question-sets/{exam_type}/isolation-test")
            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["exam_type"] == exam_type

        # 驗證無法跨類型存取
        response = await e2e_helper.api_client.get("/question-sets/cka/isolation-test")
        cka_data = response.json()

        response = await e2e_helper.api_client.get("/question-sets/ckad/isolation-test")
        ckad_data = response.json()

        # 確保資料確實不同
        assert cka_data["metadata"]["passing_score"] != ckad_data["metadata"]["passing_score"]
        assert len(cka_data["questions"]) != len(ckad_data["questions"])

    @pytest.mark.e2e
    async def test_certification_specific_scoring(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        sample_vm_config,
        cka_question_set,
        ckad_question_set,
        cks_question_set
    ):
        """測試不同認證類型的評分機制"""

        test_cases = [
            ("cka", "scoring-test", cka_question_set, 74),
            ("ckad", "scoring-test", ckad_question_set, 66),
            ("cks", "scoring-test", cks_question_set, 67)
        ]

        vm_config_id = await e2e_helper.create_vm_config(sample_vm_config)

        for exam_type, set_id, question_set, expected_passing_score in test_cases:
            # 設定題組
            await self._setup_question_set(exam_type, set_id, question_set)

        # 重載題組
        await e2e_helper.api_client.post("/question-sets/reload")

        for exam_type, set_id, question_set, expected_passing_score in test_cases:
            # 建立考試會話
            session_id = await e2e_helper.create_exam_session(f"{exam_type}/{set_id}", vm_config_id)

            # 開始考試
            await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/start")

            # 提交一些答案
            for question in question_set["questions"][:2]:  # 提交前兩題
                await e2e_helper.api_client.post(
                    f"/exam-sessions/{session_id}/submit-answer",
                    json={
                        "question_id": question["id"],
                        "answer": {"solution": "kubectl get pods"}
                    }
                )

            # 完成考試
            await e2e_helper.api_client.post(f"/exam-sessions/{session_id}/finish")

            # 檢查評分結果
            response = await e2e_helper.api_client.get(f"/exam-sessions/{session_id}/results")
            assert response.status_code == 200
            results = response.json()

            # 驗證評分包含認證特定的及格分數
            assert "total_score" in results
            assert "passing_score" in results
            assert results["passing_score"] == expected_passing_score

    @pytest.mark.e2e
    async def test_all_certifications_list_endpoint(
        self,
        docker_compose_environment,
        e2e_helper: E2ETestHelper,
        cka_question_set,
        ckad_question_set,
        cks_question_set
    ):
        """測試題組列表端點返回所有認證類型"""

        # 設定所有認證類型的題組
        await self._setup_question_set("cka", "list-test", cka_question_set)
        await self._setup_question_set("ckad", "list-test", ckad_question_set)
        await self._setup_question_set("cks", "list-test", cks_question_set)

        # 重載題組
        await e2e_helper.api_client.post("/question-sets/reload")

        # 取得所有題組列表
        response = await e2e_helper.api_client.get("/question-sets")
        assert response.status_code == 200
        question_sets = response.json()

        # 驗證所有認證類型都存在
        exam_types_found = set()
        for qs in question_sets:
            if "list-test" in qs["id"]:
                exam_type = qs["id"].split("/")[0]
                exam_types_found.add(exam_type)

        assert "cka" in exam_types_found
        assert "ckad" in exam_types_found
        assert "cks" in exam_types_found