FROM quay.io/kubespray/kubespray:v2.28.1

# 安裝 Python FastAPI 依賴
USER root

# 建立 API 應用程式目錄
RUN mkdir -p /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# 複製整個 src 目錄
COPY src/ /app/src/

# 設定 mount 點
RUN mkdir -p /app/data

# 設定工作目錄
WORKDIR /app

# 設定 Python 路徑
ENV PYTHONPATH=/app

# 暴露 API 端口
EXPOSE 8080

# 啟動 FastAPI 服務 (使用標準 uvicorn 方式)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]