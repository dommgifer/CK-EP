"""
T099: ExamSessionService 單元測試
測試考試會話服務的功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any, Optional
from uuid import uuid4

import sys
sys.path.append("../../src")

from src.services.exam_session_service import ExamSessionService
from src.models.exam_session import ExamSession, ExamSessionStatus
from src.models.question_set_data import QuestionSetData, QuestionSetMetadata, QuestionData
from src.services.question_set_file_manager import QuestionSetFileManager
from src.services.vm_cluster_service import VMClusterService
from src.services.scoring_service import ScoringService


class TestExamSessionService:
    """ExamSessionService 測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫會話"""
        mock_session = Mock()
        mock_session.query.return_value = mock_session
        mock_session.filter.return_value = mock_session
        mock_session.first.return_value = None
        mock_session.all.return_value = []
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        mock_session.refresh = Mock()
        return mock_session

    @pytest.fixture
    def mock_question_set_manager(self):
        """模擬題組管理器"""
        manager = Mock(spec=QuestionSetFileManager)
        manager.get_question_set = AsyncMock()
        manager.list_question_sets_by_exam_type = AsyncMock(return_value=[])
        return manager

    @pytest.fixture
    def mock_vm_cluster_service(self):
        """模擬 VM 叢集服務"""
        service = Mock(spec=VMClusterService)
        service.setup_kubernetes_cluster = AsyncMock()
        service.cleanup_cluster = AsyncMock()
        service.get_cluster_status = AsyncMock()
        return service

    @pytest.fixture
    def mock_scoring_service(self):
        """模擬評分服務"""
        service = Mock(spec=ScoringService)
        service.score_exam_session = AsyncMock()
        return service

    @pytest.fixture
    def exam_session_service(self, mock_db_session, mock_question_set_manager,
                           mock_vm_cluster_service, mock_scoring_service):
        """考試會話服務實例"""
        service = ExamSessionService(
            db_session=mock_db_session,
            question_set_manager=mock_question_set_manager,
            vm_cluster_service=mock_vm_cluster_service,
            scoring_service=mock_scoring_service
        )
        return service

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
                content="測試題目 1",
                weight=30.0,
                kubernetes_objects=["Pod"],
                hints=["提示 1"],
                verification_scripts=["test1.sh"],
                preparation_scripts=[]
            ),
            QuestionData(
                id=2,
                content="測試題目 2",
                weight=70.0,
                kubernetes_objects=["Service"],
                hints=["提示 2"],
                verification_scripts=["test2.sh"],
                preparation_scripts=[]
            )
        ]

        return QuestionSetData(metadata=metadata, questions=questions)

    @pytest.fixture
    def sample_exam_session(self) -> ExamSession:
        """範例考試會話"""
        session_id = str(uuid4())
        return ExamSession(
            id=session_id,
            question_set_id="cka/test-001",
            vm_cluster_config_id="test-cluster",
            status=ExamSessionStatus.CREATED,
            created_at=datetime.now(timezone.utc),
            time_limit_minutes=120,
            current_question_index=0,
            answers={},
            progress=0.0,
            vnc_url=None,
            environment_ready=False
        )

    async def test_create_exam_session_success(self, exam_session_service, mock_question_set_manager,
                                             sample_question_set_data, mock_db_session):
        """測試成功建立考試會話"""
        # 設定模擬
        mock_question_set_manager.get_question_set.return_value = sample_question_set_data
        mock_db_session.query.return_value.filter.return_value.first.return_value = None  # 沒有活動會話

        # 執行測試
        session = await exam_session_service.create_exam_session(
            question_set_id="cka/test-001",
            vm_cluster_config_id="test-cluster"
        )

        # 驗證結果
        assert session is not None
        assert session.question_set_id == "cka/test-001"
        assert session.vm_cluster_config_id == "test-cluster"
        assert session.status == ExamSessionStatus.CREATED
        assert session.time_limit_minutes == 120
        assert session.current_question_index == 0

        # 驗證呼叫
        mock_question_set_manager.get_question_set.assert_called_once_with("cka/test-001")
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_create_exam_session_question_set_not_found(self, exam_session_service,
                                                            mock_question_set_manager):
        """測試題組不存在時建立會話失敗"""
        # 設定模擬
        mock_question_set_manager.get_question_set.return_value = None

        # 執行測試並驗證異常
        with pytest.raises(ValueError, match="題組不存在"):
            await exam_session_service.create_exam_session(
                question_set_id="nonexistent/set",
                vm_cluster_config_id="test-cluster"
            )

    async def test_create_exam_session_active_session_exists(self, exam_session_service,
                                                           mock_question_set_manager,
                                                           sample_question_set_data,
                                                           mock_db_session,
                                                           sample_exam_session):
        """測試已有活動會話時建立會話失敗"""
        # 設定模擬
        mock_question_set_manager.get_question_set.return_value = sample_question_set_data
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試並驗證異常
        with pytest.raises(RuntimeError, match="已有活動的考試會話"):
            await exam_session_service.create_exam_session(
                question_set_id="cka/test-001",
                vm_cluster_config_id="test-cluster"
            )

    async def test_get_exam_session_existing(self, exam_session_service, mock_db_session,
                                           sample_exam_session):
        """測試取得存在的考試會話"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試
        session = await exam_session_service.get_exam_session(sample_exam_session.id)

        # 驗證結果
        assert session == sample_exam_session
        mock_db_session.query.assert_called_once_with(ExamSession)

    async def test_get_exam_session_not_found(self, exam_session_service, mock_db_session):
        """測試取得不存在的考試會話"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # 執行測試
        session = await exam_session_service.get_exam_session("nonexistent-id")

        # 驗證結果
        assert session is None

    async def test_start_exam_session_success(self, exam_session_service, mock_vm_cluster_service,
                                            mock_db_session, sample_exam_session):
        """測試成功開始考試會話"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.CREATED
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session
        mock_vm_cluster_service.setup_kubernetes_cluster.return_value = {
            "vnc_url": "http://localhost:6080/vnc.html",
            "cluster_ready": True
        }

        # 執行測試
        result = await exam_session_service.start_exam_session(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True
        assert sample_exam_session.status == ExamSessionStatus.IN_PROGRESS
        assert sample_exam_session.started_at is not None
        assert sample_exam_session.vnc_url == "http://localhost:6080/vnc.html"
        assert sample_exam_session.environment_ready is True

        # 驗證呼叫
        mock_vm_cluster_service.setup_kubernetes_cluster.assert_called_once()
        mock_db_session.commit.assert_called()

    async def test_start_exam_session_invalid_status(self, exam_session_service, mock_db_session,
                                                   sample_exam_session):
        """測試無效狀態時開始考試失敗"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.COMPLETED
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試並驗證異常
        with pytest.raises(ValueError, match="只能開始狀態為 CREATED 的考試會話"):
            await exam_session_service.start_exam_session(sample_exam_session.id)

    async def test_pause_exam_session(self, exam_session_service, mock_db_session, sample_exam_session):
        """測試暫停考試會話"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試
        result = await exam_session_service.pause_exam_session(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True
        assert sample_exam_session.status == ExamSessionStatus.PAUSED
        assert sample_exam_session.paused_at is not None

        # 驗證呼叫
        mock_db_session.commit.assert_called()

    async def test_resume_exam_session(self, exam_session_service, mock_db_session, sample_exam_session):
        """測試恢復考試會話"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.PAUSED
        sample_exam_session.paused_at = datetime.now(timezone.utc)
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試
        result = await exam_session_service.resume_exam_session(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True
        assert sample_exam_session.status == ExamSessionStatus.IN_PROGRESS
        assert sample_exam_session.resumed_at is not None

        # 驗證呼叫
        mock_db_session.commit.assert_called()

    async def test_submit_answer(self, exam_session_service, mock_db_session, sample_exam_session):
        """測試提交答案"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        sample_exam_session.current_question_index = 0
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試
        answer_data = {"solution": "kubectl create pod test --image=nginx"}
        result = await exam_session_service.submit_answer(
            sample_exam_session.id,
            question_id=1,
            answer=answer_data
        )

        # 驗證結果
        assert result["success"] is True
        assert "1" in sample_exam_session.answers
        assert sample_exam_session.answers["1"] == answer_data

        # 驗證呼叫
        mock_db_session.commit.assert_called()

    async def test_next_question(self, exam_session_service, mock_db_session, sample_exam_session,
                                mock_question_set_manager, sample_question_set_data):
        """測試移動到下一題"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        sample_exam_session.current_question_index = 0
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session
        mock_question_set_manager.get_question_set.return_value = sample_question_set_data

        # 執行測試
        result = await exam_session_service.next_question(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True
        assert sample_exam_session.current_question_index == 1
        assert result["question_id"] == 2

        # 驗證呼叫
        mock_db_session.commit.assert_called()

    async def test_previous_question(self, exam_session_service, mock_db_session, sample_exam_session,
                                   mock_question_set_manager, sample_question_set_data):
        """測試移動到上一題"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        sample_exam_session.current_question_index = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session
        mock_question_set_manager.get_question_set.return_value = sample_question_set_data

        # 執行測試
        result = await exam_session_service.previous_question(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True
        assert sample_exam_session.current_question_index == 0
        assert result["question_id"] == 1

        # 驗證呼叫
        mock_db_session.commit.assert_called()

    async def test_complete_exam_session(self, exam_session_service, mock_db_session,
                                       sample_exam_session, mock_scoring_service):
        """測試完成考試會話"""
        # 設定模擬
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        sample_exam_session.started_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session
        mock_scoring_service.score_exam_session.return_value = {
            "total_score": 85.0,
            "passed": True,
            "question_scores": {1: 25.0, 2: 60.0}
        }

        # 執行測試
        result = await exam_session_service.complete_exam_session(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True
        assert sample_exam_session.status == ExamSessionStatus.COMPLETED
        assert sample_exam_session.completed_at is not None
        assert sample_exam_session.final_score == 85.0

        # 驗證呼叫
        mock_scoring_service.score_exam_session.assert_called_once_with(sample_exam_session)
        mock_db_session.commit.assert_called()

    async def test_get_session_progress(self, exam_session_service, mock_db_session,
                                      sample_exam_session, mock_question_set_manager,
                                      sample_question_set_data):
        """測試取得會話進度"""
        # 設定模擬
        sample_exam_session.current_question_index = 1
        sample_exam_session.answers = {"1": {"solution": "answer1"}}
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session
        mock_question_set_manager.get_question_set.return_value = sample_question_set_data

        # 執行測試
        progress = await exam_session_service.get_session_progress(sample_exam_session.id)

        # 驗證結果
        assert progress["current_question_index"] == 1
        assert progress["total_questions"] == 2
        assert progress["answered_questions"] == 1
        assert progress["progress_percentage"] == 50.0
        assert progress["time_remaining"] is not None

    async def test_cleanup_session(self, exam_session_service, mock_db_session,
                                 sample_exam_session, mock_vm_cluster_service):
        """測試清理會話"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試
        result = await exam_session_service.cleanup_session(sample_exam_session.id)

        # 驗證結果
        assert result["success"] is True

        # 驗證呼叫
        mock_vm_cluster_service.cleanup_cluster.assert_called_once()

    async def test_time_limit_exceeded(self, exam_session_service, mock_db_session,
                                     sample_exam_session):
        """測試時間限制超過處理"""
        # 設定模擬：會話開始時間超過限制
        sample_exam_session.status = ExamSessionStatus.IN_PROGRESS
        sample_exam_session.started_at = datetime.now(timezone.utc) - timedelta(minutes=150)  # 超過120分鐘
        sample_exam_session.time_limit_minutes = 120
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 執行測試
        result = await exam_session_service.check_time_limit(sample_exam_session.id)

        # 驗證結果
        assert result["time_exceeded"] is True
        assert sample_exam_session.status == ExamSessionStatus.COMPLETED

    async def test_error_handling_database_error(self, exam_session_service, mock_db_session):
        """測試資料庫錯誤處理"""
        # 設定模擬
        mock_db_session.commit.side_effect = Exception("Database error")

        # 執行測試並驗證異常處理
        with pytest.raises(Exception):
            await exam_session_service.create_exam_session(
                question_set_id="cka/test-001",
                vm_cluster_config_id="test-cluster"
            )

        # 驗證回滾被呼叫
        mock_db_session.rollback.assert_called()

    async def test_concurrent_session_operations(self, exam_session_service, mock_db_session,
                                               sample_exam_session):
        """測試並發會話操作"""
        # 設定模擬
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 同時執行多個操作
        tasks = [
            exam_session_service.get_session_progress(sample_exam_session.id),
            exam_session_service.submit_answer(sample_exam_session.id, 1, {"test": "answer"}),
            exam_session_service.pause_exam_session(sample_exam_session.id)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 驗證沒有嚴重異常（某些可能因為狀態變更而失敗，這是正常的）
        serious_errors = [r for r in results if isinstance(r, Exception)
                         and not isinstance(r, (ValueError, RuntimeError))]
        assert len(serious_errors) == 0

    async def test_session_state_validation(self, exam_session_service, mock_db_session,
                                          sample_exam_session):
        """測試會話狀態驗證"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_exam_session

        # 測試在不同狀態下的操作限制
        test_cases = [
            (ExamSessionStatus.CREATED, "submit_answer", ValueError),
            (ExamSessionStatus.COMPLETED, "start_exam_session", ValueError),
            (ExamSessionStatus.PAUSED, "submit_answer", ValueError),
        ]

        for status, method, expected_exception in test_cases:
            sample_exam_session.status = status

            with pytest.raises(expected_exception):
                if method == "submit_answer":
                    await exam_session_service.submit_answer(sample_exam_session.id, 1, {})
                elif method == "start_exam_session":
                    await exam_session_service.start_exam_session(sample_exam_session.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])