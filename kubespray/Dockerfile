FROM quay.io/kubespray/kubespray:v2.23.1

# 安裝 Python FastAPI 依賴
USER root
RUN pip install fastapi uvicorn pydantic

# 建立 API 應用程式目錄
RUN mkdir -p /kubespray/api

# 複製整個 src 目錄
COPY src/ /kubespray/api/src/

# 設定 mount 點
RUN mkdir -p /kubespray/inventory
RUN mkdir -p /kubespray/templates  
RUN mkdir -p /kubespray/question_sets

# 設定工作目錄
WORKDIR /kubespray/api

# 設定 Python 路徑
ENV PYTHONPATH=/kubespray/api

# 暴露 API 端口
EXPOSE 8080

# 啟動 FastAPI 服務 (使用標準 uvicorn 方式)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]