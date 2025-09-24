"""
T101: ScoringService 單元測試
測試自動評分服務的功能
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, mock_open
from typing import Dict, Any, List
from pathlib import Path

import sys
sys.path.append("../../src")

from src.services.scoring_service import ScoringService
from src.models.exam_session import ExamSession, ExamSessionStatus
from src.models.question_set_data import QuestionSetData, QuestionSetMetadata, QuestionData
from src.models.exam_result import ExamResult
from src.services.vm_cluster_service import VMClusterService


class TestScoringService:
    """ScoringService 測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫會話"""
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        return mock_session

    @pytest.fixture
    def mock_vm_cluster_service(self):
        """模擬 VM 叢集服務"""
        service = Mock(spec=VMClusterService)
        service.execute_verification_script = AsyncMock()
        return service

    @pytest.fixture
    def scoring_service(self, mock_db_session, mock_vm_cluster_service):
        """評分服務實例"""
        return ScoringService(
            db_session=mock_db_session,
            vm_cluster_service=mock_vm_cluster_service
        )

    @pytest.fixture
    def sample_question_set_data(self) -> QuestionSetData:
        """範例題組資料"""
        metadata = QuestionSetMetadata(
            exam_type="CKA",
            set_id="test-001",
            name="測試題組",
            description="用於測試的題組",
            time_limit_minutes=120,
            passing_score=70.0,
            difficulty_level="intermediate",
            version="1.0.0",
            created_at="2025-09-24T08:00:00Z",
            updated_at="2025-09-24T08:00:00Z",
            tags=["test"]
        )

        questions = [
            QuestionData(
                id=1,
                content="建立一個 Pod",
                weight=30.0,
                kubernetes_objects=["Pod"],
                hints=["使用 kubectl create"],
                verification_scripts=["q1_verify_pod.sh"],
                preparation_scripts=[]
            ),
            QuestionData(
                id=2,
                content="建立一個 Service",
                weight=40.0,
                kubernetes_objects=["Service"],
                hints=["使用 kubectl expose"],
                verification_scripts=["q2_verify_service.sh"],
                preparation_scripts=[]
            ),
            QuestionData(
                id=3,
                content="配置 NetworkPolicy",
                weight=30.0,
                kubernetes_objects=["NetworkPolicy"],
                hints=["使用 YAML 檔案"],
                verification_scripts=["q3_verify_netpol.sh"],
                preparation_scripts=[]
            )
        ]

        return QuestionSetData(metadata=metadata, questions=questions)

    @pytest.fixture
    def sample_exam_session(self, sample_question_set_data) -> ExamSession:
        """範例考試會話"""
        session = ExamSession(
            id="test-session-001",
            question_set_id="cka/test-001",
            vm_cluster_config_id="test-cluster",
            status=ExamSessionStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            time_limit_minutes=120,
            current_question_index=2,
            answers={
                "1": {"solution": "kubectl create pod test-pod --image=nginx"},
                "2": {"solution": "kubectl expose pod test-pod --port=80"},
                "3": {"solution": "kubectl apply -f networkpolicy.yaml"}
            },
            progress=100.0,
            final_score=None
        )
        # 模擬關聯的題組資料
        session._question_set_data = sample_question_set_data
        return session

    async def test_score_exam_session_all_correct(self, scoring_service, sample_exam_session,
                                                mock_vm_cluster_service, mock_db_session):
        """測試所有答案正確的評分"""
        # 設定模擬：所有驗證腳本都成功
        mock_vm_cluster_service.execute_verification_script.side_effect = [
            {
                "success": True,
                "output": '{"earned_points": 30, "total_points": 30}',
                "exit_code": 0
            },
            {
                "success": True,
                "output": '{"earned_points": 40, "total_points": 40}',
                "exit_code": 0
            },
            {
                "success": True,
                "output": '{"earned_points": 30, "total_points": 30}',
                "exit_code": 0
            }
        ]

        # 執行測試
        result = await scoring_service.score_exam_session(sample_exam_session)

        # 驗證結果
        assert result["total_score"] == 100.0
        assert result["passed"] is True
        assert result["question_scores"] == {1: 30.0, 2: 40.0, 3: 30.0}

        # 驗證資料庫操作
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_score_exam_session_partial_correct(self, scoring_service, sample_exam_session,
                                                    mock_vm_cluster_service):
        """測試部分答案正確的評分"""
        # 設定模擬：混合結果
        mock_vm_cluster_service.execute_verification_script.side_effect = [
            {
                "success": True,
                "output": '{"earned_points": 30, "total_points": 30}',  # 滿分
                "exit_code": 0
            },
            {
                "success": True,
                "output": '{"earned_points": 20, "total_points": 40}',  # 部分分數
                "exit_code": 0
            },
            {
                "success": False,
                "output": '{"earned_points": 0, "total_points": 30}',   # 零分
                "exit_code": 1
            }
        ]

        # 執行測試
        result = await scoring_service.score_exam_session(sample_exam_session)

        # 驗證結果
        assert result["total_score"] == 50.0  # (30 + 20 + 0) / 100 * 100
        assert result["passed"] is False  # 低於 70% 及格線
        assert result["question_scores"] == {1: 30.0, 2: 20.0, 3: 0.0}

    async def test_score_exam_session_no_answers(self, scoring_service, sample_exam_session):
        """測試沒有答案的評分"""
        # 清空答案
        sample_exam_session.answers = {}

        # 執行測試
        result = await scoring_service.score_exam_session(sample_exam_session)

        # 驗證結果
        assert result["total_score"] == 0.0
        assert result["passed"] is False
        assert result["question_scores"] == {1: 0.0, 2: 0.0, 3: 0.0}

    async def test_execute_verification_script_success(self, scoring_service, mock_vm_cluster_service):
        """測試成功執行驗證腳本"""
        # 設定模擬
        mock_vm_cluster_service.execute_verification_script.return_value = {
            "success": True,
            "output": "驗證成功\n總分：30/30",
            "exit_code": 0
        }

        # 執行測試
        result = await scoring_service._execute_verification_script(
            session_id="test-session",
            script_path="/path/to/verify.sh"
        )

        # 驗證結果
        assert result["success"] is True
        assert result["output"] == "驗證成功\n總分：30/30"

    async def test_execute_verification_script_failure(self, scoring_service, mock_vm_cluster_service):
        """測試驗證腳本執行失敗"""
        # 設定模擬
        mock_vm_cluster_service.execute_verification_script.return_value = {
            "success": False,
            "output": "驗證失敗：Pod 不存在",
            "exit_code": 1
        }

        # 執行測試
        result = await scoring_service._execute_verification_script(
            session_id="test-session",
            script_path="/path/to/verify.sh"
        )

        # 驗證結果
        assert result["success"] is False
        assert "Pod 不存在" in result["output"]

    async def test_parse_verification_result_json_format(self, scoring_service):
        """測試解析 JSON 格式的驗證結果"""
        # 測試有效的 JSON 輸出
        json_output = '{"earned_points": 25, "total_points": 30, "success_rate": 83.33}'

        result = await scoring_service._parse_verification_result(json_output, 30.0)

        assert result["earned_points"] == 25.0
        assert result["success"] is True

    async def test_parse_verification_result_text_format(self, scoring_service):
        """測試解析純文字格式的驗證結果"""
        # 測試純文字輸出
        text_output = "✓ Pod 建立成功 (+10 分)\n✗ Service 配置錯誤\n總分：10/30"

        result = await scoring_service._parse_verification_result(text_output, 30.0)

        # 應該回退到基於退出碼的評分
        assert result["earned_points"] >= 0.0

    async def test_parse_verification_result_malformed_json(self, scoring_service):
        """測試解析格式錯誤的 JSON"""
        malformed_json = '{"earned_points": 25, "total_points": 30'  # 缺少結尾括號

        result = await scoring_service._parse_verification_result(malformed_json, 30.0)

        # 應該回退到預設評分方式
        assert "earned_points" in result

    async def test_calculate_weighted_scores(self, scoring_service, sample_question_set_data):
        """測試加權分數計算"""
        question_results = {
            1: {"earned_points": 25.0, "total_points": 30.0},
            2: {"earned_points": 35.0, "total_points": 40.0},
            3: {"earned_points": 15.0, "total_points": 30.0}
        }

        result = await scoring_service._calculate_weighted_scores(
            question_results, sample_question_set_data
        )

        # 驗證計算結果
        # 總分 = (25/30)*30 + (35/40)*40 + (15/30)*30 = 25 + 35 + 15 = 75
        assert result["total_score"] == 75.0
        assert result["question_scores"] == {1: 25.0, 2: 35.0, 3: 15.0}

    async def test_determine_pass_status(self, scoring_service, sample_question_set_data):
        """測試及格狀態判斷"""
        # 測試及格情況
        pass_result = await scoring_service._determine_pass_status(75.0, sample_question_set_data)
        assert pass_result is True

        # 測試不及格情況
        fail_result = await scoring_service._determine_pass_status(65.0, sample_question_set_data)
        assert fail_result is False

        # 測試邊界情況
        boundary_result = await scoring_service._determine_pass_status(70.0, sample_question_set_data)
        assert boundary_result is True

    async def test_save_exam_result(self, scoring_service, sample_exam_session, mock_db_session):
        """測試儲存考試結果"""
        score_data = {
            "total_score": 85.0,
            "passed": True,
            "question_scores": {1: 25.0, 2: 35.0, 3: 25.0},
            "execution_details": {"script1": "success", "script2": "success"}
        }

        # 執行測試
        result = await scoring_service._save_exam_result(sample_exam_session, score_data)

        # 驗證結果
        assert isinstance(result, ExamResult)
        assert result.total_score == 85.0
        assert result.passed is True

        # 驗證資料庫操作
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_error_handling_script_not_found(self, scoring_service, mock_vm_cluster_service):
        """測試腳本不存在的錯誤處理"""
        # 設定模擬
        mock_vm_cluster_service.execute_verification_script.side_effect = FileNotFoundError("Script not found")

        # 執行測試
        result = await scoring_service._execute_verification_script(
            session_id="test-session",
            script_path="/nonexistent/script.sh"
        )

        # 驗證錯誤處理
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    async def test_timeout_handling(self, scoring_service, mock_vm_cluster_service):
        """測試執行逾時處理"""
        # 設定模擬
        mock_vm_cluster_service.execute_verification_script.side_effect = asyncio.TimeoutError("Script timeout")

        # 執行測試
        result = await scoring_service._execute_verification_script(
            session_id="test-session",
            script_path="/path/to/slow_script.sh"
        )

        # 驗證逾時處理
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    async def test_concurrent_scoring_operations(self, scoring_service, sample_exam_session,
                                               mock_vm_cluster_service):
        """測試並發評分操作"""
        # 設定模擬
        mock_vm_cluster_service.execute_verification_script.return_value = {
            "success": True,
            "output": '{"earned_points": 30, "total_points": 30}',
            "exit_code": 0
        }

        # 建立多個會話
        sessions = []
        for i in range(3):
            session = ExamSession(
                id=f"test-session-{i}",
                question_set_id="cka/test-001",
                vm_cluster_config_id="test-cluster",
                status=ExamSessionStatus.COMPLETED,
                answers={"1": {"solution": "test"}},
                progress=100.0
            )
            session._question_set_data = sample_exam_session._question_set_data
            sessions.append(session)

        # 同時執行評分
        tasks = [scoring_service.score_exam_session(session) for session in sessions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 驗證沒有異常
        for result in results:
            assert not isinstance(result, Exception)
            assert "total_score" in result

    async def test_performance_metrics_collection(self, scoring_service, sample_exam_session,
                                                mock_vm_cluster_service):
        """測試效能指標收集"""
        # 設定模擬
        mock_vm_cluster_service.execute_verification_script.return_value = {
            "success": True,
            "output": '{"earned_points": 30, "total_points": 30, "execution_time": 2.5}',
            "exit_code": 0
        }

        # 記錄開始時間
        start_time = datetime.now()

        # 執行測試
        result = await scoring_service.score_exam_session(sample_exam_session)

        # 計算執行時間
        execution_time = (datetime.now() - start_time).total_seconds()

        # 驗證效能
        assert execution_time < 10.0  # 應該在 10 秒內完成
        assert result["total_score"] >= 0.0

    async def test_detailed_scoring_breakdown(self, scoring_service, sample_exam_session,
                                            mock_vm_cluster_service):
        """測試詳細評分細節"""
        # 設定模擬：詳細的驗證結果
        mock_vm_cluster_service.execute_verification_script.side_effect = [
            {
                "success": True,
                "output": json.dumps({
                    "earned_points": 25,
                    "total_points": 30,
                    "details": {
                        "pod_created": True,
                        "pod_running": True,
                        "image_correct": False
                    }
                }),
                "exit_code": 0
            },
            {
                "success": True,
                "output": json.dumps({
                    "earned_points": 40,
                    "total_points": 40,
                    "details": {
                        "service_created": True,
                        "port_correct": True,
                        "selector_correct": True
                    }
                }),
                "exit_code": 0
            },
            {
                "success": False,
                "output": json.dumps({
                    "earned_points": 0,
                    "total_points": 30,
                    "details": {
                        "policy_created": False,
                        "selector_correct": False
                    }
                }),
                "exit_code": 1
            }
        ]

        # 執行測試
        result = await scoring_service.score_exam_session(sample_exam_session)

        # 驗證詳細結果
        assert result["total_score"] == 65.0  # (25 + 40 + 0) / 100 * 100
        assert result["passed"] is False
        assert "execution_details" in result

    async def test_scoring_edge_cases(self, scoring_service, sample_exam_session):
        """測試評分邊界情況"""
        # 測試空題組
        sample_exam_session._question_set_data.questions = []

        result = await scoring_service.score_exam_session(sample_exam_session)

        # 應該處理空題組情況
        assert result["total_score"] == 0.0
        assert result["passed"] is False

    async def test_database_transaction_rollback(self, scoring_service, sample_exam_session,
                                               mock_db_session, mock_vm_cluster_service):
        """測試資料庫事務回滾"""
        # 設定模擬：評分成功但資料庫儲存失敗
        mock_vm_cluster_service.execute_verification_script.return_value = {
            "success": True,
            "output": '{"earned_points": 30, "total_points": 30}',
            "exit_code": 0
        }
        mock_db_session.commit.side_effect = Exception("Database error")

        # 執行測試並驗證異常處理
        with pytest.raises(Exception):
            await scoring_service.score_exam_session(sample_exam_session)

        # 驗證回滾被呼叫
        mock_db_session.rollback.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])