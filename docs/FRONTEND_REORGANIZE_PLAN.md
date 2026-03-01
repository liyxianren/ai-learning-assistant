# 前端文件整理实施方案

## 背景

当前前端静态文件（HTML、CSS、JS）散落在项目根目录，与后端代码、文档、部署配置混在一起，结构不清晰。需要将前端文件集中到 `frontend/` 目录中，保持与 `backend/` 对称的项目结构。

## 用户选择汇总

| 决策项 | 选择 |
|--------|------|
| 前端目录名称 | `frontend/` |
| 部署配置（Dockerfile 等） | 保留在项目根目录 |
| 文档文件 | 移入 `docs/` 目录 |
| 空目录 assets/、config/ | 移入前端目录 |
| 前端子目录结构 | 保持现有 css/、js/ 平铺 |
| .env.example | 保留在根目录 |

## 当前结构

```
项目根目录/
├── home.html              ← 前端文件散落在根目录
├── index.html             ←
├── css/style.css          ←
├── js/main.js             ←
├── js/user.js             ←
├── assets/                ← 空目录
├── config/                ← 空目录
├── nginx.conf             ← 部署配置
├── Dockerfile             ← 部署配置
├── .dockerignore          ← 部署配置
├── .env.example           ← 环境变量模板
├── .gitignore
├── backend/               ← 后端代码
├── ai学习助手.md           ← 文档散落
├── chatglm_api.md         ←
├── 前端开发TODO.md         ←
├── 后端开发TODO.md         ←
├── 学习助手.docx           ←
├── 开发计划.md             ←
└── FLASK_REFACTOR_PLAN.md ←
```

## 目标结构

```
项目根目录/
├── frontend/                  # 前端代码（集中管理）
│   ├── home.html              #   落地页 / 登录注册
│   ├── index.html             #   主应用页
│   ├── css/
│   │   └── style.css          #   样式
│   ├── js/
│   │   ├── main.js            #   主应用逻辑
│   │   └── user.js            #   用户认证逻辑
│   ├── assets/                #   静态资源（预留）
│   └── config/                #   前端配置（预留）
├── backend/                   # 后端代码
├── docs/                      # 项目文档（集中管理）
│   ├── ai学习助手.md
│   ├── chatglm_api.md
│   ├── 前端开发TODO.md
│   ├── 后端开发TODO.md
│   ├── 学习助手.docx
│   ├── 开发计划.md
│   └── FLASK_REFACTOR_PLAN.md
├── Dockerfile                 # 部署配置（根目录）
├── nginx.conf
├── .dockerignore
├── .env.example
└── .gitignore
```

## 分步实施

### 步骤 1：创建目录

```bash
mkdir -p frontend/css frontend/js frontend/assets frontend/config
mkdir -p docs
```

### 步骤 2：移动前端文件

```bash
# HTML 页面
mv home.html frontend/
mv index.html frontend/

# CSS
mv css/style.css frontend/css/
rmdir css

# JavaScript
mv js/main.js frontend/js/
mv js/user.js frontend/js/
rmdir js

# 空目录
rmdir assets config    # 原位置删除（已在步骤1中新建到 frontend/ 下）
```

### 步骤 3：移动文档文件

```bash
mv ai学习助手.md docs/
mv chatglm_api.md docs/
mv 前端开发TODO.md docs/
mv 后端开发TODO.md docs/
mv 学习助手.docx docs/
mv 开发计划.md docs/
mv FLASK_REFACTOR_PLAN.md docs/
```

### 步骤 4：更新 Dockerfile

前端文件已移入 `frontend/`，需更新 COPY 源路径：

```dockerfile
# 修改前
COPY . /usr/share/nginx/html

# 修改后
COPY frontend/ /usr/share/nginx/html
```

完整 Dockerfile：

```dockerfile
FROM nginx:alpine
COPY frontend/ /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 步骤 5：更新 .dockerignore

只需保留与根目录相关的排除规则，确保 `frontend/` 不被意外排除：

```dockerignore
.git
.gitignore

backend/
docs/

.env
.env.*

.vscode
.idea
.trae
.claude

*.md
!frontend/**

*.log
*.tmp
.DS_Store
```

### 步骤 6：验证

前端文件内部的相对路径（`css/style.css`、`js/user.js`、`js/main.js`、`home.html`）不需要修改，因为它们在 `frontend/` 内的相对位置关系保持不变。

验证清单：

- [ ] `docker build -t test .` 构建成功
- [ ] `docker run -p 8080:80 test` 启动后访问 `http://localhost:8080` 能到达 home.html
- [ ] 登录后跳转到 index.html 正常
- [ ] CSS 样式加载正常
- [ ] JS 功能（登录、注册、解题）正常

## 不需要修改的文件

以下文件无需改动，因为相对路径关系在 `frontend/` 内部保持一致：

| 文件 | 引用 | 是否需要改 |
|------|------|-----------|
| `frontend/home.html` | `css/style.css`, `js/user.js` | 否 |
| `frontend/index.html` | `css/style.css`, `js/user.js`, `js/main.js`, `home.html` | 否 |
| `nginx.conf` | 只配置 nginx 内部路径 | 否 |
| `frontend/js/user.js` | 只用 API URL，无文件路径 | 否 |

## 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `Dockerfile` | `COPY .` → `COPY frontend/` |
| `.dockerignore` | 更新排除规则，确保 frontend/ 和 nginx.conf 被包含 |
