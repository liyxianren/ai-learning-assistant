/**
 * 全局错误处理中间件
 */

const errorHandler = (err, req, res, next) => {
    console.error('错误:', err);

    // 默认错误响应
    const statusCode = err.statusCode || 500;
    const message = err.message || '服务器内部错误';

    res.status(statusCode).json({
        success: false,
        error: message,
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    });
};

// 404 处理
const notFoundHandler = (req, res) => {
    res.status(404).json({
        success: false,
        error: '接口不存在'
    });
};

module.exports = {
    errorHandler,
    notFoundHandler
};
