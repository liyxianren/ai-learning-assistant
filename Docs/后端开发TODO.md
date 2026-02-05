# 后端开发 TODO.md

## 项目概述

后端服务作为 AI 学习助手的 API 代理层，负责：
1. 保护 API 密钥安全（不在前端暴露）
2. 处理多模态模型和文本模型的调用
3. 实现多 Agent 协作流程
4. 提供流式输出支持
5. 可选：用户管理、历史记录存储、家长监督功能

---

## 技术选型

### 方案一：轻量级（推荐初期使用）
- **Node.js + Express** - 轻量快速，适合原型开发
- 或 **Python + FastAPI** - 异步性能优秀

### 方案二：完整功能
- **Node.js + Express + MongoDB** - 需要数据库时
- **Python + FastAPI + PostgreSQL** - 完整后端架构

### 本计划采用方案一（可扩展）

---

## 项目结构

```
backend/
├── src/
│   ├── config/
│   │   └── config.js           # 配置文件
│   ├── controllers/
│   │   ├── imageController.js  # 图像识别控制
│   │   ├── parseController.js  # 题目解析控制
│   │   └── solveController.js  # 解答生成控制
│   ├── services/
│   │   ├── aiService.js        # AI 模型调用服务
│   │   └── pipelineService.js  # 多 Agent 流水线服务
│   ├── routes/
│   │   └── api.js              # API 路由
│   ├── middleware/
│   │   ├── errorHandler.js     # 错误处理
│   │   └── rateLimiter.js      # 限流中间件
│   └── app.js                  # 应用入口
├── .env                        # 环境变量
├── package.json
└── README.md
```

---

## 任务清单

### 阶段一：项目初始化

- [ ] 1.1 创建项目结构
  - [ ] 初始化 Node.js 项目
  - [ ] 创建目录结构
  - [ ] 安装基础依赖

- [ ] 1.2 基础配置
  - [ ] 创建 .env 文件
  - [ ] 配置 API 密钥（多模态模型、DeepSeek）
  - [ ] 配置服务器端口
  - [ ] 配置 CORS

- [ ] 1.3 基础服务搭建
  - [ ] 创建 Express 应用
  - [ ] 配置中间件
  - [ ] 创建基础路由
  - [ ] 健康检查接口

---

### 阶段二：AI 服务封装

- [ ] 2.1 多模态模型服务
  - [ ] 封装图像识别 API 调用
  - [ ] 支持 Base64 图片输入
  - [ ] Prompt 模板管理
  - [ ] 响应解析

- [ ] 2.2 文本模型服务
  - [ ] 封装 DeepSeek API 调用
  - [ ] 支持流式输出
  - [ ] Prompt 模板管理
  - [ ] 响应解析

- [ ] 2.3 统一 AI 服务层
  - [ ] 抽象 AI 调用接口
  - [ ] 错误重试机制
  - [ ] 超时处理
  - [ ] 日志记录

---

### 阶段三：多 Agent 流水线

- [ ] 3.1 Agent 1: 图像识别
  - [ ] 接收图片数据
  - [ ] 调用多模态模型
  - [ ] 提取题目文本
  - [ ] 返回结构化数据

- [ ] 3.2 Agent 2: 题目解析
  - [ ] 接收题目文本
  - [ ] 调用文本模型
  - [ ] 解析题目类型、知识点、难度
  - [ ] 返回 JSON 格式结果

- [ ] 3.3 Agent 3: 解答生成
  - [ ] 接收题目和解析结果
  - [ ] 调用文本模型
  - [ ] 生成详细解答
  - [ ] 支持流式输出

- [ ] 3.4 流水线编排
  - [ ] 顺序执行控制
  - [ ] 数据传递
  - [ ] 错误中断处理
  - [ ] 超时控制

---

### 阶段四：API 接口开发

- [ ] 4.1 单 Agent 接口
  - [ ] POST /api/recognize - 图像识别
  - [ ] POST /api/parse - 题目解析
  - [ ] POST /api/solve - 解答生成

- [ ] 4.2 完整流程接口
  - [ ] POST /api/solve-problem - 完整解题流程
  - [ ] 支持文字输入
  - [ ] 支持图片输入
  - [ ] 返回完整结果

- [ ] 4.3 流式接口
  - [ ] POST /api/solve-stream - 流式解答
  - [ ] SSE 实现
  - [ ] 分段返回结果

---

### 阶段五：中间件与工具

- [ ] 5.1 错误处理
  - [ ] 全局错误捕获
  - [ ] 自定义错误类
  - [ ] 错误响应格式

- [ ] 5.2 限流与防护
  - [ ] 请求频率限制
  - [ ] IP 黑名单
  - [ ] 请求大小限制

- [ ] 5.3 日志系统
  - [ ] 请求日志
  - [ ] 错误日志
  - [ ] AI 调用日志

- [ ] 5.4 输入验证
  - [ ] 参数校验
  - [ ] 图片大小验证
  - [ ] 内容安全过滤

---

### 阶段六：Prompt 管理

- [ ] 6.1 Prompt 模板
  - [ ] 图像识别 Prompt
  - [ ] 题目解析 Prompt
  - [ ] 解答生成 Prompt

- [ ] 6.2 Prompt 优化
  - [ ] 版本管理
  - [ ] A/B 测试支持
  - [ ] 动态调整

---

### 阶段七：数据存储（可选扩展）

- [ ] 7.1 数据库设计
  - [ ] 用户表
  - [ ] 查询记录表
  - [ ] 历史记录表

- [ ] 7.2 历史记录接口
  - [ ] GET /api/history - 获取历史记录
  - [ ] POST /api/history - 保存记录
  - [ ] 不可删除逻辑

- [ ] 7.3 家长监督接口
  - [ ] GET /api/summary - 每日汇总
  - [ ] 邮件发送服务

---

### 阶段八：部署与运维

- [ ] 8.1 部署配置
  - [ ] Dockerfile
  - [ ] docker-compose.yml
  - [ ] 环境变量配置

- [ ] 8.2 监控与告警
  - [ ] 健康检查
  - [ ] 性能监控
  - [ ] 错误告警

- [ ] 8.3 文档
  - [ ] API 文档（Swagger/OpenAPI）
  - [ ] 部署文档
  - [ ] 使用说明

---

## API 接口设计

### 1. 图像识别

```http
POST /api/recognize
Content-Type: application/json

{
  "image": "base64_encoded_image_string"
}

Response:
{
  "success": true,
  "data": {
    "text": "识别的题目文本"
  }
}
```

### 2. 题目解析

```http
POST /api/parse
Content-Type: application/json

{
  "text": "题目文本"
}

Response:
{
  "success": true,
  "data": {
    "type": "选择题",
    "subject": "数学",
    "knowledgePoints": ["一元二次方程", "求根公式"],
    "difficulty": "中等",
    "prerequisites": ["方程基础", "平方根运算"]
  }
}
```

### 3. 解答生成

```http
POST /api/solve
Content-Type: application/json

{
  "text": "题目文本",
  "parseResult": { ... }
}

Response:
{
  "success": true,
  "data": {
    "thinking": "解题思路...",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "answer": "最终答案",
    "summary": "知识总结"
  }
}
```

### 4. 完整流程

```http
POST /api/solve-problem
Content-Type: application/json

{
  "type": "text",  // 或 "image"
  "content": "题目文本或base64图片"
}

Response:
{
  "success": true,
  "data": {
    "recognizedText": "识别的文本（图片输入时）",
    "parseResult": { ... },
    "solution": { ... }
  }
}
```

### 5. 流式解答

```http
POST /api/solve-stream
Content-Type: application/json

{
  "text": "题目文本",
  "parseResult": { ... }
}

Response: SSE Stream
```

---

## 环境变量配置

```env
# 服务器配置
PORT=3000
NODE_ENV=development

# AI 模型 API 密钥
MULTIMODAL_API_KEY=your_multimodal_api_key
MULTIMODAL_API_URL=https://api.multimodal-model.com

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_URL=https://api.deepseek.com

# 可选：数据库配置
# DATABASE_URL=mongodb://localhost:27017/ai-learning-assistant

# 可选：Redis 缓存
# REDIS_URL=redis://localhost:6379
```

---

## 依赖清单

```json
{
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0",
    "express-rate-limit": "^6.0.0",
    "helmet": "^7.0.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0"
  }
}
```

---

## 开发顺序建议

1. 搭建基础 Express 服务
2. 封装 AI 模型调用服务
3. 实现单 Agent 接口
4. 实现多 Agent 流水线
5. 添加流式输出支持
6. 完善中间件（错误处理、限流等）
7. 添加日志和监控
8. 编写文档和部署配置

---

## 注意事项

1. **API 密钥安全**: 绝不暴露在前端，所有调用通过后端代理
2. **错误处理**: 每个环节都要有降级方案
3. **超时控制**: AI 调用可能较慢，设置合理超时时间
4. **流式输出**: 提升用户体验，减少等待感
5. **日志记录**: 便于问题排查和优化
