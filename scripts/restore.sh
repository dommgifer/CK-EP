#!/bin/bash
"""
DW-CK 系統恢復腳本
從備份檔案恢復系統資料、配置和狀態
"""

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 顯示幫助訊息
show_help() {
    echo "DW-CK 系統恢復腳本"
    echo
    echo "使用方式: $0 [選項] <備份檔案>"
    echo
    echo "選項:"
    echo "  --force              強制恢復，不要求確認"
    echo "  --no-database        跳過資料庫恢復"
    echo "  --no-config          跳過配置檔案恢復"
    echo "  --no-questions       跳過題組資料恢復"
    echo "  --restore-dir DIR    指定恢復目錄 (預設: 當前目錄)"
    echo "  --dry-run           只顯示將要執行的操作，不實際執行"
    echo "  --help              顯示此幫助訊息"
    echo
    echo "範例:"
    echo "  $0 /backup/dw-ck/dw-ck-backup-20231201-120000.tar.gz"
    echo "  $0 --dry-run backup.tar.gz"
    echo "  $0 --no-database --force backup.tar.gz"
}

# 檢查恢復環境
check_restore_environment() {
    log_info "檢查恢復環境..."

    # 檢查必要工具
    local required_tools=("docker" "docker-compose" "tar" "sqlite3")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "必要工具未安裝: $tool"
            exit 1
        fi
    done

    # 檢查備份檔案
    if [[ ! -f "$BACKUP_FILE" ]]; then
        log_error "備份檔案不存在: $BACKUP_FILE"
        exit 1
    fi

    # 驗證備份檔案完整性
    if [[ -f "${BACKUP_FILE}.md5" ]]; then
        log_info "驗證備份檔案完整性..."
        if md5sum -c "${BACKUP_FILE}.md5" >/dev/null 2>&1; then
            log_success "備份檔案完整性驗證通過"
        else
            log_error "備份檔案完整性驗證失敗"
            exit 1
        fi
    else
        log_warning "未找到備份檔案檢查碼，跳過完整性驗證"
    fi

    # 檢查 tar 檔案
    if ! tar -tzf "$BACKUP_FILE" >/dev/null 2>&1; then
        log_error "備份檔案格式無效"
        exit 1
    fi

    log_success "恢復環境檢查通過"
}

# 停止服務
stop_services() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會停止 DW-CK 服務"
        return
    fi

    log_info "停止 DW-CK 服務..."

    # 停止主應用服務
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose down || true
    fi

    # 停止監控服務
    if [[ -f "monitoring/docker-compose.monitoring.yml" ]]; then
        docker-compose -f monitoring/docker-compose.monitoring.yml down || true
    fi

    log_success "服務已停止"
}

# 備份當前狀態
backup_current_state() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會備份當前狀態"
        return
    fi

    log_info "備份當前狀態..."

    local current_backup_dir="${RESTORE_DIR}/pre-restore-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$current_backup_dir"

    # 備份重要檔案和目錄
    local items_to_backup=(
        "data"
        "docker-compose.yml"
        ".env"
        "nginx/nginx.conf"
    )

    for item in "${items_to_backup[@]}"; do
        if [[ -e "$item" ]]; then
            cp -r "$item" "$current_backup_dir/" 2>/dev/null || true
            log_info "已備份當前狀態: $item"
        fi
    done

    log_success "當前狀態備份至: $current_backup_dir"
}

# 解壓備份檔案
extract_backup() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會解壓備份檔案"
        return
    fi

    log_info "解壓備份檔案..."

    TEMP_EXTRACT_DIR=$(mktemp -d)
    tar -xzf "$BACKUP_FILE" -C "$TEMP_EXTRACT_DIR"

    # 尋找備份內容目錄
    BACKUP_CONTENT_DIR=$(find "$TEMP_EXTRACT_DIR" -maxdepth 1 -type d -name "dw-ck-backup-*" | head -1)

    if [[ -z "$BACKUP_CONTENT_DIR" ]]; then
        log_error "無法找到備份內容目錄"
        exit 1
    fi

    log_success "備份檔案已解壓至: $BACKUP_CONTENT_DIR"
}

# 恢復資料庫
restore_database() {
    if [[ "$NO_DATABASE" == "true" ]]; then
        log_info "跳過資料庫恢復"
        return
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會恢復資料庫"
        return
    fi

    log_info "恢復資料庫..."

    local db_backup_dir="$BACKUP_CONTENT_DIR/database"

    if [[ ! -d "$db_backup_dir" ]]; then
        log_warning "備份中未找到資料庫目錄"
        return
    fi

    # 建立資料目錄
    mkdir -p data

    # 恢復 SQLite 資料庫
    if [[ -f "$db_backup_dir/exam_sessions.db" ]]; then
        cp "$db_backup_dir/exam_sessions.db" data/
        log_success "SQLite 資料庫已恢復"

        # 驗證資料庫完整性
        if sqlite3 data/exam_sessions.db "PRAGMA integrity_check;" | grep -q "ok"; then
            log_success "SQLite 資料庫完整性驗證通過"
        else
            log_error "SQLite 資料庫完整性驗證失敗"
        fi
    fi

    # 恢復 Redis 資料 (如果 Redis 正在運行)
    if [[ -f "$db_backup_dir/redis-dump.rdb" ]] && docker ps | grep -q "redis"; then
        log_info "恢復 Redis 資料..."

        # 停止 Redis 容器
        docker stop dw-ck-redis-1 2>/dev/null || true

        # 複製備份檔案到 Redis 容器卷
        docker run --rm -v dw-ck_redis-data:/data -v "$db_backup_dir":/backup alpine cp /backup/redis-dump.rdb /data/dump.rdb

        log_success "Redis 資料已恢復"
    fi
}

# 恢復配置檔案
restore_configuration() {
    if [[ "$NO_CONFIG" == "true" ]]; then
        log_info "跳過配置檔案恢復"
        return
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會恢復配置檔案"
        return
    fi

    log_info "恢復配置檔案..."

    local config_backup_dir="$BACKUP_CONTENT_DIR/configuration"

    if [[ ! -d "$config_backup_dir" ]]; then
        log_warning "備份中未找到配置目錄"
        return
    fi

    # 恢復主要配置檔案
    local config_files=(
        "docker-compose.yml"
        ".env"
        "nginx/nginx.conf"
    )

    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_backup_dir/$config_file" ]]; then
            mkdir -p "$(dirname "$config_file")"
            cp "$config_backup_dir/$config_file" "$config_file"
            log_info "已恢復配置檔案: $config_file"
        fi
    done

    # 恢復資料目錄配置
    if [[ -d "$config_backup_dir/vm_configs" ]]; then
        cp -r "$config_backup_dir/vm_configs" data/
        log_success "VM 配置已恢復"
    fi

    if [[ -d "$config_backup_dir/ssh_keys" ]]; then
        cp -r "$config_backup_dir/ssh_keys" data/
        chmod -R 600 data/ssh_keys/*
        log_success "SSH 金鑰已恢復"
    fi

    if [[ -d "$config_backup_dir/kubespray_configs" ]]; then
        cp -r "$config_backup_dir/kubespray_configs" data/
        log_success "Kubespray 配置已恢復"
    fi

    # 恢復監控配置
    if [[ -d "$config_backup_dir/monitoring" ]]; then
        cp -r "$config_backup_dir/monitoring" ./
        log_success "監控配置已恢復"
    fi
}

# 恢復題組資料
restore_question_sets() {
    if [[ "$NO_QUESTIONS" == "true" ]]; then
        log_info "跳過題組資料恢復"
        return
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會恢復題組資料"
        return
    fi

    log_info "恢復題組資料..."

    local questions_backup_dir="$BACKUP_CONTENT_DIR/question_sets"

    if [[ ! -d "$questions_backup_dir" ]]; then
        log_warning "備份中未找到題組目錄"
        return
    fi

    # 建立題組目錄
    mkdir -p data/question_sets/{cka,ckad,cks}

    # 恢復題組檔案
    if [[ -d "$questions_backup_dir" ]]; then
        cp -r "$questions_backup_dir"/* data/question_sets/ 2>/dev/null || true

        # 統計恢復的題組
        local restored_count=$(find data/question_sets -name "metadata.json" | wc -l)
        log_success "題組資料已恢復 ($restored_count 個題組)"

        # 顯示題組摘要
        if [[ -f "$questions_backup_dir/backup_summary.txt" ]]; then
            log_info "題組摘要:"
            cat "$questions_backup_dir/backup_summary.txt" | grep -E "(總題組數|CKA|CKAD|CKS)" || true
        fi
    fi
}

# 恢復考試結果
restore_exam_results() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會恢復考試結果"
        return
    fi

    log_info "恢復考試結果..."

    local results_backup_dir="$BACKUP_CONTENT_DIR/exam_results"

    if [[ -d "$results_backup_dir" ]]; then
        mkdir -p data/exam_results
        cp -r "$results_backup_dir"/* data/exam_results/ 2>/dev/null || true

        local restored_count=$(find data/exam_results -name "*.json" | wc -l)
        log_success "考試結果已恢復 ($restored_count 個結果檔案)"
    else
        log_info "備份中無考試結果資料"
    fi
}

# 恢復日誌檔案
restore_logs() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會恢復日誌檔案"
        return
    fi

    log_info "恢復日誌檔案..."

    local logs_backup_file="$BACKUP_CONTENT_DIR/logs.tar.gz"

    if [[ -f "$logs_backup_file" ]]; then
        mkdir -p /var/log
        tar -xzf "$logs_backup_file" -C /var/log/

        log_success "日誌檔案已恢復"
    else
        log_info "備份中無日誌檔案"
    fi
}

# 啟動服務
start_services() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會啟動服務"
        return
    fi

    log_info "啟動 DW-CK 服務..."

    # 啟動主應用服務
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose up -d
        log_success "主應用服務已啟動"
    fi

    # 等待服務啟動
    log_info "等待服務啟動..."
    sleep 30

    # 檢查服務狀態
    if curl -s http://localhost/api/v1/health > /dev/null; then
        log_success "API 服務正常運行"
    else
        log_warning "API 服務可能尚未就緒"
    fi

    # 啟動監控服務（可選）
    if [[ -f "monitoring/docker-compose.monitoring.yml" ]]; then
        log_info "啟動監控服務..."
        docker-compose -f monitoring/docker-compose.monitoring.yml up -d
        log_success "監控服務已啟動"
    fi
}

# 驗證恢復結果
verify_restore() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將會驗證恢復結果"
        return
    fi

    log_info "驗證恢復結果..."

    # 檢查重要檔案和目錄
    local check_items=(
        "data/question_sets:題組資料目錄"
        "data/vm_configs:VM配置目錄"
        "docker-compose.yml:Docker Compose配置"
    )

    local verification_passed=true

    for item in "${check_items[@]}"; do
        local path="${item%%:*}"
        local description="${item##*:}"

        if [[ -e "$path" ]]; then
            log_success "✓ $description 存在"
        else
            log_error "✗ $description 缺失: $path"
            verification_passed=false
        fi
    done

    # 檢查 API 連接性
    if curl -s http://localhost/api/v1/health > /dev/null; then
        log_success "✓ API 服務可連接"
    else
        log_warning "✗ API 服務連接失敗"
    fi

    # 檢查資料庫
    if [[ -f "data/exam_sessions.db" ]]; then
        if sqlite3 data/exam_sessions.db "SELECT COUNT(*) FROM sqlite_master;" > /dev/null 2>&1; then
            log_success "✓ SQLite 資料庫可存取"
        else
            log_error "✗ SQLite 資料庫存取失敗"
            verification_passed=false
        fi
    fi

    if [[ "$verification_passed" == "true" ]]; then
        log_success "恢復驗證通過"
    else
        log_error "恢復驗證失敗"
        exit 1
    fi
}

# 清理暫存檔案
cleanup() {
    if [[ -n "$TEMP_EXTRACT_DIR" ]] && [[ -d "$TEMP_EXTRACT_DIR" ]]; then
        rm -rf "$TEMP_EXTRACT_DIR"
        log_info "暫存檔案已清理"
    fi
}

# 顯示恢復摘要
show_restore_summary() {
    log_success "DW-CK 系統恢復完成！"
    echo
    echo "恢復摘要："
    echo "  備份檔案: $BACKUP_FILE"
    echo "  恢復目錄: $RESTORE_DIR"
    echo "  恢復時間: $(date)"
    echo
    echo "服務狀態："
    echo "  API 服務: http://localhost/api/v1/health"
    echo "  前端介面: http://localhost"
    echo
    log_info "請檢查應用程式功能是否正常運作"
}

# 主函數
main() {
    log_info "開始 DW-CK 系統恢復..."

    # 改變到恢復目錄
    cd "$RESTORE_DIR"

    # 設定清理處理器
    trap cleanup EXIT

    # 確認操作
    if [[ "$FORCE" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        echo
        log_warning "此操作將會覆蓋現有的系統資料和配置"
        read -p "確定要繼續嗎？ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消"
            exit 0
        fi
    fi

    # 執行恢復步驟
    check_restore_environment
    extract_backup
    stop_services
    backup_current_state
    restore_database
    restore_configuration
    restore_question_sets
    restore_exam_results
    restore_logs
    start_services
    verify_restore

    if [[ "$DRY_RUN" != "true" ]]; then
        show_restore_summary
    else
        log_info "模擬運行完成"
    fi

    log_success "DW-CK 系統恢復作業完成！"
}

# 預設值
FORCE=false
NO_DATABASE=false
NO_CONFIG=false
NO_QUESTIONS=false
DRY_RUN=false
RESTORE_DIR="$(pwd)"
BACKUP_FILE=""

# 解析命令列參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --no-database)
            NO_DATABASE=true
            shift
            ;;
        --no-config)
            NO_CONFIG=true
            shift
            ;;
        --no-questions)
            NO_QUESTIONS=true
            shift
            ;;
        --restore-dir)
            RESTORE_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        -*)
            log_error "未知選項: $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$BACKUP_FILE" ]]; then
                BACKUP_FILE="$1"
            else
                log_error "只能指定一個備份檔案"
                exit 1
            fi
            shift
            ;;
    esac
done

# 檢查必要參數
if [[ -z "$BACKUP_FILE" ]]; then
    log_error "必須指定備份檔案"
    show_help
    exit 1
fi

# 轉換為絕對路徑
BACKUP_FILE=$(realpath "$BACKUP_FILE")
RESTORE_DIR=$(realpath "$RESTORE_DIR")

# 執行主函數
main "$@"