/**
 * AI 学习助手 - 主入口文件
 * 负责界面交互、事件绑定和整体流程控制
 */

// ========================================
// 全局状态管理
// ========================================

const AppState = {
    currentTab: 'text', // 'text' | 'image'
    isProcessing: false,
    currentStep: 0, // 0: 未开始, 1: 识别中, 2: 解析中, 3: 解答中
    imageData: null, // 压缩后的图片 Base64
    recognizedText: '',
    parseResult: null,
    solution: null,
    history: [],
    currentUser: null
};

const RAW_API_BASE = window.AppConfig?.API_BASE_URL ?? 'http://localhost:3000';
const API_BASE = RAW_API_BASE
    .replace(/\/+$/, '')
    .replace(/\/api$/, '');

function buildApiUrl(path) {
    return `${API_BASE}${path}`;
}

// ========================================
// DOM 元素引用
// ========================================

const DOM = {
    // 用户状态
    authButtons: document.getElementById('auth-buttons'),
    userInfo: document.getElementById('user-info'),
    userAvatar: document.getElementById('user-avatar'),
    userName: document.getElementById('user-name'),
    logoutBtn: document.getElementById('logout-btn'),

    // Tab 切换
    tabBtns: document.querySelectorAll('.tab-btn'),
    textPanel: document.getElementById('text-panel'),
    imagePanel: document.getElementById('image-panel'),

    // 文字输入
    textInput: document.getElementById('text-input'),
    charCount: document.querySelector('.char-count'),
    clearTextBtn: document.getElementById('clear-text'),

    // 图片输入
    uploadArea: document.getElementById('upload-area'),
    imageInput: document.getElementById('image-input'),
    imagePreviewWrapper: document.getElementById('image-preview-wrapper'),
    imagePreview: document.getElementById('image-preview'),
    imageSize: document.getElementById('image-size'),
    removeImageBtn: document.getElementById('remove-image'),

    // 提交按钮
    submitBtn: document.getElementById('submit-btn'),
    btnText: document.querySelector('.btn-text'),
    btnLoading: document.querySelector('.btn-loading'),

    // 步骤指示器
    progressSection: document.getElementById('progress-section'),
    steps: document.querySelectorAll('.step'),

    // 结果展示
    resultSection: document.getElementById('result-section'),
    recognitionCard: document.getElementById('recognition-card'),
    recognizedText: document.getElementById('recognized-text'),
    editRecognitionBtn: document.getElementById('edit-recognition'),

    parseCard: document.getElementById('parse-card'),
    parseType: document.getElementById('parse-type'),
    parseSubject: document.getElementById('parse-subject'),
    parseKnowledge: document.getElementById('parse-knowledge'),
    parseDifficulty: document.getElementById('parse-difficulty'),

    solutionCard: document.getElementById('solution-card'),
    solutionThinking: document.getElementById('solution-thinking'),
    solutionSteps: document.getElementById('solution-steps'),
    solutionAnswer: document.getElementById('solution-answer'),
    solutionSummary: document.getElementById('solution-summary'),

    // 历史记录
    historyBtn: document.getElementById('history-btn'),
    historySidebar: document.getElementById('history-sidebar'),
    closeHistoryBtn: document.getElementById('close-history'),
    historyList: document.getElementById('history-list'),
    overlay: document.getElementById('overlay'),

    // 折叠按钮
    toggleBtns: document.querySelectorAll('.toggle-btn')
};

// ========================================
// 初始化
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    await initUserState();
    initEventListeners();
    loadHistory();
    updateSubmitButton();
});

// ========================================
// 事件监听器
// ========================================

function initEventListeners() {
    // 用户登出
    if (DOM.logoutBtn) {
        DOM.logoutBtn.addEventListener('click', () => {
            UserManager.logout();
            AppState.currentUser = null;
            updateUserDisplay();
        });
    }

    // Tab 切换
    DOM.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // 文字输入
    DOM.textInput.addEventListener('input', handleTextInput);
    DOM.clearTextBtn.addEventListener('click', clearText);

    // 图片上传
    DOM.uploadArea.addEventListener('click', () => DOM.imageInput.click());
    DOM.uploadArea.addEventListener('dragover', handleDragOver);
    DOM.uploadArea.addEventListener('dragleave', handleDragLeave);
    DOM.uploadArea.addEventListener('drop', handleDrop);
    DOM.imageInput.addEventListener('change', handleImageSelect);
    DOM.removeImageBtn.addEventListener('click', removeImage);

    // 提交按钮
    DOM.submitBtn.addEventListener('click', handleSubmit);

    // 历史记录
    DOM.historyBtn.addEventListener('click', openHistory);
    DOM.closeHistoryBtn.addEventListener('click', closeHistory);
    DOM.overlay.addEventListener('click', closeHistory);

    // 折叠按钮
    DOM.toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => toggleCard(btn));
    });

    // 编辑识别结果
    DOM.editRecognitionBtn.addEventListener('click', editRecognition);

    // 键盘快捷键
    document.addEventListener('keydown', handleKeyboard);
}

// ========================================
// Tab 切换
// ========================================

function switchTab(tab) {
    AppState.currentTab = tab;

    // 更新按钮状态
    DOM.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    // 切换面板
    DOM.textPanel.classList.toggle('active', tab === 'text');
    DOM.imagePanel.classList.toggle('active', tab === 'image');

    // 更新提交按钮状态
    updateSubmitButton();

    // 隐藏结果区域
    hideResults();
}

// ========================================
// 文字输入处理
// ========================================

function handleTextInput() {
    const text = DOM.textInput.value;
    const count = text.length;

    DOM.charCount.textContent = `${count} / 2000`;

    if (count > 2000) {
        DOM.charCount.style.color = 'var(--error-color)';
    } else {
        DOM.charCount.style.color = 'var(--text-tertiary)';
    }

    updateSubmitButton();
}

function clearText() {
    DOM.textInput.value = '';
    DOM.charCount.textContent = '0 / 2000';
    DOM.charCount.style.color = 'var(--text-tertiary)';
    updateSubmitButton();
}

// ========================================
// 图片处理
// ========================================

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    DOM.uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    DOM.uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    DOM.uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processImage(files[0]);
    }
}

function handleImageSelect(e) {
    const file = e.target.files[0];
    if (file) {
        processImage(file);
    }
}

function processImage(file) {
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        showError('请选择图片文件');
        return;
    }

    // 验证文件大小 (5MB)
    if (file.size > 5 * 1024 * 1024) {
        showError('图片大小不能超过 5MB');
        return;
    }

    // 读取并压缩图片
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            compressImage(img, file.type);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function compressImage(img, type) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // 计算压缩后的尺寸
    let width = img.width;
    let height = img.height;
    const maxSize = 1024;

    if (width > maxSize || height > maxSize) {
        if (width > height) {
            height = (height / width) * maxSize;
            width = maxSize;
        } else {
            width = (width / height) * maxSize;
            height = maxSize;
        }
    }

    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(img, 0, 0, width, height);

    // 转换为 Base64 (质量 0.8)
    const compressedData = canvas.toDataURL(type, 0.8);
    AppState.imageData = compressedData;

    // 显示预览
    showImagePreview(compressedData);
    updateSubmitButton();
}

function showImagePreview(dataUrl) {
    DOM.imagePreview.src = dataUrl;

    // 计算压缩后的大小
    const sizeInBytes = Math.ceil(dataUrl.length * 0.75);
    const sizeInKB = (sizeInBytes / 1024).toFixed(1);
    DOM.imageSize.textContent = `压缩后: ${sizeInKB} KB`;

    DOM.uploadArea.style.display = 'none';
    DOM.imagePreviewWrapper.style.display = 'flex';
}

function removeImage(e) {
    e.stopPropagation();

    AppState.imageData = null;
    DOM.imageInput.value = '';
    DOM.imagePreview.src = '';

    DOM.uploadArea.style.display = 'block';
    DOM.imagePreviewWrapper.style.display = 'none';

    updateSubmitButton();
}

// ========================================
// 提交处理
// ========================================

function updateUserDisplay() {
    if (UserManager.isLoggedIn()) {
        const user = UserManager.getSavedUser();
        AppState.currentUser = user;

        if (DOM.authButtons) DOM.authButtons.style.display = 'none';
        if (DOM.userInfo) DOM.userInfo.style.display = 'flex';
        if (DOM.userName) DOM.userName.textContent = user.username;
        if (DOM.userAvatar) DOM.userAvatar.textContent = user.username.charAt(0).toUpperCase();
    } else {
        AppState.currentUser = null;

        if (DOM.authButtons) DOM.authButtons.style.display = 'flex';
        if (DOM.userInfo) DOM.userInfo.style.display = 'none';
    }
}

async function initUserState() {
    await UserManager.init();
    updateUserDisplay();
}

function updateSubmitButton() {
    let canSubmit = false;

    if (AppState.currentTab === 'text') {
        canSubmit = DOM.textInput.value.trim().length > 0;
    } else {
        canSubmit = AppState.imageData !== null;
    }

    DOM.submitBtn.disabled = !canSubmit || AppState.isProcessing;
}

async function handleSubmit() {
    if (AppState.isProcessing) return;

    AppState.isProcessing = true;
    updateSubmitButton();
    showLoading(true);
    hideResults();

    try {
        if (UserManager.isLoggedIn() && AppState.currentTab === 'text') {
            // 登录用户使用完整解题流程（自动保存历史记录）
            await solveWithFullPipeline();
        } else {
            // 未登录用户或图片输入：使用原有流程
            if (AppState.currentTab === 'text') {
                AppState.recognizedText = DOM.textInput.value.trim();
                await skipRecognitionStep();
            } else {
                await performRecognition();
            }

            // 执行解析和解答
            await performParsing();
            await performSolving();

            // 保存到历史记录
            saveToHistory();
        }

    } catch (error) {
        console.error('处理失败:', error);
        showError(error.message || '处理失败，请重试');
    } finally {
        AppState.isProcessing = false;
        showLoading(false);
        updateSubmitButton();
        hideProgress();
    }
}

async function solveWithFullPipeline() {
    const content = AppState.currentTab === 'text'
        ? DOM.textInput.value.trim()
        : AppState.imageData;

    showProgress(1);
    showProgress(2);
    showProgress(3);

    const response = await fetch(buildApiUrl('/api/solve-problem'), {
        method: 'POST',
        headers: UserManager.getHeaders(),
        body: JSON.stringify({
            type: AppState.currentTab,
            content: content
        })
    });

    if (!response.ok) {
        throw new Error('解题失败');
    }

    const result = await response.json();

    if (!result.success) {
        throw new Error(result.error || '解题失败');
    }

    // 更新状态
    AppState.recognizedText = result.data.recognizedText;
    AppState.parseResult = result.data.parseResult;
    AppState.solution = result.data.solution;

    // 显示结果
    showRecognitionResult();
    showParseResult();
    showSolutionResult();

    // 刷新历史记录
    loadHistoryFromServer();
}

// ========================================
// 多 Agent 流程
// ========================================

async function performRecognition() {
    showProgress(1);

    // 调用后端 API 进行图像识别
    const response = await fetch(buildApiUrl('/api/recognize'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: AppState.imageData })
    });

    if (!response.ok) throw new Error('识别失败');

    const result = await response.json();
    if (!result.success) throw new Error(result.error || '识别失败');

    AppState.recognizedText = result.data.text;

    showRecognitionResult();
}

async function skipRecognitionStep() {
    showProgress(1);
    // 文字输入不需要识别，直接显示
    showRecognitionResult();
}

async function performParsing() {
    showProgress(2);

    // 调用后端 API 进行题目解析
    const response = await fetch(buildApiUrl('/api/parse'), {
        method: 'POST',
        headers: UserManager.getHeaders(),
        body: JSON.stringify({
            text: AppState.recognizedText,
            userId: AppState.currentUser?.id
        })
    });

    if (!response.ok) throw new Error('解析失败');

    const result = await response.json();
    if (!result.success) throw new Error(result.error || '解析失败');

    AppState.parseResult = result.data;

    showParseResult();
}

async function performSolving() {
    showProgress(3);

    // 调用后端 API 生成解答
    const response = await fetch(buildApiUrl('/api/solve'), {
        method: 'POST',
        headers: UserManager.getHeaders(),
        body: JSON.stringify({
            text: AppState.recognizedText,
            parseResult: AppState.parseResult,
            userId: AppState.currentUser?.id
        })
    });

    if (!response.ok) throw new Error('解答生成失败');

    const result = await response.json();
    if (!result.success) throw new Error(result.error || '解答生成失败');

    AppState.solution = result.data;

    showSolutionResult();
}

// ========================================
// 结果显示
// ========================================

function showRecognitionResult() {
    DOM.recognizedText.textContent = AppState.recognizedText;
    DOM.resultSection.style.display = 'flex';
}

function showParseResult() {
    const result = AppState.parseResult;

    DOM.parseType.textContent = result.type;
    DOM.parseSubject.textContent = result.subject;

    // 知识点标签
    DOM.parseKnowledge.innerHTML = result.knowledgePoints
        .map(point => `<span class="parse-tag">${point}</span>`)
        .join('');

    // 难度等级
    DOM.parseDifficulty.textContent = result.difficulty;
    DOM.parseDifficulty.className = 'parse-value difficulty ' +
        (result.difficulty === '简单' ? 'easy' :
            result.difficulty === '中等' ? 'medium' : 'hard');
}

function showSolutionResult() {
    const solution = AppState.solution;

    DOM.solutionThinking.textContent = solution.thinking;

    DOM.solutionSteps.innerHTML = solution.steps
        .map((step, index) => `<p><strong>步骤 ${index + 1}:</strong> ${step}</p>`)
        .join('');

    DOM.solutionAnswer.textContent = solution.answer;
    DOM.solutionSummary.textContent = solution.summary;
}

function hideResults() {
    DOM.resultSection.style.display = 'none';
}

// ========================================
// 进度指示器
// ========================================

function showProgress(step) {
    AppState.currentStep = step;
    DOM.progressSection.style.display = 'block';

    DOM.steps.forEach((s, index) => {
        const stepNum = index + 1;
        s.classList.remove('active', 'completed');

        if (stepNum === step) {
            s.classList.add('active');
        } else if (stepNum < step) {
            s.classList.add('completed');
        }
    });
}

function hideProgress() {
    DOM.progressSection.style.display = 'none';
    AppState.currentStep = 0;
}

// ========================================
// 加载状态
// ========================================

function showLoading(show) {
    DOM.btnText.style.display = show ? 'none' : 'flex';
    DOM.btnLoading.style.display = show ? 'flex' : 'none';
}

// ========================================
// 卡片折叠
// ========================================

function toggleCard(btn) {
    const targetId = btn.dataset.target;
    const target = document.getElementById(targetId);

    btn.classList.toggle('collapsed');
    target.style.display = btn.classList.contains('collapsed') ? 'none' : 'block';
}

// ========================================
// 编辑识别结果
// ========================================

function editRecognition() {
    const newText = prompt('编辑识别的题目内容:', AppState.recognizedText);
    if (newText !== null && newText.trim() !== '') {
        AppState.recognizedText = newText.trim();
        DOM.recognizedText.textContent = AppState.recognizedText;
    }
}

// ========================================
// 历史记录
// ========================================

function loadHistory() {
    if (UserManager.isLoggedIn()) {
        // 登录用户：从后端获取历史记录
        loadHistoryFromServer();
    } else {
        // 未登录用户：从本地存储获取
        try {
            const saved = localStorage.getItem('ai-learning-history');
            if (saved) {
                AppState.history = JSON.parse(saved);
                renderHistory();
            }
        } catch (e) {
            console.error('加载历史记录失败:', e);
        }
    }
}

async function loadHistoryFromServer() {
    try {
        const response = await fetch(buildApiUrl('/api/history'), {
            method: 'GET',
            headers: UserManager.getHeaders()
        });

        const result = await response.json();

        if (result.success) {
            // 转换为本地格式
            AppState.history = result.data.records.map(record => ({
                id: record.id,
                timestamp: record.createdAt,
                type: 'text',
                content: record.question.substring(0, 50) + (record.question.length > 50 ? '...' : ''),
                recognizedText: record.question,
                parseResult: record.parseResult,
                solution: record.solution,
                fromServer: true
            }));
            renderHistory();
        }
    } catch (error) {
        console.error('加载服务器历史记录失败:', error);
    }
}

function saveToHistory() {
    const item = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: AppState.currentTab,
        content: AppState.currentTab === 'text'
            ? DOM.textInput.value.trim().substring(0, 50) + '...'
            : '图片题目',
        recognizedText: AppState.recognizedText,
        parseResult: AppState.parseResult,
        solution: AppState.solution
    };

    AppState.history.unshift(item);

    // 限制历史记录数量（最多 50 条）
    if (AppState.history.length > 50) {
        AppState.history = AppState.history.slice(0, 50);
    }

    // 保存到本地存储
    localStorage.setItem('ai-learning-history', JSON.stringify(AppState.history));
    renderHistory();
}

function renderHistory() {
    if (AppState.history.length === 0) {
        DOM.historyList.innerHTML = '<p style="text-align: center; color: var(--text-tertiary); padding: 20px;">暂无历史记录</p>';
        return;
    }

    DOM.historyList.innerHTML = AppState.history.map(item => `
        <div class="history-item" data-id="${item.id}">
            <div class="history-item-title">${escapeHtml(item.content)}</div>
            <div class="history-item-time">${formatTime(item.timestamp)}</div>
        </div>
    `).join('');

    // 绑定点击事件
    DOM.historyList.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', () => loadHistoryItem(parseInt(item.dataset.id)));
    });
}

function loadHistoryItem(id) {
    const item = AppState.history.find(h => h.id === id);
    if (!item) return;

    // 恢复数据
    AppState.recognizedText = item.recognizedText;
    AppState.parseResult = item.parseResult;
    AppState.solution = item.solution;

    // 显示结果
    showRecognitionResult();
    showParseResult();
    showSolutionResult();

    closeHistory();

    // 滚动到结果区域
    DOM.resultSection.scrollIntoView({ behavior: 'smooth' });
}

function openHistory() {
    DOM.historySidebar.classList.add('open');
    DOM.overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeHistory() {
    DOM.historySidebar.classList.remove('open');
    DOM.overlay.classList.remove('show');
    document.body.style.overflow = '';
}

// ========================================
// 键盘快捷键
// ========================================

function handleKeyboard(e) {
    // Ctrl/Cmd + Enter 提交
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (!DOM.submitBtn.disabled) {
            handleSubmit();
        }
    }

    // ESC 关闭历史记录
    if (e.key === 'Escape') {
        closeHistory();
    }
}

// ========================================
// 工具函数
// ========================================

function simulateDelay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showError(message) {
    alert(message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    // 小于 1 分钟
    if (diff < 60000) {
        return '刚刚';
    }

    // 小于 1 小时
    if (diff < 3600000) {
        return `${Math.floor(diff / 60000)} 分钟前`;
    }

    // 小于 24 小时
    if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)} 小时前`;
    }

    // 大于 24 小时
    return date.toLocaleDateString('zh-CN');
}

// ========================================
// API 调用（实际项目中使用）
// ========================================

/*
async function callRecognitionAPI(imageData) {
    const response = await fetch('/api/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData })
    });
    
    if (!response.ok) throw new Error('识别失败');
    
    const data = await response.json();
    return data.text;
}

async function callParseAPI(text) {
    const response = await fetch('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    
    if (!response.ok) throw new Error('解析失败');
    
    return await response.json();
}

async function callSolveAPI(text, parseResult) {
    const response = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, parseResult })
    });
    
    if (!response.ok) throw new Error('解答生成失败');
    
    return await response.json();
}
*/
