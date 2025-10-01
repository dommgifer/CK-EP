#!/bin/bash
# 開發環境快速啟動腳本

set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 啟動 Kubernetes 考試模擬器 - 開發模式 (Vite Dev Server)${NC}"
echo ""

# 檢查 Docker 是否運行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未運行，請先啟動 Docker${NC}"
    exit 1
fi

# 顯示當前模式
echo -e "${YELLOW}📋 開發模式特性：${NC}"
echo "  ✅ 前端 HMR 即時更新 (Vite Dev Server)"
echo "  ✅ 後端源碼即時更新 (uvicorn --reload)"
echo "  ✅ 詳細日誌輸出 (DEBUG 級別)"
echo "  ✅ 無需重建 image"
echo "  ✅ 自動解決快取問題"
echo ""

# 顯示提示
echo -e "${YELLOW}⚠️  注意事項：${NC}"
echo "  • 如果修改 requirements.txt，需執行："
echo "    docker compose -f docker-compose.yml -f docker-compose.dev.yml build backend kubespray-api"
echo "  • 如果修改 package.json，需執行："
echo "    docker compose -f docker-compose.yml -f docker-compose.dev.yml build frontend"
echo "  • 停止服務：docker compose -f docker-compose.yml -f docker-compose.dev.yml down"
echo ""

# 停止並移除現有容器
echo -e "${BLUE}🛑 停止現有容器...${NC}"
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# 啟動服務
echo -e "${GREEN}🔧 啟動開發環境...${NC}"
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d "$@"

# 等待服務就緒
echo -e "${BLUE}⏳ 等待服務啟動...${NC}"
sleep 5

# 顯示服務狀態
echo ""
echo -e "${GREEN}📊 服務狀態：${NC}"
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

# 顯示前端日誌（檢查 Vite 是否啟動）
echo ""
echo -e "${GREEN}📋 前端服務日誌：${NC}"
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs frontend --tail 20

echo ""
echo -e "${GREEN}✅ 開發環境已啟動！${NC}"
echo ""
echo -e "${BLUE}🌐 訪問網址: http://192.168.1.19${NC}"
echo -e "${BLUE}🔥 HMR 已啟用 - 修改源碼即時更新${NC}"
echo -e "${BLUE}🛠️  後端 API: http://192.168.1.19/api/v1/${NC}"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "  • 修改 frontend/src/* 檔案會自動觸發 HMR"
echo "  • 修改 backend/src/* 檔案會自動重載"
echo "  • 查看前端日誌: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f frontend"
echo "  • 查看後端日誌: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f backend"
echo ""