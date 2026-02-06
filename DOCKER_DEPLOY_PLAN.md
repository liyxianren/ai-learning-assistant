# 单容器 Docker 部署方案（Zeabur）

## 背景

项目前后端已分离为 `frontend/`（纯静态）和 `backend/`（Flask + Gunicorn）。Zeabur 平台每个服务对应一个容器，为简化部署和节省成本，将前后端合并到一个 Docker 容器中。

## 架构

```
┌─────────────────────────────────────────┐
│             Docker Container            │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │         Nginx (:80)               │  │
│  │                                   │  │
│  │  /           → 静态文件 (frontend) │  │
│  │  /api/*      → proxy_pass :3000   │  │
│  └────────────────┬──────────────────┘  │
│                   │                     │
│  ┌────────────────▼──────────────────┐  │
│  │     Gunicorn (:3000)              │  │
│  │     Flask Backend                 │  │
│  └───────────────────────────────────┘  │
│                                         │
│  supervisord 管理两个进程                 │
└─────────────────────────────────────────┘
          ↕ Zeabur 暴露 :80
```

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 基础镜像 | python:3.12-slim | 后端需要 Python，nginx 通过 apt 安装 |
| 进程管理 | supervisord | 轻量，单容器管理多进程的标准方案 |
| 前端服务 | nginx | 静态文件 + 反向代理 |
| 后端服务 | gunicorn | Flask 生产部署标准 |
| 对外端口 | 80 | Zeabur 自动识别 |

## 需要创建/修改的文件

### 1. 根目录 `Dockerfile`（替换现有）

合并前后端到单一镜像：

```dockerfile
FROM python:3.12-slim

# 安装 nginx 和 supervisor
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor && \
    rm -rf /var/lib/apt/lists/*

# --- 后端 ---
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# --- 前端 ---
COPY frontend/ /usr/share/nginx/html

# --- 配置文件 ---
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

# 删除 nginx 默认站点（避免冲突）
RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 80

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/app.conf"]
```

**要点：**
- 不再使用 nginx 的 envsubst 模板机制，nginx.conf 直接硬编码 `127.0.0.1:3000`（同容器内通信）
- 先复制 requirements.txt 单独安装依赖，利用 Docker 层缓存

### 2. 根目录 `nginx.conf`（修改现有）

后端地址从 `${BACKEND_URL}` 改为固定的 `127.0.0.1:3000`：

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root   /usr/share/nginx/html;
        index  home.html index.html;
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;

        # SSE 流式响应支持
        proxy_buffering off;
        proxy_cache off;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

### 3. 根目录 `supervisord.conf`（新建）

```ini
[supervisord]
nodaemon=true
logfile=/dev/stdout
logfile_maxbytes=0
pidfile=/tmp/supervisord.pid

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:gunicorn]
command=gunicorn -c gunicorn.conf.py wsgi:app
directory=/app/backend
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=FLASK_ENV="production"
```

### 4. 根目录 `.dockerignore`（修改现有）

```dockerignore
.git
.gitignore
.vscode
.idea
.trae
.claude

docs/

*.md
*.docx
*.log
*.tmp
.DS_Store

backend/.env
backend/data/app.db
backend/__pycache__
backend/app/__pycache__
backend/app/**/__pycache__
```

**注意：**
- 不再排除 `backend/`（现在需要打包）
- 排除 `backend/.env`（敏感信息通过 Zeabur 环境变量注入）
- 排除 `app.db`（运行时自动创建）
- 排除 `__pycache__`

### 5. `backend/.env` 处理

**不打入镜像**。所有环境变量在 Zeabur 控制台配置：

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `FLASK_ENV` | 否 | 默认 `production`（supervisord 中已设置） |
| `CHATGLM_API_KEY` | 是 | 智谱 API 密钥 |
| `CHATGLM_API_URL` | 否 | 默认已内置 |
| `CHATGLM_MODEL` | 否 | 默认 `glm-4.7-flashx` |
| `JWT_SECRET` | 是 | 生产环境必须修改 |
| `CORS_ORIGIN` | 否 | 同容器部署可设为 `*` |

### 6. 删除 `backend/Dockerfile`

后端不再单独构建镜像，删除此文件。

## 实施步骤

1. **创建** `supervisord.conf`
2. **修改** `nginx.conf` — 后端地址改为 `http://127.0.0.1:3000`
3. **替换** `Dockerfile` — 合并前后端的单容器构建
4. **修改** `.dockerignore` — 包含 backend/，排除敏感文件
5. **删除** `backend/Dockerfile` — 不再需要单独后端镜像
6. **本地验证** `docker build -t ai-learning . && docker run -p 8080:80 -e CHATGLM_API_KEY=xxx ai-learning`
7. **推送 Zeabur** — 在 Zeabur 控制台配置环境变量

## 验证清单

- [ ] `docker build` 构建成功
- [ ] 容器启动后 `curl http://localhost:8080/` 返回 home.html
- [ ] `curl http://localhost:8080/api/health` 返回 `{"success": true}`
- [ ] 注册 → 登录 → 解题完整流程可用
- [ ] SSE 流式解答正常返回
- [ ] Zeabur 部署后域名访问正常
