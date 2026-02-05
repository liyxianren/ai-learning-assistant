/**
 * ChatGLM 服务封装
 * 封装智谱 AI GLM-4.7 模型的 API 调用
 */

const axios = require('axios');
const config = require('../config/config');

class ChatGLMService {
    constructor() {
        this.apiKey = config.chatglm.apiKey;
        this.apiUrl = config.chatglm.apiUrl;
        // 使用轻量版模型，响应更快
        this.model = 'glm-4.7-flashx';
        this.enableThinking = false; // 关闭思考模式，提高速度
        this.timeout = config.chatglm.timeout;
    }

    /**
     * 基础请求方法
     * @param {Object} data - 请求数据
     * @param {boolean} stream - 是否流式输出
     * @returns {Promise} 响应结果
     */
    async request(data, stream = false) {
        const headers = {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
        };

        const requestConfig = {
            headers,
            timeout: this.timeout,
            responseType: stream ? 'stream' : 'json'
        };

        try {
            const response = await axios.post(this.apiUrl, data, requestConfig);
            return response;
        } catch (error) {
            console.error('ChatGLM API 请求失败:', error.message);
            if (error.response) {
                console.error('错误详情:', error.response.data);
            }
            throw new Error(`ChatGLM API 错误: ${error.message}`);
        }
    }

    /**
     * 题目解析 - 分析题目类型、知识点、难度
     * @param {string} text - 题目文本
     * @returns {Promise<Object>} 解析结果
     */
    async parseProblem(text) {
        const prompt = `你是一位经验丰富的教师，请分析以下题目：

题目：${text}

请按以下 JSON 格式输出分析结果（只输出 JSON，不要添加 markdown 代码块标记或其他内容）：

{
    "type": "题目类型（选择/填空/解答/判断）",
    "subject": "所属学科",
    "knowledgePoints": ["知识点1", "知识点2"],
    "difficulty": "难度等级（简单/中等/困难）",
    "prerequisites": ["前置知识1", "前置知识2"]
}`;

        const requestData = {
            model: this.model,
            messages: [
                {
                    role: 'system',
                    content: '你是一位专业的教育分析师，擅长分析各类学科题目。你必须只输出纯 JSON 格式，不要添加任何 markdown 标记或其他文字。'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: 0.1,
            max_tokens: 1024
        };

        // 启用思考模式（如果配置允许）
        if (this.enableThinking) {
            requestData.thinking = { type: 'enabled' };
        }

        const response = await this.request(requestData);
        
        // 检查响应结构
        console.log('ChatGLM 完整响应:', JSON.stringify(response.data, null, 2));
        
        if (!response.data || !response.data.choices || !response.data.choices[0]) {
            console.error('ChatGLM 响应结构异常:', response.data);
            throw new Error('ChatGLM 响应结构异常');
        }
        
        let content = response.data.choices[0].message?.content;
        
        if (!content || content.trim() === '') {
            console.error('ChatGLM 返回内容为空');
            throw new Error('ChatGLM 返回内容为空');
        }
        
        console.log('ChatGLM 原始返回:', content);
        
        // 尝试多种方式提取 JSON
        let jsonStr = content;
        
        // 1. 尝试提取 markdown 代码块
        const codeBlockMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
        if (codeBlockMatch) {
            jsonStr = codeBlockMatch[1].trim();
        }
        
        // 2. 尝试提取花括号内容
        const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            jsonStr = jsonMatch[0];
        }
        
        // 3. 清理可能的特殊字符
        jsonStr = jsonStr.trim();
        
        try {
            return JSON.parse(jsonStr);
        } catch (e) {
            console.error('JSON 解析失败，尝试清理后重试');
            console.error('原始内容:', content);
            console.error('提取的字符串:', jsonStr);
            
            // 尝试移除可能的 BOM 或其他不可见字符
            jsonStr = jsonStr.replace(/^\uFEFF/, '').trim();
            
            try {
                return JSON.parse(jsonStr);
            } catch (e2) {
                throw new Error(`解析结果格式错误: ${e2.message}`);
            }
        }
    }

    /**
     * 生成解答 - 根据题目和解析结果生成详细解答
     * @param {string} text - 题目文本
     * @param {Object} parseResult - 解析结果
     * @returns {Promise<Object>} 解答结果
     */
    async generateSolution(text, parseResult) {
        const prompt = `你是一位耐心的 AI 教师，请为学生提供详细的解答。

题目：${text}

题目类型：${parseResult.type}
所属学科：${parseResult.subject}
知识点：${parseResult.knowledgePoints.join('、')}
难度等级：${parseResult.difficulty}

请按以下格式输出解答：

【解题思路】
分析题目的解题思路和方法

【详细步骤】
1. 步骤一
2. 步骤二
3. 步骤三
...

【最终答案】
给出简洁明确的答案

【知识总结】
总结本题涉及的知识点和解题技巧`;

        const requestData = {
            model: this.model,
            messages: [
                {
                    role: 'system',
                    content: '你是一位优秀的 AI 教师，擅长用清晰、易懂的方式讲解题目。你会引导学生思考，不仅给出答案，还会解释为什么这样做。'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: 0.7,
            max_tokens: 1024
        };

        // 启用思考模式（如果配置允许）
        if (this.enableThinking) {
            requestData.thinking = { type: 'enabled' };
        }

        const response = await this.request(requestData);
        const content = response.data.choices[0].message.content;
        
        // 解析结构化内容
        return this.parseSolutionContent(content);
    }

    /**
     * 流式生成解答
     * @param {string} text - 题目文本
     * @param {Object} parseResult - 解析结果
     * @param {Function} onData - 数据回调 (data, done, error)
     */
    async generateSolutionStream(text, parseResult, onData) {
        const prompt = `你是一位耐心的 AI 教师，请为学生提供详细的解答。

题目：${text}
题目类型：${parseResult.type}
所属学科：${parseResult.subject}
知识点：${parseResult.knowledgePoints.join('、')}

请提供详细的解题思路、步骤、答案和知识总结。`;

        const requestData = {
            model: this.model,
            messages: [
                {
                    role: 'system',
                    content: '你是一位优秀的 AI 教师，擅长用清晰、易懂的方式讲解题目。'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: 0.7,
            max_tokens: 2000,
            stream: true
        };

        // 启用思考模式（如果配置允许）
        if (this.enableThinking) {
            requestData.thinking = { type: 'enabled' };
        }

        try {
            const response = await this.request(requestData, true);

            response.data.on('data', (chunk) => {
                const lines = chunk.toString().split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            onData(null, true, null);
                            return;
                        }
                        try {
                            const parsed = JSON.parse(data);
                            const delta = parsed.choices[0]?.delta;
                            
                            // 处理思考内容
                            if (delta?.reasoning_content) {
                                // 思考内容可以选择性输出
                                // onData(`[思考] ${delta.reasoning_content}`, false, null);
                            }
                            
                            // 处理正式内容
                            if (delta?.content) {
                                onData(delta.content, false, null);
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                }
            });

            response.data.on('end', () => {
                onData(null, true, null);
            });

            response.data.on('error', (error) => {
                onData(null, true, error.message);
            });
        } catch (error) {
            onData(null, true, error.message);
        }
    }

    /**
     * 解析解答内容
     * @param {string} content - AI 返回的内容
     * @returns {Object} 结构化的解答
     */
    parseSolutionContent(content) {
        const result = {
            thinking: '',
            steps: [],
            answer: '',
            summary: ''
        };

        // 提取解题思路
        const thinkingMatch = content.match(/【解题思路】\s*\n?([\s\S]*?)(?=【|$)/);
        if (thinkingMatch) {
            result.thinking = thinkingMatch[1].trim();
        }

        // 提取详细步骤
        const stepsMatch = content.match(/【详细步骤】\s*\n?([\s\S]*?)(?=【|$)/);
        if (stepsMatch) {
            const stepsText = stepsMatch[1].trim();
            result.steps = stepsText
                .split('\n')
                .filter(line => line.trim())
                .map(line => line.replace(/^\d+\.\s*/, '').trim());
        }

        // 提取最终答案
        const answerMatch = content.match(/【最终答案】\s*\n?([\s\S]*?)(?=【|$)/);
        if (answerMatch) {
            result.answer = answerMatch[1].trim();
        }

        // 提取知识总结
        const summaryMatch = content.match(/【知识总结】\s*\n?([\s\S]*?)(?=【|$)/);
        if (summaryMatch) {
            result.summary = summaryMatch[1].trim();
        }

        return result;
    }

    /**
     * 健康检查
     * @returns {Promise<boolean>} 是否健康
     */
    async healthCheck() {
        try {
            const requestData = {
                model: this.model,
                messages: [
                    {
                        role: 'user',
                        content: '你好'
                    }
                ],
                max_tokens: 10
            };

            await this.request(requestData);
            return true;
        } catch (error) {
            console.error('ChatGLM 健康检查失败:', error.message);
            return false;
        }
    }
}

module.exports = new ChatGLMService();
