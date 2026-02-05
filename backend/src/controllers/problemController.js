/**
 * 题目控制器
 * 处理题目相关的 HTTP 请求
 */

const pipelineService = require('../services/pipelineService');
const config = require('../config/config');
const { optionalAuth, getCurrentUser } = require('../middleware/auth');
const userModel = require('../models/user');

class ProblemController {
    /**
     * 图像识别
     * POST /api/recognize
     */
    async recognize(req, res) {
        try {
            const { image } = req.body;

            if (!image) {
                return res.status(400).json({
                    success: false,
                    error: '缺少图片数据'
                });
            }

            // 检查图片大小
            const sizeInBytes = Buffer.from(image.split(',')[1] || image, 'base64').length;
            if (sizeInBytes > config.limits.maxImageSize) {
                return res.status(400).json({
                    success: false,
                    error: '图片大小超过限制'
                });
            }

            const result = await pipelineService.recognizeOnly(image);
            res.json(result);
        } catch (error) {
            console.error('识别接口错误:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * 题目解析
     * POST /api/parse
     */
    async parse(req, res) {
        try {
            const { text, userId } = req.body;

            if (!text || text.trim() === '') {
                return res.status(400).json({
                    success: false,
                    error: '缺少题目文本'
                });
            }

            const result = await pipelineService.parseOnly(text);
            res.json(result);
        } catch (error) {
            console.error('解析接口错误:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * 生成解答
     * POST /api/solve
     */
    async solve(req, res) {
        try {
            const { text, parseResult, userId } = req.body;

            if (!text || text.trim() === '') {
                return res.status(400).json({
                    success: false,
                    error: '缺少题目文本'
                });
            }

            if (!parseResult) {
                return res.status(400).json({
                    success: false,
                    error: '缺少解析结果'
                });
            }

            const result = await pipelineService.solveOnly(text, parseResult);
            res.json(result);
        } catch (error) {
            console.error('解答接口错误:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * 完整解题流程
     * POST /api/solve-problem
     */
    async solveProblem(req, res) {
        try {
            const { type, content, userId } = req.body;

            if (!type || !content) {
                return res.status(400).json({
                    success: false,
                    error: '缺少必要参数'
                });
            }

            if (type !== 'text' && type !== 'image') {
                return res.status(400).json({
                    success: false,
                    error: '无效的输入类型'
                });
            }

            // 获取用户信息（如果已登录）
            let username = null;
            if (req.user) {
                const user = userModel.findById(req.user.id);
                if (user) {
                    username = user.username;
                }
            }

            const result = await pipelineService.solveProblem({ 
                type, 
                content,
                userId: req.user?.id,
                username
            });
            res.json(result);
        } catch (error) {
            console.error('解题接口错误:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * 流式生成解答
     * POST /api/solve-stream
     */
    async solveStream(req, res) {
        try {
            const { text, parseResult } = req.body;

            if (!text || !parseResult) {
                return res.status(400).json({
                    success: false,
                    error: '缺少必要参数'
                });
            }

            // 设置 SSE 头
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');

            await pipelineService.solveStream(text, parseResult, (data, done, error) => {
                if (error) {
                    res.write(`data: ${JSON.stringify({ error })}\n\n`);
                    res.end();
                    return;
                }

                if (done) {
                    res.write(`data: [DONE]\n\n`);
                    res.end();
                    return;
                }

                res.write(`data: ${JSON.stringify({ content: data })}\n\n`);
            });
        } catch (error) {
            console.error('流式解答接口错误:', error);
            res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
            res.end();
        }
    }
}

module.exports = new ProblemController();
