#!/bin/bash

# CKA 001 - 題目 2 驗證腳本
# 驗證 NetworkPolicy 配置

set -euo pipefail

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 計分變數
TOTAL_POINTS=40
EARNED_POINTS=0
ERRORS=()

echo -e "${YELLOW}開始驗證題目 2：網路政策配置${NC}"
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

# 驗證 1：檢查 NetworkPolicy 是否存在
echo "檢查 NetworkPolicy 'deny-all-ingress' 是否存在..."
if kubectl get networkpolicy deny-all-ingress -n default >/dev/null 2>&1; then
    add_success 8 "NetworkPolicy 'deny-all-ingress' 存在"

    # 驗證 NetworkPolicy 的 podSelector
    POD_SELECTOR=$(kubectl get networkpolicy deny-all-ingress -n default -o jsonpath='{.spec.podSelector.matchLabels.app}' 2>/dev/null || echo "")
    if [[ "$POD_SELECTOR" == "restricted" ]]; then
        add_success 8 "podSelector 配置正確：app=restricted"
    else
        add_error "podSelector 配置不正確，預期：app=restricted，實際：$POD_SELECTOR"
    fi

    # 驗證 policyTypes
    POLICY_TYPES=$(kubectl get networkpolicy deny-all-ingress -n default -o jsonpath='{.spec.policyTypes[0]}' 2>/dev/null || echo "")
    if [[ "$POLICY_TYPES" == "Ingress" ]]; then
        add_success 4 "policyTypes 配置正確：Ingress"
    else
        add_error "policyTypes 配置不正確，預期：Ingress，實際：$POLICY_TYPES"
    fi

else
    add_error "NetworkPolicy 'deny-all-ingress' 不存在"
fi

# 驗證 2：檢查 Ingress 規則
echo "檢查 Ingress 規則配置..."
if kubectl get networkpolicy deny-all-ingress -n default >/dev/null 2>&1; then
    # 檢查是否有允許的來源標籤
    FROM_SELECTOR=$(kubectl get networkpolicy deny-all-ingress -n default -o jsonpath='{.spec.ingress[0].from[0].podSelector.matchLabels.role}' 2>/dev/null || echo "")
    if [[ "$FROM_SELECTOR" == "frontend" ]]; then
        add_success 8 "允許來源標籤配置正確：role=frontend"
    else
        add_error "允許來源標籤配置不正確，預期：role=frontend，實際：$FROM_SELECTOR"
    fi

    # 檢查埠配置
    ALLOWED_PORT=$(kubectl get networkpolicy deny-all-ingress -n default -o jsonpath='{.spec.ingress[0].ports[0].port}' 2>/dev/null || echo "")
    ALLOWED_PROTOCOL=$(kubectl get networkpolicy deny-all-ingress -n default -o jsonpath='{.spec.ingress[0].ports[0].protocol}' 2>/dev/null || echo "")

    if [[ "$ALLOWED_PORT" == "8080" ]]; then
        add_success 4 "允許埠配置正確：8080"
    else
        add_error "允許埠配置不正確，預期：8080，實際：$ALLOWED_PORT"
    fi

    if [[ "$ALLOWED_PROTOCOL" == "TCP" ]]; then
        add_success 4 "協定配置正確：TCP"
    else
        add_error "協定配置不正確，預期：TCP，實際：$ALLOWED_PROTOCOL"
    fi
fi

# 驗證 3：檢查測試 Pod 是否存在（可選）
echo "檢查測試環境..."
RESTRICTED_POD_EXISTS=false
FRONTEND_POD_EXISTS=false

# 檢查是否有帶 app=restricted 標籤的 Pod
if kubectl get pods -l app=restricted -n default >/dev/null 2>&1; then
    RESTRICTED_POD_COUNT=$(kubectl get pods -l app=restricted -n default --no-headers | wc -l)
    if [[ $RESTRICTED_POD_COUNT -gt 0 ]]; then
        RESTRICTED_POD_EXISTS=true
        add_success 2 "找到 $RESTRICTED_POD_COUNT 個帶有 app=restricted 標籤的 Pod"
    fi
fi

# 檢查是否有帶 role=frontend 標籤的 Pod
if kubectl get pods -l role=frontend -n default >/dev/null 2>&1; then
    FRONTEND_POD_COUNT=$(kubectl get pods -l role=frontend -n default --no-headers | wc -l)
    if [[ $FRONTEND_POD_COUNT -gt 0 ]]; then
        FRONTEND_POD_EXISTS=true
        add_success 2 "找到 $FRONTEND_POD_COUNT 個帶有 role=frontend 標籤的 Pod"
    fi
fi

# 如果沒有測試 Pod，給予提示但不扣分
if [[ "$RESTRICTED_POD_EXISTS" == false ]] && [[ "$FRONTEND_POD_EXISTS" == false ]]; then
    echo -e "${YELLOW}⚠ 建議：建立測試 Pod 來驗證 NetworkPolicy 的實際效果${NC}"
fi

# 驗證 4：驗證 NetworkPolicy YAML 結構完整性
echo "驗證 NetworkPolicy 結構完整性..."
NETPOL_YAML=$(kubectl get networkpolicy deny-all-ingress -n default -o yaml 2>/dev/null || echo "")

if [[ -n "$NETPOL_YAML" ]]; then
    # 檢查是否包含必要的欄位
    if echo "$NETPOL_YAML" | grep -q "podSelector:" && echo "$NETPOL_YAML" | grep -q "policyTypes:" && echo "$NETPOL_YAML" | grep -q "ingress:"; then
        add_success 4 "NetworkPolicy 結構完整"
    else
        add_error "NetworkPolicy 結構不完整，缺少必要欄位"
    fi
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

# 顯示建議的測試指令
echo -e "\n${YELLOW}建議的測試指令：${NC}"
echo "1. 建立受限 Pod："
echo "   kubectl run restricted-pod --image=nginx --labels='app=restricted' --port=8080"
echo ""
echo "2. 建立前端 Pod："
echo "   kubectl run frontend-pod --image=busybox --labels='role=frontend' -- sleep 3600"
echo ""
echo "3. 測試連線（從前端 Pod 到受限 Pod）："
echo "   kubectl exec frontend-pod -- nc -zv \$RESTRICTED_POD_IP 8080"

# 輸出 JSON 格式結果供系統讀取
cat > /tmp/q2_result.json <<EOF
{
    "question_id": 2,
    "total_points": $TOTAL_POINTS,
    "earned_points": $EARNED_POINTS,
    "success_rate": $(echo "scale=2; $EARNED_POINTS * 100 / $TOTAL_POINTS" | bc -l),
    "errors": [$(printf '"%s",' "${ERRORS[@]}" | sed 's/,$//')],
    "restricted_pods_exist": $RESTRICTED_POD_EXISTS,
    "frontend_pods_exist": $FRONTEND_POD_EXISTS,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "\n${GREEN}驗證完成！詳細結果已儲存至 /tmp/q2_result.json${NC}"

# 回傳適當的退出碼
if [[ $EARNED_POINTS -ge $((TOTAL_POINTS * 7 / 10)) ]]; then
    exit 0  # 70% 以上視為通過
else
    exit 1  # 未達標準
fi