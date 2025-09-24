#!/bin/bash

# T091: Bastion Container 啟動腳本
# 初始化 SSH 服務和考試環境

set -e

echo "=== Kubernetes 考試 Bastion 容器啟動 ==="

# 設定時區
export TZ=${TZ:-UTC}
echo "設定時區為: $TZ"

# 檢查並建立必要目錄
mkdir -p /var/run/sshd
mkdir -p /workspace/manifests
mkdir -p /workspace/scripts
mkdir -p /workspace/logs
mkdir -p /kubeconfig

# 設定權限
chmod 755 /var/run/sshd
chown -R exam:exam /workspace
chown -R exam:exam /kubeconfig

# 建立 SSH banner
cat > /etc/ssh/banner << 'EOF'
===============================================
    Kubernetes 考試模擬環境 - Bastion 容器
===============================================
歡迎進入 Kubernetes 考試環境！

可用工具：
- kubectl (k)    - Kubernetes 命令列工具
- helm           - Helm 包管理器
- etcdctl        - etcd 命令列工具
- crictl         - 容器運行時介面工具
- k9s            - Kubernetes 互動式介面
- jq, yq         - JSON/YAML 處理工具

考試提示：
1. 使用 'k' 作為 kubectl 的簡寫
2. kubeconfig 已自動載入
3. 所有 YAML 檔案建議儲存在 /workspace/manifests/
4. 檢查腳本放在 /workspace/scripts/

祝您考試順利！
===============================================
EOF

# 檢查 kubeconfig
if [ -f "/kubeconfig/config" ]; then
    echo "找到 kubeconfig 檔案"
    export KUBECONFIG=/kubeconfig/config

    # 設定 kubeconfig 權限
    chmod 600 /kubeconfig/config

    # 測試 kubectl 連線
    if kubectl cluster-info >/dev/null 2>&1; then
        echo "✓ kubectl 連線測試成功"
        kubectl get nodes --no-headers 2>/dev/null | wc -l | xargs echo "叢集節點數量:"
    else
        echo "⚠ kubectl 連線測試失敗，請檢查叢集狀態"
    fi
else
    echo "⚠ 未找到 kubeconfig 檔案，將在環境準備完成後載入"
fi

# 檢查 SSH 金鑰
if [ -f "/root/.ssh/authorized_keys" ]; then
    echo "✓ 找到 SSH 授權金鑰"
    chmod 600 /root/.ssh/authorized_keys
else
    echo "⚠ 未找到 SSH 授權金鑰"
fi

if [ -f "/home/exam/.ssh/authorized_keys" ]; then
    chmod 600 /home/exam/.ssh/authorized_keys
    chown exam:exam /home/exam/.ssh/authorized_keys
    echo "✓ exam 使用者 SSH 金鑰已設定"
fi

# 建立考試專用腳本
cat > /workspace/scripts/check-cluster.sh << 'EOF'
#!/bin/bash
# 快速檢查叢集狀態

echo "=== Kubernetes 叢集狀態檢查 ==="
echo
echo "節點狀態:"
kubectl get nodes -o wide
echo
echo "系統 Pods:"
kubectl get pods -n kube-system
echo
echo "所有 Namespaces:"
kubectl get namespaces
echo
echo "Storage Classes:"
kubectl get storageclass
echo
echo "叢集資訊:"
kubectl cluster-info
EOF

cat > /workspace/scripts/common-resources.sh << 'EOF'
#!/bin/bash
# 建立常用資源的快速腳本

case "$1" in
    "pod")
        kubectl run ${2:-test-pod} --image=${3:-nginx} --restart=Never --dry-run=client -o yaml
        ;;
    "deployment")
        kubectl create deployment ${2:-test-deploy} --image=${3:-nginx} --replicas=${4:-1} --dry-run=client -o yaml
        ;;
    "service")
        kubectl create service clusterip ${2:-test-svc} --tcp=${3:-80}:${4:-80} --dry-run=client -o yaml
        ;;
    "configmap")
        kubectl create configmap ${2:-test-cm} --from-literal=key1=value1 --dry-run=client -o yaml
        ;;
    "secret")
        kubectl create secret generic ${2:-test-secret} --from-literal=key1=value1 --dry-run=client -o yaml
        ;;
    *)
        echo "使用方式: $0 [pod|deployment|service|configmap|secret] [名稱] [參數...]"
        echo "範例:"
        echo "  $0 pod my-pod nginx"
        echo "  $0 deployment my-deploy nginx 3"
        echo "  $0 service my-svc 80 8080"
        ;;
esac
EOF

# 設定腳本權限
chmod +x /workspace/scripts/*.sh

# 建立常用別名腳本
cat > /home/exam/.bash_aliases << 'EOF'
# Kubernetes 考試專用別名
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kgn='kubectl get nodes'
alias kaf='kubectl apply -f'
alias kdf='kubectl delete -f'
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'
alias kgns='kubectl get namespaces'
alias kgsec='kubectl get secrets'
alias kgcm='kubectl get configmaps'

# 快速 YAML 生成
alias mkpod='kubectl run test-pod --image=nginx --restart=Never --dry-run=client -o yaml'
alias mkdeploy='kubectl create deployment test-deploy --image=nginx --dry-run=client -o yaml'
alias mksvc='kubectl create service clusterip test-svc --tcp=80:80 --dry-run=client -o yaml'

# 工作目錄快捷方式
alias work='cd /workspace'
alias manifests='cd /workspace/manifests'
alias scripts='cd /workspace/scripts'

# 快速檢查
alias check='/workspace/scripts/check-cluster.sh'
alias checkcluster='kubectl get nodes,pods,services,deployments --all-namespaces'
EOF

chown exam:exam /home/exam/.bash_aliases

# 設定考試環境變數
echo "export KUBECONFIG=/kubeconfig/config" >> /home/exam/.bashrc
echo "export EDITOR=vim" >> /home/exam/.bashrc
echo "export TERM=xterm-256color" >> /home/exam/.bashrc

# 啟動訊息
echo ""
echo "=== Bastion 容器準備完成 ==="
echo "SSH 服務即將啟動"
echo "可用端口: 22"
echo "使用者: root, exam"
echo "工作目錄: /workspace"
echo ""

# 執行原始命令
exec "$@"