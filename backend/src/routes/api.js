/**
 * API 路由配置
 */

const express = require('express');
const router = express.Router();
const problemController = require('../controllers/problemController');

// 健康检查
router.get('/health', (req, res) => {
    res.json({
        success: true,
        message: '服务正常运行',
        timestamp: new Date().toISOString()
    });
});

// 图像识别
router.post('/recognize', problemController.recognize);

// 题目解析
router.post('/parse', problemController.parse);

// 生成解答
router.post('/solve', problemController.solve);

// 完整解题流程
router.post('/solve-problem', problemController.solveProblem);

// 流式生成解答
router.post('/solve-stream', problemController.solveStream);

module.exports = router;
