#!/bin/bash
"""
DW-CK 系統備份腳本
自動化備份資料庫、配置檔案、題組資料和其他重要檔案
"""

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 預設配置
BACKUP_DIR="${BACKUP_DIR:-/backup/dw-ck}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_NAME="dw-ck-backup-${TIMESTAMP}"

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

# 檢查備份環境
check_backup_environment() {
    log_info "檢查備份環境..."

    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi

    # 建立備份目錄
    mkdir -p "${BACKUP_DIR}"

    # 檢查磁碟空間
    AVAILABLE_SPACE=$(df -BG "${BACKUP_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $AVAILABLE_SPACE -lt 5 ]]; then
        log_error "備份目錄可用空間少於 5GB"
        exit 1
    fi

    # 檢查 Docker 容器狀態
    if ! docker ps --filter "name=dw-ck" | grep -q "Up"; then
        log_warning "DW-CK 容器未運行，某些備份可能不完整"
    fi

    log_success "備份環境檢查完成"
}

# 備份資料庫
backup_database() {
    log_info "備份資料庫..."

    local db_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/database"
    mkdir -p "${db_backup_dir}"

    # SQLite 資料庫備份
    if [[ -f "data/exam_sessions.db" ]]; then
        log_info "備份 SQLite 資料庫..."
        sqlite3 data/exam_sessions.db ".backup ${db_backup_dir}/exam_sessions.db"
        sqlite3 data/exam_sessions.db ".dump" > "${db_backup_dir}/exam_sessions.sql"
        log_success "SQLite 資料庫備份完成"
    else
        log_warning "SQLite 資料庫檔案不存在"
    fi

    # Redis 資料備份
    if docker ps --filter "name=dw-ck-redis" --filter "status=running" | grep -q "redis"; then
        log_info "備份 Redis 資料..."

        # 建立 Redis 備份
        docker exec dw-ck-redis-1 redis-cli BGSAVE

        # 等待備份完成
        while [[ $(docker exec dw-ck-redis-1 redis-cli LASTSAVE) == $(docker exec dw-ck-redis-1 redis-cli LASTSAVE) ]]; do
            sleep 1
        done

        # 複製備份檔案
        docker cp dw-ck-redis-1:/data/dump.rdb "${db_backup_dir}/redis-dump.rdb"

        # 匯出 Redis 資料為文字格式
        docker exec dw-ck-redis-1 redis-cli --rdb "${db_backup_dir}/redis-export.rdb"

        log_success "Redis 資料備份完成"
    else
        log_warning "Redis 容器未運行"
    fi

    # 計算資料庫備份檢查碼
    if [[ -d "${db_backup_dir}" ]]; then
        find "${db_backup_dir}" -type f -exec md5sum {} \; > "${db_backup_dir}/checksums.md5"
        log_success "資料庫備份檢查碼已生成"
    fi
}

# 備份配置檔案
backup_configuration() {
    log_info "備份配置檔案..."

    local config_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/configuration"
    mkdir -p "${config_backup_dir}"

    # 備份主要配置檔案
    local config_files=(
        "docker-compose.yml"
        ".env"
        "nginx/nginx.conf"
        "backend/requirements.txt"
        "frontend/package.json"
        "frontend/package-lock.json"
    )

    for config_file in "${config_files[@]}"; do
        if [[ -f "${config_file}" ]]; then
            cp "${config_file}" "${config_backup_dir}/"
            log_info "已備份: ${config_file}"
        else
            log_warning "配置檔案不存在: ${config_file}"
        fi
    done

    # 備份 VM 配置目錄
    if [[ -d "data/vm_configs" ]]; then
        cp -r data/vm_configs "${config_backup_dir}/"
        log_success "VM 配置備份完成"
    fi

    # 備份 SSH 金鑰（如果存在）
    if [[ -d "data/ssh_keys" ]]; then
        cp -r data/ssh_keys "${config_backup_dir}/"
        chmod -R 600 "${config_backup_dir}/ssh_keys"
        log_success "SSH 金鑰備份完成"
    fi

    # 備份 Kubespray 配置
    if [[ -d "data/kubespray_configs" ]]; then
        cp -r data/kubespray_configs "${config_backup_dir}/"
        log_success "Kubespray 配置備份完成"
    fi

    # 備份監控配置
    if [[ -d "monitoring" ]]; then
        cp -r monitoring "${config_backup_dir}/"
        log_success "監控配置備份完成"
    fi

    log_success "配置檔案備份完成"
}

# 備份題組資料
backup_question_sets() {
    log_info "備份題組資料..."

    local questions_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/question_sets"
    mkdir -p "${questions_backup_dir}"

    if [[ -d "data/question_sets" ]]; then
        # 備份所有題組
        cp -r data/question_sets/* "${questions_backup_dir}/" 2>/dev/null || true

        # 建立題組清單
        find data/question_sets -name "metadata.json" | while read -r metadata_file; do
            local exam_type=$(dirname "${metadata_file}" | awk -F'/' '{print $(NF-1)}')
            local set_id=$(basename "$(dirname "${metadata_file}")")
            local title=$(jq -r '.title' "${metadata_file}")
            echo "${exam_type}/${set_id}: ${title}" >> "${questions_backup_dir}/question_sets_list.txt"
        done

        # 統計題組資訊
        local total_sets=$(find data/question_sets -name "metadata.json" | wc -l)
        local cka_sets=$(find data/question_sets/cka -name "metadata.json" 2>/dev/null | wc -l)
        local ckad_sets=$(find data/question_sets/ckad -name "metadata.json" 2>/dev/null | wc -l)
        local cks_sets=$(find data/question_sets/cks -name "metadata.json" 2>/dev/null | wc -l)

        cat > "${questions_backup_dir}/backup_summary.txt" << EOF
題組備份摘要
備份時間: ${TIMESTAMP}
總題組數: ${total_sets}
CKA 題組: ${cka_sets}
CKAD 題組: ${ckad_sets}
CKS 題組: ${cks_sets}
EOF

        log_success "題組資料備份完成 (${total_sets} 個題組)"
    else
        log_warning "題組資料目錄不存在"
    fi
}

# 備份考試結果
backup_exam_results() {
    log_info "備份考試結果..."

    local results_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/exam_results"
    mkdir -p "${results_backup_dir}"

    if [[ -d "data/exam_results" ]]; then
        cp -r data/exam_results/* "${results_backup_dir}/" 2>/dev/null || true

        # 統計考試結果
        local result_count=$(find data/exam_results -name "*.json" 2>/dev/null | wc -l)
        log_success "考試結果備份完成 (${result_count} 個結果檔案)"
    else
        log_warning "考試結果目錄不存在"
    fi
}

# 備份日誌檔案
backup_logs() {
    log_info "備份日誌檔案..."

    local logs_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}/logs"
    mkdir -p "${logs_backup_dir}"

    # 備份應用程式日誌
    if [[ -d "/var/log/dw-ck" ]]; then
        cp -r /var/log/dw-ck "${logs_backup_dir}/"
        log_success "應用程式日誌備份完成"
    fi

    # 備份 Docker 容器日誌
    log_info "備份容器日誌..."
    local containers=("dw-ck-backend-1" "dw-ck-frontend-1" "dw-ck-nginx-1" "dw-ck-redis-1")

    for container in "${containers[@]}"; do
        if docker ps --filter "name=${container}" | grep -q "${container}"; then
            docker logs "${container}" > "${logs_backup_dir}/${container}.log" 2>&1
            log_info "已備份容器日誌: ${container}"
        fi
    done

    # 壓縮日誌檔案以節省空間
    if [[ -d "${logs_backup_dir}" ]]; then
        tar -czf "${logs_backup_dir}.tar.gz" -C "${logs_backup_dir}" . && rm -rf "${logs_backup_dir}"
        log_success "日誌檔案已壓縮備份"
    fi
}

# 建立系統狀態快照
create_system_snapshot() {
    log_info "建立系統狀態快照..."

    local snapshot_dir="${BACKUP_DIR}/${BACKUP_NAME}/system_snapshot"
    mkdir -p "${snapshot_dir}"

    # Docker 容器狀態
    docker ps -a > "${snapshot_dir}/docker_containers.txt"
    docker images > "${snapshot_dir}/docker_images.txt"
    docker network ls > "${snapshot_dir}/docker_networks.txt"
    docker volume ls > "${snapshot_dir}/docker_volumes.txt"

    # 系統資源使用情況
    df -h > "${snapshot_dir}/disk_usage.txt"
    free -h > "${snapshot_dir}/memory_usage.txt"
    ps aux > "${snapshot_dir}/processes.txt"
    netstat -tuln > "${snapshot_dir}/network_ports.txt" 2>/dev/null || ss -tuln > "${snapshot_dir}/network_ports.txt"

    # 應用程式版本資訊
    echo "Backup created at: $(date)" > "${snapshot_dir}/backup_info.txt"
    echo "System: $(uname -a)" >> "${snapshot_dir}/backup_info.txt"
    echo "Docker version: $(docker --version)" >> "${snapshot_dir}/backup_info.txt"
    echo "Docker Compose version: $(docker-compose --version)" >> "${snapshot_dir}/backup_info.txt"

    # Git 版本資訊（如果是 Git 倉庫）
    if [[ -d ".git" ]]; then
        git log --oneline -5 > "${snapshot_dir}/git_commits.txt" 2>/dev/null || true
        git status > "${snapshot_dir}/git_status.txt" 2>/dev/null || true
    fi

    log_success "系統狀態快照建立完成"
}

# 壓縮備份檔案
compress_backup() {
    log_info "壓縮備份檔案..."

    local backup_path="${BACKUP_DIR}/${BACKUP_NAME}"

    if [[ -d "${backup_path}" ]]; then
        tar -czf "${backup_path}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}"

        # 驗證壓縮檔案
        if tar -tzf "${backup_path}.tar.gz" >/dev/null 2>&1; then
            rm -rf "${backup_path}"
            log_success "備份檔案壓縮完成: ${backup_path}.tar.gz"

            # 顯示備份檔案大小
            local backup_size=$(du -h "${backup_path}.tar.gz" | cut -f1)
            log_info "備份檔案大小: ${backup_size}"
        else
            log_error "備份檔案壓縮驗證失敗"
            exit 1
        fi
    fi
}

# 清理舊備份
cleanup_old_backups() {
    log_info "清理 ${RETENTION_DAYS} 天前的舊備份..."

    find "${BACKUP_DIR}" -name "dw-ck-backup-*.tar.gz" -mtime +${RETENTION_DAYS} -delete

    local remaining_backups=$(find "${BACKUP_DIR}" -name "dw-ck-backup-*.tar.gz" | wc -l)
    log_success "清理完成，剩餘 ${remaining_backups} 個備份檔案"
}

# 發送備份通知
send_backup_notification() {
    log_info "發送備份通知..."

    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    local backup_size=$(du -h "${backup_file}" | cut -f1)
    local notification_file="${BACKUP_DIR}/last_backup.json"

    # 建立備份資訊
    cat > "${notification_file}" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "backup_file": "${backup_file}",
    "backup_size": "${backup_size}",
    "status": "completed",
    "retention_days": ${RETENTION_DAYS}
}
EOF

    # 如果配置了 webhook，發送通知
    if [[ -n "${BACKUP_WEBHOOK_URL}" ]]; then
        curl -X POST "${BACKUP_WEBHOOK_URL}" \
             -H "Content-Type: application/json" \
             -d @"${notification_file}" 2>/dev/null || log_warning "無法發送 webhook 通知"
    fi

    log_success "備份通知已建立"
}

# 驗證備份完整性
verify_backup_integrity() {
    log_info "驗證備份完整性..."

    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

    # 驗證 tar 檔案
    if tar -tzf "${backup_file}" >/dev/null 2>&1; then
        log_success "備份檔案結構驗證通過"
    else
        log_error "備份檔案結構驗證失敗"
        return 1
    fi

    # 建立檢查碼
    md5sum "${backup_file}" > "${backup_file}.md5"
    log_success "備份檔案檢查碼已建立"

    # 建立備份清單
    tar -tzf "${backup_file}" > "${BACKUP_DIR}/${BACKUP_NAME}-contents.txt"
    log_success "備份內容清單已建立"
}

# 顯示備份摘要
show_backup_summary() {
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    local backup_size=$(du -h "${backup_file}" | cut -f1)

    log_success "備份作業完成！"
    echo
    echo "備份摘要："
    echo "  備份檔案: ${backup_file}"
    echo "  檔案大小: ${backup_size}"
    echo "  備份時間: ${TIMESTAMP}"
    echo "  保留期限: ${RETENTION_DAYS} 天"
    echo
    log_info "使用 ./scripts/restore.sh 來恢復備份"
}

# 主函數
main() {
    log_info "開始 DW-CK 系統備份..."

    # 改變到專案根目錄
    cd "$(dirname "$0")/.."

    # 執行備份步驟
    check_backup_environment
    backup_database
    backup_configuration
    backup_question_sets
    backup_exam_results
    backup_logs
    create_system_snapshot
    compress_backup
    verify_backup_integrity
    cleanup_old_backups
    send_backup_notification
    show_backup_summary

    log_success "DW-CK 系統備份完成！"
}

# 處理命令列參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --help)
            echo "DW-CK 備份腳本"
            echo
            echo "使用方式: $0 [選項]"
            echo
            echo "選項:"
            echo "  --backup-dir DIR      指定備份目錄 (預設: /backup/dw-ck)"
            echo "  --retention-days N    指定備份保留天數 (預設: 30)"
            echo "  --help               顯示此幫助訊息"
            echo
            echo "環境變數:"
            echo "  BACKUP_DIR           備份目錄"
            echo "  RETENTION_DAYS       備份保留天數"
            echo "  BACKUP_WEBHOOK_URL   備份通知 webhook URL"
            exit 0
            ;;
        *)
            log_error "未知參數: $1"
            exit 1
            ;;
    esac
done

# 如果直接執行此腳本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi