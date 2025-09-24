# Kubernetes 考試模擬器

支援 CKAD、CKA、CKS 三種 Kubernetes 認證考試模擬的完整平台。

## 🚀 快速開始

### 先決條件

- Docker 和 Docker Compose
- 可透過 SSH 連線的 Kubernetes 叢集（或待部署的 VM）
- SSH 私鑰檔案

### 安裝步驟

1. **準備 SSH 金鑰**
   ```bash
   # 將您的 SSH 私鑰複製到指定位置
   cp ~/.ssh/id_rsa data/ssh_keys/id_rsa
   chmod 600 data/ssh_keys/id_rsa
   ```

2. **執行初始化**
   ```bash
   ./init.sh
   ```

3. **存取系統**
   - Web 介面: http://localhost
   - API 文件: http://localhost/api/docs

## 📁 專案結構

```
├── backend/          # FastAPI 後端服務
├── frontend/         # React 前端應用
├── nginx/            # nginx 反向代理配置
├── containers/       # VNC 和 Bastion 容器
├── data/             # 資料存儲
│   ├── question_sets/     # 題組 JSON 檔案
│   ├── vm_configs/        # VM 配置檔案
│   ├── ssh_keys/          # SSH 私鑰檔案
│   └── exam_results/      # 考試結果備份
└── docker-compose.yml     # Docker 服務配置
```

## 🎯 主要功能

- **多認證支援**: CKAD、CKA、CKS
- **自動化部署**: 使用 Kubespray 自動部署 Kubernetes
- **遠端桌面**: noVNC Web 介面存取
- **即時評分**: 自動化評分系統
- **檔案系統題庫**: JSON 檔案管理題組
- **單一會話**: 同時僅允許一個活動考試會話

## 🔧 開發指令

```bash
# 啟動所有服務
docker-compose up -d

# 停止服務
docker-compose down

# 查看日誌
docker-compose logs -f [service_name]

# 重新建置
docker-compose build [service_name]

# 進入容器除錯
docker-compose exec backend bash
docker-compose exec frontend sh
```

## 📝 配置說明

### VM 配置檔案

請參考 `data/vm_configs/example-cluster.json` 建立您的叢集配置。

### 題組管理

題組檔案位於 `data/question_sets/` 目錄：
- `metadata.json`: 題組基本資訊
- `questions.json`: 具體題目內容

## 🔍 疑難排解

### 常見問題

1. **SSH 連線失敗**
   - 檢查 SSH 私鑰權限：`chmod 600 data/ssh_keys/id_rsa`
   - 確認目標主機 SSH 服務運行
   - 檢查防火牆設定

2. **健康檢查失敗**
   - 檢查 Docker 服務狀態：`docker-compose ps`
   - 查看服務日誌：`docker-compose logs backend`

3. **無法存取 Web 介面**
   - 確認 80 埠未被佔用
   - 檢查 nginx 配置：`docker-compose logs nginx`

## 📄 授權

此專案採用 MIT 授權條款。