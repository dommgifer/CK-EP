# 資料模型設計

## 實體關係概述

本文件定義 Kubernetes 考試模擬器的核心資料實體、屬性和關係。

**重要設計變更**: 題組採用檔案系統管理，而非資料庫存儲。題組透過 JSON 檔案定義，系統啟動時載入並快取在記憶體中。

## 核心實體

### 1. ExamSession (考試會話)
```python
{
  "id": "uuid",
  "exam_type": "string",  # CKA, CKAD, CKS
  "question_set_id": "string",
  "status": "string",  # preparing, active, paused, completed, failed
  "start_time": "datetime",
  "end_time": "datetime",
  "time_limit_minutes": "integer",
  "current_question_index": "integer",
  "vm_cluster_config": "VMClusterConfig",
  "environment_status": "string",  # configuring, ready, error
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**驗證規則**:
- 同時只能有一個 active 狀態的會話
- time_limit_minutes 必須 > 0
- exam_type 必須是有效的認證類型

**狀態轉換**:
- preparing → active → completed/failed
- active ↔ paused (可暫停/恢復)

### 2. QuestionSetFileManager (題組檔案管理器)
```python
{
  "base_path": "string",  # /app/data/question_sets
  "loaded_sets": "dict[string, QuestionSetData]",  # 記憶體快取
  "file_watchers": "list[FileWatcher]",  # 檔案監控器
  "last_reload": "datetime",
  "validation_schema": "JSONSchema"
}
```

**職責**:
- 掃描檔案系統中的題組目錄
- 載入和驗證 JSON 檔案格式
- 維護記憶體快取
- 監控檔案變更並自動重載

### 3. QuestionSetData (題組資料 - 記憶體物件)
```python
{
  "set_id": "string",  # e.g., "cka-001"
  "exam_type": "string",  # CKA, CKAD, CKS
  "metadata": "QuestionSetMetadata",  # 從 metadata.json 載入
  "questions": "list[QuestionData]",  # 從 questions.json 載入
  "scripts_path": "string",  # 腳本目錄路徑
  "file_paths": {
    "metadata": "string",
    "questions": "string",
    "scripts": "string"
  },
  "loaded_at": "datetime",
  "file_modified_at": "datetime"
}
```

### 4. QuestionSetMetadata (題組元資料)
```python
{
  "exam_type": "string",
  "set_id": "string",
  "name": "string",
  "description": "string",
  "difficulty": "string",  # easy, medium, hard
  "time_limit": "integer",  # 分鐘
  "total_questions": "integer",
  "passing_score": "integer",  # 及格分數百分比
  "created_date": "string",
  "version": "string",
  "tags": "list[string]",
  "topics": "list[TopicInfo]",
  "exam_domains": "list[DomainInfo]"
}
```

### 5. QuestionData (題目資料 - 記憶體物件)
```python
{
  "id": "integer",
  "content": "string",  # Markdown 格式的題目內容
  "weight": "float",  # 題目權重
  "kubernetes_objects": "list[string]",  # 涉及的 K8s 物件
  "hints": "list[string]",
  "verification_scripts": "list[string]",  # 腳本檔案路徑
  "preparation_scripts": "list[string]"  # 準備腳本路徑
}
```

### 6. VMClusterConfig (VM 叢集配置)
```python
{
  "id": "uuid",
  "name": "string",
  "master_nodes": "list[VMNode]",
  "worker_nodes": "list[VMNode]",
  "ssh_username": "string",
  # ssh_private_key_path 固定為 "/root/.ssh/id_rsa" (使用者管理)
  "connection_status": "string",  # untested, success, failed
  "last_tested_at": "datetime",
  "error_message": "string",  # 連線失敗時的錯誤訊息
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**驗證規則**:
- 至少一個 master_node
- ssh_username 必填
- SSH 私鑰必須存在於 data/ssh_keys/id_rsa

**SSH 金鑰管理**:
- 私鑰路徑固定為容器內的 `/root/.ssh/id_rsa`
- 對應主機路徑為 `data/ssh_keys/id_rsa`
- 使用者負責準備和管理 SSH 金鑰

### 7. VMNode (VM 節點)
```python
{
  "ip_address": "string",
  "hostname": "string",  # 可選
  "role": "string",  # master, worker
  "ssh_port": "integer"  # 預設 22
}
```

**驗證規則**:
- ip_address 必須是有效的 IP 格式
- role 必須是 master 或 worker
- ssh_port 必須在有效範圍內 (1-65535)

### 8. ExamResult (考試結果)
```python
{
  "session_id": "uuid",
  "question_results": "list[QuestionResult]",
  "total_score": "integer",
  "max_score": "integer",
  "completion_time_minutes": "integer",
  "status": "string",  # completed, timeout, failed
  "created_at": "datetime"
}
```

### 9. QuestionResult (題目結果)
```python
{
  "question_id": "string",
  "score": "integer",
  "max_score": "integer",
  "verification_results": "list[VerificationResult]",
  "time_spent_minutes": "integer",
  "completed_at": "datetime"
}
```

### 10. VerificationResult (驗證結果)
```python
{
  "script_id": "string",
  "exit_code": "integer",
  "stdout": "string",
  "stderr": "string",
  "execution_time_seconds": "float",
  "passed": "boolean",
  "score": "float",  # 基於權重計算的分數
  "executed_at": "datetime"
}
```

## 檔案系統結構

### 題組檔案組織
```
data/question_sets/
├── cka/                    # CKA 認證題組
│   ├── 001/
│   │   ├── metadata.json   # 題組元資料
│   │   ├── questions.json  # 題目內容
│   │   ├── base-overwrite.yml      # 覆蓋基礎 K8s 配置
│   │   ├── addons-overwrite.yml    # 覆蓋 addon 配置
│   │   ├── network/        # CNI 網路配置目錄（可選）
│   │   │   └── k8s-net-calico.yml  # Calico CNI 配置
│   │   └── scripts/        # 驗證和準備腳本
│   │       ├── verify/     # 驗證腳本目錄
│   │       │   ├── q1_check_pod.sh
│   │       │   └── q2_check_service.sh
│   │       └── prepare/    # 準備腳本目錄
│   │           └── setup_namespace.sh
│   └── 002/
├── ckad/                   # CKAD 認證題組
│   └── 001/
├── cks/                    # CKS 認證題組
│   └── 001/
│       ├── metadata.json
│       ├── questions.json
│       ├── base-overwrite.yml      # CKS 特定的基礎配置
│       ├── addons-overwrite.yml    # CKS 特定的 addon 配置
│       ├── network/        # CNI 網路配置目錄
│       │   ├── k8s-net-cilium.yml  # Cilium CNI 配置
│       │   └── custom-security.yml # 自定義安全配置
│       └── scripts/
└── templates/              # 全域配置範本
    ├── all/
    │   └── etcd.yml        # 預設 etcd 配置
    ├── base.yml            # 預設 k8s-cluster.yml
    └── addons.yml          # 預設 addons.yml
```

### JSON 檔案格式

#### metadata.json 範例
```json
{
  "exam_type": "CKS",
  "set_id": "001",
  "name": "CKS 模擬測驗 001 - 基礎安全強化",
  "description": "涵蓋完整的 CKS 考試主題",
  "difficulty": "medium",
  "time_limit": 120,
  "total_questions": 15,
  "passing_score": 66,
  "created_date": "2024-01-15",
  "version": "2.0",
  "tags": ["security", "rbac", "network-policies"],
  "topics": [...]
}
```

#### questions.json 範例
```json
{
  "set_info": {
    "exam_type": "CKS",
    "set_id": "001",
    "name": "CKS 完整模擬認證考試"
  },
  "questions": [
    {
      "id": 1,
      "content": "建立一個名為 `untrusted` 的 RuntimeClass...",
      "weight": 3.75,
      "kubernetes_objects": ["RuntimeClass", "Pod"],
      "hints": ["您可以在模板檔案中找到..."],
      "verification_scripts": ["q1_check_runtime.sh"],
      "preparation_scripts": ["setup_runtime.sh"]
    }
  ]
}
```

### 檔案載入流程
1. **系統啟動**: 掃描 `/data/question_sets/` 目錄
2. **驗證格式**: 檢查 JSON 檔案格式和必要欄位
3. **載入配置範本**: 載入 `templates/` 下的全域 Kubespray 配置範本
4. **建立索引**: 依據 exam_type 和 set_id 建立記憶體索引
5. **載入快取**: 將題組資料和 Kubespray 配置載入記憶體快取
6. **監控變更**: 啟動檔案監控器，自動重載變更

## 實體關係與資料架構

### 核心實體關係圖
```
┌─────────────────┐     1:1     ┌─────────────────┐
│  ExamSession    │ ◄─────────► │ VMClusterConfig │
│                 │             │                 │
│ - id            │             │ - id            │
│ - exam_type     │             │ - name          │
│ - status        │             │ - master_nodes  │
│ - start_time    │             │ - worker_nodes  │
└─────────────────┘             └─────────────────┘
         │ 1:1                           │ 1:N
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│   ExamResult    │             │     VMNode      │
│                 │             │                 │
│ - total_score   │             │ - ip_address    │
│ - status        │             │ - hostname      │
│ - created_at    │             │ - role          │
└─────────────────┘             └─────────────────┘
         │ 1:N
         ▼
┌─────────────────┐     1:N     ┌─────────────────┐
│ QuestionResult  │ ◄─────────► │VerificationResult│
│                 │             │                 │
│ - question_id   │             │ - script_id     │
│ - score         │             │ - exit_code     │
│ - completed_at  │             │ - passed        │
└─────────────────┘             └─────────────────┘
```

### 題組檔案系統架構
```
記憶體快取層 (QuestionSetFileManager)
├── exam_type 索引: CKA → [QuestionSetData]
├── set_id 索引: "cka-001" → QuestionSetData
└── file_path 索引: "/path/metadata.json" → QuestionSetData

檔案系統層
data/question_sets/
├── cka/001/
│   ├── metadata.json ────┐
│   ├── questions.json ───┼─→ 載入至 QuestionSetData
│   └── scripts/ ─────────┘    (記憶體物件)
│       ├── verify/
│       └── prepare/
├── ckad/001/
└── cks/001/

QuestionSetData (記憶體)
├── metadata: QuestionSetMetadata
├── questions: [QuestionData]
└── scripts_path: string
```

### 資料流向圖
```
1. 系統啟動時檔案載入:
   檔案系統 → QuestionSetFileManager → 記憶體快取
   templates/ → 全域 Kubespray 配置範本載入

2. 考試會話建立:
   API 請求 → ExamSession (SQLite) → QuestionSetData (記憶體)

3. Kubespray 配置生成流程:
   題組選擇 → 載入題組 Kubespray 配置 → 配置合併 → 生成會話配置

   詳細流程:
   a. 讀取 templates/base.yml、addons.yml、all/etcd.yml
   b. 讀取題組的 base-overwrite.yml、addons-overwrite.yml
   c. 掃描題組的 network/ 目錄，取得所有 CNI 配置檔案
   d. 執行深度 YAML 合併 (base + overwrite)
   e. 生成 kubespray_configs/session_{id}/ 配置目錄
   f. 複製所有 network/ 目錄下的 YAML 檔案到會話配置
   g. 複製會話專用 SSH 金鑰和 inventory 檔案

4. VM 環境配置:
   VMClusterConfig (SQLite) → Backend API → Kubespray 容器服務 → SSH 連線 → 使用者 VM

   詳細流程:
   a. Backend 讀取 VMClusterConfig 和會話配置
   b. 呼叫 Kubespray 容器內的部署腳本
   c. 使用生成的 kubespray_configs/session_{id}/ 配置
   d. 執行官方 Kubespray playbook

5. VNC + Bastion 雙容器會話流程:
   使用者瀏覽器 → nginx → VNC Container → SSH → Bastion Container → kubectl → K8s 叢集

   詳細流程:
   a. 啟動 VNC Container (ConSol debian-xfce-vnc 基底)
   b. 啟動 Bastion Container (掛載 kubeconfig 和題組腳本)
   c. 配置 VNC 到 Bastion 的 SSH 連線
   d. 使用者透過瀏覽器存取 noVNC 介面
   e. 在 VNC 桌面開啟終端機，SSH 連線到 Bastion
   f. 在 Bastion 內執行 kubectl 和驗證腳本

6. 題目驗證流程:
   Bastion Container → 執行驗證腳本 → kubectl 檢查 → 回傳結果 → VerificationResult

7. 檔案監控更新:
   檔案變更 → 監控器觸發 → 重新載入 → 更新記憶體快取
```

**重要變更**:
- QuestionSet, Question, VerificationScript 不再是資料庫實體
- 題組資料透過 QuestionSetFileManager 從檔案系統載入
- 考試會話引用的是記憶體中的 QuestionSetData 物件

## 索引策略

### 資料庫索引
- ExamSession.status (查詢活動會話)
- VMClusterConfig.connection_status (查詢可用配置)

### 記憶體索引 (QuestionSetFileManager)
- exam_type → list[QuestionSetData] (按認證類型查詢)
- set_id → QuestionSetData (快速存取特定題組)
- file_path → QuestionSetData (檔案變更時快速定位)

## 資料驗證規則

### 業務規則
1. **單一活動會話**: 全系統最多只能有一個 status='active' 的 ExamSession
2. **題目權重**: 每個題組內所有題目的 weight 總和應該合理分配
3. **時間限制**: ExamSession.time_limit_minutes 不能超過題組的最大允許時間
4. **檔案完整性**: metadata.json 和 questions.json 必須同時存在且格式正確

### JSON 檔案驗證規則
1. **metadata.json 必要欄位**: exam_type, set_id, name, time_limit, total_questions
2. **questions.json 必要欄位**: set_info, questions (非空陣列)
3. **question 必要欄位**: id, content, weight, kubernetes_objects
4. **檔案一致性**: metadata 和 questions 的 exam_type, set_id 必須一致

### 資料完整性
1. **檔案監控**: 自動偵測檔案變更並重新載入
2. **軟刪除**: ExamSession 和 ExamResult 採用軟刪除，保留審計記錄
3. **錯誤處理**: JSON 格式錯誤時保留舊版本，記錄錯誤日誌

## 快取策略

### Redis 快取
- `session:{session_id}`: 活動會話狀態
- `vm_status:{config_id}`: VM 連線狀態

### 記憶體快取 (QuestionSetFileManager)
- 所有題組資料在系統啟動時載入記憶體
- 檔案變更時自動重新載入特定題組
- 支援部分重載，無需重啟整個系統

### 快取失效策略
- 會話狀態變更時清除相關快取
- VM 配置更新時清除狀態快取
- 檔案系統監控觸發自動重載

## 檔案系統結構

```
data/
├── ssh_keys/             # SSH 金鑰目錄 (使用者管理)
│   ├── id_rsa           # 固定的 SSH 私鑰
│   ├── id_rsa.pub       # SSH 公鑰 (可選)
│   └── README.md        # 使用說明
├── vm_configs/          # VM 配置檔案 (簡化)
├── kubespray_configs/   # Kubespray 會話配置 (mount 到官方容器)
│   ├── session_001/        # 動態創建的會話配置
│   │   ├── inventory/
│   │   │   └── hosts.yaml  # Ansible inventory
│   │   └── group_vars/     # 會話專用配置
│   └── session_002/        # 另一個會話配置
├── question_sets/       # 題組檔案
│   └── {exam_type}/
│       └── {set_id}/
│           ├── questions.json
│           ├── scripts/
│           └── configs/
```