/**
 * AI 服务层
 * 封装多模态模型和文本模型的 API 调用
 * 使用 ChatGLM 作为主文本模型
 */

const axios = require('axios');
const config = require('../config/config');
const chatglmService = require('./chatglmService');

class AIService {
    constructor() {
        this.multimodalConfig = config.multimodal;
        // 使用 ChatGLM 作为主要文本模型
        this.textModel = chatglmService;
    }

    /**
     * 图像识别 - 使用 GLM-4.6V 多模态模型识别图片中的题目
     * @param {string} imageBase64 - Base64 编码的图片（支持 data:image/xxx;base64,... 格式）
     * @returns {Promise<string>} 识别的文本
     */
    async recognizeImage(imageBase64) {
        try {
            // 确保图片格式正确（GLM-4.6V 需要完整的 data URL）
            let imageUrl = imageBase64;
            if (!imageBase64.startsWith('data:')) {
                // 如果没有 data: 前缀，尝试添加（默认 PNG）
                imageUrl = `data:image/png;base64,${imageBase64}`;
            }

            console.log(`使用多模态模型: ${this.multimodalConfig.model}`);
            console.log(`API URL: ${this.multimodalConfig.apiUrl}`);

            const response = await axios.post(
                this.multimodalConfig.apiUrl,
                {
                    model: this.multimodalConfig.model,
                    messages: [
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'image_url',
                                    image_url: {
                                        url: imageUrl
                                    }
                                },
                                {
                                    type: 'text',
                                    text: '请仔细识别图片中的题目内容，提取所有文字、数字、公式。保持题目的原始格式，如果是数学题保留公式表达式。只输出识别到的文本内容，不要添加任何解释或说明。'
                                }
                            ]
                        }
                    ],
                    max_tokens: 2000,
                    temperature: 0.1  // 低温度以提高识别准确性
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.multimodalConfig.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: this.multimodalConfig.timeout
                }
            );

            const content = response.data.choices[0].message.content;
            console.log('图像识别成功，识别到的文本长度:', content.length);
            return content;
        } catch (error) {
            console.error('图像识别失败:', error.response?.data || error.message);
            const errorMsg = error.response?.data?.error?.message || error.message;
            throw new Error(`图像识别失败: ${errorMsg}`);
        }
    }

    /**
     * 题目解析 - 分析题目类型、知识点、难度
     * 使用 ChatGLM 实现
     * @param {string} text - 题目文本
     * @returns {Promise<Object>} 解析结果
     */
    async parseProblem(text) {
        return this.textModel.parseProblem(text);
    }

    /**
     * 生成解答 - 根据题目和解析结果生成详细解答
     * 使用 ChatGLM 实现
     * @param {string} text - 题目文本
     * @param {Object} parseResult - 解析结果
     * @returns {Promise<Object>} 解答结果
     */
    async generateSolution(text, parseResult) {
        return this.textModel.generateSolution(text, parseResult);
    }

    /**
     * 流式生成解答
     * 使用 ChatGLM 实现
     * @param {string} text - 题目文本
     * @param {Object} parseResult - 解析结果
     * @param {Function} onData - 数据回调
     */
    async generateSolutionStream(text, parseResult, onData) {
        return this.textModel.generateSolutionStream(text, parseResult, onData);
    }

    /**
     * 解析解答内容
     * @param {string} content - AI 返回的内容
     * @returns {Object} 结构化的解答
     */
    parseSolutionContent(content) {
        return this.textModel.parseSolutionContent(content);
    }

    /**
     * 健康检查
     * @returns {Promise<Object>} 各服务健康状态
     */
    async healthCheck() {
        const results = {
            multimodal: false,
            multimodalModel: this.multimodalConfig.model,
            chatglm: false
        };

        // 检查多模态模型 (GLM-4.6V)
        try {
            // 对于视觉模型，发送简单文本请求进行连通性测试
            await axios.post(
                this.multimodalConfig.apiUrl,
                {
                    model: this.multimodalConfig.model,
                    messages: [{
                        role: 'user',
                        content: [
                            { type: 'text', text: '你好' }
                        ]
                    }],
                    max_tokens: 10
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.multimodalConfig.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 15000
                }
            );
            results.multimodal = true;
        } catch (error) {
            console.error('多模态模型健康检查失败:', error.response?.data || error.message);
        }

        // 检查 ChatGLM
        results.chatglm = await this.textModel.healthCheck();

        return results;
    }
}

module.exports = new AIService();
