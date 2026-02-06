# Flask 后端重构实施方案

## Context

当前后端使用 Node.js + Express 5.2.1 构建，采用 JSON 文件存储数据，实现了一个 AI 学习助手系统（图像识别 → 题目解析 → 生成解答）。需要将其完整重构为 Python Flask 框架，同时升级数据存储为 SQLite + SQLAlchemy，并保持所有 API 端点和响应格式完全兼容前端。

## 技术选型汇总

| 组件 | 选择 |
|------|------|
| 项目结构 | Blueprint 模块化 |
| 数据存储 | SQLite + Flask-SQLAlchemy |
| 认证方案 | Flask-JWT-Extended |
| 密码加密 | Werkzeug (pbkdf2) |
| HTTP 客户端 | requests |
| 流式响应 | Flask Response + generator |
| 参数验证 | marshmallow |
| 部署 | Gunicorn + Dockerfile |
| 代码位置 | 替换现有 backend/ 目录 |

## 目标目录结构

```
backend/
├── app/
│   ├── __init__.py              # create_app() 工厂函数 + Blueprint 注册
│   ├── config.py                # 配置类 (从 .env 读取)
│   ├── extensions.py            # 扩展初始化 (db, jwt, ma, limiter, cors)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User SQLAlchemy 模型
│   │   └── history.py           # History SQLAlchemy 模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py              # 注册/登录参数验证 Schema
│   │   ├── problem.py           # 解题相关参数验证 Schema
│   │   └── history.py           # 历史记录参数验证 Schema
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── auth.py              # /api/auth/* 路由
│   │   ├── api.py               # /api/* 路由 (health, recognize, parse, solve 等)
│   │   └── history.py           # /api/history/* 路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py        # AI 服务层 (对应 aiService.js)
│   │   ├── chatglm_service.py   # ChatGLM API 封装 (对应 chatglmService.js)
│   │   └── pipeline_service.py  # 多 Agent 管线 (对应 pipelineService.js)
│   └── utils/
│       ├── __init__.py
│       └── errors.py            # 统一错误处理
├── migrations/
│   └── migrate_json_to_sqlite.py  # JSON → SQLite 数据迁移脚本
├── data/                          # 保留原始 JSON 文件供迁移使用
│   ├── users.json
│   └── history.json
├── .env                           # 环境变量 (复用现有 key)
├── requirements.txt               # Python 依赖
├── Dockerfile                     # 新的 Flask Dockerfile
├── gunicorn.conf.py               # Gunicorn 配置
└── wsgi.py                        # WSGI 入口
```

## 分步实施计划

### 步骤 1：项目初始化

创建基础文件和依赖配置。

**文件：`backend/requirements.txt`**
```
Flask==3.1.*
Flask-SQLAlchemy==3.1.*
Flask-JWT-Extended==4.7.*
Flask-Cors==5.0.*
Flask-Limiter==3.8.*
marshmallow==3.23.*
python-dotenv==1.1.*
requests==2.32.*
gunicorn==23.*
```

**文件：`backend/.env`** — 复用现有环境变量 key，调整命名：
```
FLASK_ENV=development
PORT=3000
CHATGLM_API_KEY=<现有值>
CHATGLM_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
CHATGLM_MODEL=glm-4.7-flashx
MULTIMODAL_API_KEY=<现有值>
MULTIMODAL_API_URL=https://api.openai.com/v1/chat/completions
MULTIMODAL_MODEL=gpt-4-vision-preview
JWT_SECRET=ai-learning-assistant-secret-key
CORS_ORIGIN=http://localhost:8080
REQUEST_TIMEOUT=120
RATE_LIMIT_MAX_REQUESTS=30
MAX_IMAGE_SIZE=5242880
```

---

### 步骤 2：配置与扩展

**文件：`backend/app/config.py`**
- Config 基类 + DevelopmentConfig / ProductionConfig 子类
- 从 .env 读取所有配置项
- 配置项与当前 Node.js 版本 `config.js` 一一对应

**文件：`backend/app/extensions.py`**
- 初始化 SQLAlchemy、JWTManager、Marshmallow、Limiter、CORS
- 所有扩展在 `create_app()` 中统一 `init_app()`

---

### 步骤 3：数据模型 (SQLAlchemy)

**文件：`backend/app/models/user.py`**
- 对应当前 `models/user.js`
- 字段：`id` (UUID), `username` (unique), `password_hash`, `created_at`, `last_login_at`
- 使用 `werkzeug.security.generate_password_hash / check_password_hash` 替代 SHA-256
- 方法：`set_password()`, `check_password()`, `to_dict()`

**文件：`backend/app/models/history.py`**
- 对应当前 `models/history.js`
- 字段：`id` (UUID), `user_id` (FK), `username`, `question` (Text), `parse_result` (JSON), `solution` (JSON), `created_at`
- 方法：`to_dict()`
- 关系：`user = db.relationship('User', backref='histories')`

---

### 步骤 4：参数验证 Schema (marshmallow)

**文件：`backend/app/schemas/auth.py`**
- `RegisterSchema`: username (3-20字符), password (>=6字符), confirm_password (与password一致)
- `LoginSchema`: username (必填), password (必填)

**文件：`backend/app/schemas/problem.py`**
- `RecognizeSchema`: image (必填)
- `ParseSchema`: text (必填，非空)
- `SolveSchema`: text (必填), parse_result (必填，dict)
- `SolveProblemSchema`: type (必填, oneof text/image), content (必填)
- `SolveStreamSchema`: text (必填), parse_result (必填)

**文件：`backend/app/schemas/history.py`**
- `HistoryQuerySchema`: page (默认1), limit (默认20, 最大100)

---

### 步骤 5：Blueprint 路由

**文件：`backend/app/blueprints/auth.py`** — 对应 `routes/auth.js`

| 端点 | 方法 | 认证 | 功能 |
|------|------|------|------|
| `/api/auth/register` | POST | 无 | 注册 |
| `/api/auth/login` | POST | 无 | 登录，返回 JWT |
| `/api/auth/me` | GET | 必须 | 当前用户信息 |
| `/api/auth/logout` | POST | 无 | 登出 (返回成功即可) |

**文件：`backend/app/blueprints/api.py`** — 对应 `routes/api.js` + `controllers/problemController.js`

| 端点 | 方法 | 认证 | 功能 |
|------|------|------|------|
| `/api/health` | GET | 无 | 健康检查 |
| `/api/recognize` | POST | 无 | 图像识别 |
| `/api/parse` | POST | 无 | 题目解析 |
| `/api/solve` | POST | 无 | 生成解答 |
| `/api/solve-problem` | POST | 可选 | 完整解题流程 |
| `/api/solve-stream` | POST | 无 | SSE 流式解答 |

**文件：`backend/app/blueprints/history.py`** — 对应 `routes/history.js`

| 端点 | 方法 | 认证 | 功能 |
|------|------|------|------|
| `/api/history` | GET | 必须 | 分页获取历史 |
| `/api/history/<id>` | GET | 必须 | 获取单条详情 |
| `/api/history/<id>` | DELETE | 必须 | 删除单条 |
| `/api/history` | DELETE | 必须 | 清空全部 |

**关键：所有响应格式保持与现有 Node.js 版本一致**，统一使用：
```json
{
  "success": true/false,
  "data": { ... },
  "message": "...",
  "error": "..."
}
```

---

### 步骤 6：服务层

**文件：`backend/app/services/chatglm_service.py`** — 对应 `chatglmService.js`
- 使用 `requests` 库调用 ChatGLM API
- `parse_problem(text)` → 返回 JSON (type, subject, knowledgePoints, difficulty, prerequisites)
- `generate_solution(text, parse_result)` → 返回结构化解答
- `generate_solution_stream(text, parse_result)` → 返回 generator，逐 chunk yield
- `parse_solution_content(content)` → 提取【解题思路】【详细步骤】【最终答案】【知识总结】
- `health_check()` → 测试 API 连通性
- 保持与原始 JS 版本相同的 prompt 模板和 temperature 参数

**文件：`backend/app/services/ai_service.py`** — 对应 `aiService.js`
- `recognize_image(image_base64)` → 调用多模态模型 (GPT-4V) 做 OCR
- `parse_problem(text)` → 委托 chatglm_service
- `generate_solution(text, parse_result)` → 委托 chatglm_service
- `generate_solution_stream(text, parse_result)` → 委托 chatglm_service
- `health_check()` → 检查多模态和 ChatGLM 连通性

**文件：`backend/app/services/pipeline_service.py`** — 对应 `pipelineService.js`
- `solve_problem(input_data)` → 完整管线：识别 → 解析 → 解答 → 保存历史
- `recognize_only(image_base64)` → 仅图像识别
- `parse_only(text)` → 仅题目解析
- `solve_only(text, parse_result)` → 仅生成解答
- `solve_stream(text, parse_result)` → 返回 SSE generator

---

### 步骤 7：SSE 流式响应实现

在 `/api/solve-stream` 端点中：
```python
@bp.route('/solve-stream', methods=['POST'])
def solve_stream():
    # 验证参数 ...
    def generate():
        for chunk in pipeline_service.solve_stream(text, parse_result):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )
```

---

### 步骤 8：错误处理

**文件：`backend/app/utils/errors.py`**
- 自定义异常类：`APIError(message, status_code)`
- 全局错误处理器：注册到 app，统一返回 `{"success": false, "error": "..."}`
- 404 处理器：返回 `{"success": false, "error": "接口不存在"}`

---

### 步骤 9：应用工厂

**文件：`backend/app/__init__.py`**
```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)

    # 注册 Blueprint
    from .blueprints.auth import bp as auth_bp
    from .blueprints.api import bp as api_bp
    from .blueprints.history import bp as history_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api/history')

    # 注册错误处理器
    register_error_handlers(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app
```

**文件：`backend/wsgi.py`**
```python
from app import create_app
app = create_app()
```

---

### 步骤 10：数据迁移脚本

**文件：`backend/migrations/migrate_json_to_sqlite.py`**
- 读取 `data/users.json` → 逐条插入 User 表
  - 旧密码是 SHA-256 哈希，迁移时需特殊处理：
    - 方案：在 User 模型增加 `password_legacy` 字段标记旧密码
    - 登录时如果检测到旧格式密码，验证后自动用 Werkzeug 重新哈希并更新
- 读取 `data/history.json` → 逐条插入 History 表
  - 将 `parseResult` / `solution` 对象直接存为 JSON 字段
- 打印迁移统计（用户数、历史记录数）

---

### 步骤 11：部署配置

**文件：`backend/gunicorn.conf.py`**
```python
bind = '0.0.0.0:3000'
workers = 2
timeout = 120
```

**文件：`backend/Dockerfile`**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
```

---

### 步骤 12：清理

- 删除 Node.js 相关文件：`package.json`, `package-lock.json`, `node_modules/`, `.dockerignore`, 旧 `src/` 目录
- 保留 `data/` 目录中的 JSON 文件直到数据迁移完成
- 更新根目录 Dockerfile（如果前端和后端共用）

---

## 实施顺序

1. **步骤 1-2**：项目初始化 + 配置（基础骨架）
2. **步骤 3-4**：数据模型 + Schema（数据层）
3. **步骤 8-9**：错误处理 + 应用工厂（应用骨架可运行）
4. **步骤 5**：Blueprint 路由（API 端点）
5. **步骤 6-7**：服务层 + SSE（核心业务逻辑）
6. **步骤 10**：数据迁移
7. **步骤 11**：部署配置
8. **步骤 12**：清理

## 验证方案

1. **启动测试**：`flask run` 启动成功，访问 `GET /api/health` 返回正常
2. **认证流程**：注册 → 登录 → 获取用户信息 → 登出
3. **解题流程**：`POST /api/parse` → `POST /api/solve` → 确认返回格式一致
4. **完整管线**：`POST /api/solve-problem` 端到端执行
5. **流式响应**：`POST /api/solve-stream` 确认 SSE 数据逐块返回
6. **历史记录**：CRUD 操作 + 分页查询
7. **数据迁移**：运行迁移脚本，验证旧用户可以登录，历史记录完整
8. **Docker 部署**：`docker build` + `docker run` 验证容器运行正常

## 需要注意的兼容性问题

- **API 响应格式**：必须与当前 Node.js 版本完全一致，前端无需修改
- **JWT Token**：Flask-JWT-Extended 生成的 token 格式与前端 `Authorization: Bearer <token>` 兼容
- **密码兼容**：迁移后旧用户首次登录需要兼容 SHA-256 旧密码，验证通过后自动升级为 Werkzeug 哈希
- **SSE 格式**：`data: {"content": "..."}\n\n` 和 `data: [DONE]\n\n` 保持一致
- **CORS**：保持与当前配置相同的 origin 和 credentials 设置
