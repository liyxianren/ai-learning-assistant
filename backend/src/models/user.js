/**
 * 用户模型
 * 处理用户数据的存储和验证
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const USERS_FILE = path.join(__dirname, '../../data/users.json');

class UserModel {
    /**
     * 读取所有用户
     */
    readUsers() {
        try {
            const data = fs.readFileSync(USERS_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return [];
        }
    }

    /**
     * 保存用户列表
     * @param {Array} users - 用户列表
     */
    saveUsers(users) {
        fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
    }

    /**
     * 根据用户名查找用户
     * @param {string} username - 用户名
     */
    findByUsername(username) {
        const users = this.readUsers();
        return users.find(user => user.username === username);
    }

    /**
     * 根据用户ID查找用户
     * @param {string} userId - 用户ID
     */
    findById(userId) {
        const users = this.readUsers();
        return users.find(user => user.id === userId);
    }

    /**
     * 创建新用户
     * @param {Object} userData - 用户数据
     */
    create(userData) {
        const users = this.readUsers();
        
        // 检查用户名是否已存在
        if (this.findByUsername(userData.username)) {
            throw new Error('用户名已存在');
        }

        const newUser = {
            id: crypto.randomUUID(),
            username: userData.username,
            password: this.hashPassword(userData.password),
            createdAt: new Date().toISOString(),
            lastLoginAt: null
        };

        users.push(newUser);
        this.saveUsers(users);

        // 返回不包含密码的用户信息
        const { password, ...userInfo } = newUser;
        return userInfo;
    }

    /**
     * 更新用户最后登录时间
     * @param {string} userId - 用户ID
     */
    updateLastLogin(userId) {
        const users = this.readUsers();
        const userIndex = users.findIndex(user => user.id === userId);
        
        if (userIndex !== -1) {
            users[userIndex].lastLoginAt = new Date().toISOString();
            this.saveUsers(users);
        }
    }

    /**
     * 验证用户密码
     * @param {string} username - 用户名
     * @param {string} password - 密码
     */
    verifyPassword(username, password) {
        const user = this.findByUsername(username);
        if (!user) {
            return null;
        }

        const hashedPassword = this.hashPassword(password);
        if (hashedPassword === user.password) {
            return user;
        }

        return null;
    }

    /**
     * 密码加密
     * @param {string} password - 原始密码
     */
    hashPassword(password) {
        return crypto.createHash('sha256').update(password).digest('hex');
    }
}

module.exports = new UserModel();
