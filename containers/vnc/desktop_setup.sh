#!/bin/bash

# T090: VNC 桌面環境設定腳本
# 客製化桌面環境以適合 Kubernetes 考試

set -e

echo "=== 設定 Kubernetes 考試桌面環境 ==="

# 設定 Xfce4 桌面環境
XFCE_CONFIG_DIR="$HOME/.config/xfce4"
mkdir -p "$XFCE_CONFIG_DIR/desktop"
mkdir -p "$XFCE_CONFIG_DIR/panel"

# 設定桌面背景為深色
cat > "$XFCE_CONFIG_DIR/desktop/backdrop.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="2"/>
    <property name="file-icons" type="empty">
      <property name="show-home" type="bool" value="true"/>
      <property name="show-filesystem" type="bool" value="false"/>
      <property name="show-removable" type="bool" value="false"/>
      <property name="show-trash" type="bool" value="true"/>
    </property>
  </property>
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="color-style" type="int" value="0"/>
        <property name="color1" type="array">
          <value type="uint" value="5140"/>
          <value type="uint" value="5140"/>
          <value type="uint" value="5140"/>
          <value type="uint" value="65535"/>
        </property>
      </property>
    </property>
  </property>
</channel>
EOF

# 設定面板（工具列）
cat > "$XFCE_CONFIG_DIR/panel/panels.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="panels" type="uint" value="1">
    <property name="panel-0" type="empty">
      <property name="position" type="string" value="p=6;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/>
        <value type="int" value="2"/>
        <value type="int" value="3"/>
        <value type="int" value="4"/>
        <value type="int" value="5"/>
        <value type="int" value="6"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="applicationsmenu"/>
    <property name="plugin-2" type="string" value="places"/>
    <property name="plugin-3" type="string" value="directorymenu">
      <property name="base-directory" type="string" value="/headless/workspace"/>
    </property>
    <property name="plugin-4" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="exo-terminal-emulator.desktop"/>
      </property>
    </property>
    <property name="plugin-5" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="firefox-esr.desktop"/>
      </property>
    </property>
    <property name="plugin-6" type="string" value="clock"/>
  </property>
</channel>
EOF

# 設定終端機預設值
mkdir -p "$HOME/.config/xfce4/terminal"
cat > "$HOME/.config/xfce4/terminal/terminalrc" << 'EOF'
[Configuration]
MiscAlwaysShowTabs=FALSE
MiscBell=FALSE
MiscBellUrgent=FALSE
MiscBordersDefault=TRUE
MiscCursorBlinks=FALSE
MiscCursorShape=TERMINAL_CURSOR_SHAPE_BLOCK
MiscDefaultGeometry=100x30
MiscInheritGeometry=FALSE
MiscMenubarDefault=FALSE
MiscMouseAutohide=FALSE
MiscMouseWheelZoom=TRUE
MiscToolbarDefault=FALSE
MiscConfirmClose=TRUE
MiscCycleTabs=TRUE
MiscTabCloseButtons=TRUE
MiscTabCloseMiddleClick=TRUE
MiscTabPosition=GTK_POS_TOP
MiscHighlightUrls=TRUE
MiscMiddleClickOpensUri=FALSE
MiscCopyOnSelect=FALSE
MiscShowRelaunchDialog=TRUE
MiscRewrapOnResize=TRUE
MiscUseShiftArrowsToScroll=FALSE
MiscSlimTabs=FALSE
MiscNewTabAdjacent=FALSE
ScrollingBar=TERMINAL_SCROLLBAR_RIGHT
ScrollingLines=10000
ColorForeground=#ffffff
ColorBackground=#1e1e1e
ColorCursor=#ffffff
FontName=Monospace 11
EOF

# 建立桌面捷徑
DESKTOP_DIR="$HOME/Desktop"
mkdir -p "$DESKTOP_DIR"

# 終端機捷徑
cat > "$DESKTOP_DIR/Terminal.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Terminal
Comment=Kubernetes 考試終端機
Exec=xfce4-terminal --working-directory=/headless/workspace
Icon=utilities-terminal
Terminal=false
Categories=System;TerminalEmulator;
EOF

# 工作區捷徑
cat > "$DESKTOP_DIR/Workspace.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Workspace
Comment=考試工作目錄
Exec=thunar /headless/workspace
Icon=folder
Terminal=false
Categories=System;FileManager;
EOF

# Firefox 捷徑（用於查看 Kubernetes 文件）
cat > "$DESKTOP_DIR/Firefox.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Firefox
Comment=Web 瀏覽器（查看文件）
Exec=firefox-esr https://kubernetes.io/docs/
Icon=firefox-esr
Terminal=false
Categories=Network;WebBrowser;
EOF

# kubectl 檢查腳本捷徑
cat > "$DESKTOP_DIR/Check-Cluster.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Check Cluster
Comment=檢查 Kubernetes 叢集狀態
Exec=xfce4-terminal --working-directory=/headless/workspace --command="bash -c 'check; read -p \"按任意鍵繼續...\"'"
Icon=system-search
Terminal=false
Categories=Development;
EOF

# 設定捷徑權限
chmod +x "$DESKTOP_DIR"/*.desktop

# 設定 vim 為預設編輯器
echo 'export EDITOR=vim' >> "$HOME/.profile"
echo 'export VISUAL=vim' >> "$HOME/.profile"

# 設定檔案管理器預設目錄
mkdir -p "$HOME/.config/gtk-3.0"
echo "file:///headless/workspace Workspace" >> "$HOME/.config/gtk-3.0/bookmarks"

echo "桌面環境設定完成"