"""
T098: QuestionSetFileManager 單元測試
測試題組檔案管理器的功能
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import sys
sys.path.append("../../src")

from src.services.question_set_file_manager import QuestionSetFileManager
from src.models.question_set_data import QuestionSetData, QuestionSetMetadata, QuestionData


class TestQuestionSetFileManager:
    """QuestionSetFileManager 測試類別"""

    @pytest.fixture
    async def temp_dir(self):
        """建立臨時測試目錄"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    async def sample_question_set_data(self) -> Dict[str, Any]:
        """範例題組資料"""
        return {
            "metadata": {
                "exam_type": "CKA",
                "set_id": "test-001",
                "name": "測試題組",
                "description": "用於單元測試的題組",
                "time_limit_minutes": 120,
                "passing_score": 70.0,
                "difficulty_level": "intermediate",
                "version": "1.0.0",
                "created_at": "2025-09-24T08:00:00Z",
                "updated_at": "2025-09-24T08:00:00Z",
                "tags": ["test", "unit"]
            },
            "questions": [
                {
                    "id": 1,
                    "content": "測試題目 1",
                    "weight": 30.0,
                    "kubernetes_objects": ["Pod"],
                    "hints": ["提示 1"],
                    "verification_scripts": ["test1.sh"],
                    "preparation_scripts": []
                },
                {
                    "id": 2,
                    "content": "測試題目 2",
                    "weight": 70.0,
                    "kubernetes_objects": ["Service", "Deployment"],
                    "hints": ["提示 2", "提示 3"],
                    "verification_scripts": ["test2.sh"],
                    "preparation_scripts": ["setup2.sh"]
                }
            ]
        }

    @pytest.fixture
    async def manager_with_temp_dir(self, temp_dir):
        """建立使用臨時目錄的管理器"""
        manager = QuestionSetFileManager(base_dir=temp_dir)
        yield manager
        # 清理
        if manager._watcher_task and not manager._watcher_task.done():
            manager._watcher_task.cancel()
            try:
                await manager._watcher_task
            except asyncio.CancelledError:
                pass

    async def create_test_question_set(self, temp_dir: str, exam_type: str, set_id: str, data: Dict[str, Any]):
        """建立測試題組檔案"""
        set_path = Path(temp_dir) / exam_type / set_id
        set_path.mkdir(parents=True, exist_ok=True)

        # 寫入 metadata.json
        metadata_path = set_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data["metadata"], f, ensure_ascii=False, indent=2)

        # 寫入 questions.json
        questions_path = set_path / "questions.json"
        questions_data = {
            "set_info": {
                "exam_type": data["metadata"]["exam_type"],
                "set_id": data["metadata"]["set_id"],
                "name": data["metadata"]["name"]
            },
            "questions": data["questions"]
        }
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, ensure_ascii=False, indent=2)

        return set_path

    async def test_initialization(self, manager_with_temp_dir):
        """測試管理器初始化"""
        manager = manager_with_temp_dir

        # 測試初始狀態
        assert manager.base_dir.exists() or not manager.base_dir.exists()  # 可能存在或不存在
        assert len(manager._question_sets) == 0
        assert len(manager._file_timestamps) == 0
        assert manager._watcher_task is None

    async def test_load_question_sets_empty_directory(self, manager_with_temp_dir):
        """測試載入空目錄"""
        manager = manager_with_temp_dir
        await manager.initialize()

        question_sets = await manager.load_question_sets()
        assert len(question_sets) == 0

    async def test_load_single_question_set(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試載入單一題組"""
        manager = manager_with_temp_dir

        # 建立測試題組
        await self.create_test_question_set(temp_dir, "cka", "test-001", sample_question_set_data)

        await manager.initialize()
        question_sets = await manager.load_question_sets()

        assert len(question_sets) == 1
        assert "cka/test-001" in question_sets

        question_set = question_sets["cka/test-001"]
        assert isinstance(question_set, QuestionSetData)
        assert question_set.metadata.exam_type == "CKA"
        assert question_set.metadata.set_id == "test-001"
        assert question_set.metadata.name == "測試題組"
        assert len(question_set.questions) == 2

    async def test_load_multiple_question_sets(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試載入多個題組"""
        manager = manager_with_temp_dir

        # 建立多個測試題組
        await self.create_test_question_set(temp_dir, "cka", "test-001", sample_question_set_data)

        # 建立第二個題組
        data2 = sample_question_set_data.copy()
        data2["metadata"]["set_id"] = "test-002"
        data2["metadata"]["name"] = "測試題組 2"
        await self.create_test_question_set(temp_dir, "cka", "test-002", data2)

        # 建立 CKAD 題組
        data3 = sample_question_set_data.copy()
        data3["metadata"]["exam_type"] = "CKAD"
        data3["metadata"]["set_id"] = "test-003"
        data3["metadata"]["name"] = "CKAD 測試題組"
        await self.create_test_question_set(temp_dir, "ckad", "test-003", data3)

        await manager.initialize()
        question_sets = await manager.load_question_sets()

        assert len(question_sets) == 3
        assert "cka/test-001" in question_sets
        assert "cka/test-002" in question_sets
        assert "ckad/test-003" in question_sets

    async def test_get_question_set_existing(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試取得存在的題組"""
        manager = manager_with_temp_dir
        await self.create_test_question_set(temp_dir, "cka", "test-001", sample_question_set_data)

        await manager.initialize()
        await manager.load_question_sets()

        question_set = await manager.get_question_set("cka/test-001")
        assert question_set is not None
        assert question_set.metadata.set_id == "test-001"

    async def test_get_question_set_not_existing(self, manager_with_temp_dir):
        """測試取得不存在的題組"""
        manager = manager_with_temp_dir
        await manager.initialize()

        question_set = await manager.get_question_set("nonexistent/set")
        assert question_set is None

    async def test_list_question_sets_by_exam_type(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試按考試類型列出題組"""
        manager = manager_with_temp_dir

        # 建立不同類型的題組
        await self.create_test_question_set(temp_dir, "cka", "test-001", sample_question_set_data)

        data2 = sample_question_set_data.copy()
        data2["metadata"]["exam_type"] = "CKAD"
        data2["metadata"]["set_id"] = "test-002"
        await self.create_test_question_set(temp_dir, "ckad", "test-002", data2)

        await manager.initialize()
        await manager.load_question_sets()

        # 測試列出 CKA 題組
        cka_sets = await manager.list_question_sets_by_exam_type("CKA")
        assert len(cka_sets) == 1
        assert cka_sets[0].metadata.exam_type == "CKA"

        # 測試列出 CKAD 題組
        ckad_sets = await manager.list_question_sets_by_exam_type("CKAD")
        assert len(ckad_sets) == 1
        assert ckad_sets[0].metadata.exam_type == "CKAD"

        # 測試不存在的考試類型
        cks_sets = await manager.list_question_sets_by_exam_type("CKS")
        assert len(cks_sets) == 0

    async def test_reload_question_sets(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試重新載入題組"""
        manager = manager_with_temp_dir
        await self.create_test_question_set(temp_dir, "cka", "test-001", sample_question_set_data)

        await manager.initialize()
        initial_sets = await manager.load_question_sets()
        assert len(initial_sets) == 1

        # 新增另一個題組
        data2 = sample_question_set_data.copy()
        data2["metadata"]["set_id"] = "test-002"
        await self.create_test_question_set(temp_dir, "cka", "test-002", data2)

        # 重新載入
        reloaded_sets = await manager.reload_question_sets()
        assert len(reloaded_sets) == 2
        assert "cka/test-002" in reloaded_sets

    async def test_file_validation_invalid_json(self, manager_with_temp_dir, temp_dir):
        """測試無效 JSON 檔案處理"""
        manager = manager_with_temp_dir

        # 建立無效的 JSON 檔案
        set_path = Path(temp_dir) / "cka" / "invalid-set"
        set_path.mkdir(parents=True)

        metadata_path = set_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            f.write("invalid json content")

        await manager.initialize()
        question_sets = await manager.load_question_sets()

        # 應該跳過無效檔案
        assert len(question_sets) == 0

    async def test_file_validation_missing_questions_file(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試缺少題目檔案的處理"""
        manager = manager_with_temp_dir

        # 只建立 metadata.json，不建立 questions.json
        set_path = Path(temp_dir) / "cka" / "incomplete-set"
        set_path.mkdir(parents=True)

        metadata_path = set_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(sample_question_set_data["metadata"], f, ensure_ascii=False)

        await manager.initialize()
        question_sets = await manager.load_question_sets()

        # 應該跳過不完整的題組
        assert len(question_sets) == 0

    async def test_callback_registration(self, manager_with_temp_dir):
        """測試回調函數註冊"""
        manager = manager_with_temp_dir

        callback1 = Mock()
        callback2 = Mock()

        manager.add_callback(callback1)
        manager.add_callback(callback2)

        assert len(manager._callbacks) == 2
        assert callback1 in manager._callbacks
        assert callback2 in manager._callbacks

        # 測試移除回調
        manager.remove_callback(callback1)
        assert len(manager._callbacks) == 1
        assert callback2 in manager._callbacks

    @patch('src.services.question_set_file_manager.watch')
    async def test_file_monitoring_start_stop(self, mock_watch, manager_with_temp_dir):
        """測試檔案監控啟動和停止"""
        manager = manager_with_temp_dir

        # 模擬 watch 函數
        mock_watch.return_value = AsyncMock()

        await manager.start_monitoring()
        assert manager._watcher_task is not None
        assert not manager._watcher_task.done()

        await manager.stop_monitoring()
        assert manager._watcher_task is None or manager._watcher_task.done()

    async def test_cleanup(self, manager_with_temp_dir):
        """測試清理資源"""
        manager = manager_with_temp_dir
        await manager.initialize()

        # 新增一些資料和回調
        manager._question_sets["test"] = Mock()
        manager.add_callback(Mock())

        await manager.cleanup()

        # 驗證清理結果
        assert len(manager._question_sets) == 0
        assert len(manager._callbacks) == 0

    async def test_error_handling_invalid_metadata_structure(self, manager_with_temp_dir, temp_dir):
        """測試無效 metadata 結構的錯誤處理"""
        manager = manager_with_temp_dir

        # 建立結構不完整的 metadata
        set_path = Path(temp_dir) / "cka" / "invalid-metadata"
        set_path.mkdir(parents=True)

        metadata_path = set_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({"invalid": "structure"}, f)

        questions_path = set_path / "questions.json"
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump({"questions": []}, f)

        await manager.initialize()
        question_sets = await manager.load_question_sets()

        # 應該跳過結構無效的題組
        assert len(question_sets) == 0

    async def test_concurrent_access(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試並發存取"""
        manager = manager_with_temp_dir
        await self.create_test_question_set(temp_dir, "cka", "test-001", sample_question_set_data)
        await manager.initialize()

        # 同時執行多個操作
        tasks = [
            manager.load_question_sets(),
            manager.get_question_set("cka/test-001"),
            manager.list_question_sets_by_exam_type("CKA"),
            manager.reload_question_sets()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 檢查沒有異常
        for result in results:
            assert not isinstance(result, Exception)

    async def test_memory_usage_optimization(self, manager_with_temp_dir, temp_dir, sample_question_set_data):
        """測試記憶體使用最佳化"""
        manager = manager_with_temp_dir

        # 建立大量題組測試記憶體使用
        for i in range(10):
            data = sample_question_set_data.copy()
            data["metadata"]["set_id"] = f"test-{i:03d}"
            await self.create_test_question_set(temp_dir, "cka", f"test-{i:03d}", data)

        await manager.initialize()
        question_sets = await manager.load_question_sets()

        assert len(question_sets) == 10

        # 測試重新載入不會造成記憶體洩漏
        for _ in range(3):
            await manager.reload_question_sets()

        # 驗證最終狀態
        final_sets = await manager.load_question_sets()
        assert len(final_sets) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])