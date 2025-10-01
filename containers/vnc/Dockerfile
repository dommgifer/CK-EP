# T090: VNC Container 最終配置
# 基於 ConSol debian-xfce-vnc 的考試環境配置

FROM consol/debian-xfce-vnc:v2.0.4

# 維護者資訊
LABEL maintainer="Kubernetes Exam Simulator"
LABEL description="VNC Desktop Environment for Kubernetes Exam Simulation"
LABEL version="1.0.0"

# 使用 root 進行安裝
USER 0

# 安裝必要工具
RUN apt-get update && apt-get install -y \
    openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# kubectl, helm 等工具會在 Bastion 容器中提供，VNC 容器只需要 SSH 連線能力

# 建立必要的目錄結構
RUN mkdir -p /headless/.ssh \
    && mkdir -p /headless/workspace \
    && chown -R 1000:1000 /headless

# 考試環境變數
ENV VNC_PW=examvnc
ENV VNC_RESOLUTION=1280x1024
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NO_VNC_PORT=6901
ENV HOME=/headless
ENV SHELL=/bin/bash

# kubectl 在 bastion 容器中，這裡不需要設定

# 切換回 VNC 使用者
USER 1000

# 暴露 VNC 和 noVNC 端口
EXPOSE 5901 6901

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:6901/ || exit 1

# 使用原始啟動方式（ENTRYPOINT + CMD）
ENTRYPOINT ["/dockerstartup/vnc_startup.sh"]
CMD ["--wait"]