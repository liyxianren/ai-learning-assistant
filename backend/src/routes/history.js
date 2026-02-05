/**
 * 历史记录路由
 * 处理用户解题历史的增删改查
 */

const express = require('express');
const router = express.Router();
const historyModel = require('../models/history');
const { verifyToken } = require('../middleware/auth');

/**
 * GET /api/history
 * 获取当前用户的历史记录列表
 */
router.get('/', verifyToken, async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        
        const result = historyModel.findByUserId(req.user.id, { page, limit });
        
        res.json({
            success: true,
            data: result
        });
    } catch (error) {
        console.error('获取历史记录失败:', error);
        res.status(500).json({
            success: false,
            error: '获取历史记录失败'
        });
    }
});

/**
 * GET /api/history/:id
 * 获取单条历史记录详情
 */
router.get('/:id', verifyToken, async (req, res) => {
    try {
        const record = historyModel.findById(req.params.id, req.user.id);
        
        if (!record) {
            return res.status(404).json({
                success: false,
                error: '记录不存在或无权限查看'
            });
        }
        
        res.json({
            success: true,
            data: { record }
        });
    } catch (error) {
        console.error('获取历史记录详情失败:', error);
        res.status(500).json({
            success: false,
            error: '获取历史记录详情失败'
        });
    }
});

/**
 * DELETE /api/history/:id
 * 删除单条历史记录
 */
router.delete('/:id', verifyToken, async (req, res) => {
    try {
        const success = historyModel.deleteById(req.params.id, req.user.id);
        
        if (!success) {
            return res.status(404).json({
                success: false,
                error: '记录不存在或无权限删除'
            });
        }
        
        res.json({
            success: true,
            message: '删除成功'
        });
    } catch (error) {
        console.error('删除历史记录失败:', error);
        res.status(500).json({
            success: false,
            error: '删除历史记录失败'
        });
    }
});

/**
 * DELETE /api/history
 * 清空当前用户所有历史记录
 */
router.delete('/', verifyToken, async (req, res) => {
    try {
        const success = historyModel.deleteByUserId(req.user.id);
        
        res.json({
            success: true,
            message: '清空历史记录成功'
        });
    } catch (error) {
        console.error('清空历史记录失败:', error);
        res.status(500).json({
            success: false,
            error: '清空历史记录失败'
        });
    }
});

module.exports = router;
