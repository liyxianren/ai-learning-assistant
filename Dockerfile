# =====================================================
# AI 学习助手 - 前后端一体化 Docker 镜像
# =====================================================

FROM node:18-alpine

# 只安装 Nginx（不需要 Supervisor）
RUN apk add --no-cache nginx

# 创建目录
RUN mkdir -p /run/nginx /app/backend/data

# ===== 后端 =====
WORKDIR /app/backend
COPY backend/package*.json ./
RUN npm ci --only=production
COPY backend/src ./src
COPY backend/data ./data

# ===== 前端 =====
RUN rm -rf /usr/share/nginx/html/*
COPY frontend/ /usr/share/nginx/html/

# ===== 启动脚本 =====
RUN cat > /start.sh <<'SCRIPT'
#!/bin/sh

set -e

echo "========================================"
echo "  AI Learning Assistant"
echo "========================================"

# 平台入口端口（Zeabur 会注入 PORT）
APP_PORT="${PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-3000}"
PUBLIC_API_BASE_URL="${PUBLIC_API_BASE_URL:-}"

# 初始化数据文件
cd /app/backend
[ -f data/users.json ] || echo '[]' > data/users.json
[ -f data/history.json ] || echo '[]' > data/history.json

# 生成前端配置
echo "window.AppConfig={API_BASE_URL:\"${PUBLIC_API_BASE_URL}\"};" > /usr/share/nginx/html/js/config.js

# 生成 Nginx 配置（使用平台端口）
cat > /etc/nginx/nginx.conf <<EOF
worker_processes auto;
error_log /dev/stderr warn;
pid /run/nginx/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /dev/stdout combined;
    sendfile on;
    keepalive_timeout 65;
    gzip on;

    server {
        listen ${APP_PORT};
        root /usr/share/nginx/html;
        index home.html;

        location / {
            try_files \$uri \$uri/ /home.html;
        }

        location /api {
            proxy_pass http://127.0.0.1:${BACKEND_PORT};
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_buffering off;
            proxy_read_timeout 300s;
        }
    }
}
EOF

# 启动后端（后台运行）
echo "Starting backend..."
NODE_ENV=production PORT="${BACKEND_PORT}" node src/app.js &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 验证后端启动
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Backend started (PID: $BACKEND_PID)"
else
    echo "ERROR: Backend failed to start!"
    exit 1
fi

# 启动 Nginx（前台运行，保持容器存活）
echo "Starting Nginx on port ${APP_PORT}..."
nginx -g "daemon off;"
SCRIPT

RUN chmod +x /start.sh

EXPOSE 8080

CMD ["/start.sh"]
