# Kubespray API Server

這是為 Kubernetes 考試模擬器提供的 Kubespray 配置生成和部署服務。

## 架構重構

根據 `/specs/001-k8s-home-ubuntu/plan.md` 的設計規格，本專案已從單一檔案重構為模組化架構。

### 目錄結構

```
kubespray/
├── Dockerfile               # 容器映像建構檔案
├── requirements.txt         # Python 依賴項
├── README.md               # 本檔案
└── src/                    # 主要原始碼目錄
    ├── __init__.py
    ├── main.py             # FastAPI 應用初始化與啟動
    ├── models/             # 資料模型
    │   ├── __init__.py
    │   └── schemas.py      # Pydantic 模型定義
    ├── services/           # 業務邏輯服務
    │   ├── __init__.py
    │   ├── kubespray_service.py  # Kubespray 相關服務
    │   └── health_service.py     # 健康檢查服務
    ├── api/                # API 路由層
    │   ├── __init__.py
    │   └── kubespray_routes.py   # Kubespray API 路由
    └── lib/                # 共用程式庫（未來使用）
```

### 重構改進

1. **分離關注點**：將原本的單一檔案分解為模型、服務、API 三層架構
2. **模組化設計**：每個元件都有清楚的職責邊界
3. **可測試性**：服務層可以獨立進行單元測試
4. **可維護性**：程式碼組織更清晰，便於理解和修改
5. **擴展性**：新增功能時可以清楚知道應該放在哪個層次
6. **一致性**：與 backend 服務保持相同的結構模式

### API 端點

- `GET /` - 根端點，回傳服務資訊
- `GET /health` - 健康檢查端點
- `POST /exam-sessions/{session_id}/kubespray/inventory` - 生成 Kubespray inventory 配置

### 使用方式

#### 本地測試
```bash
# 建構映像
docker compose -f docker-compose.test.yml build kubespray-api

# 啟動服務
docker compose -f docker-compose.test.yml up kubespray-api -d

# 測試 API
curl http://localhost:8080/health
```

#### 產生 Inventory 配置
```bash
curl -X POST http://localhost:8080/exam-sessions/test-session-001/kubespray/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "vm_config": {
      "name": "test-cluster",
      "nodes": [
        {"name": "master01", "ip": "192.168.1.100", "role": "master"},
        {"name": "worker01", "ip": "192.168.1.101", "role": "worker"}
      ],
      "ssh_config": {
        "user": "root",
        "port": 22
      }
    },
    "question_set_id": "cka/001"
  }'
```

## 技術堆疊

- **Python 3.11+**: 主要程式語言
- **FastAPI**: Web 框架，提供高效能 REST API
- **Pydantic**: 資料驗證和序列化
- **PyYAML**: YAML 檔案處理
- **Uvicorn**: ASGI 伺服器

## 相依項目

- 基礎映像：`quay.io/kubespray/kubespray:v2.23.1`
- 掛載目錄：
  - `/kubespray/inventory` - inventory 配置輸出目錄
  - `/kubespray/question_sets` - 題組範本目錄
  - `/root/.ssh` - SSH 金鑰目錄

## 容器配置

容器啟動時會：
1. 繼承 Kubespray 官方映像的所有 Ansible 工具
2. 安裝額外的 FastAPI 相依項目
3. 複製重構後的程式碼到容器中
4. 使用標準的 uvicorn 方式在 port 8080 啟動 API 服務