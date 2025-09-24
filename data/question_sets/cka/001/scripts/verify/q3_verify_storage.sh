#!/bin/bash

# CKA 001 - 題目 3 驗證腳本
# 驗證持久化儲存配置

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

echo -e "${YELLOW}開始驗證題目 3：持久化儲存配置${NC}"
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

# 驗證 1：檢查 PersistentVolume 是否存在
echo "檢查 PersistentVolume 'data-pv' 是否存在..."
if kubectl get pv data-pv >/dev/null 2>&1; then
    add_success 3 "PersistentVolume 'data-pv' 存在"

    # 驗證 PV 容量
    PV_CAPACITY=$(kubectl get pv data-pv -o jsonpath='{.spec.capacity.storage}')
    if [[ "$PV_CAPACITY" == "1Gi" ]]; then
        add_success 3 "PV 容量配置正確：$PV_CAPACITY"
    else
        add_error "PV 容量配置不正確，預期：1Gi，實際：$PV_CAPACITY"
    fi

    # 驗證 PV 存取模式
    PV_ACCESS_MODE=$(kubectl get pv data-pv -o jsonpath='{.spec.accessModes[0]}')
    if [[ "$PV_ACCESS_MODE" == "ReadWriteOnce" ]]; then
        add_success 2 "PV 存取模式配置正確：$PV_ACCESS_MODE"
    else
        add_error "PV 存取模式配置不正確，預期：ReadWriteOnce，實際：$PV_ACCESS_MODE"
    fi

    # 驗證 PV hostPath 配置
    PV_TYPE=$(kubectl get pv data-pv -o jsonpath='{.spec.hostPath.path}' 2>/dev/null || echo "")
    if [[ "$PV_TYPE" == "/tmp/data" ]]; then
        add_success 3 "PV hostPath 配置正確：$PV_TYPE"
    else
        add_error "PV hostPath 配置不正確，預期：/tmp/data，實際：$PV_TYPE"
    fi

    # 檢查 PV 狀態
    PV_STATUS=$(kubectl get pv data-pv -o jsonpath='{.status.phase}')
    if [[ "$PV_STATUS" == "Bound" ]]; then
        add_success 2 "PV 狀態正確：$PV_STATUS（已綁定）"
    elif [[ "$PV_STATUS" == "Available" ]]; then
        echo -e "${YELLOW}ⓘ PV 狀態：$PV_STATUS（可用但未綁定）${NC}"
    else
        add_error "PV 狀態異常：$PV_STATUS"
    fi

else
    add_error "PersistentVolume 'data-pv' 不存在"
fi

# 驗證 2：檢查 PersistentVolumeClaim 是否存在
echo "檢查 PersistentVolumeClaim 'data-pvc' 是否存在..."
if kubectl get pvc data-pvc -n default >/dev/null 2>&1; then
    add_success 3 "PersistentVolumeClaim 'data-pvc' 存在"

    # 驗證 PVC 請求容量
    PVC_REQUEST=$(kubectl get pvc data-pvc -n default -o jsonpath='{.spec.resources.requests.storage}')
    if [[ "$PVC_REQUEST" == "500Mi" ]]; then
        add_success 3 "PVC 請求容量配置正確：$PVC_REQUEST"
    else
        add_error "PVC 請求容量配置不正確，預期：500Mi，實際：$PVC_REQUEST"
    fi

    # 驗證 PVC 存取模式
    PVC_ACCESS_MODE=$(kubectl get pvc data-pvc -n default -o jsonpath='{.spec.accessModes[0]}')
    if [[ "$PVC_ACCESS_MODE" == "ReadWriteOnce" ]]; then
        add_success 2 "PVC 存取模式配置正確：$PVC_ACCESS_MODE"
    else
        add_error "PVC 存取模式配置不正確，預期：ReadWriteOnce，實際：$PVC_ACCESS_MODE"
    fi

    # 檢查 PVC 狀態
    PVC_STATUS=$(kubectl get pvc data-pvc -n default -o jsonpath='{.status.phase}')
    if [[ "$PVC_STATUS" == "Bound" ]]; then
        add_success 2 "PVC 狀態正確：$PVC_STATUS（已綁定）"

        # 檢查綁定的 PV
        BOUND_PV=$(kubectl get pvc data-pvc -n default -o jsonpath='{.spec.volumeName}')
        if [[ "$BOUND_PV" == "data-pv" ]]; then
            add_success 2 "PVC 正確綁定到 PV：$BOUND_PV"
        else
            add_error "PVC 綁定到錯誤的 PV，預期：data-pv，實際：$BOUND_PV"
        fi
    else
        add_error "PVC 狀態異常：$PVC_STATUS"
    fi

else
    add_error "PersistentVolumeClaim 'data-pvc' 不存在"
fi

# 驗證 3：檢查 Pod 是否存在並正確掛載
echo "檢查 Pod 'storage-pod' 是否存在..."
if kubectl get pod storage-pod -n default >/dev/null 2>&1; then
    add_success 2 "Pod 'storage-pod' 存在"

    # 驗證 Pod 狀態
    POD_STATUS=$(kubectl get pod storage-pod -n default -o jsonpath='{.status.phase}')
    if [[ "$POD_STATUS" == "Running" ]]; then
        add_success 3 "Pod 'storage-pod' 處於 Running 狀態"
    else
        add_error "Pod 'storage-pod' 不在 Running 狀態，目前狀態：$POD_STATUS"
    fi

    # 驗證 Pod 映像
    POD_IMAGE=$(kubectl get pod storage-pod -n default -o jsonpath='{.spec.containers[0].image}')
    if [[ "$POD_IMAGE" == "busybox" ]]; then
        add_success 1 "Pod 使用正確映像：$POD_IMAGE"
    else
        add_error "Pod 映像不正確，預期：busybox，實際：$POD_IMAGE"
    fi

    # 驗證掛載點
    MOUNT_PATH=$(kubectl get pod storage-pod -n default -o jsonpath='{.spec.containers[0].volumeMounts[0].mountPath}' 2>/dev/null || echo "")
    if [[ "$MOUNT_PATH" == "/data" ]]; then
        add_success 2 "卷掛載路徑配置正確：$MOUNT_PATH"
    else
        add_error "卷掛載路徑配置不正確，預期：/data，實際：$MOUNT_PATH"
    fi

    # 驗證使用的卷名
    VOLUME_NAME=$(kubectl get pod storage-pod -n default -o jsonpath='{.spec.containers[0].volumeMounts[0].name}' 2>/dev/null || echo "")
    PVC_VOLUME=$(kubectl get pod storage-pod -n default -o jsonpath='{.spec.volumes[0].persistentVolumeClaim.claimName}' 2>/dev/null || echo "")

    if [[ "$PVC_VOLUME" == "data-pvc" ]]; then
        add_success 3 "Pod 正確使用 PVC：$PVC_VOLUME"
    else
        add_error "Pod 未正確使用 PVC，預期：data-pvc，實際：$PVC_VOLUME"
    fi

else
    add_error "Pod 'storage-pod' 不存在"
fi

# 驗證 4：測試檔案讀寫（如果 Pod 正在運行）
echo "測試檔案讀寫功能..."
if kubectl get pod storage-pod -n default >/dev/null 2>&1; then
    POD_STATUS=$(kubectl get pod storage-pod -n default -o jsonpath='{.status.phase}')
    if [[ "$POD_STATUS" == "Running" ]]; then
        # 測試寫入檔案
        if kubectl exec storage-pod -n default -- sh -c 'echo "test data" > /data/test.txt' >/dev/null 2>&1; then
            add_success 1 "成功在掛載點寫入檔案"

            # 測試讀取檔案
            TEST_CONTENT=$(kubectl exec storage-pod -n default -- cat /data/test.txt 2>/dev/null || echo "")
            if [[ "$TEST_CONTENT" == "test data" ]]; then
                add_success 1 "成功從掛載點讀取檔案"
            else
                add_error "無法從掛載點讀取檔案或內容不正確"
            fi

            # 清理測試檔案
            kubectl exec storage-pod -n default -- rm -f /data/test.txt >/dev/null 2>&1 || true
        else
            add_error "無法在掛載點寫入檔案"
        fi
    else
        echo -e "${YELLOW}⚠ Pod 未運行，跳過檔案讀寫測試${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Pod 不存在，跳過檔案讀寫測試${NC}"
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

# 顯示建議的除錯指令
echo -e "\n${YELLOW}建議的除錯指令：${NC}"
echo "1. 檢查 PV 狀態：kubectl get pv data-pv -o wide"
echo "2. 檢查 PVC 狀態：kubectl get pvc data-pvc -o wide"
echo "3. 檢查 Pod 詳情：kubectl describe pod storage-pod"
echo "4. 檢查綁定關係：kubectl get pv,pvc"

# 輸出 JSON 格式結果供系統讀取
cat > /tmp/q3_result.json <<EOF
{
    "question_id": 3,
    "total_points": $TOTAL_POINTS,
    "earned_points": $EARNED_POINTS,
    "success_rate": $(echo "scale=2; $EARNED_POINTS * 100 / $TOTAL_POINTS" | bc -l),
    "errors": [$(printf '"%s",' "${ERRORS[@]}" | sed 's/,$//')],
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "\n${GREEN}驗證完成！詳細結果已儲存至 /tmp/q3_result.json${NC}"

# 回傳適當的退出碼
if [[ $EARNED_POINTS -ge $((TOTAL_POINTS * 7 / 10)) ]]; then
    exit 0  # 70% 以上視為通過
else
    exit 1  # 未達標準
fi