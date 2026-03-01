# Zeabur Docker 单容器部署教程

## 一、当前配置文件审查

基于 [Zeabur Dockerfile 部署文档](https://zeabur.com/docs/zh-CN/deploy/dockerfile) 和 [环境变量文档](https://zeabur.com/docs/zh-CN/deploy/variables) 逐一审查项目配置。

### 1.1 Dockerfile — 正确

```dockerfile
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

COPY frontend/ /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 80

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/app.conf"]
```

审查结论：
- `EXPOSE 80` 满足 Zeabur 端口自动检测要求
- 单阶段构建，Zeabur 会自动将控制台设置的环境变量注入容器运行时
- `backend/requirements.txt` 先单独 COPY 再安装，利用 Docker 层缓存
- supervisord 同时管理 nginx 和 gunicorn 两个进程

### 1.2 nginx.conf — 正确

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root   /usr/share/nginx/html;
        index  index.html app.html;
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        ...
        proxy_buffering off;   # SSE 流式必须
        proxy_cache off;
    }

    gzip on;
    ...
}
```

审查结论：
- 后端地址硬编码 `127.0.0.1:3000`，单容器内部通信无需模板变量
- `proxy_buffering off` 确保 SSE 流式响应正常
- `proxy_read_timeout 120s` 匹配后端 gunicorn 的 120s 超时

### 1.3 supervisord.conf — 需修复一处

当前配置：

```ini
[program:gunicorn]
...
environment=FLASK_ENV="production"
```

**问题**：supervisord 默认会继承父进程的所有环境变量，`environment=` 只是追加/覆盖指定项。这里只设置了 `FLASK_ENV`，Zeabur 注入的 `CHATGLM_API_KEY` 等变量能正常传递给 gunicorn，所以实际可以工作。

但更安全的写法是同时设置 `CORS_ORIGIN`，避免生产环境下 CORS 阻止请求：

```ini
environment=FLASK_ENV="production",CORS_ORIGIN="*"
```

### 1.4 .dockerignore — 正确

```
.git
.gitignore
.vscode / .idea / .trae / .claude

docs/

*.md / *.docx / *.log / *.tmp / .DS_Store

backend/.env          ← 敏感信息不打入镜像
backend/data/app.db   ← 数据库在运行时创建
backend/__pycache__   ← Python 缓存
```

审查结论：
- `backend/.env` 被排除，API 密钥不会泄漏到镜像中
- `backend/` 目录本身没有被排除（之前的前端专用 .dockerignore 排除了它，现已修正）
- `backend/data/users.json` 和 `history.json` 会被保留用于迁移

### 1.5 后端配置 — 需注意一处

`backend/app/config.py` 中：

```python
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:8080")
```

默认值是 `http://localhost:8080`，在 Zeabur 上需要通过环境变量覆盖为 `*`（因为单容器模式下前端请求是同源的，CORS 实际不会触发，但设为 `*` 更安全）。

### 1.6 backend/Dockerfile — 应删除

`backend/Dockerfile` 是旧的独立后端镜像配置，已被根目录合并 Dockerfile 取代。文件虽然无害（不会影响构建），但会造成混淆，建议删除。

### 1.7 审查总结

| 文件 | 状态 | 备注 |
|------|------|------|
| `Dockerfile` | ✅ 正确 | 单容器，EXPOSE 80 |
| `nginx.conf` | ✅ 正确 | 反向代理 + SSE 支持 |
| `supervisord.conf` | ⚠️ 建议优化 | 追加 `CORS_ORIGIN="*"` |
| `.dockerignore` | ✅ 正确 | 排除敏感文件 |
| `backend/app/config.py` | ⚠️ 需环境变量覆盖 | 设置 `CORS_ORIGIN=*` |
| `backend/Dockerfile` | ❌ 应删除 | 已被取代 |
| `frontend/js/user.js` | ✅ 正确 | `API_BASE = ''` 同源请求 |
| `backend/gunicorn.conf.py` | ✅ 正确 | 绑定 3000，2 workers |

---

## 二、Zeabur 部署步骤

### 步骤 1：推送代码到 GitHub

确保以下文件已提交到 Git 仓库：

```
Dockerfile
nginx.conf
supervisord.conf
.dockerignore
frontend/          （所有前端文件）
backend/           （所有后端文件，不含 .env 和 app.db）
```

### 步骤 2：Zeabur 创建项目

1. 登录 [Zeabur 控制台](https://dash.zeabur.com)
2. 点击 **Create Project**
3. 选择地域（推荐：亚太区域，延迟较低）

### 步骤 3：添加服务

1. 在项目中点击 **Add Service** → **Git Repository**
2. 授权并选择你的 GitHub 仓库
3. Zeabur 会自动检测到根目录的 `Dockerfile`，以 Docker 模式构建

### 步骤 4：配置环境变量

进入服务 → **Variables** 标签页，添加以下变量：

#### 必填变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `CHATGLM_API_KEY` | `你的智谱API密钥` | 从 [智谱开放平台](https://open.bigmodel.cn/) 获取 |
| `JWT_SECRET` | `自定义强密码字符串` | 生产环境必须修改，不能用默认值 |

#### 推荐变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `CORS_ORIGIN` | `*` | 单容器部署设为 `*` 即可 |
| `FLASK_ENV` | `production` | supervisord 已默认设置，可不填 |

#### 可选变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `CHATGLM_API_URL` | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | 智谱 API 地址 |
| `CHATGLM_MODEL` | `glm-4.7-flashx` | 对话模型 |
| `MULTIMODAL_API_KEY` | （空，回退用 CHATGLM_API_KEY） | 多模态模型密钥 |
| `MULTIMODAL_MODEL` | `gpt-4-vision-preview` | 图像识别模型 |
| `REQUEST_TIMEOUT` | `120` | 请求超时秒数 |
| `RATE_LIMIT_MAX_REQUESTS` | `30` | 每分钟最大请求数 |

**批量编辑**：点击 **Edit Raw Environment Variables**，粘贴以下内容：

```env
CHATGLM_API_KEY=你的智谱API密钥
JWT_SECRET=你的JWT密钥
CORS_ORIGIN=*
```

### 步骤 5：绑定域名

1. 进入服务 → **Networking** 标签页
2. 点击 **Generate Domain** 获取 Zeabur 免费域名（如 `xxx.zeabur.app`）
3. 或点击 **Custom Domain** 绑定自有域名

### 步骤 6：触发部署

配置完环境变量后，Zeabur 会自动重新部署。可以在 **Deployments** 标签页查看构建日志。

---

## 三、验证部署

### 3.1 健康检查

访问 `https://你的域名/api/health`，应返回：

```json
{
  "success": true,
  "message": "服务正常运行",
  "timestamp": "2026-02-06T..."
}
```

### 3.2 页面访问

- 访问 `https://你的域名/` → 应显示登录/注册页面（index.html）
- 登录后 → 应跳转到主应用页面（app.html）

### 3.3 完整功能测试

1. **注册**：创建新账号
2. **登录**：用新账号登录
3. **解题**：输入文字题目，点击开始解答
4. **历史记录**：确认解题记录被保存

---

## 四、注意事项

### 4.1 数据持久化

当前使用 SQLite，数据库文件存储在容器内 `/app/backend/data/app.db`。**容器重启时数据会丢失**。

如果需要数据持久化，有两个方案：
- 升级为云数据库（PostgreSQL），Zeabur 提供一键 PostgreSQL 服务
- 短期方案：SQLite 适合演示和小规模使用

### 4.2 API 密钥安全

- **绝不要**将 API 密钥提交到 Git 仓库
- `backend/.env` 已在 `.dockerignore` 和 `.gitignore` 中排除
- 所有密钥通过 Zeabur 控制台的环境变量配置

### 4.3 构建缓存

Zeabur 支持 Docker 层缓存。`requirements.txt` 单独 COPY 的写法确保依赖不变时跳过 pip install，加速后续构建。

### 4.4 日志查看

在 Zeabur 控制台 → 服务 → **Logs** 标签页可以查看 nginx 和 gunicorn 的实时日志（supervisord 将两者的 stdout/stderr 都输出到容器标准输出）。

---

## 五、架构图

```
用户浏览器
    │
    ▼
Zeabur (HTTPS 终止)
    │
    ▼ :80
┌──────────────────────────────────┐
│         Docker Container         │
│                                  │
│  ┌──────────────────────────┐    │
│  │     supervisord (PID 1)  │    │
│  └──┬──────────────┬────────┘    │
│     │              │             │
│  ┌──▼───┐   ┌─────▼──────────┐  │
│  │nginx │   │  gunicorn:3000 │  │
│  │ :80  │──▶│  Flask Backend  │  │
│  └──┬───┘   └────────────────┘  │
│     │                            │
│  静态文件                         │
│  /usr/share/nginx/html           │
│  ├── index.html (登录页)          │
│  ├── app.html   (主应用)          │
│  ├── css/style.css               │
│  └── js/main.js, user.js        │
└──────────────────────────────────┘
```
