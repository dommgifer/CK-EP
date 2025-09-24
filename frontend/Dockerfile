# 多階段建構：第一階段建置應用
FROM node:18-alpine as builder

# 設定環境變數
ENV NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL=warn

# 安裝 dumb-init 用於正確的信號處理
RUN apk add --no-cache dumb-init

# 建立非 root 使用者
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY package*.json ./

# 安裝所有依賴（包括開發依賴用於建置）
RUN npm install --include=dev && \
    npm cache clean --force

# 複製應用程式碼
COPY --chown=nextjs:nodejs . .

# 建置應用
RUN npm run build

# 第二階段：生產映像
FROM nginx:alpine as production

# 安裝 dumb-init
RUN apk add --no-cache dumb-init

# 建立非 root 使用者
RUN addgroup -g 1001 -S nginx && \
    adduser -S nginx -u 1001 -G nginx

# 從建置階段複製建置結果
COPY --from=builder /app/dist /usr/share/nginx/html

# 複製 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 建立 nginx 所需的目錄並設定權限
RUN mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /usr/share/nginx/html \
    && chown -R nginx:nginx /etc/nginx/conf.d

# 設定正確的權限
RUN touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

# 切換到非 root 使用者
USER nginx

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# 暴露埠 (nginx 預設使用 8080 for non-root)
EXPOSE 8080

# 使用 dumb-init 啟動 nginx
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]