# T091: Bastion Container 最終配置
# Alpine 基底的輕量工具容器，專注於 Kubernetes 考試工具

FROM alpine:3.19

# 維護者資訊
LABEL maintainer="Kubernetes Exam Simulator"
LABEL description="Bastion Container with Kubernetes Tools"
LABEL version="1.0.0"

# 安裝基本工具和相依套件
RUN apk update && apk add --no-cache \
    # 基本系統工具
    bash \
    bash-completion \
    openssh \
    openssh-server \
    sudo \
    shadow \
    # 網路和除錯工具
    curl \
    wget \
    netcat-openbsd \
    bind-tools \
    iputils \
    tcpdump \
    # 編輯器和文件處理
    vim \
    nano \
    git \
    tree \
    less \
    # JSON/YAML 處理工具
    jq \
    yq \
    # 開發和監控工具
    htop \
    tmux \
    screen \
    strace \
    # Python (某些考試腳本需要)
    python3 \
    py3-pip \
    # 時間同步
    tzdata \
    && rm -rf /var/cache/apk/*

# 建立考試專用使用者
RUN addgroup -g 1000 exam \
    && adduser -D -s /bin/bash -G exam -u 1000 exam \
    && echo 'exam:exampass' | chpasswd \
    && echo 'exam ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/exam

# 設定 SSH 服務
RUN ssh-keygen -A \
    && mkdir -p /var/run/sshd \
    && mkdir -p /root/.ssh \
    && mkdir -p /home/exam/.ssh

# 複製 SSH 配置
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY bashrc /home/exam/.bashrc
COPY vimrc /home/exam/.vimrc

# 設定權限
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chmod 600 /etc/ssh/sshd_config \
    && chmod 700 /home/exam/.ssh \
    && chown -R exam:exam /home/exam

# 安裝 kubectl
RUN KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt) \
    && curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# 安裝 helm
RUN HELM_VERSION=v3.13.0 \
    && curl -L "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" | tar -xz \
    && mv linux-amd64/helm /usr/local/bin/ \
    && rm -rf linux-amd64

# 安裝 etcdctl
RUN ETCD_VERSION=v3.5.9 \
    && curl -L "https://github.com/etcd-io/etcd/releases/download/${ETCD_VERSION}/etcd-${ETCD_VERSION}-linux-amd64.tar.gz" | tar -xz \
    && mv etcd-${ETCD_VERSION}-linux-amd64/etcdctl /usr/local/bin/ \
    && rm -rf etcd-${ETCD_VERSION}-linux-amd64

# 安裝 crictl（容器運行時介面工具）
RUN CRICTL_VERSION=v1.28.0 \
    && curl -L "https://github.com/kubernetes-sigs/cri-tools/releases/download/${CRICTL_VERSION}/crictl-${CRICTL_VERSION}-linux-amd64.tar.gz" | tar -xz \
    && mv crictl /usr/local/bin/

# 安裝 k9s（Kubernetes 互動式介面）
RUN K9S_VERSION=v0.27.4 \
    && curl -L "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_amd64.tar.gz" | tar -xz \
    && mv k9s /usr/local/bin/

# 建立工作目錄
RUN mkdir -p /workspace \
    && mkdir -p /scripts \
    && mkdir -p /kubeconfig \
    && chown -R exam:exam /workspace /scripts /kubeconfig

# 環境變數
ENV SHELL=/bin/bash
ENV TERM=xterm-256color
ENV KUBECONFIG=/kubeconfig/config

# 設定 kubectl 自動完成和別名
RUN echo 'source <(kubectl completion bash)' >> /etc/bash.bashrc \
    && echo 'alias k=kubectl' >> /etc/bash.bashrc \
    && echo 'complete -F __start_kubectl k' >> /etc/bash.bashrc

# 暴露 SSH 端口
EXPOSE 22

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ss -ln | grep :22 || exit 1

# 工作目錄
WORKDIR /workspace

# 啟動腳本
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D"]