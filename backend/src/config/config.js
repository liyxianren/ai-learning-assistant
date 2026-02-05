/**
 * 配置文件
 * 集中管理所有环境变量和配置项
 */

require('dotenv').config();

const config = {
    // 服务器配置
    server: {
        port: process.env.PORT || 3000,
        env: process.env.NODE_ENV || 'development',
    },

    // 多模态模型配置（图像识别）- 使用 GLM-4.6V
    multimodal: {
        apiKey: process.env.MULTIMODAL_API_KEY || process.env.CHATGLM_API_KEY,
        apiUrl: process.env.MULTIMODAL_API_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        model: process.env.MULTIMODAL_MODEL || 'glm-4.6v-flashx',
        timeout: parseInt(process.env.REQUEST_TIMEOUT) || 60000,
    },

    // ChatGLM 配置（题目解析和解答）- 主用
    chatglm: {
        apiKey: process.env.CHATGLM_API_KEY,
        apiUrl: process.env.CHATGLM_API_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        model: process.env.CHATGLM_MODEL || 'glm-4.7',
        enableThinking: process.env.CHATGLM_ENABLE_THINKING === 'true',
        timeout: parseInt(process.env.REQUEST_TIMEOUT) || 60000,
    },

    // DeepSeek 配置（备选方案）
    deepseek: {
        apiKey: process.env.DEEPSEEK_API_KEY,
        apiUrl: process.env.DEEPSEEK_API_URL || 'https://api.deepseek.com/v1/chat/completions',
        model: process.env.DEEPSEEK_MODEL || 'deepseek-chat',
        timeout: parseInt(process.env.REQUEST_TIMEOUT) || 60000,
    },

    // 通义千问配置（备选）
    qwen: {
        apiKey: process.env.QWEN_API_KEY,
        apiUrl: process.env.QWEN_API_URL,
        model: process.env.QWEN_MODEL || 'qwen-vl-plus',
    },

    // JWT 配置
    jwt: {
        secret: process.env.JWT_SECRET || 'ai-learning-assistant-secret-key',
        expiresIn: process.env.JWT_EXPIRES_IN || '7d',
    },

    // 请求限制
    limits: {
        maxImageSize: parseInt(process.env.MAX_IMAGE_SIZE) || 5 * 1024 * 1024, // 5MB
        rateLimitWindowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 60000, // 1分钟
        rateLimitMaxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 30,
    },

    // CORS 配置
    cors: {
        // 生产环境允许同源请求，开发环境允许本地访问
        origin: process.env.CORS_ORIGIN || (process.env.NODE_ENV === 'production' ? true : 'http://localhost:8080'),
        credentials: true,
    },

    // 验证配置
    validate() {
        // ChatGLM API 密钥是必需的（同时用于文本和多模态）
        const required = [
            'chatglm.apiKey',
        ];

        const missing = required.filter(key => {
            const keys = key.split('.');
            let value = this;
            for (const k of keys) {
                value = value[k];
                if (!value) return true;
            }
            return false;
        });

        if (missing.length > 0) {
            console.warn('警告: 以下配置项未设置:', missing.join(', '));
            console.warn('某些功能可能无法正常工作');
        }

        // 显示当前多模态模型配置
        console.log(`多模态模型: ${this.multimodal.model}`);
        console.log(`多模态 API: ${this.multimodal.apiUrl}`);
    }
};

// 验证配置
config.validate();

module.exports = config;
