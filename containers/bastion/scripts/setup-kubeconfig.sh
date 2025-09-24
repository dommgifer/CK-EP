#!/bin/bash
# 設定 Kubernetes 叢集配置

set -e

CLUSTER_IP=$1
CLUSTER_USER=$2

if [[ -z "$CLUSTER_IP" || -z "$CLUSTER_USER" ]]; then
    echo "使用方式: $0 <cluster_ip> <cluster_user>"
    exit 1
fi

echo "設定 Kubernetes 叢集連線..."
echo "叢集 IP: $CLUSTER_IP"
echo "使用者: $CLUSTER_USER"

# 複製 kubeconfig 檔案
if ssh -o StrictHostKeyChecking=no "$CLUSTER_USER@$CLUSTER_IP" "test -f ~/.kube/config"; then
    scp -o StrictHostKeyChecking=no "$CLUSTER_USER@$CLUSTER_IP:~/.kube/config" /root/.kube/config
    echo "✓ kubeconfig 檔案已複製"
else
    echo "✗ 無法找到 kubeconfig 檔案"
    exit 1
fi

# 測試連線
if kubectl cluster-info >/dev/null 2>&1; then
    echo "✓ Kubernetes 叢集連線成功"
    kubectl get nodes
else
    echo "✗ Kubernetes 叢集連線失敗"
    exit 1
fi

echo "Kubernetes 環境設定完成"