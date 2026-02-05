/**
 * 历史记录模型
 * 处理用户解题历史的存储和查询
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const HISTORY_FILE = path.join(__dirname, '../../data/history.json');

class HistoryModel {
    /**
     * 读取所有历史记录
     */
    readHistory() {
        try {
            const data = fs.readFileSync(HISTORY_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return [];
        }
    }

    /**
     * 保存历史记录列表
     * @param {Array} history - 历史记录列表
     */
    saveHistory(history) {
        fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
    }

    /**
     * 创建新历史记录
     * @param {Object} recordData - 记录数据
     */
    create(recordData) {
        const history = this.readHistory();
        
        const newRecord = {
            id: crypto.randomUUID(),
            userId: recordData.userId,
            username: recordData.username,
            question: recordData.question,
            parseResult: recordData.parseResult,
            solution: recordData.solution,
            createdAt: new Date().toISOString()
        };

        // 添加到列表开头（最新在前）
        history.unshift(newRecord);
        this.saveHistory(history);

        return newRecord;
    }

    /**
     * 获取用户的历史记录
     * @param {string} userId - 用户ID
     * @param {Object} options - 查询选项
     */
    findByUserId(userId, options = {}) {
        const history = this.readHistory();
        
        // 过滤该用户的记录
        let userHistory = history.filter(record => record.userId === userId);
        
        // 分页
        const page = options.page || 1;
        const limit = options.limit || 20;
        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        
        const total = userHistory.length;
        userHistory = userHistory.slice(startIndex, endIndex);
        
        return {
            records: userHistory,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit)
            }
        };
    }

    /**
     * 获取单条历史记录
     * @param {string} recordId - 记录ID
     * @param {string} userId - 用户ID（用于权限验证）
     */
    findById(recordId, userId) {
        const history = this.readHistory();
        const record = history.find(r => r.id === recordId);
        
        if (!record) {
            return null;
        }
        
        // 验证是否是该用户的记录
        if (record.userId !== userId) {
            return null;
        }
        
        return record;
    }

    /**
     * 删除历史记录
     * @param {string} recordId - 记录ID
     * @param {string} userId - 用户ID（用于权限验证）
     */
    deleteById(recordId, userId) {
        const history = this.readHistory();
        const index = history.findIndex(r => r.id === recordId);
        
        if (index === -1) {
            return false;
        }
        
        // 验证是否是该用户的记录
        if (history[index].userId !== userId) {
            return false;
        }
        
        history.splice(index, 1);
        this.saveHistory(history);
        
        return true;
    }

    /**
     * 清空用户所有历史记录
     * @param {string} userId - 用户ID
     */
    deleteByUserId(userId) {
        const history = this.readHistory();
        const newHistory = history.filter(r => r.userId !== userId);
        
        if (newHistory.length === history.length) {
            return false;
        }
        
        this.saveHistory(newHistory);
        return true;
    }
}

module.exports = new HistoryModel();
