# =====================================================
# AI 学习助手 - 前后端一体化 Docker 镜像
# 适配 Zeabur 部署
# =====================================================

FROM node:18-alpine

# 安装 Nginx 和 Supervisor
RUN apk add --no-cache nginx supervisor

# 创建必要目录
RUN mkdir -p /var/log/supervisor /run/nginx /app/backend /etc/supervisor.d

# ===== 后端设置 =====
WORKDIR /app/backend

# 先复制 package.json 以利用 Docker 缓存
COPY backend/package*.json ./
RUN npm ci --only=production

# 复制后端代码
COPY backend/src ./src
COPY backend/data ./data

# ===== 前端设置 =====
# 清空 Nginx 默认页面
RUN rm -rf /usr/share/nginx/html/*

# 复制前端静态文件
COPY frontend/ /usr/share/nginx/html/

# ===== Nginx 配置 (监听 8080 端口) =====
RUN cat > /etc/nginx/nginx.conf <<'NGINXCONF'
worker_processes auto;
error_log /dev/stderr warn;
pid /run/nginx/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';
    access_log /dev/stdout main;

    sendfile on;
    keepalive_timeout 65;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    server {
        listen 8080;
        server_name localhost;

        root /usr/share/nginx/html;
        index home.html index.html;

        # 前端路由
        location / {
            try_files $uri $uri/ /home.html;
        }

        # API 反向代理到 Node.js 后端
        location /api {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 支持流式响应 (SSE)
            proxy_buffering off;
            proxy_cache off;
            proxy_read_timeout 300s;

            # WebSocket 支持
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # 静态资源缓存
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
}
NGINXCONF

# ===== Supervisor 配置 =====
RUN cat > /etc/supervisor.d/app.ini <<'SUPCONF'
[supervisord]
nodaemon=true
logfile=/dev/null
logfile_maxbytes=0
pidfile=/var/run/supervisord.pid
user=root

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:backend]
command=node /app/backend/src/app.js
directory=/app/backend
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=NODE_ENV="production",PORT="3000"
SUPCONF

# ===== 启动脚本 =====
RUN cat > /docker-entrypoint.sh <<'SCRIPT'
#!/bin/sh
set -e

echo "=========================================="
echo "  AI 学习助手 启动中..."
echo "  Nginx 端口: 8080"
echo "  后端端口: 3000"
echo "=========================================="

# 注入前端配置 - API 路径由代码中指定，这里设为空
cat > /usr/share/nginx/html/js/config.js <<CONFIG
window.AppConfig = {
    API_BASE_URL: ''
};
CONFIG

echo "前端配置已生成"
echo "启动服务..."

exec supervisord -c /etc/supervisord.conf
SCRIPT
RUN chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:8080/api/health || exit 1

# 启动
ENTRYPOINT ["/docker-entrypoint.sh"]
