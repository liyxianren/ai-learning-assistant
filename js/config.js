/**
 * 应用运行时配置
 * 
 * 在本地开发环境，使用默认值。
 * 在 Docker 部署环境，此文件会被 docker-entrypoint.sh 动态替换。
 */
window.AppConfig = {
    // 后端地址 - 本地开发
    API_BASE_URL: 'http://localhost:3000'
};
