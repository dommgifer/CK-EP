#!/bin/bash
"""
E2E 測試執行腳本
自動化完整的端對端測試流程
"""

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查必要工具
check_requirements() {
    log_info "檢查測試環境需求..."

    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi

    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝"
        exit 1
    fi

    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安裝"
        exit 1
    fi

    # 檢查 Chrome (用於 Selenium)
    if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
        log_warning "Chrome/Chromium 未檢測到，將使用 headless 模式"
    fi

    log_success "環境需求檢查完成"
}

# 設定測試環境
setup_test_environment() {
    log_info "設定測試環境..."

    # 建立測試虛擬環境
    if [ ! -d "tests/e2e/venv" ]; then
        log_info "建立 Python 虛擬環境..."
        python3 -m venv tests/e2e/venv
    fi

    # 啟動虛擬環境
    source tests/e2e/venv/bin/activate

    # 安裝測試依賴
    log_info "安裝測試依賴..."
    pip install -r tests/e2e/requirements.txt

    # 下載 ChromeDriver
    log_info "設定 WebDriver..."
    python3 -c "
from webdriver_manager.chrome import ChromeDriverManager
ChromeDriverManager().install()
" || log_warning "ChromeDriver 安裝失敗，可能影響 UI 測試"

    log_success "測試環境設定完成"
}

# 準備測試資料
prepare_test_data() {
    log_info "準備測試資料..."

    # 建立測試題組目錄
    mkdir -p data/question_sets/{cka,ckad,cks}

    # 建立測試用 SSH 金鑰目錄
    mkdir -p data/ssh_keys

    # 如果不存在測試金鑰則建立一個
    if [ ! -f "data/ssh_keys/id_rsa" ]; then
        log_warning "建立測試用 SSH 金鑰（僅用於測試）"
        ssh-keygen -t rsa -b 2048 -f data/ssh_keys/id_rsa -N ""
    fi

    log_success "測試資料準備完成"
}

# 執行 E2E 測試
run_e2e_tests() {
    log_info "開始執行 E2E 測試..."

    # 啟動虛擬環境
    source tests/e2e/venv/bin/activate

    # 設定測試環境變數
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    export TEST_ENV=e2e

    # 執行測試
    pytest tests/e2e/ \
        -v \
        --tb=short \
        --maxfail=3 \
        --timeout=600 \
        --html=tests/e2e/reports/report.html \
        --self-contained-html \
        --cov=backend/src \
        --cov-report=html:tests/e2e/reports/coverage \
        --cov-report=term-missing \
        -m "e2e" \
        "$@"

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_success "所有 E2E 測試通過！"
    else
        log_error "E2E 測試失敗，退出代碼: $exit_code"
    fi

    return $exit_code
}

# 清理測試環境
cleanup_test_environment() {
    log_info "清理測試環境..."

    # 停止所有測試容器
    docker-compose down -v --remove-orphans 2>/dev/null || true

    # 清理測試資料（可選）
    if [ "$CLEANUP_DATA" = "true" ]; then
        log_warning "清理測試資料..."
        rm -rf data/question_sets/*/e2e-test-*
        rm -rf data/question_sets/*/timeout-test*
        rm -rf data/question_sets/*/concurrent-test*
    fi

    log_success "測試環境清理完成"
}

# 顯示測試報告
show_test_report() {
    log_info "測試報告位置:"
    echo "  HTML 報告: tests/e2e/reports/report.html"
    echo "  覆蓋率報告: tests/e2e/reports/coverage/index.html"

    if command -v xdg-open &> /dev/null; then
        log_info "正在開啟測試報告..."
        xdg-open tests/e2e/reports/report.html 2>/dev/null || true
    fi
}

# 主函數
main() {
    log_info "開始 E2E 測試流程..."

    # 改變到專案根目錄
    cd "$(dirname "$0")/.."

    # 建立報告目錄
    mkdir -p tests/e2e/reports

    # 檢查需求
    check_requirements

    # 設定測試環境
    setup_test_environment

    # 準備測試資料
    prepare_test_data

    # 設定清理處理器
    trap cleanup_test_environment EXIT

    # 執行測試
    if run_e2e_tests "$@"; then
        log_success "E2E 測試流程完成！"
        show_test_report
        exit 0
    else
        log_error "E2E 測試失敗！"
        show_test_report
        exit 1
    fi
}

# 如果直接執行此腳本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi