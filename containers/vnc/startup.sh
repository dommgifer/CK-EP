#!/bin/bash

# T090: VNC Container 啟動腳本
# 自訂 VNC 桌面環境的啟動邏輯

set -e

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

# 建立考試專用目錄
mkdir -p "$HOME/workspace/manifests"
mkdir -p "$HOME/workspace/scripts"
mkdir -p "$HOME/workspace/logs"

# 建立常用 Kubernetes 範本目錄
mkdir -p "$HOME/.vim/templates"

# 建立 Pod 範本
cat > "$HOME/.vim/templates/pod.yaml" << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name:
  namespace: default
  labels:
    app:
spec:
  containers:
  - name:
    image:
    ports:
    - containerPort: 80
  restartPolicy: Never
EOF

# 建立 Deployment 範本
cat > "$HOME/.vim/templates/deployment.yaml" << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name:
  namespace: default
  labels:
    app:
spec:
  replicas: 1
  selector:
    matchLabels:
      app:
  template:
    metadata:
      labels:
        app:
    spec:
      containers:
      - name:
        image:
        ports:
        - containerPort: 80
EOF

# 建立 Service 範本
cat > "$HOME/.vim/templates/service.yaml" << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name:
  namespace: default
spec:
  selector:
    app:
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
EOF

# 建立 ConfigMap 範本
cat > "$HOME/.vim/templates/configmap.yaml" << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name:
  namespace: default
data:
  key1: value1
  key2: value2
EOF

echo "考試範本已建立完成"

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

# 顯示考試環境資訊
echo ""
echo "=== 考試環境準備完成 ==="
echo "工作目錄: $HOME/workspace"
echo "範本目錄: $HOME/.vim/templates"
echo "SSH 配置: $HOME/.ssh/config"
echo ""
echo "常用指令："
echo "  k          - kubectl 別名"
echo "  check      - 檢查叢集狀態"
echo "  timer 3600 - 啟動計時器（3600秒）"
echo ""
echo "Vim 範本快捷鍵："
echo "  <leader>kp - Pod 範本"
echo "  <leader>kd - Deployment 範本"
echo "  <leader>ks - Service 範本"
echo "  <leader>kc - ConfigMap 範本"
echo ""

# 呼叫原始啟動腳本
exec "$@"