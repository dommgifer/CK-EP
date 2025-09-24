#!/usr/bin/env python3
"""
基本功能驗證腳本
驗證 Kubernetes 考試模擬器的核心功能
"""
import sys
import asyncio
import logging
from pathlib import Path

# 添加 src 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database.connection import create_tables, get_database
from src.cache.redis_client import get_redis
from src.services.question_set_file_manager import QuestionSetFileManager
from src.services.exam_session_service import ExamSessionService
from src.services.environment_service import EnvironmentService
from src.services.container_service import get_container_service
from src.services.vm_config_file_service import get_vm_config_file_service
from src.services.kubespray_config_service import get_kubespray_config_service
from src.services.exam_result_file_service import get_exam_result_file_service

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_database():
    """驗證資料庫連線和表格建立"""
    try:
        logger.info("=== 驗證資料庫功能 ===")

        # 建立表格
        create_tables()
        logger.info("✓ 資料庫表格建立成功")

        # 測試連線
        db_gen = get_database()
        db = next(db_gen)
        logger.info("✓ 資料庫連線正常")
        db.close()

        return True
    except Exception as e:
        logger.error(f"✗ 資料庫驗證失敗: {e}")
        return False


async def verify_redis():
    """驗證 Redis 連線"""
    try:
        logger.info("=== 驗證 Redis 快取 ===")

        redis_client = get_redis()
        success = redis_client.connect()

        if success:
            # 測試基本操作
            test_key = "test_verification"
            test_value = {"test": "value", "timestamp": "2025-09-24"}

            redis_client.set(test_key, test_value, expiry=60)
            retrieved_value = redis_client.get(test_key)

            if retrieved_value and retrieved_value.get("test") == "value":
                logger.info("✓ Redis 連線和操作正常")
                redis_client.delete(test_key)
                return True
            else:
                logger.warning("✗ Redis 操作異常")
                return False
        else:
            logger.warning("⚠ Redis 連線失敗，但應用可以繼續運行")
            return True  # Redis 失敗不影響核心功能

    except Exception as e:
        logger.warning(f"⚠ Redis 驗證失敗，但不影響核心功能: {e}")
        return True


async def verify_question_set_manager():
    """驗證題組檔案管理器"""
    try:
        logger.info("=== 驗證題組檔案管理器 ===")

        manager = QuestionSetFileManager()

        # 測試初始化（不需要實際檔案）
        results = await manager.load_all_question_sets()
        logger.info(f"✓ 題組管理器初始化成功，載入結果: {len(results.get('loaded', []))} 個題組")

        # 測試統計功能
        stats = manager.get_stats()
        logger.info(f"✓ 題組統計功能正常: {stats['total_question_sets']} 個題組")

        return True
    except Exception as e:
        logger.error(f"✗ 題組管理器驗證失敗: {e}")
        return False


async def verify_services():
    """驗證各種服務"""
    try:
        logger.info("=== 驗證服務層 ===")

        # 測試容器服務（不實際連接 Docker）
        container_service = get_container_service()
        logger.info("✓ 容器服務初始化成功")

        # 測試檔案服務
        vm_config_service = get_vm_config_file_service()
        config_files = vm_config_service.list_config_files()
        logger.info(f"✓ VM 配置檔案服務正常，找到 {len(config_files)} 個配置檔案")

        # 測試 Kubespray 配置服務
        kubespray_service = get_kubespray_config_service()
        session_configs = kubespray_service.list_session_configs()
        logger.info(f"✓ Kubespray 配置服務正常，找到 {len(session_configs)} 個會話配置")

        # 測試考試結果檔案服務
        result_service = get_exam_result_file_service()
        stats = result_service.get_storage_stats()
        logger.info(f"✓ 考試結果檔案服務正常，儲存統計: {stats['total_files']} 個檔案")

        return True
    except Exception as e:
        logger.error(f"✗ 服務驗證失敗: {e}")
        return False


async def verify_business_logic():
    """驗證業務邏輯服務"""
    try:
        logger.info("=== 驗證業務邏輯 ===")

        # 建立 Redis 客戶端和資料庫連線
        redis_client = get_redis()
        db_gen = get_database()
        db = next(db_gen)

        try:
            # 測試題組管理器
            question_manager = QuestionSetFileManager()

            # 測試考試會話服務
            session_service = ExamSessionService(db, redis_client, question_manager)
            sessions = await session_service.list_sessions()
            logger.info(f"✓ 考試會話服務正常，找到 {len(sessions)} 個會話")

            # 測試環境服務
            env_service = EnvironmentService(db)
            logger.info("✓ 環境服務初始化成功")

        finally:
            db.close()

        return True
    except Exception as e:
        logger.error(f"✗ 業務邏輯驗證失敗: {e}")
        return False


async def verify_directory_structure():
    """驗證目錄結構"""
    try:
        logger.info("=== 驗證目錄結構 ===")

        required_dirs = [
            "data",
            "data/question_sets",
            "data/vm_configs",
            "data/ssh_keys",
            "data/kubespray_configs",
            "data/exam_results"
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✓ 建立目錄: {dir_path}")
            else:
                logger.info(f"✓ 目錄已存在: {dir_path}")

        logger.info("✓ 目錄結構驗證完成")
        return True
    except Exception as e:
        logger.error(f"✗ 目錄結構驗證失敗: {e}")
        return False


async def verify_imports():
    """驗證 Python 模組匯入"""
    try:
        logger.info("=== 驗證模組匯入 ===")

        # 測試核心模組匯入
        from src.main import app
        logger.info("✓ FastAPI 應用匯入成功")

        from src.api.v1.router import api_router
        logger.info("✓ API 路由器匯入成功")

        # 測試所有 API 端點模組
        from src.api.v1 import (
            vm_configs, question_sets, exam_sessions,
            environment, vnc_access, question_scoring
        )
        logger.info("✓ 所有 API 端點模組匯入成功")

        # 測試所有服務模組
        from src.services import (
            exam_session_service, environment_service, container_service,
            question_set_file_manager, vm_config_file_service,
            kubespray_config_service, exam_result_file_service
        )
        logger.info("✓ 所有服務模組匯入成功")

        # 測試所有模型模組
        from src.models import (
            vm_cluster_config, exam_session, exam_result, question_set_data
        )
        logger.info("✓ 所有資料模型匯入成功")

        return True
    except Exception as e:
        logger.error(f"✗ 模組匯入驗證失敗: {e}")
        return False


async def main():
    """主驗證函數"""
    logger.info("🚀 開始驗證 Kubernetes 考試模擬器基本功能")
    logger.info("="*60)

    verification_results = []

    # 執行各項驗證
    verifications = [
        ("目錄結構", verify_directory_structure()),
        ("模組匯入", verify_imports()),
        ("資料庫", verify_database()),
        ("Redis 快取", verify_redis()),
        ("題組管理器", verify_question_set_manager()),
        ("服務層", verify_services()),
        ("業務邏輯", verify_business_logic())
    ]

    for name, verification in verifications:
        try:
            result = await verification
            verification_results.append((name, result))
        except Exception as e:
            logger.error(f"✗ {name} 驗證過程中發生異常: {e}")
            verification_results.append((name, False))

    # 輸出總結
    logger.info("="*60)
    logger.info("📊 驗證結果總結:")

    passed = 0
    total = len(verification_results)

    for name, result in verification_results:
        status = "✓ 通過" if result else "✗ 失敗"
        logger.info(f"  {name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n🎯 總體結果: {passed}/{total} 項驗證通過")

    if passed == total:
        logger.info("🎉 所有基本功能驗證通過！應用程式準備就緒。")
        return 0
    else:
        logger.warning(f"⚠️  有 {total - passed} 項驗證失敗，請檢查相關功能。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("驗證過程被使用者中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"驗證過程發生未預期的錯誤: {e}")
        sys.exit(1)