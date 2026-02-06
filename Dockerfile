# =====================================================
# AI 学习助手 - 前后端一体化 Docker 镜像
# 适配 Zeabur 部署
# =====================================================

FROM node:18-alpine

# 安装 Nginx 和 Supervisor
RUN apk add --no-cache nginx supervisor

# 创建必要目录
RUN mkdir -p /var/log/supervisor /run/nginx /app/backend /etc/supervisor/conf.d

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
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY *.html /usr/share/nginx/html/

# ===== Nginx 配置模板 =====
RUN cat > /etc/nginx/nginx.conf.template <<'EOF'
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
        listen 80;
        listen 8080;
        listen 3000;
        server_name localhost;

        root /usr/share/nginx/html;
        index home.html index.html;

        # 前端路由
        location / {
            try_files $uri $uri/ /home.html;
        }

        # 浏览器默认请求，避免无意义 404 日志
        location = /favicon.ico {
            access_log off;
            log_not_found off;
            return 204;
        }

        # API 反向代理到 Node.js 后端
        location /api {
            proxy_pass http://127.0.0.1:3001;
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
EOF

# ===== Supervisor 配置 =====
RUN cat > /etc/supervisor/conf.d/supervisord.conf <<'EOF'
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
environment=NODE_ENV="production",PORT="3001"
EOF

# ===== 启动脚本 =====
RUN cat > /docker-entrypoint.sh <<'SCRIPT'
#!/bin/sh
set -e

echo "=========================================="
echo "  AI 学习助手 启动中..."
echo "  Nginx 监听端口: 80 / 8080 / 3000"
echo "  Backend 监听端口: 3001"
echo "=========================================="

# 生成 Nginx 配置
cp /etc/nginx/nginx.conf.template /etc/nginx/nginx.conf

# 注入前端配置 - 使用相对路径 (通过 Nginx 代理)
cat > /usr/share/nginx/html/js/config.js <<CONFIG
window.AppConfig = {
    API_BASE_URL: '/api'
};
CONFIG

echo "前端配置已生成"
echo "启动 Supervisor..."

exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
SCRIPT
RUN chmod +x /docker-entrypoint.sh

# 暴露端口 (Zeabur 会使用 PORT 环境变量)
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/api/health || wget -q --spider http://localhost:3000/api/health || wget -q --spider http://localhost:80/api/health || exit 1

# 启动
ENTRYPOINT ["/docker-entrypoint.sh"]
