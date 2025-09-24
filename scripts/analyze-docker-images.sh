#!/bin/bash

# T107: 容器映像大小最佳化 - Docker 映像分析工具
# 分析和比較 Docker 映像大小、層級和最佳化機會

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 映像名稱
BACKEND_IMAGE="k8s-exam-simulator-backend"
FRONTEND_IMAGE="k8s-exam-simulator-frontend"
NGINX_IMAGE="k8s-exam-simulator-nginx"
VNC_IMAGE="k8s-exam-simulator-vnc"
BASTION_IMAGE="k8s-exam-simulator-bastion"

echo -e "${BLUE}🔍 Kubernetes 考試模擬器 - Docker 映像分析${NC}"
echo "=" * 60

# 函數：取得映像大小
get_image_size() {
    local image_name=$1
    if docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep -q "$image_name"; then
        docker images --format "{{.Size}}" "$image_name:latest" 2>/dev/null || echo "N/A"
    else
        echo "不存在"
    fi
}

# 函數：取得映像詳細資訊
get_image_details() {
    local image_name=$1
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image_name"; then
        docker inspect "$image_name:latest" --format '{{.Size}}' 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# 函數：分析映像層級
analyze_image_layers() {
    local image_name=$1
    echo -e "\n${YELLOW}🔎 分析映像層級: $image_name${NC}"

    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image_name"; then
        docker history "$image_name:latest" --format "table {{.CreatedBy}}\t{{.Size}}" --no-trunc 2>/dev/null || {
            echo "無法分析映像層級"
            return 1
        }
    else
        echo "映像不存在: $image_name"
        return 1
    fi
}

# 函數：轉換大小為 MB
size_to_mb() {
    local size=$1
    if [[ $size == *"GB"* ]]; then
        echo "$size" | sed 's/GB//' | awk '{printf "%.0f", $1 * 1024}'
    elif [[ $size == *"MB"* ]]; then
        echo "$size" | sed 's/MB//' | awk '{printf "%.0f", $1}'
    elif [[ $size == *"KB"* ]]; then
        echo "$size" | sed 's/KB//' | awk '{printf "%.1f", $1 / 1024}'
    else
        # 假設是 bytes
        awk "BEGIN {printf \"%.1f\", $size / 1024 / 1024}"
    fi
}

# 函數：映像大小評分
grade_image_size() {
    local size_mb=$1
    local image_type=$2

    case $image_type in
        "backend")
            if (( $(echo "$size_mb < 200" | bc -l) )); then
                echo "A+ 🟢"
            elif (( $(echo "$size_mb < 400" | bc -l) )); then
                echo "A 🟢"
            elif (( $(echo "$size_mb < 600" | bc -l) )); then
                echo "B 🟡"
            elif (( $(echo "$size_mb < 800" | bc -l) )); then
                echo "C 🟠"
            else
                echo "D 🔴"
            fi
            ;;
        "frontend")
            if (( $(echo "$size_mb < 50" | bc -l) )); then
                echo "A+ 🟢"
            elif (( $(echo "$size_mb < 100" | bc -l) )); then
                echo "A 🟢"
            elif (( $(echo "$size_mb < 200" | bc -l) )); then
                echo "B 🟡"
            elif (( $(echo "$size_mb < 300" | bc -l) )); then
                echo "C 🟠"
            else
                echo "D 🔴"
            fi
            ;;
        "utility")
            if (( $(echo "$size_mb < 100" | bc -l) )); then
                echo "A+ 🟢"
            elif (( $(echo "$size_mb < 200" | bc -l) )); then
                echo "A 🟢"
            elif (( $(echo "$size_mb < 300" | bc -l) )); then
                echo "B 🟡"
            elif (( $(echo "$size_mb < 500" | bc -l) )); then
                echo "C 🟠"
            else
                echo "D 🔴"
            fi
            ;;
    esac
}

# 主要分析函數
analyze_images() {
    echo -e "\n${GREEN}📊 映像大小分析${NC}"
    echo "映像名稱                    | 大小      | 評分    | 類型"
    echo "-" * 65

    declare -A images
    images["$BACKEND_IMAGE"]="backend"
    images["$FRONTEND_IMAGE"]="frontend"
    images["$NGINX_IMAGE"]="utility"
    images["$VNC_IMAGE"]="utility"
    images["$BASTION_IMAGE"]="utility"

    total_size_mb=0
    image_count=0

    for image_name in "${!images[@]}"; do
        image_type=${images[$image_name]}
        size=$(get_image_size "$image_name")

        if [[ $size != "不存在" && $size != "N/A" ]]; then
            size_mb=$(size_to_mb "$size")
            grade=$(grade_image_size "$size_mb" "$image_type")

            printf "%-28s | %-9s | %-8s | %s\n" "$image_name" "$size" "$grade" "$image_type"

            total_size_mb=$(echo "$total_size_mb + $size_mb" | bc -l)
            ((image_count++))
        else
            printf "%-28s | %-9s | %-8s | %s\n" "$image_name" "$size" "N/A" "$image_type"
        fi
    done

    echo "-" * 65
    if (( image_count > 0 )); then
        printf "總大小: %.1f MB | 映像數: %d\n" "$total_size_mb" "$image_count"
    fi
}

# 分析基礎映像
analyze_base_images() {
    echo -e "\n${GREEN}🔍 基礎映像分析${NC}"

    base_images=("python:3.11-slim" "node:18-alpine" "nginx:alpine" "consol/debian-xfce-vnc" "alpine:3.19")

    echo "基礎映像             | 大小"
    echo "-" * 35

    for base_image in "${base_images[@]}"; do
        if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$base_image"; then
            size=$(docker images --format "{{.Size}}" "$base_image" 2>/dev/null || echo "未知")
            printf "%-20s | %s\n" "$base_image" "$size"
        else
            printf "%-20s | %s\n" "$base_image" "未下載"
        fi
    done
}

# 最佳化建議
optimization_suggestions() {
    echo -e "\n${GREEN}💡 最佳化建議${NC}"

    # 檢查是否使用多階段建構
    echo "🔍 檢查多階段建構使用情況..."

    for dockerfile in "backend/Dockerfile" "frontend/Dockerfile"; do
        if [[ -f "$dockerfile" ]]; then
            if grep -q "FROM.*as.*" "$dockerfile"; then
                echo "✅ $dockerfile: 使用多階段建構"
            else
                echo "⚠️  $dockerfile: 建議使用多階段建構"
            fi
        fi
    done

    echo ""
    echo "📋 一般最佳化建議:"
    echo "1. 使用 Alpine 基礎映像減少大小"
    echo "2. 使用多階段建構分離建置和運行環境"
    echo "3. 合併 RUN 指令減少層級數量"
    echo "4. 清理套件管理器快取和臨時檔案"
    echo "5. 使用 .dockerignore 排除不必要的檔案"
    echo "6. 最小化安裝的套件和依賴"
    echo "7. 使用非 root 使用者提高安全性"
    echo ""

    # 檢查 .dockerignore 檔案
    echo "🔍 檢查 .dockerignore 檔案..."
    for dir in "backend" "frontend"; do
        if [[ -f "$dir/.dockerignore" ]]; then
            echo "✅ $dir/.dockerignore: 存在"
        else
            echo "⚠️  $dir/.dockerignore: 建議建立以排除不必要檔案"
        fi
    done
}

# 效能影響分析
performance_impact() {
    echo -e "\n${GREEN}⚡ 效能影響分析${NC}"

    total_size_mb=0
    for image_name in "$BACKEND_IMAGE" "$FRONTEND_IMAGE" "$VNC_IMAGE" "$BASTION_IMAGE"; do
        size=$(get_image_size "$image_name")
        if [[ $size != "不存在" && $size != "N/A" ]]; then
            size_mb=$(size_to_mb "$size")
            total_size_mb=$(echo "$total_size_mb + $size_mb" | bc -l)
        fi
    done

    echo "📊 映像大小對效能的影響:"
    printf "   總下載大小: %.1f MB\n" "$total_size_mb"

    # 估算下載時間
    download_time_1mbps=$(echo "scale=1; $total_size_mb * 8 / 1" | bc -l)
    download_time_10mbps=$(echo "scale=1; $total_size_mb * 8 / 10" | bc -l)
    download_time_100mbps=$(echo "scale=1; $total_size_mb * 8 / 100" | bc -l)

    printf "   估算下載時間 (1 Mbps): %.1f 秒\n" "$download_time_1mbps"
    printf "   估算下載時間 (10 Mbps): %.1f 秒\n" "$download_time_10mbps"
    printf "   估算下載時間 (100 Mbps): %.1f 秒\n" "$download_time_100mbps"

    # 記憶體影響
    echo ""
    echo "💾 記憶體使用影響:"
    echo "   - 每個映像層級都會消耗記憶體"
    echo "   - 較大的映像需要更多磁碟空間"
    echo "   - 容器啟動時間與映像大小呈正比"
}

# 比較分析
compare_with_benchmarks() {
    echo -e "\n${GREEN}📈 基準比較${NC}"

    echo "映像類型    | 理想大小 | 可接受大小 | 需最佳化"
    echo "-" * 45
    echo "後端 API   | <200MB   | <400MB     | >600MB"
    echo "前端靜態   | <50MB    | <100MB     | >200MB"
    echo "工具容器   | <100MB   | <200MB     | >300MB"
    echo ""

    # 實際映像與基準比較
    for image_name in "$BACKEND_IMAGE" "$FRONTEND_IMAGE"; do
        size=$(get_image_size "$image_name")
        if [[ $size != "不存在" && $size != "N/A" ]]; then
            size_mb=$(size_to_mb "$size")

            if [[ $image_name == *"backend"* ]]; then
                if (( $(echo "$size_mb < 200" | bc -l) )); then
                    status="理想 ✅"
                elif (( $(echo "$size_mb < 400" | bc -l) )); then
                    status="可接受 🟡"
                else
                    status="需最佳化 🔴"
                fi
            else
                if (( $(echo "$size_mb < 50" | bc -l) )); then
                    status="理想 ✅"
                elif (( $(echo "$size_mb < 100" | bc -l) )); then
                    status="可接受 🟡"
                else
                    status="需最佳化 🔴"
                fi
            fi

            printf "%s: %.1f MB - %s\n" "$image_name" "$size_mb" "$status"
        fi
    done
}

# 生成最佳化報告
generate_optimization_report() {
    local report_file="docker-optimization-report.md"

    echo -e "\n${GREEN}📋 生成最佳化報告${NC}"

    cat > "$report_file" << EOF
# Docker 映像最佳化報告

生成時間: $(date)

## 映像大小分析

$(analyze_images | sed 's/\x1b\[[0-9;]*m//g')

## 最佳化建議

### 立即行動項目
- [ ] 檢查並清理不必要的依賴
- [ ] 確保所有 Dockerfile 使用多階段建構
- [ ] 建立 .dockerignore 檔案排除不必要檔案
- [ ] 使用 Alpine 基礎映像

### 中期改善
- [ ] 實作映像層級快取策略
- [ ] 使用 Docker BuildKit 進階功能
- [ ] 考慮使用 distroless 映像
- [ ] 設定自動化映像掃描

### 監控指標
- 映像總大小目標: < 1GB
- 建構時間目標: < 5 分鐘
- 容器啟動時間: < 30 秒

EOF

    echo "報告已儲存至: $report_file"
}

# 主程式執行
main() {
    echo -e "${BLUE}開始分析 Docker 映像...${NC}\n"

    # 檢查 Docker 是否可用
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安裝或不可用${NC}"
        exit 1
    fi

    # 檢查是否有映像存在
    if ! docker images --format "{{.Repository}}" | grep -q "k8s-exam-simulator"; then
        echo -e "${YELLOW}⚠️  未找到專案映像，請先建構映像：${NC}"
        echo "docker-compose build"
        echo ""
    fi

    analyze_images
    analyze_base_images
    optimization_suggestions
    performance_impact
    compare_with_benchmarks

    # 如果有 --report 參數，生成詳細報告
    if [[ "${1:-}" == "--report" ]]; then
        generate_optimization_report
    fi

    echo -e "\n${GREEN}✅ 分析完成${NC}"
}

# 檢查參數
if [[ "${1:-}" == "--help" ]]; then
    echo "用法: $0 [--report] [--help]"
    echo ""
    echo "選項:"
    echo "  --report    生成詳細的最佳化報告"
    echo "  --help      顯示此幫助訊息"
    exit 0
fi

main "$@"