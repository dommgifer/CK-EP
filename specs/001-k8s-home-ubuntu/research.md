# Phase 0: Research & Technical Decisions

## 技術決策摘要

本文件記錄 Kubernetes 考試模擬器的技術研究結果和架構決策。

## 1. 容器編排和部署策略

### Decision: Docker Compose
**Rationale**:
- 本地開發和部署的簡單性
- 服務間網路配置直觀
- 資源限制和隔離控制
- 適合單機部署的考試環境

**Alternatives considered**:
- Kubernetes：過於複雜，本身就是被模擬的目標
- 直接 Docker：缺乏服務編排和網路管理
- VM 直接部署：資源效率低，管理複雜

## 2. 前端技術棧

### Decision: React 18 + TypeScript
**Rationale**:
- 組件化開發，適合複雜的考試介面
- 強型別支援，減少執行時錯誤
- 豐富的生態系統（VNC client libraries）
- 良好的測試工具支援

**Alternatives considered**:
- Vue.js：學習成本較低但生態相對較小
- Plain JavaScript：缺乏大型應用開發優勢
- Angular：過於重量級

## 3. 後端 API 框架

### Decision: FastAPI + Python 3.11+
**Rationale**:
- 自動 API 文件生成（OpenAPI）
- 強型別支援（Pydantic）
- 優秀的非同步處理能力
- 與 Ansible/Kubespray 整合容易

**Alternatives considered**:
- Django：過於重量級，ORM 不必要
- Flask：缺乏內建型別和文件支援
- Node.js：缺乏 Python 生態系統優勢

## 4. 遠端桌面解決方案

### Decision: noVNC + TigerVNC
**Rationale**:
- 純 Web 瀏覽器存取，無需插件
- 輕量級 VNC 伺服器
- 易於容器化部署
- 支援剪貼簿和檔案傳輸

**Alternatives considered**:
- RDP：需要額外的客戶端軟體
- X11 forwarding：網路延遲問題
- SSH Web terminals：缺乏圖形介面

## 5. Kubernetes 自動化部署

### Decision: Kubespray (官方容器化版本)
**Rationale**:
- 官方支援，穩定可靠
- 支援多種 CNI 和配置選項
- Ansible playbook 易於客製化
- 容器化版本易於整合

**Alternatives considered**:
- kubeadm：手動步驟過多
- kops：主要針對雲端環境
- Rancher：過於複雜，非必要功能太多

## 6. 資料存儲策略

### Decision: SQLite + Redis 混合架構
**Rationale**:
- SQLite：輕量級，適合小規模資料（考試配置、結果）
- Redis：會話管理、快取、即時狀態追蹤
- 無需額外資料庫伺服器維護

**Alternatives considered**:
- PostgreSQL：過於重量級
- 純檔案系統：缺乏查詢能力
- 記憶體內資料庫：持久性問題

## 7. 測試策略

### Decision: 分層測試 + 契約測試
**Rationale**:
- Unit tests：pytest (backend), Jest (frontend)
- Contract tests：API 介面契約驗證
- Integration tests：完整使用者流程測試
- E2E tests：真實環境驗證

**Testing Tools**:
- Backend: pytest + pytest-asyncio + httpx
- Frontend: Jest + React Testing Library + MSW
- API: OpenAPI contract testing
- Integration: Docker Compose test environments

## 8. 會話和狀態管理

### Decision: Redis-based Session Store
**Rationale**:
- 支援單一活動會話限制
- 即時狀態更新和同步
- 會話過期和清理機制
- 分散式部署準備

## 9. 安全性考量

### Decision: SSH Key Management + Network Isolation
**Rationale**:
- SSH 私鑰安全存儲（加密）
- 容器網路隔離
- VNC 連線驗證
- 敏感配置環境變數化

**Security Measures**:
- SSH 金鑰輪換機制
- VNC 密碼保護
- API 請求驗證
- 檔案系統權限控制

## 10. 效能優化

### Decision: 非同步處理 + 快取策略
**Rationale**:
- Kubespray 部署非同步執行
- Redis 快取常用配置
- 前端狀態管理優化
- Docker 映像層快取

## 實作優先順序

1. **Phase 1**: 核心 API 和資料模型
2. **Phase 2**: Kubespray 整合和 VM 管理
3. **Phase 3**: VNC 和遠端桌面整合
4. **Phase 4**: 前端使用者介面
5. **Phase 5**: 評分和驗證系統

## 風險和減緩策略

### 高風險項目
1. **SSH 連線穩定性**
   - 減緩：連線測試和重試機制

2. **VNC 效能和延遲**
   - 減緩：本地網路優化和壓縮設定

3. **Kubespray 部署失敗**
   - 減緩：詳細日誌和狀態追蹤

### 中風險項目
1. **Docker 資源限制**
   - 減緩：資源監控和清理機制

2. **前端狀態同步**
   - 減緩：WebSocket 即時更新

## 結論

技術棧選擇平衡了開發效率、系統穩定性和維護成本。採用容器化和微服務架構為未來擴展提供彈性，同時保持單使用者系統的簡潔性。