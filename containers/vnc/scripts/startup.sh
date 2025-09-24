#!/bin/bash
# VNC 容器啟動腳本

echo "啟動 VNC 桌面環境..."

# 設定 SSH 金鑰權限
if [ -f "/headless/.ssh/id_rsa" ]; then
    chmod 600 /headless/.ssh/id_rsa
    echo "SSH 金鑰權限已設定"
fi

# 建立 SSH 配置
cat > /headless/.ssh/config << EOF
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
chmod 600 /headless/.ssh/config

# 在桌面建立快速連結
mkdir -p /headless/Desktop
cat > /headless/Desktop/Terminal.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Terminal
Comment=打開終端機
Exec=xfce4-terminal
Icon=utilities-terminal
Terminal=false
Categories=System;TerminalEmulator;
EOF
chmod +x /headless/Desktop/Terminal.desktop

cat > /headless/Desktop/Firefox.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Firefox
Comment=Web 瀏覽器
Exec=firefox
Icon=firefox
Terminal=false
Categories=Network;WebBrowser;
EOF
chmod +x /headless/Desktop/Firefox.desktop

echo "VNC 環境設定完成"

# 啟動原始 VNC 服務
exec /dockerstartup/vnc_startup.sh