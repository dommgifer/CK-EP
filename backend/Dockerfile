# 使用多階段建構來減少最終映像大小
FROM python:3.11-slim AS base

# 設定 Python 環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 建立非 root 使用者
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 設定工作目錄
WORKDIR /app

# 第一階段：建立依賴環境
FROM base AS deps

# 安裝建構工具（僅在建構階段需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# 複製依賴檔案
COPY requirements.txt .

# 建立虛擬環境並安裝依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安裝 Python 依賴
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# 第二階段：生產映像
FROM base AS production

# 只安裝運行時需要的系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    docker.io \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# 從建構階段複製虛擬環境
COPY --from=deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 建立應用程式目錄結構
RUN mkdir -p /app/src /app/data \
    && chown -R appuser:appuser /app

# 複製應用程式碼
COPY --chown=appuser:appuser src/ ./src/

# 建立資料目錄並設定權限 (將透過 volume 掛載)
RUN mkdir -p data/{vm_configs,ssh_keys,kubespray_configs,question_sets,exam_results} \
    && chown -R appuser:appuser data/

# 設定環境變數
ENV DATA_DIR=/app/data

# 切換到非 root 使用者
USER appuser

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 暴露埠
EXPOSE 8000

# 啟動應用（生產環境不使用 --reload）
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]