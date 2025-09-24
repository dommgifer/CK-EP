# Tasks: Kubernetes 考試模擬器

**輸入**: 設計文件來自 `/home/ubuntu/DW-CK/specs/001-k8s-home-ubuntu/`
**前置條件**: research.md (完成), data-model.md (完成), contracts/ (完成), quickstart.md (完成)

## 執行流程 (main)
```
1. 載入技術架構設計
   → 技術棧: Docker Compose + FastAPI + React + noVNC + Kubespray
   → 前端: React 18 + TypeScript，後端: FastAPI + Python 3.11+
   → 儲存: SQLite + Redis + JSON 檔案系統
2. 載入設計文件:
   → data-model.md: 8個核心實體 → model 任務
   → contracts/api-spec.yaml: 26個 API 端點 → 契約測試任務
   → research.md: 技術決策 → 設定任務
   → quickstart.md: 整合場景 → 整合測試任務
3. 產生任務分類:
   → Setup: Docker Compose 配置、專案初始化、依賴設定
   → Tests: API 契約測試、整合測試
   → Core: 資料模型、服務邏輯、API 端點
   → Integration: 檔案系統管理、VNC 整合、Kubespray 服務
   → Polish: 前端實作、單元測試、效能調優
4. 套用任務規則:
   → 不同檔案 = 標記 [P] 可平行
   → 相同檔案 = 序列執行
   → 測試優先 (TDD)
5. 任務編號 (T001, T002...)
6. 產生依賴圖
7. 建立平行執行範例
8. 驗證任務完整性
9. 回傳: 成功 (任務就緒執行)
```

## 格式: `[ID] [P?] 描述`
- **[P]**: 可平行執行 (不同檔案，無依賴性)
- 描述中包含確切的檔案路徑

## 路徑慣例
- **Web 應用**: `backend/src/`, `frontend/src/`
- **nginx 配置**: `nginx/`
- **資料目錄**: `data/`
- **Docker**: `docker-compose.yml`, Dockerfiles

## Phase 3.1: Setup 和專案初始化

- [X] T001 建立專案目錄結構 (backend/, frontend/, nginx/, data/)
- [X] T002 建立 Docker Compose 配置檔案 docker-compose.yml
- [X] T003 [P] 建立 backend Dockerfile 與 Python 依賴 backend/requirements.txt
- [X] T004 [P] 建立 frontend Dockerfile 與 package.json frontend/package.json
- [X] T005 [P] 建立 nginx 配置檔案 nginx/nginx.conf
- [X] T006 [P] 建立 VNC Container Dockerfile（基於 ConSol debian-xfce-vnc）
- [X] T007 [P] 建立 Bastion Container Dockerfile（Alpine 3.19 + 考試工具）
- [X] T008 [P] 建立環境變數檔案 .env.example
- [X] T009 [P] 配置 Python 開發環境 backend/pyproject.toml 與 linting 工具

## Phase 3.2: Tests First (TDD) ⚠️ 必須在 3.3 之前完成
**關鍵: 這些測試必須先寫好且失敗，才能進行任何實作**

### API 契約測試 [P]
- [X] T010 [P] VM 配置 API 契約測試 backend/tests/contract/test_vm_configs.py
- [X] T011 [P] 題組管理 API 契約測試 backend/tests/contract/test_question_sets.py
- [X] T012 [P] 考試會話 API 契約測試 backend/tests/contract/test_exam_sessions.py
- [X] T013 [P] 環境管理 API 契約測試 backend/tests/contract/test_environment.py
- [X] T014 [P] VNC 連線 API 契約測試 backend/tests/contract/test_vnc_access.py
- [X] T015 [P] 題目評分 API 契約測試 backend/tests/contract/test_question_scoring.py

### 整合測試 [P]
- [X] T016 [P] 完整考試流程整合測試 backend/tests/integration/test_exam_flow.py
- [X] T017 [P] VM 連線測試整合測試 backend/tests/integration/test_vm_connection.py
- [X] T018 [P] 題組檔案載入整合測試 backend/tests/integration/test_question_file_loading.py
- [X] T019 [P] Kubespray 部署整合測試 backend/tests/integration/test_kubespray_deployment.py
- [X] T020 [P] VNC 容器啟動整合測試 backend/tests/integration/test_vnc_container.py

## Phase 3.3: 資料模型和核心實作 (只能在測試失敗後)

### 資料模型 [P]
- [X] T021 [P] ExamSession 模型 backend/src/models/exam_session.py
- [X] T022 [P] VMClusterConfig 模型 backend/src/models/vm_cluster_config.py
- [X] T023 [P] VMNode 模型 backend/src/models/vm_node.py
- [X] T024 [P] ExamResult 模型 backend/src/models/exam_result.py
- [X] T025 [P] QuestionResult 模型 backend/src/models/question_result.py
- [X] T026 [P] VerificationResult 模型 backend/src/models/verification_result.py

### 檔案系統管理 [P]
- [X] T027 [P] QuestionSetFileManager 類別 backend/src/services/question_set_file_manager.py
- [X] T028 [P] QuestionSetData 資料類別 backend/src/models/question_set_data.py
- [X] T029 [P] QuestionData 資料類別 backend/src/models/question_data.py

### 核心服務層
- [X] T030 VMClusterService CRUD 操作 backend/src/services/vm_cluster_service.py
- [X] T031 ExamSessionService 考試會話管理 backend/src/services/exam_session_service.py
- [X] T032 QuestionSetService 題組管理服務 backend/src/services/question_set_service.py
- [X] T033 EnvironmentService Kubespray 環境配置 backend/src/services/environment_service.py
- [X] T034 VNCService 容器管理服務 backend/src/services/vnc_service.py
- [X] T035 ScoringService 題目評分服務 backend/src/services/scoring_service.py

## Phase 3.4: API 端點實作

### VM 配置管理端點
- [X] T036 GET /api/v1/vm-configs 端點 backend/src/api/vm_configs.py
- [X] T037 POST /api/v1/vm-configs 端點 backend/src/api/vm_configs.py
- [X] T038 GET /api/v1/vm-configs/{config_id} 端點 backend/src/api/vm_configs.py
- [X] T039 PUT /api/v1/vm-configs/{config_id} 端點 backend/src/api/vm_configs.py
- [X] T040 DELETE /api/v1/vm-configs/{config_id} 端點 backend/src/api/vm_configs.py
- [X] T041 POST /api/v1/vm-configs/{config_id}/test-connection 端點 backend/src/api/vm_configs.py

### 題組管理端點
- [X] T042 GET /api/v1/question-sets 端點 backend/src/api/question_sets.py
- [X] T043 GET /api/v1/question-sets/{set_id} 端點 backend/src/api/question_sets.py
- [X] T044 POST /api/v1/question-sets/reload 端點 backend/src/api/question_sets.py

### 考試會話管理端點
- [X] T045 GET /api/v1/exam-sessions 端點 backend/src/api/exam_sessions.py
- [X] T046 POST /api/v1/exam-sessions 端點 backend/src/api/exam_sessions.py
- [X] T047 GET /api/v1/exam-sessions/{session_id} 端點 backend/src/api/exam_sessions.py
- [X] T048 PATCH /api/v1/exam-sessions/{session_id} 端點 backend/src/api/exam_sessions.py
- [X] T049 POST /api/v1/exam-sessions/{session_id}/start 端點 backend/src/api/exam_sessions.py
- [X] T050 POST /api/v1/exam-sessions/{session_id}/pause 端點 backend/src/api/exam_sessions.py
- [X] T051 POST /api/v1/exam-sessions/{session_id}/resume 端點 backend/src/api/exam_sessions.py
- [X] T052 POST /api/v1/exam-sessions/{session_id}/complete 端點 backend/src/api/exam_sessions.py

### 環境管理端點
- [X] T053 GET /api/v1/exam-sessions/{session_id}/environment/status 端點 backend/src/api/environment.py
- [X] T054 POST /api/v1/exam-sessions/{session_id}/environment/provision 端點 backend/src/api/environment.py

### VNC 和評分端點
- [X] T055 POST /api/v1/exam-sessions/{session_id}/vnc/token 端點 backend/src/api/vnc_access.py
- [X] T056 POST /api/v1/exam-sessions/{session_id}/questions/{question_id}/submit 端點 backend/src/api/question_scoring.py
- [X] T057 PATCH /api/v1/exam-sessions/{session_id}/navigation 端點 backend/src/api/question_scoring.py

## Phase 3.5: 整合和中介軟體

### 資料庫和快取整合
- [X] T058 SQLAlchemy 資料庫連線配置 backend/src/database/connection.py
- [X] T059 Redis 快取連線配置 backend/src/cache/redis_client.py
- [X] T060 資料庫遷移腳本設定 backend/alembic/

### 檔案系統整合
- [X] T061 題組檔案監控器實作 backend/src/services/question_set_file_manager.py
- [X] T062 SSH 金鑰管理服務 backend/src/services/ssh_key_service.py
- [X] T063 Kubespray 配置生成器 backend/src/services/kubespray_config_service.py

### 容器服務整合
- [X] T064 Docker 容器管理服務 backend/src/services/container_service.py
- [X] T065 VNC 容器啟動邏輯 backend/src/services/vnc_container_service.py
- [X] T066 Bastion 容器管理服務 backend/src/services/bastion_container_service.py

### 中介軟體和錯誤處理
- [X] T067 錯誤處理中介軟體 backend/src/middleware/error.py
- [X] T068 請求日誌中介軟體 backend/src/middleware/logging.py
- [X] T069 單一會話限制中介軟體 backend/src/middleware/session_guard.py
- [X] T070 輸入驗證和安全中介軟體 backend/src/middleware/validation.py

## Phase 3.6: 前端 React 應用

### 核心組件 [P]
- [X] T071 [P] 主要路由設定 frontend/src/App.tsx
- [X] T072 [P] VM 配置管理頁面 frontend/src/pages/VMConfigPage.tsx
- [X] T073 [P] 題組選擇頁面 frontend/src/pages/QuestionSetPage.tsx
- [X] T074 [P] 考試會話建立頁面 frontend/src/pages/CreateExamPage.tsx
- [X] T075 [P] 考試進行頁面 frontend/src/pages/ExamPage.tsx
- [X] T076 [P] 考試結果頁面 frontend/src/pages/ResultsPage.tsx

### UI 組件 [P]
- [X] T077 [P] VM 節點配置組件 frontend/src/components/VMNodeConfig.tsx
- [X] T078 [P] 題目導航組件 frontend/src/components/QuestionNavigation.tsx
- [X] T079 [P] VNC 檢視器組件 frontend/src/components/VNCViewer.tsx
- [X] T080 [P] 環境狀態組件 frontend/src/components/EnvironmentStatus.tsx
- [X] T081 [P] 計時器組件 frontend/src/components/ExamTimer.tsx
- [X] T082 [P] 評分結果顯示組件 frontend/src/components/ScoreDisplay.tsx

### API 客戶端服務 [P]
- [X] T083 [P] VM 配置 API 客戶端 frontend/src/services/vmConfigApi.ts
- [X] T084 [P] 題組 API 客戶端 frontend/src/services/questionSetApi.ts
- [X] T085 [P] 考試會話 API 客戶端 frontend/src/services/examSessionApi.ts
- [X] T086 [P] 環境管理 API 客戶端 frontend/src/services/environmentApi.ts

### 狀態管理 [P]
- [X] T087 [P] 考試會話狀態管理 frontend/src/stores/examSessionStore.ts
- [X] T088 [P] VM 配置狀態管理 frontend/src/stores/vmConfigStore.ts
- [X] T089 [P] 題組狀態管理 frontend/src/stores/questionSetStore.ts

## Phase 3.7: 容器配置和部署

### Docker 容器配置
- [X] T090 VNC Container 最終配置和測試 containers/vnc/
- [X] T091 Bastion Container 最終配置和測試 containers/bastion/
- [X] T092 nginx 反向代理最終配置 nginx/nginx.conf
- [X] T093 Docker Compose 服務整合測試 docker-compose.yml

### 範例資料和腳本
- [X] T094 [P] 範例題組 JSON 檔案 data/question_sets/cka/001/
- [X] T095 [P] 範例驗證腳本 data/question_sets/cka/001/scripts/verify/
- [X] T096 [P] 範例 Kubespray 配置範本 data/kubespray_configs/templates/
- [X] T097 [P] 初始化資料庫腳本 scripts/init_database.py

## Phase 3.8: 測試和品質保證

### 單元測試 [P]
- [X] T098 [P] QuestionSetFileManager 單元測試 backend/tests/unit/test_question_set_file_manager.py
- [X] T099 [P] ExamSessionService 單元測試 backend/tests/unit/test_exam_session_service.py
- [X] T100 [P] VMClusterService 單元測試 backend/tests/unit/test_vm_cluster_service.py
- [X] T101 [P] ScoringService 單元測試 backend/tests/unit/test_scoring_service.py

### 前端測試 [P]
- [X] T102 [P] 主要頁面組件測試 frontend/src/__tests__/pages/
- [X] T103 [P] UI 組件單元測試 frontend/src/__tests__/components/
- [X] T104 [P] API 客戶端測試 frontend/src/__tests__/services/

### 效能和最佳化
- [X] T105 後端 API 效能測試 (目標 <200ms 回應時間)
- [X] T106 前端建構最佳化 (bundle 大小、程式碼分割)
- [X] T107 容器映像大小最佳化
- [X] T108 記憶體使用量最佳化

### 文件和維護
- [X] T109 [P] API 文件生成和驗證 docs/api.md
- [X] T110 [P] 部署指南更新 docs/deployment.md
- [X] T111 [P] 故障排除指南 docs/troubleshooting.md
- [X] T112 [P] 使用者手冊 docs/user-guide.md

## Phase 3.9: 最終整合和驗證

### 端對端測試
- [X] T113 完整考試流程 E2E 測試
- [X] T114 多認證類型 (CKA/CKAD/CKS) 驗證測試
- [X] T115 容器故障恢復測試
- [X] T116 手動測試檢查清單驗證

### 生產準備
- [X] T117 安全性檢查和滲透測試
- [X] T118 效能基準測試
- [X] T119 監控和日誌配置
- [X] T120 備份和恢復程序

## 依賴關係

### 主要依賴鏈
- Setup (T001-T009) 必須最先完成
- 測試 (T010-T020) 必須在實作前完成 (TDD)
- 資料模型 (T021-T029) 阻塞服務層 (T030-T035)
- 服務層 (T030-T035) 阻塞 API 端點 (T036-T057)
- API 端點完成後才能進行前端整合 (T071-T089)

### 特定依賴
- T027 (QuestionSetFileManager) 阻塞 T032 (QuestionSetService)
- T058 (資料庫連線) 阻塞所有資料模型測試
- T059 (Redis 客戶端) 阻塞會話管理功能
- T061 (檔案監控器) 阻塞 T044 (reload 端點)
- T063 (Kubespray 配置) 阻塞 T054 (provision 端點)
- T064 (Docker 服務) 阻塞 T065, T066 (容器服務)

### 前端依賴
- T083-T086 (API 客戶端) 阻塞 T087-T089 (狀態管理)
- T087-T089 (狀態管理) 阻塞 T071-T076 (頁面組件)

## 平行執行範例

### 契約測試階段 (可同時執行)
```
Task: "VM 配置 API 契約測試 backend/tests/contract/test_vm_configs.py"
Task: "題組管理 API 契約測試 backend/tests/contract/test_question_sets.py"
Task: "考試會話 API 契約測試 backend/tests/contract/test_exam_sessions.py"
Task: "環境管理 API 契約測試 backend/tests/contract/test_environment.py"
Task: "VNC 連線 API 契約測試 backend/tests/contract/test_vnc_access.py"
Task: "題目評分 API 契約測試 backend/tests/contract/test_question_scoring.py"
```

### 資料模型階段 (可同時執行)
```
Task: "ExamSession 模型 backend/src/models/exam_session.py"
Task: "VMClusterConfig 模型 backend/src/models/vm_cluster_config.py"
Task: "VMNode 模型 backend/src/models/vm_node.py"
Task: "ExamResult 模型 backend/src/models/exam_result.py"
Task: "QuestionResult 模型 backend/src/models/question_result.py"
Task: "VerificationResult 模型 backend/src/models/verification_result.py"
```

### 前端組件階段 (可同時執行)
```
Task: "VM 配置管理頁面 frontend/src/pages/VMConfigPage.tsx"
Task: "題組選擇頁面 frontend/src/pages/QuestionSetPage.tsx"
Task: "考試會話建立頁面 frontend/src/pages/CreateExamPage.tsx"
Task: "考試進行頁面 frontend/src/pages/ExamPage.tsx"
Task: "考試結果頁面 frontend/src/pages/ResultsPage.tsx"
```

## 注意事項

- **[P] 任務**: 不同檔案，無依賴性，可平行執行
- **TDD 原則**: 必須先寫測試且失敗，才能實作功能
- **提交頻率**: 每個任務完成後都要提交
- **檔案衝突**: 避免多個任務修改同一檔案
- **容器測試**: T090-T093 需要完整的 Docker 環境測試

## 任務生成規則

1. **來自 API 契約**:
   - 每個 API 端點 → 契約測試任務 [P]
   - 每個端點 → 實作任務

2. **來自資料模型**:
   - 每個實體 → 模型建立任務 [P]
   - 關係和服務 → 服務層任務

3. **來自快速入門場景**:
   - 每個使用情境 → 整合測試 [P]
   - Quickstart 場景 → 驗證任務

4. **排序原則**:
   - 設定 → 測試 → 模型 → 服務 → 端點 → 前端 → 部署

## 驗證檢查清單

- [ ] 所有 API 契約都有對應測試
- [ ] 所有實體都有模型任務
- [ ] 所有測試都在實作之前
- [ ] 平行任務真正獨立
- [ ] 每個任務指定確切檔案路徑
- [ ] 沒有任務與其他 [P] 任務修改相同檔案
- [ ] 涵蓋完整的 Kubernetes 考試模擬器功能範圍