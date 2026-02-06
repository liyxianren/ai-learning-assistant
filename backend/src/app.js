/**
 * AI 学习助手 - 后端服务入口
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const config = require('./config/config');
const apiRoutes = require('./routes/api');
const authRoutes = require('./routes/auth');
const historyRoutes = require('./routes/history');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

// 创建 Express 应用
const app = express();

// Zeabur/Nginx 反向代理场景，信任第一层代理头（X-Forwarded-For）
app.set('trust proxy', 1);

// 安全中间件
app.use(helmet());

// CORS 配置
app.use(cors(config.cors));

// 限流配置
const limiter = rateLimit({
    windowMs: config.limits.rateLimitWindowMs,
    max: config.limits.rateLimitMaxRequests,
    standardHeaders: true,
    legacyHeaders: false,
    message: {
        success: false,
        error: '请求过于频繁，请稍后再试'
    }
});
app.use(limiter);

// 请求体解析
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 请求日志
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - ${req.headers['origin'] || 'unknown'}`);
    if (req.method !== 'GET' && req.method !== 'HEAD') {
        console.log('Request body:', JSON.stringify(req.body, null, 2));
    }
    next();
});

// API 路由
app.use('/api', apiRoutes);

// 认证路由
app.use('/api/auth', authRoutes);

// 历史记录路由
app.use('/api/history', historyRoutes);

// 404 处理
app.use(notFoundHandler);

// 全局错误处理
app.use(errorHandler);

// 启动服务器
const PORT = config.server.port;
app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════╗
║                                                ║
║     AI 学习助手后端服务启动成功！              ║
║                                                ║
║     服务地址: http://localhost:${PORT}            ║
║     环境: ${config.server.env}                          ║
║                                                ║
╚════════════════════════════════════════════════╝
    `);
    console.log('可用接口:');
    console.log('  GET  /api/health        - 健康检查');
    console.log('  POST /api/recognize     - 图像识别');
    console.log('  POST /api/parse         - 题目解析');
    console.log('  POST /api/solve         - 生成解答');
    console.log('  POST /api/solve-problem - 完整解题流程');
    console.log('  POST /api/solve-stream  - 流式生成解答');
    console.log('\n等待请求...\n');
});

module.exports = app;
