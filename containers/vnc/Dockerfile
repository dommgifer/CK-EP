# T090: VNC Container 最終配置
# 基於 ConSol debian-xfce-vnc 的考試環境配置

FROM consol/debian-xfce-vnc:1.6.1

# 維護者資訊
LABEL maintainer="Kubernetes Exam Simulator"
LABEL description="VNC Desktop Environment for Kubernetes Exam Simulation"
LABEL version="1.0.0"

# 使用 root 進行安裝
USER 0

# 更新包管理器並安裝考試必要工具
RUN apt-get update && apt-get install -y \
    # SSH 和網路工具
    openssh-client \
    curl \
    wget \
    netcat-openbsd \
    telnet \
    dnsutils \
    iputils-ping \
    traceroute \
    # 編輯器和開發工具
    vim \
    nano \
    git \
    unzip \
    zip \
    tree \
    # 監控和除錯工具
    htop \
    tmux \
    screen \
    tcpdump \
    strace \
    # JSON 處理工具
    jq \
    yq \
    # 瀏覽器
    firefox-esr \
    # 終端機增強
    bash-completion \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安裝 kubectl (最新穩定版)
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# 安裝 helm
RUN curl https://get.helm.sh/helm-v3.13.0-linux-amd64.tar.gz | tar -xz \
    && mv linux-amd64/helm /usr/local/bin/ \
    && rm -rf linux-amd64

# 安裝 docker CLI (用於某些考試場景)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
    && echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 建立必要的目錄結構
RUN mkdir -p /headless/.ssh \
    && mkdir -p /headless/scripts \
    && mkdir -p /headless/workspace \
    && mkdir -p /headless/.kube \
    && mkdir -p /headless/Downloads

# 複製配置檔案
COPY ssh_config /headless/.ssh/config
COPY bashrc /headless/.bashrc
COPY vimrc /headless/.vimrc
COPY startup.sh /dockerstartup/startup_vnc.sh
COPY desktop_setup.sh /dockerstartup/desktop_setup.sh

# 設定權限
RUN chmod +x /dockerstartup/startup_vnc.sh \
    && chmod +x /dockerstartup/desktop_setup.sh \
    && chmod 600 /headless/.ssh/config \
    && chown -R 1000:1000 /headless

# 考試環境變數
ENV VNC_PW=examvnc
ENV VNC_RESOLUTION=1280x1024
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NO_VNC_PORT=6901
ENV HOME=/headless
ENV SHELL=/bin/bash

# 設定 kubectl 自動完成
RUN echo 'source <(kubectl completion bash)' >> /headless/.bashrc \
    && echo 'alias k=kubectl' >> /headless/.bashrc \
    && echo 'complete -F __start_kubectl k' >> /headless/.bashrc

# 切換回 VNC 使用者
USER 1000

# 設定工作目錄
WORKDIR /headless/workspace

# 暴露 VNC 和 noVNC 端口
EXPOSE 5901 6901

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:6901/ || exit 1

# 啟動腳本
CMD ["/dockerstartup/vnc_startup.sh"]