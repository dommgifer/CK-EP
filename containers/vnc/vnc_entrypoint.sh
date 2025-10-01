#!/bin/bash
# T090: VNC 容器入口點腳本
# 在啟動 VNC 之前執行自訂初始化

set -e

echo "=== Kubernetes 考試 VNC 環境啟動 ==="

# 執行自訂初始化腳本
if [ -f "/dockerstartup/custom_startup.sh" ]; then
    bash /dockerstartup/custom_startup.sh
fi

# 呼叫原始 VNC 啟動腳本
exec /dockerstartup/vnc_startup.sh "$@"