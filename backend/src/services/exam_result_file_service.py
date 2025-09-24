"""
T068: 考試結果檔案服務
處理考試結果的檔案備份和管理
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExamResultFileService:
    """考試結果檔案管理服務"""

    def __init__(self, base_dir: str = "data/exam_results"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_exam_result(self,
                        session_id: str,
                        result_data: Dict[str, Any],
                        include_session_backup: bool = True) -> Dict[str, Any]:
        """儲存考試結果"""
        try:
            # 建立結果檔案名稱
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            result_filename = f"{session_id}_{timestamp}.json"
            result_path = self.base_dir / result_filename

            # 準備完整的結果資料
            complete_result = {
                "session_id": session_id,
                "saved_at": datetime.utcnow().isoformat(),
                "result_data": result_data
            }

            # 如果需要，添加會話備份資訊
            if include_session_backup:
                complete_result["session_backup"] = {
                    "included": True,
                    "backup_timestamp": timestamp
                }

            # 寫入結果檔案
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(complete_result, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"考試結果已儲存: {result_path}")

            return {
                "session_id": session_id,
                "result_file": str(result_path),
                "filename": result_filename,
                "saved_at": complete_result["saved_at"],
                "file_size": result_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"儲存考試結果失敗: {e}")
            raise RuntimeError(f"儲存考試結果失敗: {str(e)}")

    def load_exam_result(self, filename: str) -> Dict[str, Any]:
        """載入考試結果"""
        result_path = self.base_dir / filename

        if not result_path.exists():
            raise FileNotFoundError(f"考試結果檔案不存在: {filename}")

        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"載入考試結果失敗: {e}")
            raise ValueError(f"載入考試結果失敗: {str(e)}")

    def list_exam_results(self,
                         session_id: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出考試結果"""
        results = []

        try:
            # 掃描所有 JSON 檔案
            for result_file in self.base_dir.glob("*.json"):
                try:
                    file_info = {
                        "filename": result_file.name,
                        "path": str(result_file),
                        "size": result_file.stat().st_size,
                        "created_at": datetime.fromtimestamp(result_file.stat().st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(result_file.stat().st_mtime).isoformat()
                    }

                    # 嘗試解析檔案名稱以取得會話 ID
                    filename_parts = result_file.stem.split('_')
                    if len(filename_parts) >= 2:
                        file_session_id = '_'.join(filename_parts[:-2])  # 移除日期和時間部分
                        file_info["session_id"] = file_session_id

                        # 如果指定了會話 ID，則過濾
                        if session_id and file_session_id != session_id:
                            continue

                    # 嘗試讀取基本資訊
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)

                        file_info["session_id"] = result_data.get("session_id", file_info.get("session_id"))
                        file_info["saved_at"] = result_data.get("saved_at")

                        # 提取結果摘要
                        if "result_data" in result_data:
                            result_summary = result_data["result_data"]
                            file_info["summary"] = {
                                "total_score": result_summary.get("total_score"),
                                "max_score": result_summary.get("max_score"),
                                "pass_rate": result_summary.get("pass_rate"),
                                "status": result_summary.get("status"),
                                "questions_attempted": len(result_summary.get("question_results", [])),
                                "duration_minutes": result_summary.get("duration_minutes")
                            }

                    except Exception as e:
                        file_info["error"] = f"無法讀取檔案內容: {str(e)}"

                    results.append(file_info)

                except Exception as e:
                    logger.error(f"處理結果檔案失敗 {result_file}: {e}")

            # 按修改時間排序（最新的在前）
            results.sort(key=lambda x: x.get("modified_at", ""), reverse=True)

            # 限制數量
            if limit:
                results = results[:limit]

            return results

        except Exception as e:
            logger.error(f"列出考試結果失敗: {e}")
            raise RuntimeError(f"列出考試結果失敗: {str(e)}")

    def delete_exam_result(self, filename: str, create_backup: bool = True) -> Dict[str, Any]:
        """刪除考試結果"""
        result_path = self.base_dir / filename

        if not result_path.exists():
            raise FileNotFoundError(f"考試結果檔案不存在: {filename}")

        try:
            backup_info = None

            if create_backup:
                # 建立備份
                backup_filename = f"{result_path.stem}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.deleted.json"
                backup_path = self.base_dir / backup_filename
                result_path.rename(backup_path)

                backup_info = {
                    "backup_filename": backup_filename,
                    "backup_path": str(backup_path)
                }

                logger.info(f"考試結果已刪除並備份到: {backup_path}")
            else:
                # 直接刪除
                result_path.unlink()
                logger.info(f"考試結果已刪除: {result_path}")

            return {
                "filename": filename,
                "deleted_at": datetime.utcnow().isoformat(),
                "backup_created": create_backup,
                "backup_info": backup_info
            }

        except Exception as e:
            logger.error(f"刪除考試結果失敗: {e}")
            raise RuntimeError(f"刪除考試結果失敗: {str(e)}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """取得儲存統計資訊"""
        try:
            result_files = list(self.base_dir.glob("*.json"))
            backup_files = list(self.base_dir.glob("*.deleted.json"))

            total_size = sum(f.stat().st_size for f in result_files + backup_files)
            result_size = sum(f.stat().st_size for f in result_files)
            backup_size = sum(f.stat().st_size for f in backup_files)

            # 統計各會話的結果數量
            session_counts = {}
            for result_file in result_files:
                filename_parts = result_file.stem.split('_')
                if len(filename_parts) >= 2:
                    session_id = '_'.join(filename_parts[:-2])
                    session_counts[session_id] = session_counts.get(session_id, 0) + 1

            return {
                "total_files": len(result_files),
                "backup_files": len(backup_files),
                "total_size_bytes": total_size,
                "result_size_bytes": result_size,
                "backup_size_bytes": backup_size,
                "sessions_with_results": len(session_counts),
                "session_result_counts": session_counts,
                "directory": str(self.base_dir),
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"取得儲存統計失敗: {e}")
            raise RuntimeError(f"取得儲存統計失敗: {str(e)}")

    def cleanup_old_results(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """清理舊的考試結果"""
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days_to_keep * 24 * 3600)
            cleaned_files = []
            errors = []

            for result_file in self.base_dir.glob("*.json"):
                try:
                    if result_file.stat().st_mtime < cutoff_date:
                        # 建立備份名稱
                        backup_name = f"{result_file.stem}.cleaned_{datetime.now().strftime('%Y%m%d')}.json"
                        backup_path = self.base_dir / backup_name

                        result_file.rename(backup_path)
                        cleaned_files.append({
                            "original": result_file.name,
                            "backup": backup_name,
                            "age_days": (datetime.utcnow().timestamp() - result_file.stat().st_mtime) / (24 * 3600)
                        })

                except Exception as e:
                    errors.append(f"清理檔案失敗 {result_file.name}: {str(e)}")

            logger.info(f"清理完成，處理了 {len(cleaned_files)} 個檔案")

            return {
                "cleaned_files": len(cleaned_files),
                "errors": len(errors),
                "files_cleaned": cleaned_files,
                "error_details": errors,
                "days_kept": days_to_keep,
                "cleaned_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"清理舊結果失敗: {e}")
            raise RuntimeError(f"清理舊結果失敗: {str(e)}")


# 全域考試結果檔案服務實例
exam_result_file_service = ExamResultFileService()


def get_exam_result_file_service() -> ExamResultFileService:
    """取得考試結果檔案服務依賴注入"""
    return exam_result_file_service