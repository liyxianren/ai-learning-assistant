/**
 * JWT 认证中间件
 */

const jwt = require('jsonwebtoken');
const config = require('../config/config');
const userModel = require('../models/user');

const JWT_SECRET = config.jwt?.secret || 'ai-learning-assistant-secret-key';
const JWT_EXPIRES_IN = '7d';

/**
 * 生成 JWT Token
 * @param {Object} user - 用户对象
 */
function generateToken(user) {
    const payload = {
        id: user.id,
        username: user.username
    };

    return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
}

/**
 * 验证 JWT Token 中间件
 */
function verifyToken(req, res, next) {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({
            success: false,
            error: '未提供认证令牌'
        });
    }

    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
        return res.status(401).json({
            success: false,
            error: '认证令牌格式无效'
        });
    }

    const token = parts[1];

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
        next();
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({
                success: false,
                error: '认证令牌已过期'
            });
        }

        return res.status(401).json({
            success: false,
            error: '认证令牌无效'
        });
    }
}

/**
 * 可选的认证中间件
 * 如果提供了 token 则验证，否则继续（不强制登录）
 */
function optionalAuth(req, res, next) {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return next();
    }

    const parts = authHeader.split(' ');
    if (parts.length === 2 && parts[0] === 'Bearer') {
        try {
            const token = parts[1];
            const decoded = jwt.verify(token, JWT_SECRET);
            req.user = decoded;
        } catch (error) {
            // token 无效，忽略错误
        }
    }

    next();
}

/**
 * 获取当前用户信息
 */
async function getCurrentUser(req, res, next) {
    if (req.user) {
        const user = userModel.findById(req.user.id);
        req.currentUser = user || null;
    }
    next();
}

module.exports = {
    generateToken,
    verifyToken,
    optionalAuth,
    getCurrentUser,
    JWT_SECRET
};
