#!/usr/bin/env python3

"""
資料庫初始化腳本
Kubernetes 考試模擬器系統

此腳本負責：
1. 建立 SQLite 資料庫
2. 運行 Alembic 遷移
3. 初始化基本資料
4. 驗證系統完整性
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional

# 添加 backend 模組路徑
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    # 導入模型
    from src.models.vm_cluster_config import VMClusterConfig
    from src.models.exam_session import ExamSession
    from src.models.exam_result import ExamResult
    from src.database import Base, get_database_url

except ImportError as e:
    print(f"❌ 無法導入必要的模組: {e}")
    print("請確保在正確的環境中運行此腳本")
    sys.exit(1)


class DatabaseInitializer:
    """資料庫初始化器"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or get_database_url()
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 設定 Alembic 配置
        self.alembic_cfg = Config()
        alembic_ini_path = backend_path / "alembic.ini"
        if alembic_ini_path.exists():
            self.alembic_cfg = Config(str(alembic_ini_path))
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

        print(f"📊 資料庫 URL: {self.database_url}")

    def check_prerequisites(self) -> bool:
        """檢查前置條件"""
        print("\n🔍 檢查前置條件...")

        # 檢查資料目錄
        data_dir = Path(__file__).parent.parent / "data"
        if not data_dir.exists():
            print(f"❌ 資料目錄不存在: {data_dir}")
            return False

        # 檢查必要的子目錄
        required_dirs = [
            "question_sets",
            "vm_configs",
            "ssh_keys",
            "kubespray_configs"
        ]

        for dir_name in required_dirs:
            dir_path = data_dir / dir_name
            if not dir_path.exists():
                print(f"⚠️  建立目錄: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)

        print("✅ 前置條件檢查完成")
        return True

    def create_database(self) -> bool:
        """建立資料庫檔案（如果不存在）"""
        print("\n🗄️ 檢查資料庫檔案...")

        try:
            # 對於 SQLite，確保目錄存在
            if self.database_url.startswith("sqlite:///"):
                db_path = Path(self.database_url.replace("sqlite:///", ""))
                db_dir = db_path.parent
                if not db_dir.exists():
                    print(f"📁 建立資料庫目錄: {db_dir}")
                    db_dir.mkdir(parents=True, exist_ok=True)

            # 測試連線
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            print("✅ 資料庫連線成功")
            return True

        except Exception as e:
            print(f"❌ 資料庫連線失敗: {e}")
            return False

    def run_migrations(self) -> bool:
        """運行 Alembic 遷移"""
        print("\n🔄 運行資料庫遷移...")

        try:
            # 檢查是否已有遷移版本
            try:
                command.current(self.alembic_cfg)
                print("📋 檢查現有遷移狀態")
            except Exception:
                # 首次運行，需要標記為基準版本
                print("🆕 初始化 Alembic 版本控制")
                command.stamp(self.alembic_cfg, "head")

            # 運行遷移到最新版本
            command.upgrade(self.alembic_cfg, "head")
            print("✅ 資料庫遷移完成")
            return True

        except Exception as e:
            print(f"❌ 遷移失敗: {e}")

            # 嘗試直接建立表（備案）
            try:
                print("🔧 嘗試直接建立資料表...")
                Base.metadata.create_all(bind=self.engine)
                print("✅ 資料表建立完成")
                return True
            except Exception as create_error:
                print(f"❌ 建立資料表也失敗: {create_error}")
                return False

    def verify_tables(self) -> bool:
        """驗證資料表是否正確建立"""
        print("\n🔍 驗證資料表...")

        try:
            with self.engine.connect() as conn:
                # 檢查主要資料表
                tables = [
                    "vm_cluster_configs",
                    "exam_sessions",
                    "exam_results"
                ]

                for table in tables:
                    result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"))
                    if not result.fetchone():
                        print(f"❌ 資料表不存在: {table}")
                        return False
                    else:
                        print(f"✅ 資料表存在: {table}")

                print("✅ 所有資料表驗證完成")
                return True

        except Exception as e:
            print(f"❌ 驗證資料表失敗: {e}")
            return False

    def create_sample_data(self) -> bool:
        """建立範例資料（可選）"""
        print("\n📝 建立範例資料...")

        try:
            session = self.SessionLocal()

            # 檢查是否已有資料
            if session.query(VMClusterConfig).count() > 0:
                print("ℹ️  已有 VM 配置資料，跳過建立範例資料")
                session.close()
                return True

            # 建立範例 VM 配置
            sample_config = VMClusterConfig(
                name="sample-cluster",
                description="範例 Kubernetes 叢集配置",
                nodes=[
                    {
                        "name": "master-1",
                        "ip": "192.168.1.10",
                        "roles": ["master", "etcd"],
                        "specs": {
                            "cpu": 2,
                            "memory": "4Gi",
                            "disk": "20Gi"
                        }
                    },
                    {
                        "name": "worker-1",
                        "ip": "192.168.1.11",
                        "roles": ["worker"],
                        "specs": {
                            "cpu": 2,
                            "memory": "4Gi",
                            "disk": "20Gi"
                        }
                    }
                ],
                ssh_user="ubuntu",
                created_by="system"
            )

            session.add(sample_config)
            session.commit()

            print("✅ 範例資料建立完成")
            session.close()
            return True

        except Exception as e:
            print(f"❌ 建立範例資料失敗: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False

    def test_operations(self) -> bool:
        """測試基本操作"""
        print("\n🧪 測試基本資料庫操作...")

        try:
            session = self.SessionLocal()

            # 測試查詢
            configs = session.query(VMClusterConfig).all()
            print(f"📊 找到 {len(configs)} 個 VM 配置")

            sessions = session.query(ExamSession).all()
            print(f"📊 找到 {len(sessions)} 個考試會話")

            results = session.query(ExamResult).all()
            print(f"📊 找到 {len(results)} 個考試結果")

            session.close()
            print("✅ 基本操作測試完成")
            return True

        except Exception as e:
            print(f"❌ 操作測試失敗: {e}")
            if 'session' in locals():
                session.close()
            return False

    def initialize(self, create_sample: bool = True) -> bool:
        """執行完整初始化流程"""
        print("🚀 開始初始化 Kubernetes 考試模擬器資料庫")
        print("=" * 50)

        steps = [
            ("檢查前置條件", self.check_prerequisites),
            ("建立資料庫", self.create_database),
            ("運行遷移", self.run_migrations),
            ("驗證資料表", self.verify_tables),
            ("測試操作", self.test_operations)
        ]

        if create_sample:
            steps.append(("建立範例資料", self.create_sample_data))

        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ 初始化失敗於步驟: {step_name}")
                return False

        print("\n" + "=" * 50)
        print("🎉 資料庫初始化成功完成!")
        print(f"📊 資料庫位置: {self.database_url}")
        print("🔗 您現在可以啟動應用程式了")

        return True


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="初始化 Kubernetes 考試模擬器資料庫")
    parser.add_argument("--database-url", help="資料庫 URL (預設從環境變數或配置讀取)")
    parser.add_argument("--no-sample", action="store_true", help="不建立範例資料")
    parser.add_argument("--force", action="store_true", help="強制重新初始化")

    args = parser.parse_args()

    # 檢查是否在正確的目錄
    if not (Path.cwd() / "backend" / "src").exists():
        print("❌ 請在專案根目錄執行此腳本")
        print(f"目前路徑: {Path.cwd()}")
        sys.exit(1)

    try:
        initializer = DatabaseInitializer(args.database_url)

        # 如果資料庫已存在且非強制模式，詢問是否繼續
        if not args.force:
            if "sqlite:///" in initializer.database_url:
                db_path = Path(initializer.database_url.replace("sqlite:///", ""))
                if db_path.exists() and db_path.stat().st_size > 0:
                    response = input("🤔 資料庫檔案已存在，是否要繼續初始化？(y/N): ")
                    if response.lower() not in ['y', 'yes']:
                        print("⏹️  初始化已取消")
                        sys.exit(0)

        # 執行初始化
        success = initializer.initialize(create_sample=not args.no_sample)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️  初始化已被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 初始化過程中發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()