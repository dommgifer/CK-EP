# Kubernetes 考試模擬器 - 快速入門指南

## 系統概述

本系統提供完整的 Kubernetes 認證考試模擬環境，支援 CKAD、CKA、CKS 三種認證類型的練習。系統自動化部署 Kubernetes 環境到使用者指定的 VM 叢集，並提供 Web 介面進行遠端桌面存取和即時評分。

## 環境需求

### 硬體需求
- **開發機器**: 8GB RAM, 4 CPU cores, 20GB 可用硬碟空間
- **目標 VM 叢集**:
  - Master 節點: 2GB RAM, 2 CPU cores
  - Worker 節點: 1GB RAM, 1 CPU core (每個)
  - 網路: 各節點間可互通，支援 SSH 連線

### 軟體需求
- Docker 20.10+ 和 Docker Compose v2
- Git
- 目標 VM 運行 Ubuntu 20.04+ 或 CentOS 8+
- SSH 金鑰對或密碼認證

## 快速安裝

### 1. 克隆專案
```bash
git clone <repository-url>
cd kubernetes-exam-simulator
```

### 2. 環境配置
```bash
# 複製環境配置範本
cp .env.example .env

# 編輯配置檔案
nano .env
```

主要配置項目：
```env
# 資料庫設定
DATABASE_URL=sqlite:///data/exam_simulator.db
REDIS_URL=redis://redis:6379/0

# VNC 設定
VNC_PASSWORD=secure_password
VNC_DISPLAY=:1

# SSH 設定
SSH_KEY_DIR=/app/data/ssh_keys

# 日誌設定
LOG_LEVEL=INFO
```

### 3. 啟動系統
```bash
# 建構和啟動所有服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps
```

服務啟動後，系統透過 nginx 反向代理提供統一入口：
- **Web 介面**: http://192.168.1.10 (請替換為實際伺服器 IP)
- **API 文件**: http://192.168.1.10/docs

**架構說明**：
- nginx 作為統一入口點 (port 80)，自動路由前端靜態檔案和 API 請求
- 前端透過相對路徑 `/api/v1/*` 呼叫後端服務
- 無需暴露多個端口，支援動態 IP 變更

## 系統網路架構

### 整體部署架構
```
使用者瀏覽器 (192.168.1.x)
    ↓ HTTP/HTTPS (port 80/443)
┌─────────────────────────────────────────┐
│  nginx 反向代理容器                     │
│  ├── 前端靜態檔案服務 (/)               │
│  ├── API 請求代理 (/api/* → backend)    │
│  └── VNC 連線代理 (/vnc/* → vnc)       │
└─────────────────────────────────────────┘
    ↓ Docker 內部網路
┌─────────────┬─────────────┬─────────────┐
│ frontend    │ backend     │ vnc         │
│ (靜態檔案)  │ :8000       │ :5901       │
└─────────────┼─────────────┼─────────────┘
              ↓             ↓
    ┌─────────────┐ ┌─────────────┐
    │ Redis       │ │ SQLite      │
    │ :6379       │ │ (檔案)      │
    └─────────────┘ └─────────────┘
```

### 請求流程圖
```
1. 使用者存取 → http://192.168.1.10
2. nginx 路由決策：
   ├── / → 前端靜態檔案
   ├── /api/v1/* → backend:8000
   └── /vnc/* → vnc:5901

3. 考試會話建立流程：
   瀏覽器 → nginx → backend → Kubespray 容器服務 → 使用者 VM 叢集
                           ↓                      ↓
                    API 呼叫容器內腳本        SSH 連線 (port 22)
                    動態創建 session 配置

   Docker 容器內執行：
   1. mkdir /kubespray/data/{session_id}
   2. 生成 inventory/hosts.yaml
   3. ansible-playbook -i inventory/hosts.yaml cluster.yml

   ┌─────────────────────────────────────────┐
   │ 使用者 VM 叢集                          │
   │ ├── Master 節點 (192.168.1.100)        │
   │ │   └── 安裝 Kubernetes control plane   │
   │ └── Worker 節點 (192.168.1.101)        │
   │     └── 加入 Kubernetes 叢集           │
   └─────────────────────────────────────────┘
```

### VNC 連線架構
```
瀏覽器 noVNC 客戶端
    ↓ WebSocket
nginx (/vnc/* 代理)
    ↓
VNC 容器 (桌面環境)
    ↓ kubectl 命令
Kubernetes 叢集 (使用者 VM)
```

### 4. 初始化資料庫
```bash
# 執行資料庫遷移
docker-compose exec backend python -m alembic upgrade head

# 載入範例題組 (可選)
docker-compose exec backend python scripts/load_sample_questions.py
```

## 基本使用流程

### 第一步：配置 VM 叢集

1. 開啟 Web 介面 (http://192.168.1.10，請替換為實際伺服器 IP)
2. 導航到「VM 配置」頁面
3. 點選「新增配置」
4. 輸入以下資訊：
   - 配置名稱
   - Master 節點 IP 地址
   - Worker 節點 IP 地址 (可選)
   - SSH 使用者名稱
   - SSH 私鑰或密碼

範例配置：
```json
{
  "name": "Lab Environment",
  "master_nodes": [
    {
      "ip_address": "192.168.1.100",
      "hostname": "k8s-master",
      "role": "master",
      "ssh_port": 22
    }
  ],
  "worker_nodes": [
    {
      "ip_address": "192.168.1.101",
      "hostname": "k8s-worker1",
      "role": "worker",
      "ssh_port": 22
    }
  ],
  "ssh_username": "ubuntu"
}
```

5. 點選「測試連線」確認可以連接到所有節點
6. 儲存配置

### 第二步：選擇或建立題組

#### 使用預設題組
1. 導航到「題組管理」頁面
2. 選擇適合的認證類型 (CKA/CKAD/CKS)
3. 檢視題組詳情和題目列表

#### 建立自定義題組

題組透過 JSON 檔案管理，需要在檔案系統中建立對應的目錄結構：

1. **建立題組目錄**：
   ```bash
   # 在 data/question_sets/ 下建立新的題組目錄
   mkdir -p data/question_sets/cka/002

   # 建立腳本和網路配置目錄
   mkdir -p data/question_sets/cka/002/scripts/{verify,prepare}
   mkdir -p data/question_sets/cka/002/network
   ```

2. **建立 metadata.json**：
   ```json
   {
     "exam_type": "CKA",
     "set_id": "002",
     "name": "CKA 進階模擬測驗",
     "description": "涵蓋 CKA 進階主題的實戰練習",
     "difficulty": "hard",
     "time_limit": 180,
     "total_questions": 12,
     "passing_score": 70,
     "created_date": "2025-09-22",
     "version": "1.0",
     "tags": ["advanced", "troubleshooting", "networking"],
     "topics": [
       {
         "name": "叢集維護",
         "weight": 30,
         "questions": 4,
         "description": "節點維護、升級、備份"
       }
     ]
   }
   ```

3. **建立 questions.json**：
   ```json
   {
     "set_info": {
       "exam_type": "CKA",
       "set_id": "002",
       "name": "CKA 進階模擬測驗"
     },
     "questions": [
       {
         "id": 1,
         "content": "## 任務\n\n在指定的 namespace 中建立一個 Pod，並設定適當的資源限制...",
         "weight": 8.5,
         "kubernetes_objects": ["Pod", "ResourceQuota"],
         "hints": [
           "檢查 Pod 的資源配置",
           "使用 kubectl describe 查看詳細資訊"
         ],
         "verification_scripts": ["q1_check_pod.sh", "q1_check_resources.sh"],
         "preparation_scripts": ["setup_namespace.sh"]
       }
     ]
   }
   ```

4. **建立 Kubespray 配置檔案**（選用）：

   如果該題組需要特殊的 Kubernetes 環境配置，可以建立以下檔案：

   ```bash
   # 建立基礎配置覆蓋檔案（覆蓋 templates/base.yml）
   cat > data/question_sets/cka/002/base-overwrite.yml << 'EOF'
   # 只需要定義需要改變的配置
   kube_version: v1.28.8
   cluster_name: cka-002-cluster

   # 如果需要特殊的 kubelet 配置
   kubelet_config_extra_args:
     maxPods: 200
   EOF

   # 建立 addon 配置覆蓋檔案（覆蓋 templates/addons.yml）
   cat > data/question_sets/cka/002/addons-overwrite.yml << 'EOF'
   # 啟用額外的 addon
   ingress_nginx_enabled: true
   metrics_server_enabled: true
   EOF

   # 建立網路配置目錄和 CNI 配置檔案（如果需要特定 CNI）
   mkdir -p data/question_sets/cka/002/network

   # 建立 Calico CNI 配置
   cat > data/question_sets/cka/002/network/k8s-net-calico.yml << 'EOF'
   # Calico CNI 配置
   kube_network_plugin: calico
   calico_network_backend: bird
   calico_ipip_mode: Always
   EOF

   # 可以根據需要新增更多網路配置檔案
   # cat > data/question_sets/cka/002/network/custom-network.yml << 'EOF'
   # # 自定義網路配置
   # EOF
   ```

5. **重載題組資料**：
   ```bash
   curl -X POST http://192.168.1.10/api/v1/question-sets/reload
   ```

### 第三步：開始考試會話

1. 導航到「考試管理」頁面
2. 點選「開始新考試」
3. 選擇：
   - 認證類型
   - 題組
   - VM 配置

4. 點選「建立會話」
5. 系統將同時啟動兩個平行流程：

   **🔧 考試容器啟動** (立即開始)：
   - 啟動 VNC Container (基於 ConSol debian-xfce-vnc)
   - 啟動 Bastion Container (Alpine 基底，包含考試工具)
   - 配置 VNC 到 Bastion 的 SSH 連線
   - 使用者可立即看到桌面環境 (VNC 介面可用)

   **⚙️ Kubernetes 環境配置** (並行執行)：
   - 驗證 VM 連線
   - 讀取題組的 Kubespray 配置檔案
   - 執行配置合併（base + overwrite）
   - 掃描題組的 network/ 目錄，收集所有 CNI 配置
   - 在 Kubespray 容器內創建 session 配置目錄
   - 生成合併後的 k8s-cluster.yml、addons.yml
   - 複製所有 network/ 目錄下的網路配置檔案
   - 複製 etcd 設定檔案
   - 生成 Ansible inventory 檔案
   - 執行官方 Kubespray playbook
   - 在使用者 VM 上安裝和配置 Kubernetes

6. **即時 Ansible 部署輸出**：
   - 系統介面即時顯示 Ansible playbook 原生輸出
   - 完整的任務執行日誌和節點狀態
   - 真實的安裝進度和錯誤訊息
   - 符合技術專家習慣的終端機風格介面
   - 透明且可除錯的完整部署過程

   **Ansible 輸出範例**：
   ```
   PLAY [Download and install Kubernetes] *************************

   TASK [Download kubectl binary] *********************************
   changed: [master-01]
   changed: [worker-01]
   ok: [worker-02]

   TASK [Configure kubelet service] *******************************
   running: [master-01]
   running: [worker-01]
   running: [worker-02]

   TASK [Start kubelet] ********************************************
   ok: [master-01]
   failed: [worker-01] => {"msg": "Service failed to start"}
   ok: [worker-02]
   ```

7. Kubernetes 環境配置完成後：
   - 自動將 kubeconfig 掛載到 Bastion Container
   - 更新 Bastion 內的連線配置
   - 系統自動跳轉到 VNC 頁面
   - 頁面顯示桌面環境（左側題目面板，右側 VNC 桌面）
   - 彈出「開始考試」按鈕覆蓋層

8. 點選「開始考試」

### 第四步：進行考試

1. 點選「開始考試」後，覆蓋層消失，考試正式開始：
   - **左側面板**：題目描述和導航
   - **右側面板**：VNC 遠端桌面 (noVNC 介面)
   - 考試計時器開始倒數

2. 在 VNC 遠端桌面環境中：
   - 開啟終端機
   - 執行 `ssh bastion` 連線到工具環境
   - 在 Bastion 內使用 kubectl、helm 等工具
   - 完成題目要求

3. 題目導航：
   - 使用「上一題」/「下一題」按鈕
   - 查看進度條和剩餘時間
   - 標記已完成的題目

4. 提交答案：
   - 完成題目後點選「提交答案」
   - 系統在 Bastion Container 內執行驗證腳本
   - 即時顯示得分和詳細回饋

### VNC + Bastion 雙容器架構說明

**架構優勢**：
- **VNC Container**：專注提供穩定的桌面環境，基於成熟的 ConSol 映像
- **Bastion Container**：Alpine 3.19 基底，輕量化設計 (~50MB vs Ubuntu 220MB)
- **通用工具集**：包含 kubectl、helm、jq、yq 等所有認證考試工具
- **職責分離**：桌面顯示與工具執行分離，提高穩定性和安全性
- **快速啟動**：極輕量映像，容器啟動時間大幅縮短

**使用流程**：
1. 瀏覽器 → nginx → VNC Container (noVNC 介面)
2. VNC 桌面 → 開啟終端機 → `ssh bastion`
3. Bastion 環境 → 執行 kubectl 命令 → 操作 K8s 叢集

### 第五步：檢視結果

1. 考試完成或時間到期後，系統自動生成結果報告
2. 結果包含：
   - 總分和各題目得分
   - 完成時間
   - 詳細的驗證結果
   - 解題建議和參考答案

## API 使用範例

### 準備 SSH 金鑰
```bash
# 1. 生成 SSH 金鑰對（如果還沒有）
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa

# 2. 複製私鑰到指定目錄
cp ~/.ssh/id_rsa ./data/ssh_keys/
chmod 600 ./data/ssh_keys/id_rsa

# 3. 在所有 VM 節點安裝公鑰
ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@192.168.1.100
ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@192.168.1.101

# 4. 驗證連線
ssh -i ./data/ssh_keys/id_rsa ubuntu@192.168.1.100
```

### 建立 VM 配置
```bash
curl -X POST http://192.168.1.10/api/v1/vm-configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Environment",
    "master_nodes": [
      {
        "ip_address": "192.168.1.100",
        "role": "master",
        "ssh_port": 22
      }
    ],
    "worker_nodes": [
      {
        "ip_address": "192.168.1.101",
        "role": "worker",
        "ssh_port": 22
      }
    ],
    "ssh_username": "ubuntu"
  }'
```

### 測試 VM 連線
```bash
curl -X POST http://192.168.1.10/api/v1/vm-configs/{config_id}/test-connection
```

### 建立考試會話
```bash
curl -X POST http://192.168.1.10/api/v1/exam-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "CKA",
    "question_set_id": "cka-001",
    "vm_cluster_config_id": "uuid-here"
  }'
```

### 查看環境狀態
```bash
curl http://192.168.1.10/api/v1/exam-sessions/{session_id}/environment/status
```

### 題組管理

#### 查看所有題組
```bash
curl http://192.168.1.10/api/v1/question-sets
```

#### 查看特定認證類型的題組
```bash
curl "http://192.168.1.10/api/v1/question-sets?exam_type=CKA"
```

#### 查看題組詳情
```bash
curl http://192.168.1.10/api/v1/question-sets/cka-001
```

#### 重載題組檔案
```bash
curl -X POST http://192.168.1.10/api/v1/question-sets/reload
```

## 故障排除

### 常見問題

#### 1. VM 連線失敗
**症狀**: 測試連線返回失敗
**解決方案**:
- 檢查 IP 地址是否正確
- 確認 SSH 服務正在運行
- 驗證防火牆設定
- 檢查 SSH 金鑰權限 (600)

#### 2. Kubespray 部署失敗
**症狀**: 環境配置停滯或報錯
**解決方案**:
- 檢查 VM 資源是否足夠
- 確認網路連線穩定
- 查看 Ansible 部署日誌
- 驗證 VM 系統版本相容性

#### 3. VNC 連線問題
**症狀**: 無法連接到遠端桌面
**解決方案**:
- 檢查 VNC 容器狀態
- 確認端口映射正確
- 檢查防火牆設定
- 重啟 VNC 服務

#### 4. 驗證腳本執行失敗
**症狀**: 題目評分異常
**解決方案**:
- 檢查腳本權限
- 確認 kubectl 配置正確
- 驗證 Kubernetes 叢集狀態
- 查看腳本執行日誌

#### 5. 題組檔案載入失敗
**症狀**: 題組列表為空或顯示錯誤
**解決方案**:
- 檢查 JSON 檔案格式是否正確
- 確認 metadata.json 和 questions.json 都存在
- 驗證檔案權限
- 查看後端日誌中的錯誤訊息
- 手動重載題組檔案

```bash
# 驗證 JSON 格式
cat data/question_sets/cka/001/metadata.json | jq .

# 檢查檔案權限
ls -la data/question_sets/cka/001/

# 手動重載
curl -X POST http://192.168.1.10/api/v1/question-sets/reload
```

#### 6. 檔案監控不工作
**症狀**: 修改 JSON 檔案後系統未自動重載
**解決方案**:
- 重啟後端服務
- 檢查檔案系統監控日誌
- 手動觸發重載

### 日誌檢查
```bash
# 檢視所有服務日誌
docker-compose logs

# 檢視特定服務日誌
docker-compose logs backend
docker-compose logs frontend
docker-compose logs vnc

# 即時查看日誌
docker-compose logs -f backend
```

### 重設系統
```bash
# 停止所有服務
docker-compose down

# 清除資料 (謹慎使用)
docker-compose down -v
rm -rf data/

# 重新啟動
docker-compose up -d
```

## 進階配置

### 自定義 Kubespray 配置
在 `kubespray-configs/templates/` 目錄下修改：
- `base.yml`: 基礎 Kubernetes 配置
- `addons.yml`: 插件配置
- `all/etcd.yml`: etcd 配置

### 新增驗證腳本範本
在 `scripts/verification/` 目錄下新增腳本：
```bash
#!/bin/bash
# 範例驗證腳本

# 檢查 Pod 是否存在
if kubectl get pod resource-pod &>/dev/null; then
    echo "PASS: Pod exists"
    exit 0
else
    echo "FAIL: Pod not found"
    exit 1
fi
```

### 效能調優
修改 `docker-compose.yml` 中的資源限制：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## 支援和社群

- **問題回報**: [GitHub Issues](repository-url/issues)
- **文件**: [完整文件](docs-url)
- **貢獻指南**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

這個快速入門指南涵蓋了系統的基本使用方式。更詳細的設定和進階功能請參考完整文件。