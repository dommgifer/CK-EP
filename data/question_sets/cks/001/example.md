**1. Docker daemon**
*   **背景 (Context):** 無。
*   **任務 (Task):**
    *   執行以下任務以保護叢集節點 cks000037：
    *   從 **docker** 群組中移除使用者 developer。
    *   重新配置並重新啟動 Docker daemon，以確保位於 /var/run/docker.sock 的 socket 檔案歸 **root** 群組所有。
*   **注意事項 (Notes):**
    *   **不要** 從任何其他群組中移除該使用者。
    *   完成工作後，請確保 Kubernetes 叢集是健康的。

**2. Upgrade (升級)**
*   **背景 (Context):** kubeadm 配置的叢集最近已升級，由於工作負載相容性問題，其中一個節點版本稍舊。
*   **任務 (Task):**
    *   升級叢集節點 compute-0 以匹配控制平面節點的版本。
    *   使用類似 ssh compute-0 的指令連接到 compute 節點。
*   **注意事項 (Notes):**
    *   **不要** 修改叢集中任何正在運行的工作負載。
    *   完成任務後， **不要** 忘記從 compute 節點退出。

**3. Kube-bench**
*   **背景 (Context):** 您必須解決 CIS Benchmark 工具為 kubeadm 配置的叢集發現的問題。
*   **任務 (Task):**
    *   通過配置並重新啟動受影響的組件來修復所有問題，以使新設定生效。
    *   修復 kubelet 發現的所有以下違規事項:
        *   2.1.2 確保 --anonymous-auth 參數設置為 false (FAIL)。
        *   2.1.3 確保 --authorization-mode 參數未設置為 AlwaysAllow (FAIL)。
    *   **盡可能使用 Webhook 身份驗證/授權**。
    *   修復 etcd 發現的所有以下違規事項:
        *   2.2 確保 --client-cert-auth 參數設置為 true (FAIL)。
*   **注意事項 (Notes):** 無。

**4. Kube-apiserver**
*   **背景 (Context):** 為了測試目的，kubeadm 配置的叢集 API 伺服器被配置為允許未經身份驗證和未經授權的訪問 。
*   **任務 (Task):**
    *   首先，通過以下方式配置叢集的 API 伺服器來保護它 :
        *   **禁止匿名身份驗證** 。
        *   使用授權模式 **Node,RBAC** 。
        *   使用準入控制器 **NodeRestriction** 。
    *   接下來，清理並移除 system:anonymous 的 ClusterRoleBinding 。
*   **注意事項 (Notes):**
    *   kubectl 被配置為使用未經身份驗證和未經授權的訪問。您無需更改它，但請注意，一旦您保護了叢集，kubectl 將停止工作 。
    *   您可以使用位於 /etc/kubernetes/admin.conf 的叢集原始 kubectl 配置文件來訪問受保護的叢集 。

**5. Auditing (審計)** 
*   **背景 (Context):** 您必須為 kubeadm 配置的叢集實施審計 。
*   **任務 (Task):**
    *   首先，重新配置叢集的 API 伺服器，以便 :
        *   基本審計策略位於 /etc/kubernetes/logpolicy/audit-policy.yaml 。
        *   日誌存儲在 /var/log/kubernetes/audit-logs.txt 。
        *   最多保留 2 個日誌，保留 10 天 。
    *   接下來，編輯並擴展基本策略以記錄 :
        *   namespaces 在 RequestResponse 級別的交互 。
        *   webapps 命名空間中 deployments 交互的請求體 。
        *   所有命名空間中 ConfigMap 和 Secret 在 Metadata 級別的交互 。
        *   所有其他請求在 Metadata 級別 。
*   **注意事項 (Notes):**
    *   基本策略只指定了 **不** 記錄什麼 。
    *   確保 API 伺服器使用擴展策略。否則可能導致分數降低 。

**6. Image Policy Webhook** 
*   **背景 (Context):** 您必須將容器圖像掃描器完全整合到 kubeadm 配置的叢集中 。
*   **任務 (Task):**
    *   給定一個位於 /etc/kubernetes/bouncer 的不完整配置和一個具有 HTTPS 端點 https://smooth-yak.local/image_policy 的功能性容器圖像掃描器，執行以下任務以實施一個驗證準入控制器 :
    *   首先，重新配置 API 伺服器以啟用所有準入插件，以支持提供的 **AdmissionConfiguration** 。
    *   接下來，重新配置 ImagePolicyWebhook 配置，以在後端失敗時拒絕圖像 。
    *   接下來，完成後端配置以指向容器圖像掃描器的端點 https://smooth-yak.local/image_policy 。
    *   最後，為了測試配置，部署 ~/vulnerable.yaml 中定義的測試資源，該資源使用應被拒絕的圖像 。
*   **注意事項 (Notes):**
    *   您可以根據需要刪除並重新創建資源 。
    *   容器圖像掃描器的日誌文件位於 /var/log/nginx/access_log 。

**7. Security Context (安全上下文)** 
*   **背景 (Context):** 您必須更新一個現有的 Pod，以確保其容器的不可變性 。
*   **任務 (Task):**
    *   修改命名空間 lamp 中名為 lamp-deployment 的現有 Deployment，使其容器 :
        *   以使用者 ID **20000** 運行 。
        *   使用只讀根文件系統 。
        *   禁止特權升級 。
*   **注意事項 (Notes):**
    *   Deployment 的 manifest 文件可在 ~/finer-sunbeam/lamp-deployment.yaml 找到 。

**8. Pod Security Standards (Pod 安全標準)** 
*   **背景 (Context):** 為符合規範，所有使用者命名空間都強制執行受限的 Pod 安全標準 。
*   **任務 (Task):**
    *   confidential 命名空間包含一個不符合受限 Pod 安全標準的 Deployment。因此，其 Pods 無法被調度。修改 Deployment 以符合規範並驗證 Pods 正在運行 。
*   **注意事項 (Notes):**
    *   Deployment 的 manifest 文件可在 ~/nginx-unprivileged.yaml 找到 。

**9. Analyze security issue (分析安全問題)** 
*   **任務 (Task):**
    *   分析並編輯位於 ~/subtle-bee/build/Dockerfile 的 Dockerfile，修復文件中存在的一個顯著的安全/最佳實踐問題 。
    *   分析並編輯給定的 manifest 文件 ~/subtle-bee/deployment.yaml，修復文件中存在的一個顯著的安全/最佳實踐問題 。
*   **注意事項 (Notes):**
    *   **不要** 添加或刪除指令；只修改文件中存在的一個現有指令，使其符合安全/最佳實踐要求 。
    *   **不要** 構建 Dockerfile。否則可能導致存儲空間不足和零分 。
    *   **不要** 添加或刪除字段；只修改文件中存在的一個現有字段，使其符合安全/最佳實踐要求 。
    *   您應該為任何任務使用使用者 nobody (使用者 ID 65535) 。

**10. Falco** 
*   **背景 (Context):** 一個 Pod 行為異常並對系統構成安全威脅 。
*   **任務 (Task):**
    *   首先，識別出正在訪問敏感文件 /dev/mem 的行為異常的 Pod 。
    *   接下來，識別管理該行為異常 Pod 的 Deployment 並將其副本數量縮減為零 。
*   **注意事項 (Notes):**
    *   **不要** 修改 Deployment，除了將其縮減 。
    *   **不要** 修改任何其他 Deployment 。
    *   **不要** 刪除任何 Deployment 。

**11. Service Account (服務帳戶)** 
*   **背景 (Context):** 一項安全審計發現一個 Deployment 未正確處理服務帳戶令牌，這可能導致安全漏洞 。
*   **任務 (Task):**
    *   首先，修改命名空間 monitoring 中現有的 ServiceAccount stats-monitor-sa，以關閉 API 憑證的自動掛載 。
    *   接下來，修改命名空間 monitoring 中現有的 Deployment stats-monitor，以注入一個服務帳戶令牌，該令牌掛載在 /var/run/secrets/kubernetes.io/serviceaccount/token 。
    *   使用一個名為 **token** 的投射卷 (Projected Volume) 來注入服務帳戶令牌，並確保它是只讀掛載的 。
*   **注意事項 (Notes):**
    *   Deployment 的 manifest 文件可在 ~/stats-monitor/deployment.yaml 找到 。


**12. Secret** 
*   **背景 (Context):** 您必須完成使用存儲在 TLS Secret 中的 SSL 文件保護 Web 伺服器的訪問 。
*   **任務 (Task):**
    *   在 clever-cactus 命名空間中為現有的 Deployment clever-cactus 創建一個名為 **clever-cactus** 的 TLS Secret 。
    *   使用以下 SSL 文件 :
        *   憑證文件: ~/clever-cactus/web.k8s.local.crt 。
        *   密鑰文件: ~/clever-cactus/web.k8s.local.key 。
*   **注意事項 (Notes):**
    *   Deployment 已配置為使用 TLS Secret 。
    *   **不要** 修改現有的 Deployment。否則可能導致分數降低 。

**13. Ingress TLS** 
*   **背景 (Context):** 您必須使用 HTTPS 路由公開 Web 應用程式 。
*   **任務 (Task):**
    *   在 prod 命名空間中創建一個名為 **web** 的 Ingress 資源，並按如下配置 :
        *   為主機 **web.k8s.local** 以及所有路徑到現有服務 **web** 路由流量 。
        *   啟用使用現有 Secret **web-cert** 的 TLS 終止 。
        *   將 HTTP 請求重定向到 HTTPS 。
*   **注意事項 (Notes):**
    *   您可以使用 curl -L http://web.k8s.local 命令測試 Ingress 配置 。

**14. Network Policy (網路策略)** 
*   **背景 (Context):** 您必須實施 NetworkPolicies 來控制跨命名空間的現有 Deployments 的流量流 。
*   **任務 (Task):**
    *   首先，在 prod 命名空間中創建一個名為 **deny-policy** 的 NetworkPolicy，以阻止所有入站流量 。
    *   接下來，在 data 命名空間中創建一個名為 **allow-from-prod** 的 NetworkPolicy，以僅允許來自 prod 命名空間中 Pods 的入站流量 。
*   **注意事項 (Notes):**
    *   prod 命名空間被標記為 env:prod 。
    *   data 命名空間被標記為 env:data 。
    *   **不要** 修改或刪除任何命名空間或 Pods。只創建所需的 NetworkPolicies 。

**15. Cilium Network Policy** 
*   **任務 (Task):**
    *   執行以下任務，以使用 Cilium 保護現有應用程式的內部和外部網路流量 。
    *   首先，在 nodebb 命名空間中創建一個名為 **nodebb** 的 L4 CiliumNetworkPolicy，並按如下配置 :
        *   允許在 ingress-nginx 命名空間中運行的所有 Pods 訪問 nodebb Deployment 的 Pods 。
        *   要求相互身份驗證 。
    *   接下來，擴展上一步中創建的網路策略，如下所示 :
        *   允許主機訪問 nodebb Deployment 的 Pods 。
        *   **不要** 使用相互身份驗證 。
*   **注意事項 (Notes):**
    *   您可以使用瀏覽器訪問 Cilium 的文檔 。
    *   如果您想自我檢查策略，請注意 nodebb Deployment 通過 Ingress 在 http://k8s.local/nodebb 公開 。
    *   如果您想自我檢查您的更改，主機可以通過 NodePort Service 在 http://localhost:30000 訪問 nodebb Deployment 。

**16. Bom** 
*   **背景 (Context):** alpine 命名空間中的 alpine Deployment 包含運行不同版本的 alpine 圖像的三個容器 。
*   **任務 (Task):**
    *   首先，找出哪個版本的 alpine 圖像包含 libcrypto3 包，版本為 3.1.4-r5 。
    *   接下來，使用預安裝的 **bom** 工具為識別出的圖像版本創建一個 SPDX 文檔，存儲在 ~/alpine.spdx 。
    *   最後，更新 alpine Deployment 並刪除使用識別出的圖像版本的容器 。
*   **注意事項 (Notes):**
    *   您可以在 bom 文檔中找到 **bom** 工具的文檔 。
    *   Deployment 的 manifest 文件可在 ~/alpine-deployment.yaml 找到 。
    *   **不要** 修改 Deployment 的任何其他容器 。