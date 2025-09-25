"""
T027: QuestionSetFileManager 類別
題組檔案管理器，負載入和監控 JSON 檔案
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from watchfiles import watch
import asyncio
import logging
from datetime import datetime

from ..models.question_set_data import QuestionSetData, QuestionSetMetadata, QuestionData

logger = logging.getLogger(__name__)


class QuestionSetFileManager:
    """題組檔案管理器"""

    def __init__(self, base_dir: str = "data/question_sets"):
        self.base_dir = Path(base_dir)
        self._question_sets: Dict[str, QuestionSetData] = {}
        self._file_timestamps: Dict[str, float] = {}
        self._watcher_task: Optional[asyncio.Task] = None
        self._callbacks: Set[callable] = set()

    async def initialize(self) -> None:
        """初始化管理器"""
        logger.info(f"初始化題組檔案管理器，基礎目錄: {self.base_dir}")
        await self.load_all_question_sets()
        await self.start_file_watcher()

    async def shutdown(self) -> None:
        """關閉管理器"""
        if self._watcher_task:
            self._watcher_task.cancel()
            try:
                await self._watcher_task
            except asyncio.CancelledError:
                pass
        logger.info("題組檔案管理器已關閉")

    def add_change_callback(self, callback: callable) -> None:
        """添加檔案變更回調"""
        self._callbacks.add(callback)

    def remove_change_callback(self, callback: callable) -> None:
        """移除檔案變更回調"""
        self._callbacks.discard(callback)

    async def load_all_question_sets(self) -> Dict[str, List[str]]:
        """載入所有題組"""
        results = {"loaded": [], "errors": []}

        if not self.base_dir.exists():
            logger.warning(f"題組目錄不存在: {self.base_dir}")
            return results

        # 掃描所有認證類型目錄
        for exam_type_dir in self.base_dir.iterdir():
            if not exam_type_dir.is_dir():
                continue

            exam_type = exam_type_dir.name.upper()
            logger.info(f"掃描認證類型目錄: {exam_type}")

            # 掃描該認證類型下的所有題組目錄
            for set_dir in exam_type_dir.iterdir():
                if not set_dir.is_dir():
                    continue

                set_id = set_dir.name
                logger.info(f"掃描題組目錄: {exam_type}/{set_id}")

                # 查找 metadata.json 和 questions.json 檔案
                metadata_file = set_dir / "metadata.json"
                questions_file = set_dir / "questions.json"

                if not metadata_file.exists():
                    error_msg = f"找不到 metadata.json: {metadata_file}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue

                if not questions_file.exists():
                    error_msg = f"找不到 questions.json: {questions_file}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    continue

                try:
                    question_set = await self._load_question_set(set_dir, exam_type, set_id)
                    if question_set:
                        self._question_sets[question_set.id] = question_set
                        results["loaded"].append(question_set.id)
                        logger.info(f"成功載入題組: {question_set.id}")
                except Exception as e:
                    error_msg = f"載入題組失敗 {exam_type}/{set_id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

        logger.info(f"題組載入完成，成功: {len(results['loaded'])}, 錯誤: {len(results['errors'])}")
        return results

    async def _load_question_set(self, set_dir: Path, exam_type: str, set_id: str) -> Optional[QuestionSetData]:
        """載入單個題組"""
        metadata_file = set_dir / "metadata.json"
        questions_file = set_dir / "questions.json"
        scripts_dir = set_dir / "scripts"

        # 載入 metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_data = json.load(f)

        # 載入 questions
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        # 驗證和建立模型
        metadata = QuestionSetMetadata(**metadata_data)
        questions = [QuestionData(**q) for q in questions_data["questions"]]

        # 更新檔案時間戳
        self._file_timestamps[str(metadata_file)] = metadata_file.stat().st_mtime
        self._file_timestamps[str(questions_file)] = questions_file.stat().st_mtime

        # 建立題組資料
        question_set = QuestionSetData(
            set_id=set_id,
            exam_type=exam_type,
            metadata=metadata,
            questions=questions,
            scripts_path=str(scripts_dir) if scripts_dir.exists() else "",
            file_paths={
                "metadata": str(metadata_file),
                "questions": str(questions_file),
                "scripts": str(scripts_dir) if scripts_dir.exists() else ""
            },
            loaded_at=datetime.utcnow(),
            file_modified_at=datetime.fromtimestamp(max(
                metadata_file.stat().st_mtime,
                questions_file.stat().st_mtime
            ))
        )

        return question_set

    async def start_file_watcher(self) -> None:
        """啟動檔案監控器"""
        if not self.base_dir.exists():
            logger.warning("題組目錄不存在，跳過檔案監控")
            return

        self._watcher_task = asyncio.create_task(self._watch_files())
        logger.info("檔案監控器已啟動")

    async def _watch_files(self) -> None:
        """檔案監控循環"""
        try:
            async for changes in watch(str(self.base_dir)):
                logger.info(f"檢測到檔案變更: {changes}")
                await self._handle_file_changes(changes)
        except asyncio.CancelledError:
            logger.info("檔案監控器已停止")
            raise
        except Exception as e:
            logger.error(f"檔案監控器錯誤: {e}")

    async def _handle_file_changes(self, changes) -> None:
        """處理檔案變更"""
        changed_dirs = set()

        for change_type, file_path in changes:
            file_path = Path(file_path)
            if file_path.name in ["metadata.json", "questions.json"]:
                changed_dirs.add(file_path.parent)

        # 重新載入變更的題組
        for set_dir in changed_dirs:
            try:
                # 從路徑解析認證類型和題組 ID
                exam_type = set_dir.parent.name.upper()
                set_id = set_dir.name

                question_set = await self._load_question_set(set_dir, exam_type, set_id)
                if question_set:
                    old_set = self._question_sets.get(question_set.id)
                    self._question_sets[question_set.id] = question_set

                    # 通知回調
                    for callback in self._callbacks:
                        try:
                            await callback(question_set.id, old_set, question_set)
                        except Exception as e:
                            logger.error(f"回調執行失敗: {e}")

                    logger.info(f"重新載入題組: {question_set.id}")
            except Exception as e:
                logger.error(f"重新載入題組失敗 {set_dir}: {e}")

    def get_question_set(self, set_id: str) -> Optional[QuestionSetData]:
        """獲取題組"""
        return self._question_sets.get(set_id)

    def get_all_question_sets(self) -> Dict[str, QuestionSetData]:
        """獲取所有題組"""
        return self._question_sets.copy()

    def list_question_sets(self, certification_type: Optional[str] = None) -> List[QuestionSetData]:
        """列出題組（支援篩選）"""
        question_sets = list(self._question_sets.values())

        if certification_type:
            question_sets = [qs for qs in question_sets
                           if qs.certification_type.lower() == certification_type.lower()]

        return question_sets

    async def reload_question_sets(self) -> Dict[str, List[str]]:
        """手動重新載入所有題組"""
        logger.info("手動重新載入所有題組")
        self._question_sets.clear()
        self._file_timestamps.clear()
        return await self.load_all_question_sets()

    def get_stats(self) -> Dict[str, any]:
        """獲取統計資訊"""
        total_questions = sum(len(qs.questions) for qs in self._question_sets.values())
        by_cert_type = {}
        by_difficulty = {}

        for qs in self._question_sets.values():
            cert_type = qs.certification_type
            difficulty = qs.metadata.difficulty

            by_cert_type[cert_type] = by_cert_type.get(cert_type, 0) + 1
            by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1

        return {
            "total_question_sets": len(self._question_sets),
            "total_questions": total_questions,
            "by_certification_type": by_cert_type,
            "by_difficulty": by_difficulty,
            "last_loaded": datetime.utcnow().isoformat()
        }