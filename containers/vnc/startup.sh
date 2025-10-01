#!/bin/bash

# T090: VNC Container 啟動腳本
# 自訂 VNC 桌面環境的啟動邏輯

# 不使用 set -e 避免初始化腳本中的非致命錯誤導致退出

echo "=== Kubernetes 考試 VNC 環境啟動 ==="

# 檢查環境變數
: ${VNC_PW:=examvnc}
: ${VNC_RESOLUTION:=1280x1024}
: ${DISPLAY:=:1}

echo "VNC 設定："
echo "  解析度: $VNC_RESOLUTION"
echo "  密碼: [已設定]"
echo "  顯示: $DISPLAY"

# 設定 SSH 金鑰權限（如果存在）
if [ -f "$HOME/.ssh/id_rsa" ]; then
    chmod 600 "$HOME/.ssh/id_rsa"
    echo "SSH 私鑰權限已設定"
fi

# 建立 kubeconfig 目錄
mkdir -p "$HOME/.kube"

# 設定桌面環境
if [ -f "/dockerstartup/desktop_setup.sh" ]; then
    echo "執行桌面環境設定..."
    bash /dockerstartup/desktop_setup.sh
fi

# 建立工作目錄
mkdir -p "$HOME/workspace"
echo "工作目錄已建立"

# 等待 Bastion 容器準備就緒（如果存在）
if [ -n "$BASTION_HOST" ]; then
    echo "等待 Bastion 容器準備就緒..."
    for i in {1..30}; do
        if nc -z "$BASTION_HOST" 22 2>/dev/null; then
            echo "Bastion 容器連線就緒"
            break
        fi
        echo "等待 Bastion 容器... ($i/30)"
        sleep 2
    done
fi

# 環境準備完成
echo "=== VNC 環境準備完成 ==="

# 不需要呼叫其他腳本，這只是初始化腳本
echo "=== 初始化完成，VNC 服務即將啟動 ==="