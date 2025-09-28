"""
Kubernetes 考試模擬器 - FastAPI 主應用
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .api.v1.router import api_router
from .api.v1.question_sets import initialize_question_set_manager, shutdown_question_set_manager
from .api.kubespray_proxy import router as kubespray_proxy_router
from .middleware.logging import LoggingMiddleware
from .middleware.error import ErrorHandlerMiddleware
from .database.connection import create_tables
from .cache.redis_client import get_redis

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時執行
    logger.info("正在啟動 Kubernetes 考試模擬器...")

    try:
        # 建立資料庫表格
        create_tables()
        logger.info("資料庫表格已建立")

        # 初始化 Redis 連線
        redis_client = get_redis()
        if redis_client.connect():
            logger.info("Redis 連線已建立")
        else:
            logger.warning("Redis 連線失敗，將繼續使用檔案系統")

        # 初始化題組檔案管理器
        await initialize_question_set_manager()
        logger.info("題組檔案管理器已初始化")

        logger.info("應用啟動完成")

        yield

    except Exception as e:
        logger.error(f"應用啟動失敗: {e}")
        raise

    # 關閉時執行
    logger.info("正在關閉應用...")

    try:
        # 關閉題組檔案管理器
        await shutdown_question_set_manager()
        logger.info("題組檔案管理器已關閉")

    except Exception as e:
        logger.error(f"應用關閉時發生錯誤: {e}")

    logger.info("應用已關閉")


# 建立 FastAPI 應用
app = FastAPI(
    title="Kubernetes 考試模擬器 API",
    description="支援 CKAD、CKA、CKS 三種 Kubernetes 認證考試模擬",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# 中介軟體
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# 註冊路由
app.include_router(api_router, prefix="/api/v1")
app.include_router(kubespray_proxy_router)

# 健康檢查
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "k8s-exam-simulator"}

@app.get("/")
async def root():
    """根端點"""
    return {"message": "Kubernetes 考試模擬器 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)