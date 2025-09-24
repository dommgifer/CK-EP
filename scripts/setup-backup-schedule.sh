#!/bin/bash
"""
設定自動備份排程腳本
配置 cron job 來定期執行 DW-CK 系統備份
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

# 預設配置
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"  # 每天凌晨 2 點
BACKUP_DIR="${BACKUP_DIR:-/backup/dw-ck}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
LOG_DIR="${LOG_DIR:-/var/log/dw-ck}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 顯示幫助訊息
show_help() {
    echo "DW-CK 自動備份排程設定腳本"
    echo
    echo "使用方式: $0 [選項]"
    echo
    echo "選項:"
    echo "  --schedule CRON      cron 排程表達式 (預設: '0 2 * * *' 每天凌晨2點)"
    echo "  --backup-dir DIR     備份目錄 (預設: /backup/dw-ck)"
    echo "  --retention-days N   備份保留天數 (預設: 30)"
    echo "  --log-dir DIR        日誌目錄 (預設: /var/log/dw-ck)"
    echo "  --remove            移除現有的備份排程"
    echo "  --status            顯示當前備份排程狀態"
    echo "  --test              執行備份測試"
    echo "  --help              顯示此幫助訊息"
    echo
    echo "範例:"
    echo "  $0                                  # 設定預設排程"
    echo "  $0 --schedule '0 3 * * 0'          # 每週日凌晨3點備份"
    echo "  $0 --retention-days 7              # 保留7天備份"
    echo "  $0 --remove                        # 移除備份排程"
    echo
    echo "常用 cron 排程:"
    echo "  0 2 * * *     每天凌晨2點"
    echo "  0 3 * * 0     每週日凌晨3點"
    echo "  0 4 1 * *     每月1號凌晨4點"
    echo "  */30 * * * *  每30分鐘"
}

# 檢查系統需求
check_requirements() {
    log_info "檢查系統需求..."

    # 檢查 cron 服務
    if ! command -v crontab &> /dev/null; then
        log_error "crontab 命令不可用"
        exit 1
    fi

    # 檢查 cron 服務狀態
    if ! systemctl is-active --quiet cron 2>/dev/null && ! systemctl is-active --quiet crond 2>/dev/null; then
        log_warning "cron 服務可能未運行，嘗試啟動..."
        if systemctl start cron 2>/dev/null || systemctl start crond 2>/dev/null; then
            log_success "cron 服務已啟動"
        else
            log_error "無法啟動 cron 服務"
            exit 1
        fi
    fi

    # 檢查備份腳本
    if [[ ! -f "$PROJECT_DIR/scripts/backup.sh" ]]; then
        log_error "備份腳本不存在: $PROJECT_DIR/scripts/backup.sh"
        exit 1
    fi

    # 檢查備份目錄權限
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_info "建立備份目錄: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi

    if [[ ! -w "$BACKUP_DIR" ]]; then
        log_error "備份目錄無寫入權限: $BACKUP_DIR"
        exit 1
    fi

    log_success "系統需求檢查通過"
}

# 建立日誌目錄
setup_logging() {
    log_info "設定日誌..."

    mkdir -p "$LOG_DIR"

    # 建立日誌輪替配置
    cat > /etc/logrotate.d/dw-ck-backup << EOF
$LOG_DIR/backup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
EOF

    log_success "日誌配置完成"
}

# 建立備份包裝腳本
create_backup_wrapper() {
    log_info "建立備份包裝腳本..."

    local wrapper_script="/usr/local/bin/dw-ck-backup"

    cat > "$wrapper_script" << EOF
#!/bin/bash
# DW-CK 自動備份包裝腳本
# 由 setup-backup-schedule.sh 自動生成

# 設定環境變數
export PATH="/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin"
export BACKUP_DIR="$BACKUP_DIR"
export RETENTION_DAYS="$RETENTION_DAYS"
export LOG_DIR="$LOG_DIR"

# 日誌函數
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') [\$1] \$2" >> "$LOG_DIR/backup.log"
}

log_message "INFO" "開始自動備份..."

# 改變到專案目錄
cd "$PROJECT_DIR"

# 執行備份
if "$PROJECT_DIR/scripts/backup.sh" --backup-dir "$BACKUP_DIR" --retention-days "$RETENTION_DAYS" >> "$LOG_DIR/backup.log" 2>&1; then
    log_message "SUCCESS" "備份完成"

    # 發送成功通知（如果配置了的話）
    if [[ -n "\$BACKUP_SUCCESS_WEBHOOK" ]]; then
        curl -X POST "\$BACKUP_SUCCESS_WEBHOOK" \\
             -H "Content-Type: application/json" \\
             -d '{"status":"success","message":"DW-CK backup completed successfully","timestamp":"'"\$(date -Iseconds)"'"}' \\
             >> "$LOG_DIR/backup.log" 2>&1 || true
    fi
else
    log_message "ERROR" "備份失敗"

    # 發送失敗通知（如果配置了的話）
    if [[ -n "\$BACKUP_ERROR_WEBHOOK" ]]; then
        curl -X POST "\$BACKUP_ERROR_WEBHOOK" \\
             -H "Content-Type: application/json" \\
             -d '{"status":"error","message":"DW-CK backup failed","timestamp":"'"\$(date -Iseconds)"'"}' \\
             >> "$LOG_DIR/backup.log" 2>&1 || true
    fi

    exit 1
fi
EOF

    chmod +x "$wrapper_script"
    log_success "備份包裝腳本已建立: $wrapper_script"
}

# 設定 cron job
setup_cron_job() {
    log_info "設定 cron 排程..."

    # 移除現有的 DW-CK 備份 cron job
    crontab -l 2>/dev/null | grep -v "dw-ck-backup" | crontab -

    # 添加新的 cron job
    (crontab -l 2>/dev/null; echo "$BACKUP_SCHEDULE /usr/local/bin/dw-ck-backup") | crontab -

    log_success "cron 排程已設定: $BACKUP_SCHEDULE"
}

# 移除 cron job
remove_cron_job() {
    log_info "移除備份排程..."

    # 從 crontab 中移除 DW-CK 備份任務
    crontab -l 2>/dev/null | grep -v "dw-ck-backup" | crontab -

    # 移除包裝腳本
    rm -f /usr/local/bin/dw-ck-backup

    # 移除日誌輪替配置
    rm -f /etc/logrotate.d/dw-ck-backup

    log_success "備份排程已移除"
}

# 顯示排程狀態
show_status() {
    log_info "備份排程狀態:"

    # 檢查 cron job
    local cron_jobs=$(crontab -l 2>/dev/null | grep "dw-ck-backup" || true)
    if [[ -n "$cron_jobs" ]]; then
        log_success "發現備份排程:"
        echo "$cron_jobs"
    else
        log_info "未發現備份排程"
    fi

    # 檢查包裝腳本
    if [[ -f "/usr/local/bin/dw-ck-backup" ]]; then
        log_success "備份包裝腳本存在"
    else
        log_info "備份包裝腳本不存在"
    fi

    # 檢查最近的備份
    if [[ -d "$BACKUP_DIR" ]]; then
        local latest_backup=$(find "$BACKUP_DIR" -name "dw-ck-backup-*.tar.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
        if [[ -n "$latest_backup" ]]; then
            local backup_time=$(stat -c %y "$latest_backup" 2>/dev/null)
            log_success "最新備份: $latest_backup ($backup_time)"
        else
            log_info "未找到備份檔案"
        fi
    fi

    # 檢查日誌
    if [[ -f "$LOG_DIR/backup.log" ]]; then
        log_info "最近的備份日誌:"
        tail -5 "$LOG_DIR/backup.log" | while read -r line; do
            echo "  $line"
        done
    else
        log_info "未找到備份日誌"
    fi
}

# 測試備份
test_backup() {
    log_info "執行備份測試..."

    # 建立測試備份目錄
    local test_backup_dir="/tmp/dw-ck-backup-test"
    mkdir -p "$test_backup_dir"

    # 執行備份
    if "$PROJECT_DIR/scripts/backup.sh" --backup-dir "$test_backup_dir" --retention-days 1; then
        log_success "備份測試成功"

        # 列出測試備份檔案
        local test_files=$(find "$test_backup_dir" -name "*.tar.gz" -type f)
        if [[ -n "$test_files" ]]; then
            log_info "測試備份檔案:"
            echo "$test_files" | while read -r file; do
                local size=$(du -h "$file" | cut -f1)
                echo "  $file ($size)"
            done
        fi

        # 清理測試檔案
        read -p "刪除測試備份檔案? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$test_backup_dir"
            log_info "測試檔案已刪除"
        fi
    else
        log_error "備份測試失敗"
        exit 1
    fi
}

# 建立系統監控檢查
create_monitoring_check() {
    log_info "建立備份監控檢查..."

    local monitor_script="/usr/local/bin/dw-ck-backup-monitor"

    cat > "$monitor_script" << 'EOF'
#!/bin/bash
# DW-CK 備份監控腳本

BACKUP_DIR="/backup/dw-ck"
LOG_DIR="/var/log/dw-ck"
MAX_AGE_HOURS=26  # 備份檔案最大年齡（小時）

# 檢查最新備份
latest_backup=$(find "$BACKUP_DIR" -name "dw-ck-backup-*.tar.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

if [[ -z "$latest_backup" ]]; then
    echo "ERROR: 未找到備份檔案"
    exit 1
fi

# 檢查備份年齡
backup_age=$((($(date +%s) - $(stat -c %Y "$latest_backup")) / 3600))

if [[ $backup_age -gt $MAX_AGE_HOURS ]]; then
    echo "WARNING: 備份檔案過舊 ($backup_age 小時)"
    exit 1
fi

# 檢查備份檔案大小
backup_size=$(stat -c %s "$latest_backup")
min_size=$((1024 * 1024))  # 1MB

if [[ $backup_size -lt $min_size ]]; then
    echo "WARNING: 備份檔案過小"
    exit 1
fi

# 檢查日誌錯誤
if [[ -f "$LOG_DIR/backup.log" ]]; then
    recent_errors=$(tail -100 "$LOG_DIR/backup.log" | grep -c "ERROR" || true)
    if [[ $recent_errors -gt 0 ]]; then
        echo "WARNING: 發現 $recent_errors 個備份錯誤"
        exit 1
    fi
fi

echo "OK: 備份系統正常"
exit 0
EOF

    chmod +x "$monitor_script"
    log_success "備份監控腳本已建立: $monitor_script"
}

# 主函數
main() {
    log_info "設定 DW-CK 自動備份排程..."

    # 檢查是否為 root 用戶
    if [[ $EUID -ne 0 ]]; then
        log_error "此腳本需要 root 權限執行"
        exit 1
    fi

    case "$ACTION" in
        "setup")
            check_requirements
            setup_logging
            create_backup_wrapper
            setup_cron_job
            create_monitoring_check
            log_success "自動備份排程設定完成！"
            echo
            log_info "排程: $BACKUP_SCHEDULE"
            log_info "備份目錄: $BACKUP_DIR"
            log_info "保留天數: $RETENTION_DAYS"
            log_info "日誌目錄: $LOG_DIR"
            ;;
        "remove")
            remove_cron_job
            ;;
        "status")
            show_status
            ;;
        "test")
            test_backup
            ;;
        *)
            log_error "未知操作: $ACTION"
            exit 1
            ;;
    esac
}

# 預設動作
ACTION="setup"

# 解析命令列參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --schedule)
            BACKUP_SCHEDULE="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --remove)
            ACTION="remove"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        --test)
            ACTION="test"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知參數: $1"
            show_help
            exit 1
            ;;
    esac
done

# 執行主函數
main "$@"