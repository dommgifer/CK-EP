#!/bin/bash
# Kubernetes 考試題目評分腳本

set -e

QUESTION_ID=$1
SESSION_ID=$2

if [[ -z "$QUESTION_ID" || -z "$SESSION_ID" ]]; then
    echo "使用方式: $0 <question_id> <session_id>"
    exit 1
fi

# 讀取題目配置
QUESTION_FILE="/app/question_sets/questions/${QUESTION_ID}.json"
if [[ ! -f "$QUESTION_FILE" ]]; then
    echo "錯誤: 找不到題目檔案 $QUESTION_FILE"
    exit 1
fi

# 解析評分規則
RULES=$(jq -r '.scoring.rules[]' "$QUESTION_FILE")
TOTAL_SCORE=0
MAX_SCORE=$(jq -r '.scoring.total_points' "$QUESTION_FILE")

echo "開始評分題目 $QUESTION_ID (滿分: $MAX_SCORE)"
echo "----------------------------------------"

# 執行每個評分規則
while IFS= read -r rule; do
    rule_type=$(echo "$rule" | jq -r '.type')
    rule_points=$(echo "$rule" | jq -r '.points')

    case "$rule_type" in
        "resource_exists")
            resource_type=$(echo "$rule" | jq -r '.resource_type')
            resource_name=$(echo "$rule" | jq -r '.resource_name')
            namespace=$(echo "$rule" | jq -r '.namespace // "default"')

            if kubectl get "$resource_type" "$resource_name" -n "$namespace" >/dev/null 2>&1; then
                echo "✓ 資源存在: $resource_type/$resource_name (命名空間: $namespace) +$rule_points"
                TOTAL_SCORE=$((TOTAL_SCORE + rule_points))
            else
                echo "✗ 資源不存在: $resource_type/$resource_name (命名空間: $namespace)"
            fi
            ;;

        "pod_running")
            pod_name=$(echo "$rule" | jq -r '.pod_name')
            namespace=$(echo "$rule" | jq -r '.namespace // "default"')

            status=$(kubectl get pod "$pod_name" -n "$namespace" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
            if [[ "$status" == "Running" ]]; then
                echo "✓ Pod 正在運行: $pod_name (命名空間: $namespace) +$rule_points"
                TOTAL_SCORE=$((TOTAL_SCORE + rule_points))
            else
                echo "✗ Pod 未運行: $pod_name (狀態: $status)"
            fi
            ;;

        "service_accessible")
            service_name=$(echo "$rule" | jq -r '.service_name')
            namespace=$(echo "$rule" | jq -r '.namespace // "default"')
            port=$(echo "$rule" | jq -r '.port // "80"')

            service_ip=$(kubectl get svc "$service_name" -n "$namespace" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
            if [[ -n "$service_ip" ]] && curl -s --connect-timeout 5 "$service_ip:$port" >/dev/null; then
                echo "✓ 服務可存取: $service_name:$port (命名空間: $namespace) +$rule_points"
                TOTAL_SCORE=$((TOTAL_SCORE + rule_points))
            else
                echo "✗ 服務無法存取: $service_name:$port"
            fi
            ;;

        "custom_command")
            command=$(echo "$rule" | jq -r '.command')
            expected_output=$(echo "$rule" | jq -r '.expected_output // ""')

            output=$(eval "$command" 2>/dev/null || echo "")
            if [[ -z "$expected_output" && -n "$output" ]] || [[ "$output" =~ $expected_output ]]; then
                echo "✓ 自訂指令通過: $command +$rule_points"
                TOTAL_SCORE=$((TOTAL_SCORE + rule_points))
            else
                echo "✗ 自訂指令失敗: $command"
            fi
            ;;

        *)
            echo "⚠ 未知的評分規則類型: $rule_type"
            ;;
    esac
done <<< "$(echo "$RULES" | jq -c '.')"

echo "----------------------------------------"
echo "評分完成: $TOTAL_SCORE / $MAX_SCORE"

# 輸出結果 JSON
cat <<EOF
{
    "question_id": "$QUESTION_ID",
    "session_id": "$SESSION_ID",
    "score": $TOTAL_SCORE,
    "max_score": $MAX_SCORE,
    "percentage": $(echo "scale=2; $TOTAL_SCORE * 100 / $MAX_SCORE" | bc),
    "timestamp": "$(date -Iseconds)"
}
EOF