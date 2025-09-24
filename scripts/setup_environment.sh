#!/bin/bash

# Kubernetes 考試模擬器環境設定腳本
# 此腳本用於快速設定整個考試模擬器環境

set -euo pipefail

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🚀 Kubernetes 考試模擬器環境設定${NC}"
echo "=" * 50

# 函數：顯示進度
show_progress() {
    echo -e "${YELLOW}📋 $1...${NC}"
}

# 函數：顯示成功
show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 函數：顯示錯誤
show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 檢查系統需求
show_progress "檢查系統需求"

# 檢查 Docker
if ! command -v docker &> /dev/null; then
    show_error "Docker 未安裝，請先安裝 Docker"
    exit 1
fi

# 檢查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    show_error "Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 檢查 Python 3.11+
if ! command -v python3 &> /dev/null; then
    show_error "Python 3 未安裝"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    show_error "需要 Python 3.11 或更新版本，目前版本：$PYTHON_VERSION"
    exit 1
fi

# 檢查 Node.js (用於前端建構)
if ! command -v node &> /dev/null; then
    show_error "Node.js 未安裝，請先安裝 Node.js 18+"
    exit 1
fi

show_success "系統需求檢查完成"

# 2. 建立必要目錄
show_progress "建立專案目錄結構"

REQUIRED_DIRS=(
    "data/question_sets/cka"
    "data/question_sets/ckad"
    "data/question_sets/cks"
    "data/vm_configs"
    "data/ssh_keys"
    "data/kubespray_configs/generated"
    "data/exam_results"
    "backend/logs"
    "nginx/logs"
    "redis/logs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    mkdir -p "$dir"
    echo "📁 建立目錄: $dir"
done

show_success "目錄結構建立完成"

# 3. 設定環境變數檔案
show_progress "設定環境變數"

if [[ ! -f ".env" ]]; then
    cat > .env << 'EOF'
# Kubernetes 考試模擬器環境變數

# 應用程式設定
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-in-production

# 資料庫設定
DATABASE_URL=sqlite:///./data/exam_simulator.db

# Redis 設定
REDIS_URL=redis://localhost:6379/0

# VNC 設定
VNC_PASSWORD=examvnc
VNC_RESOLUTION=1280x1024

# 時區設定
TZ=UTC

# Docker 網路設定
DOCKER_NETWORK=k8s-exam-simulator_exam-network

# CORS 設定
CORS_ORIGINS=http://localhost,http://localhost:3000
EOF

    echo "📝 建立 .env 檔案"
else
    echo "ℹ️  .env 檔案已存在，跳過"
fi

show_success "環境變數設定完成"

# 4. 安裝後端相依性
show_progress "安裝後端相依性"

cd backend
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "🐍 建立 Python 虛擬環境"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

show_success "後端相依性安裝完成"
cd "$PROJECT_ROOT"

# 5. 安裝前端相依性
show_progress "安裝前端相依性"

cd frontend
if [[ ! -d "node_modules" ]]; then
    npm install
    echo "📦 安裝前端套件"
else
    echo "ℹ️  node_modules 已存在，執行 npm ci"
    npm ci
fi

show_success "前端相依性安裝完成"
cd "$PROJECT_ROOT"

# 6. 初始化資料庫
show_progress "初始化資料庫"

cd backend
source venv/bin/activate
python ../scripts/init_database.py --no-sample

show_success "資料庫初始化完成"
cd "$PROJECT_ROOT"

# 7. 建構容器映像
show_progress "建構 Docker 映像"

# 建構前端
docker-compose build frontend

# 建構後端
docker-compose build backend

# 建構 VNC 和 Bastion 容器
if [[ -d "containers/vnc" ]]; then
    docker-compose build vnc-template
fi

if [[ -d "containers/bastion" ]]; then
    docker-compose build bastion-template
fi

show_success "Docker 映像建構完成"

# 8. 設定 SSH 金鑰提醒
show_progress "檢查 SSH 金鑰設定"

SSH_KEY_PATH="data/ssh_keys/id_rsa"
if [[ ! -f "$SSH_KEY_PATH" ]]; then
    echo -e "${YELLOW}⚠️  請將您的 SSH 私鑰放置於：$SSH_KEY_PATH${NC}"
    echo -e "${YELLOW}   此金鑰將用於連線到 VM 叢集進行 Kubernetes 部署${NC}"
else
    # 檢查金鑰權限
    chmod 600 "$SSH_KEY_PATH"
    show_success "SSH 金鑰已設定"
fi

# 9. 驗證設定
show_progress "驗證環境設定"

# 檢查 Docker 服務
docker info > /dev/null 2>&1 || {
    show_error "Docker 服務未運行，請啟動 Docker"
    exit 1
}

# 測試 Docker Compose 配置
docker-compose config > /dev/null || {
    show_error "Docker Compose 配置有誤"
    exit 1
}

show_success "環境設定驗證完成"

# 完成
echo ""
echo "=" * 50
echo -e "${GREEN}🎉 環境設定完成！${NC}"
echo ""
echo -e "${BLUE}下一步：${NC}"
echo "1. 確認 SSH 金鑰已正確放置在 data/ssh_keys/id_rsa"
echo "2. 根據需要調整 .env 檔案"
echo "3. 運行系統："
echo "   docker-compose up -d"
echo ""
echo "4. 存取應用程式："
echo "   - 前端介面: http://localhost"
echo "   - API 文件: http://localhost/api/v1/docs"
echo ""
echo -e "${YELLOW}注意事項：${NC}"
echo "- 第一次啟動可能需要較長時間下載映像"
echo "- 確保已正確設定 VM 叢集的 SSH 存取"
echo "- 檢查防火牆設定允許必要的埠存取"