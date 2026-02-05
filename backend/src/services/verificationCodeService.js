/**
 * 验证码服务
 * 生成和验证验证码
 */

const fs = require('fs');
const path = require('path');

const CODES_FILE = path.join(__dirname, '../../data/verificationCodes.json');
const CODE_EXPIRY = 10 * 60 * 1000; // 10 分钟

class VerificationCodeService {
    /**
     * 读取验证码数据
     */
    readCodes() {
        try {
            const data = fs.readFileSync(CODES_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return {};
        }
    }

    /**
     * 保存验证码数据
     * @param {Object} codes - 验证码数据
     */
    saveCodes(codes) {
        fs.writeFileSync(CODES_FILE, JSON.stringify(codes, null, 2));
    }

    /**
     * 生成验证码
     * @param {string} username - 用户名
     */
    generateCode(username) {
        const codes = this.readCodes();
        
        // 生成 6 位数字验证码
        const code = Math.floor(100000 + Math.random() * 900000).toString();
        
        // 清理过期验证码
        this.cleanupExpiredCodes(codes);
        
        codes[username] = {
            code: code,
            expiresAt: Date.now() + CODE_EXPIRY
        };
        
        this.saveCodes(codes);
        
        return code;
    }

    /**
     * 验证验证码
     * @param {string} username - 用户名
     * @param {string} inputCode - 输入的验证码
     */
    verifyCode(username, inputCode) {
        const codes = this.readCodes();
        
        // 清理过期验证码
        this.cleanupExpiredCodes(codes);
        
        const codeData = codes[username];
        
        if (!codeData) {
            return { valid: false, error: '验证码不存在或已过期' };
        }
        
        if (Date.now() > codeData.expiresAt) {
            delete codes[username];
            this.saveCodes(codes);
            return { valid: false, error: '验证码已过期' };
        }
        
        if (codeData.code !== inputCode) {
            return { valid: false, error: '验证码错误' };
        }
        
        // 验证成功后删除验证码
        delete codes[username];
        this.saveCodes(codes);
        
        return { valid: true };
    }

    /**
     * 清理过期验证码
     * @param {Object} codes - 验证码数据
     */
    cleanupExpiredCodes(codes) {
        const now = Date.now();
        for (const username in codes) {
            if (codes[username].expiresAt < now) {
                delete codes[username];
            }
        }
    }

    /**
     * 发送验证码（开发环境打印到控制台）
     * @param {string} username - 用户名
     * @param {string} code - 验证码
     */
    sendCode(username, code) {
        console.log('\n' + '='.repeat(50));
        console.log('📧 验证码发送');
        console.log('='.repeat(50));
        console.log(`用户名: ${username}`);
        console.log(`验证码: ${code}`);
        console.log(`有效期: 10 分钟`);
        console.log('='.repeat(50) + '\n');
        
        return true;
    }
}

module.exports = new VerificationCodeService();
