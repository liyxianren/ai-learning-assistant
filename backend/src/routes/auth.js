/**
 * 认证路由
 * 处理用户注册、登录等认证相关接口
 */

const express = require('express');
const router = express.Router();
const userModel = require('../models/user');
const { generateToken, verifyToken } = require('../middleware/auth');

/**
 * POST /api/auth/register
 * 用户注册
 */
router.post('/register', async (req, res) => {
    try {
        const { username, password, confirmPassword } = req.body;

        // 验证必填字段
        if (!username || !password || !confirmPassword) {
            return res.status(400).json({
                success: false,
                error: '请填写所有必填字段'
            });
        }

        // 验证用户名格式
        if (username.length < 3 || username.length > 20) {
            return res.status(400).json({
                success: false,
                error: '用户名长度必须在 3-20 个字符之间'
            });
        }

        // 验证密码格式
        if (password.length < 6) {
            return res.status(400).json({
                success: false,
                error: '密码长度不能少于 6 个字符'
            });
        }

        // 验证两次密码是否一致
        if (password !== confirmPassword) {
            return res.status(400).json({
                success: false,
                error: '两次输入的密码不一致'
            });
        }

        // 创建用户
        const user = userModel.create({ username, password });

        res.status(201).json({
            success: true,
            message: '注册成功',
            data: {
                user: {
                    id: user.id,
                    username: user.username,
                    createdAt: user.createdAt
                }
            }
        });
    } catch (error) {
        if (error.message === '用户名已存在') {
            return res.status(409).json({
                success: false,
                error: error.message
            });
        }

        console.error('注册失败:', error);
        res.status(500).json({
            success: false,
            error: '注册失败，请稍后重试'
        });
    }
});

/**
 * POST /api/auth/login
 * 用户登录
 */
router.post('/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        // 验证必填字段
        if (!username || !password) {
            return res.status(400).json({
                success: false,
                error: '请填写用户名和密码'
            });
        }

        // 验证用户
        const user = userModel.verifyPassword(username, password);
        if (!user) {
            return res.status(401).json({
                success: false,
                error: '用户名或密码错误'
            });
        }

        // 更新最后登录时间
        userModel.updateLastLogin(user.id);

        // 生成 token
        const token = generateToken(user);

        res.json({
            success: true,
            message: '登录成功',
            data: {
                token,
                user: {
                    id: user.id,
                    username: user.username
                }
            }
        });
    } catch (error) {
        console.error('登录失败:', error);
        res.status(500).json({
            success: false,
            error: '登录失败，请稍后重试'
        });
    }
});

/**
 * GET /api/auth/me
 * 获取当前用户信息
 */
router.get('/me', verifyToken, async (req, res) => {
    try {
        const user = userModel.findById(req.user.id);

        if (!user) {
            return res.status(404).json({
                success: false,
                error: '用户不存在'
            });
        }

        res.json({
            success: true,
            data: {
                user: {
                    id: user.id,
                    username: user.username,
                    createdAt: user.createdAt,
                    lastLoginAt: user.lastLoginAt
                }
            }
        });
    } catch (error) {
        console.error('获取用户信息失败:', error);
        res.status(500).json({
            success: false,
            error: '获取用户信息失败'
        });
    }
});

/**
 * POST /api/auth/logout
 * 用户登出（客户端清除 token 即可，此接口仅作记录）
 */
router.post('/logout', (req, res) => {
    res.json({
        success: true,
        message: '登出成功'
    });
});

module.exports = router;
