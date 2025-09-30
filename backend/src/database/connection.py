"""
T058: SQLAlchemy 資料庫連線配置
資料庫連線和會話管理
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 資料庫配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/exam_simulator.db")

# 建立資料庫引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DEBUG_SQL", "false").lower() == "true"
)

# 建立會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基礎模型類別
Base = declarative_base()


def get_database() -> Generator[Session, None, None]:
    """取得資料庫會話依賴注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """建立所有資料表"""
    # 導入所有模型以確保它們被註冊到 Base.metadata
    from ..models import (
        VMClusterConfig,
        ExamSession,
        ExamResult,
    )

    # 建立所有表格
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """刪除所有資料表（用於測試或重置）"""
    Base.metadata.drop_all(bind=engine)