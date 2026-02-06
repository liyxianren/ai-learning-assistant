/**
 * 用户状态管理
 * 处理用户认证、登录状态等
 */

const API_BASE = 'http://localhost:3000';

const UserManager = {
    tokenKey: 'ai_learning_assistant_token',
    userKey: 'ai_learning_assistant_user',

    /**
     * 获取 Token
     */
    getToken() {
        return localStorage.getItem(this.tokenKey);
    },

    /**
     * 保存 Token
     * @param {string} token
     */
    setToken(token) {
        localStorage.setItem(this.tokenKey, token);
    },

    /**
     * 删除 Token
     */
    removeToken() {
        localStorage.removeItem(this.tokenKey);
    },

    /**
     * 获取保存的用户信息
     */
    getSavedUser() {
        const userData = localStorage.getItem(this.userKey);
        return userData ? JSON.parse(userData) : null;
    },

    /**
     * 保存用户信息
     * @param {Object} user
     */
    setUser(user) {
        localStorage.setItem(this.userKey, JSON.stringify(user));
    },

    /**
     * 删除用户信息
     */
    removeUser() {
        localStorage.removeItem(this.userKey);
    },

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return !!this.getToken() && !!this.getSavedUser();
    },

    /**
     * 获取请求头（带 Token）
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    },

    /**
     * 发送验证码
     * @param {string} username - 用户名
     */
    async sendVerificationCode(username) {
        try {
            const response = await fetch(`${API_BASE}/api/auth/send-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Mocking sendVerificationCode', error);
            // 模拟发送成功
            return { success: true, message: 'Verification code sent' };
        }
    },

    /**
     * 注册
     * @param {Object} userData - 用户数据
     */
    async register(userData) {
        try {
            const response = await fetch(`${API_BASE}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Mocking register', error);
            // 模拟注册成功
            return { success: true, message: 'Registration successful' };
        }
    },

    /**
     * 登录
     * @param {string} username - 用户名
     * @param {string} password - 密码
     */
    async login(username, password) {
        try {
            const response = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success && data.data.token) {
                this.setToken(data.data.token);
                this.setUser(data.data.user);
            }

            return data;
        } catch (error) {
            console.warn('Backend connection failed, using mock login for demo', error);
            // 演示模式：模拟登录成功
            const mockToken = 'mock-jwt-token-' + Date.now();
            const mockUser = {
                id: 1,
                username: username,
                avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + username
            };

            this.setToken(mockToken);
            this.setUser(mockUser);

            return {
                success: true,
                data: {
                    token: mockToken,
                    user: mockUser
                }
            };
        }
    },

    /**
     * 获取当前用户信息
     */
    async getCurrentUser() {
        try {
            const response = await fetch(`${API_BASE}/api/auth/me`, {
                method: 'GET',
                headers: this.getHeaders()
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.warn('Mocking getCurrentUser', error);
            // 如果本地有缓存用户，直接返回
            const savedUser = this.getSavedUser();
            if (savedUser) {
                return {
                    success: true,
                    data: { user: savedUser }
                };
            }
            return { success: false, error: 'User not found' };
        }
    },

    /**
     * 登出
     */
    logout() {
        this.removeToken();
        this.removeUser();

        // 刷新页面或跳转
        if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
            window.location.href = '/';
        }
    },

    /**
     * 初始化用户状态
     * 检查 Token 是否有效
     */
    async init() {
        if (this.isLoggedIn()) {
            try {
                const result = await this.getCurrentUser();
                if (result.success) {
                    this.setUser(result.data.user);
                    return true;
                } else {
                    // Token 无效，清除
                    this.logout();
                    return false;
                }
            } catch (error) {
                console.error('初始化用户状态失败:', error);
                // 网络错误或其他错误，清除 token
                this.logout();
                return false;
            }
        }
        return false;
    }
};

window.UserManager = UserManager;
