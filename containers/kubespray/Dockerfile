FROM quay.io/kubespray/kubespray:v2.23.1

# 安裝 Python FastAPI 依賴
USER root
RUN pip install fastapi uvicorn pydantic

# 建立 API 應用程式目錄
RUN mkdir -p /kubespray/api

# 複製 API 應用程式
COPY app.py /kubespray/api/

# 設定 mount 點
RUN mkdir -p /kubespray/inventory
RUN mkdir -p /kubespray/templates
RUN mkdir -p /kubespray/question_sets

# 設定工作目錄
WORKDIR /kubespray

# 暴露 API 端口
EXPOSE 8080

# 啟動 FastAPI 服務
CMD ["python3", "/kubespray/api/app.py"]