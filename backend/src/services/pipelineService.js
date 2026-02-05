/**
 * 多 Agent 流水线服务
 * 协调多个 AI Agent 的顺序执行
 */

const aiService = require('./aiService');
const historyModel = require('../models/history');

class PipelineService {
    /**
     * 执行完整的解题流程
     * @param {Object} input - 输入数据
     * @param {string} input.type - 输入类型: 'text' | 'image'
     * @param {string} input.content - 文本内容或 Base64 图片
     * @param {string} input.userId - 用户ID（可选）
     * @param {string} input.username - 用户名（可选）
     * @returns {Promise<Object>} 完整结果
     */
    async solveProblem(input) {
        const result = {
            success: true,
            data: {}
        };

        try {
            // Step 1: 图像识别（如果是图片输入）
            let problemText = '';
            if (input.type === 'image') {
                console.log('开始图像识别...');
                problemText = await aiService.recognizeImage(input.content);
                result.data.recognizedText = problemText;
                console.log('图像识别完成');
            } else {
                problemText = input.content;
                result.data.recognizedText = problemText;
            }

            // Step 2: 题目解析
            console.log('开始题目解析...');
            const parseResult = await aiService.parseProblem(problemText);
            result.data.parseResult = parseResult;
            console.log('题目解析完成:', parseResult.type, parseResult.difficulty);

            // Step 3: 生成解答
            console.log('开始生成解答...');
            const solution = await aiService.generateSolution(problemText, parseResult);
            result.data.solution = solution;
            console.log('解答生成完成');

            // Step 4: 保存历史记录（如果用户已登录）
            if (input.userId) {
                console.log('保存历史记录...');
                const historyRecord = historyModel.create({
                    userId: input.userId,
                    username: input.username,
                    question: problemText,
                    parseResult: parseResult,
                    solution: solution
                });
                result.data.historyId = historyRecord.id;
                console.log('历史记录已保存:', historyRecord.id);
            }

            return result;
        } catch (error) {
            console.error('解题流程失败:', error);
            return {
                success: false,
                error: error.message,
                data: result.data
            };
        }
    }

    /**
     * 仅执行图像识别
     * @param {string} imageBase64 - Base64 图片
     * @returns {Promise<Object>} 识别结果
     */
    async recognizeOnly(imageBase64) {
        try {
            const text = await aiService.recognizeImage(imageBase64);
            return {
                success: true,
                data: { text }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 仅执行题目解析
     * @param {string} text - 题目文本
     * @returns {Promise<Object>} 解析结果
     */
    async parseOnly(text) {
        try {
            const parseResult = await aiService.parseProblem(text);
            return {
                success: true,
                data: parseResult
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 仅执行解答生成
     * @param {string} text - 题目文本
     * @param {Object} parseResult - 解析结果
     * @returns {Promise<Object>} 解答结果
     */
    async solveOnly(text, parseResult) {
        try {
            const solution = await aiService.generateSolution(text, parseResult);
            return {
                success: true,
                data: solution
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 流式生成解答
     * @param {string} text - 题目文本
     * @param {Object} parseResult - 解析结果
     * @param {Function} onData - 数据回调
     */
    async solveStream(text, parseResult, onData) {
        try {
            await aiService.generateSolutionStream(text, parseResult, onData);
        } catch (error) {
            onData(null, true, error.message);
        }
    }
}

module.exports = new PipelineService();
