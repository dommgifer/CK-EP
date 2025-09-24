#!/bin/bash
"""
監控系統設定腳本
自動配置和啟動 DW-CK 監控和日誌系統
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

# 檢查必要工具
check_requirements() {
    log_info "檢查監控系統需求..."

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

    # 檢查磁碟空間
    AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $AVAILABLE_SPACE -lt 5 ]]; then
        log_warning "可用磁碟空間少於 5GB，監控資料可能受限"
    fi

    log_success "需求檢查完成"
}

# 建立必要目錄
create_directories() {
    log_info "建立監控目錄結構..."

    # 建立日誌目錄
    mkdir -p /var/log/dw-ck/{backend,frontend,exam-sessions,vnc,kubespray}
    mkdir -p monitoring/grafana/dashboards/{json,system}

    # 設定權限
    chmod -R 755 /var/log/dw-ck
    chmod -R 755 monitoring/

    log_success "目錄結構建立完成"
}

# 配置 Grafana 儀表板
setup_grafana_dashboards() {
    log_info "設定 Grafana 儀表板..."

    # 建立 DW-CK 應用程式儀表板
    cat > monitoring/grafana/dashboards/json/dw-ck-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "DW-CK Overview",
    "tags": ["dw-ck"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "stat",
        "targets": [
          {
            "expr": "http_request_duration_seconds{job=\"dw-ck-backend\", quantile=\"0.95\"}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 2}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Active Exam Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "dw_ck_active_exam_sessions",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "HTTP Requests Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"dw-ck-backend\"}[5m])",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "5s"
  }
}
EOF

    # 建立系統資源儀表板
    cat > monitoring/grafana/dashboards/system/system-resources.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "System Resources",
    "tags": ["system"],
    "panels": [
      {
        "id": 1,
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "refId": "A"
          }
        ],
        "yAxes": [{"max": 100, "min": 0, "unit": "percent"}],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "refId": "A"
          }
        ],
        "yAxes": [{"max": 100, "min": 0, "unit": "percent"}],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      }
    ]
  }
}
EOF

    log_success "Grafana 儀表板配置完成"
}

# 啟動監控服務
start_monitoring_services() {
    log_info "啟動監控服務..."

    cd monitoring

    # 停止現有服務
    docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true

    # 啟動服務
    docker-compose -f docker-compose.monitoring.yml up -d

    # 等待服務啟動
    log_info "等待服務啟動..."
    sleep 30

    # 檢查服務狀態
    SERVICES=("prometheus" "grafana" "loki" "promtail" "alertmanager" "node-exporter" "cadvisor")

    for service in "${SERVICES[@]}"; do
        if docker ps --filter "name=dw-ck-${service}" --filter "status=running" | grep -q "${service}"; then
            log_success "${service} 正在運行"
        else
            log_error "${service} 啟動失敗"
        fi
    done

    cd ..
}

# 驗證監控系統
verify_monitoring_setup() {
    log_info "驗證監控系統..."

    # 檢查 Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus 健康檢查通過"
    else
        log_error "Prometheus 健康檢查失敗"
    fi

    # 檢查 Grafana
    if curl -s http://localhost:3001/api/health > /dev/null; then
        log_success "Grafana 健康檢查通過"
    else
        log_error "Grafana 健康檢查失敗"
    fi

    # 檢查 Loki
    if curl -s http://localhost:3100/ready > /dev/null; then
        log_success "Loki 健康檢查通過"
    else
        log_error "Loki 健康檢查失敗"
    fi

    # 檢查 AlertManager
    if curl -s http://localhost:9093/-/healthy > /dev/null; then
        log_success "AlertManager 健康檢查通過"
    else
        log_error "AlertManager 健康檢查失敗"
    fi
}

# 配置應用程式監控指標
configure_app_metrics() {
    log_info "配置應用程式監控指標..."

    # 檢查後端是否有 metrics 端點
    if curl -s http://localhost/api/v1/metrics > /dev/null; then
        log_success "後端 metrics 端點可用"
    else
        log_warning "後端 metrics 端點不可用，需要實施監控指標"
    fi

    # 建立應用程式監控配置
    cat > monitoring/app-metrics.yml << 'EOF'
# 應用程式自訂指標配置
app_metrics:
  # 考試會話指標
  exam_sessions:
    - name: active_sessions
      type: gauge
      description: "當前活動的考試會話數"

    - name: completed_sessions
      type: counter
      description: "已完成的考試會話總數"

    - name: session_duration
      type: histogram
      description: "考試會話持續時間"
      buckets: [300, 600, 1200, 1800, 3600, 7200]

  # API 效能指標
  api_metrics:
    - name: request_duration
      type: histogram
      description: "API 請求持續時間"
      buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    - name: request_count
      type: counter
      description: "API 請求總數"

    - name: error_count
      type: counter
      description: "API 錯誤總數"

  # 業務指標
  business_metrics:
    - name: vm_deployments
      type: counter
      description: "VM 部署次數"

    - name: question_sets_loaded
      type: gauge
      description: "已載入的題組數量"
EOF

    log_success "應用程式監控指標配置完成"
}

# 顯示存取資訊
show_access_info() {
    log_success "監控系統設定完成！"
    echo
    echo "存取資訊："
    echo "  Grafana:      http://localhost:3001 (admin/admin123)"
    echo "  Prometheus:   http://localhost:9090"
    echo "  AlertManager: http://localhost:9093"
    echo "  Loki:         http://localhost:3100"
    echo
    echo "系統指標："
    echo "  Node Exporter: http://localhost:9100"
    echo "  cAdvisor:      http://localhost:8080"
    echo
    log_info "建議在 Grafana 中匯入預設儀表板並設定適當的警報"
}

# 主函數
main() {
    log_info "開始設定 DW-CK 監控系統..."

    # 改變到專案根目錄
    cd "$(dirname "$0")/.."

    # 執行設定步驟
    check_requirements
    create_directories
    setup_grafana_dashboards
    configure_app_metrics
    start_monitoring_services

    # 等待服務完全啟動
    sleep 10

    verify_monitoring_setup
    show_access_info

    log_success "監控系統設定完成！"
}

# 如果直接執行此腳本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi