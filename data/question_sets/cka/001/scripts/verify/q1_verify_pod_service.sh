#!/bin/bash

# CKA 001 - 題目 1 驗證腳本
# 驗證 Pod 和 Service 的建立和功能

set -euo pipefail

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 計分變數
TOTAL_POINTS=30
EARNED_POINTS=0
ERRORS=()

echo -e "${YELLOW}開始驗證題目 1：建立 Pod 和 Service${NC}"
echo "========================================"

# 函數：新增錯誤訊息
add_error() {
    ERRORS+=("$1")
    echo -e "${RED}✗ $1${NC}"
}

# 函數：新增成功訊息
add_success() {
    local points=$1
    local message=$2
    EARNED_POINTS=$((EARNED_POINTS + points))
    echo -e "${GREEN}✓ $message (+${points} 分)${NC}"
}

# 驗證 1：檢查 Pod 是否存在
echo "檢查 Pod 'web-app' 是否存在..."
if kubectl get pod web-app -n default >/dev/null 2>&1; then
    add_success 5 "Pod 'web-app' 存在"

    # 驗證 Pod 狀態
    POD_STATUS=$(kubectl get pod web-app -n default -o jsonpath='{.status.phase}')
    if [[ "$POD_STATUS" == "Running" ]]; then
        add_success 10 "Pod 'web-app' 處於 Running 狀態"
    else
        add_error "Pod 'web-app' 不在 Running 狀態，目前狀態：$POD_STATUS"
    fi

    # 驗證 Pod 映像
    POD_IMAGE=$(kubectl get pod web-app -n default -o jsonpath='{.spec.containers[0].image}')
    if [[ "$POD_IMAGE" == "nginx:1.20" ]]; then
        add_success 5 "Pod 使用正確映像：$POD_IMAGE"
    else
        add_error "Pod 映像不正確，預期：nginx:1.20，實際：$POD_IMAGE"
    fi

else
    add_error "Pod 'web-app' 不存在"
fi

# 驗證 2：檢查 Service 是否存在
echo "檢查 Service 'web-service' 是否存在..."
if kubectl get service web-service -n default >/dev/null 2>&1; then
    add_success 5 "Service 'web-service' 存在"

    # 驗證 Service 類型
    SERVICE_TYPE=$(kubectl get service web-service -n default -o jsonpath='{.spec.type}')
    if [[ "$SERVICE_TYPE" == "ClusterIP" ]]; then
        add_success 3 "Service 類型正確：ClusterIP"
    else
        add_error "Service 類型不正確，預期：ClusterIP，實際：$SERVICE_TYPE"
    fi

    # 驗證 Service 埠配置
    SERVICE_PORT=$(kubectl get service web-service -n default -o jsonpath='{.spec.ports[0].port}')
    TARGET_PORT=$(kubectl get service web-service -n default -o jsonpath='{.spec.ports[0].targetPort}')

    if [[ "$SERVICE_PORT" == "80" ]]; then
        add_success 1 "Service 埠配置正確：$SERVICE_PORT"
    else
        add_error "Service 埠配置不正確，預期：80，實際：$SERVICE_PORT"
    fi

    if [[ "$TARGET_PORT" == "80" ]]; then
        add_success 1 "Service 目標埠配置正確：$TARGET_PORT"
    else
        add_error "Service 目標埠配置不正確，預期：80，實際：$TARGET_PORT"
    fi

else
    add_error "Service 'web-service' 不存在"
fi

# 驗證 3：測試服務連通性（如果可能的話）
echo "測試服務連通性..."
if kubectl get service web-service -n default >/dev/null 2>&1 && kubectl get pod web-app -n default >/dev/null 2>&1; then
    # 取得 Service 的 ClusterIP
    CLUSTER_IP=$(kubectl get service web-service -n default -o jsonpath='{.spec.clusterIP}')

    # 檢查端點是否存在
    ENDPOINTS=$(kubectl get endpoints web-service -n default -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || echo "")
    if [[ -n "$ENDPOINTS" ]]; then
        add_success 5 "Service 有有效的端點：$ENDPOINTS"
    else
        add_error "Service 沒有有效的端點"
    fi
else
    add_error "無法執行連通性測試，Pod 或 Service 不存在"
fi

# 顯示結果摘要
echo ""
echo "========================================"
echo -e "${YELLOW}驗證結果摘要${NC}"
echo "========================================"
echo "獲得分數：$EARNED_POINTS / $TOTAL_POINTS"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo -e "\n${RED}發現以下問題：${NC}"
    for error in "${ERRORS[@]}"; do
        echo -e "  • $error"
    done
fi

# 輸出 JSON 格式結果供系統讀取
cat > /tmp/q1_result.json <<EOF
{
    "question_id": 1,
    "total_points": $TOTAL_POINTS,
    "earned_points": $EARNED_POINTS,
    "success_rate": $(echo "scale=2; $EARNED_POINTS * 100 / $TOTAL_POINTS" | bc -l),
    "errors": [$(printf '"%s",' "${ERRORS[@]}" | sed 's/,$//')],
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "\n${GREEN}驗證完成！詳細結果已儲存至 /tmp/q1_result.json${NC}"

# 回傳適當的退出碼
if [[ $EARNED_POINTS -ge $((TOTAL_POINTS * 7 / 10)) ]]; then
    exit 0  # 70% 以上視為通過
else
    exit 1  # 未達標準
fi