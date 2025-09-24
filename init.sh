#!/bin/bash
# Kubernetes 考試模擬器初始化腳本

set -e

echo "=== Kubernetes 考試模擬器初始化 ==="

# 檢查 Docker 是否運行
if ! docker info >/dev/null 2>&1; then
    echo "錯誤: Docker 未運行，請先啟動 Docker"
    exit 1
fi

# 檢查 docker-compose 是否可用
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "錯誤: 找不到 docker-compose，請先安裝"
    exit 1
fi

# 建立必要的目錄
echo "建立必要的目錄..."
mkdir -p data/{ssh_keys,exam_results}
mkdir -p nginx/ssl
mkdir -p frontend/dist

# 設定 SSH 金鑰權限
if [[ -f "data/ssh_keys/id_rsa" ]]; then
    chmod 600 data/ssh_keys/id_rsa
    echo "✓ SSH 私鑰權限已設定"
else
    echo "⚠ 請將您的 SSH 私鑰放置到 data/ssh_keys/id_rsa"
fi

# 建立範例 SSL 憑證（自簽名）
if [[ ! -f "nginx/ssl/cert.pem" ]]; then
    echo "建立範例 SSL 憑證..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=TW/ST=Taiwan/L=Taipei/O=K8s Exam/CN=localhost" 2>/dev/null || echo "⚠ 無法建立 SSL 憑證，跳過"
fi

# 檢查 Redis 資料目錄
echo "準備 Redis 資料目錄..."
docker volume create k8s-exam_redis_data >/dev/null 2>&1 || true

# 建置並啟動服務
echo "建置 Docker 映像..."
docker-compose build

echo "啟動核心服務..."
docker-compose up -d nginx backend redis

# 等待服務啟動
echo "等待服務啟動..."
sleep 10

# 健康檢查
echo "執行健康檢查..."
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✓ 服務啟動成功"
else
    echo "⚠ 健康檢查失敗，請檢查服務狀態"
fi

echo ""
echo "=== 初始化完成 ==="
echo "Web 介面: http://localhost"
echo "API 文件: http://localhost/api/docs"
echo ""
echo "使用指令："
echo "  啟動服務: docker-compose up -d"
echo "  停止服務: docker-compose down"
echo "  查看日誌: docker-compose logs -f"
echo ""
echo "注意事項："
echo "1. 請確保您的 SSH 私鑰已放置到 data/ssh_keys/id_rsa"
echo "2. 請確保目標 VM 可透過 SSH 連線"
echo "3. 建議在生產環境中使用有效的 SSL 憑證"