<template>
    <div class="chat-view">
      <aside class="chat-sidebar">
        <!-- 侧边栏头部 -->
        <div class="sidebar-header">
          <button class="sidebar-back-btn" @click="goHome">
            <i class="fas fa-arrow-left"></i>
            <span class="btn-label">返回</span>
          </button>
          <span class="sidebar-title">对话记录</span>
        </div>

        <!-- 对话列表 -->
        <div class="conversation-list">
          <div
            v-for="(conv, index) in conversationList"
            :key="index"
            :class="['conv-item', { active: conv.active }]"
            @click="selectConversation(index)"
          >
            <i :class="conv.icon"></i>
            <div class="conv-info">
              <span class="conv-title">{{ conv.title }}</span>
              <span class="conv-time">{{ conv.time }}</span>
            </div>
            <!-- 删除单个对话按钮 -->
            <button class="delete-conv-btn" @click.stop="deleteConversation(index)" title="删除此对话">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <!-- 清空历史记录（清空侧边栏列表） -->
        <div class="clear-history-wrapper">
          <button class="clear-history-btn" @click="clearAllHistory">
            <i class="fas fa-trash-alt"></i>
            <span>清空历史记录</span>
          </button>
        </div>

        <!-- 侧边栏底部用户信息 - 修改为使用用户头像 -->
        <div class="sidebar-footer">
          <div class="user-card">
            <!-- 使用用户头像 -->
            <img
              v-if="userInfo.avatar"
              :src="userInfo.avatar"
              alt="用户头像"
              class="user-avatar-img"
            />
            <i v-else class="fas fa-user-circle"></i>
            <div class="user-detail">
              <span class="user-name">{{ userInfo.name || '用户' }}</span>
              <span class="user-status">
                <span class="status-dot-small"></span>
                {{ userInfo.isOnline ? '在线' : '离线' }}
              </span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ========================================== -->
      <!-- 主对话区域 -->
      <!-- ========================================== -->
      <main class="chat-main">
        <!-- 头部 -->
        <header class="chat-header">
          <!-- 手机端返回按钮（仅手机端显示） -->
          <button class="mobile-back-btn" @click="goHome">
            <i class="fas fa-arrow-left"></i>
          </button>

          <div class="header-info">
            <i class="fas fa-robot"></i>
            <h2 class="header-title">探店助手</h2>
            <span :class="['status-badge', { online: isOnline }]">
              <span class="status-dot"></span>
              {{ isOnline ? '在线' : '离线' }}
            </span>
          </div>

          <!-- 清空对话按钮（只清空当前聊天内容） -->
          <button class="desktop-clear-btn" @click="clearChat" title="清空当前对话">
            <i class="fas fa-trash-alt"></i>
            <span class="clear-label">清空对话</span>
          </button>
        </header>

        <!-- 快捷提问 -->
        <div class="quick-questions">
          <button
            v-for="q in quickQuestions"
            :key="q"
            class="question-btn"
            @click="sendMessage(q)"
          >
            {{ q }}
          </button>
        </div>

        <!-- 对话容器 -->
        <div class="chat-container" ref="chatContainer">
          <!-- 空状态 -->
          <div v-if="messages.length === 0" class="empty-state">
            <div class="empty-icon">🤖</div>
            <h3 class="empty-title">你好！我是探店助手</h3>
            <span class="empty-hint">输入你想找的餐厅或美食开始对话</span>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message-row', msg.role]"
          >
            <!-- AI 头像 -->
            <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">
              🤖
            </div>

            <div :class="['message-bubble', msg.role]">
              <div class="message-content">{{ msg.content }}</div>
              <div class="message-time">{{ msg.time }}</div>
            </div>

            <!-- 用户头像 - 修改为使用用户注册的头像 -->
            <div v-if="msg.role === 'user'" class="avatar user-avatar">
              <img
                v-if="userInfo.avatar"
                :src="userInfo.avatar"
                alt="用户头像"
                class="avatar-img"
              />
              <i v-else class="fas fa-user"></i>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="isLoading" class="message-row assistant">
            <div class="avatar assistant-avatar">🤖</div>
            <div class="message-bubble assistant">
              <div class="message-content loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <button class="tool-btn" title="附件">
              <i class="fas fa-plus"></i>
            </button>

            <input
              v-model="inputText"
              type="text"
              placeholder="输入你想问的问题..."
              @keyup.enter="sendMessage(inputText)"
              class="chat-input"
            />

            <button class="tool-btn" title="语音">
              <i class="fas fa-microphone"></i>
            </button>

            <button
              @click="sendMessage(inputText)"
              class="send-btn"
              :disabled="!inputText.trim() || isLoading"
            >
              <i class="fas fa-paper-plane"></i>
              <span class="send-label">发送</span>
            </button>
          </div>
          <p class="disclaimer">
            <i class="fas fa-shield-alt"></i>
            内容由AI生成，仅供参考
          </p>
        </div>
      </main>
    </div>
  </template>

  <script setup lang="ts">
  import { ref, nextTick, onMounted } from 'vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  // ============================================
  // 1. 类型定义
  // ============================================

  interface Message {
    id: number
    role: 'user' | 'assistant'
    content: string
    time: string
  }

  interface Conversation {
    title: string
    time: string
    icon: string
    active: boolean
  }

  // 用户信息接口
  interface UserInfo {
    id?: number
    name: string
    avatar: string
    isOnline: boolean
  }

  // ============================================
  // 2. 响应式数据
  // ============================================

  const quickQuestions = [
    '推荐附近好吃的川菜',
    '适合约会的餐厅',
    '人均100以内的餐厅',
    '安静的咖啡馆推荐',
    '下雨天适合吃的热乎的'
  ]

  const messages = ref<Message[]>([])
  const inputText = ref('')
  const isLoading = ref(false)
  const isOnline = ref(true)
  const chatContainer = ref<HTMLElement | null>(null)

  // 用户信息（可以从 localStorage、store 或 API 获取）
  const userInfo = ref<UserInfo>({
    id: 1,
    name: '用户', // 可以从注册信息获取
    avatar: '', // 用户注册时上传的头像URL
    isOnline: true
  })

  // 对话列表（电脑端侧边栏）
  const conversationList = ref<Conversation[]>([
    { title: '当前对话', time: '刚刚', icon: 'fas fa-comment', active: true },
  ])

  // ============================================
  // 3. 工具函数
  // ============================================

  const getCurrentTime = (): string => {
    const now = new Date()
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
  }

  const scrollToBottom = async (): Promise<void> => {
    await nextTick()
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }

  const goHome = (): void => {
    router.push('/')
  }

  // ============================================
  // 4. 清空功能（分开）
  // ============================================

  // 清空当前对话（只清空聊天区域）
  const clearChat = (): void => {
    if (messages.value.length === 0) return

    if (confirm('确定要清空当前对话内容吗？')) {
      messages.value = []
    }
  }

  // 清空所有历史记录（清空侧边栏列表）
  const clearAllHistory = (): void => {
    if (conversationList.value.length === 0) {
      alert('暂无历史记录')
      return
    }

    if (confirm('确定要清空所有历史记录吗？此操作不可恢复！')) {
      conversationList.value = []
    }
  }

  // 删除单个对话
  const deleteConversation = (index: number): void => {
    // 1. 验证索引有效性
    if (index < 0 || index >= conversationList.value.length) {
      console.warn('无效的对话索引:', index)
      return
    }

    // 2. 获取对话对象
    const conversation = conversationList.value[index]
    if (!conversation) {
      console.warn('对话不存在')
      return
    }

    // 3. 确认删除
    if (confirm(`确定要删除"${conversation.title}"吗？此操作不可恢复！`)) {
      conversationList.value.splice(index, 1)

      // 4. 删除后自动选中第一个对话
      if (conversationList.value.length > 0) {
        const firstConv = conversationList.value[0]
        if (firstConv) {
          firstConv.active = true
        }
      }
    }
  }

  // 选择对话
  const selectConversation = (index: number): void => {
    // 验证索引
    if (index < 0 || index >= conversationList.value.length) {
      console.warn('无效的对话索引:', index)
      return
    }

    conversationList.value.forEach((conv, i) => {
      conv.active = i === index
    })
  }

  // ============================================
  // 5. 获取用户信息
  // ============================================

  const getUserInfo = async (): Promise<void> => {
    try {
      // 方案1：从 localStorage 获取
      const storedUser = localStorage.getItem('userInfo')
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser)
        userInfo.value = {
          ...userInfo.value,
          ...parsedUser
        }
        return
      }

      // 方案2：从 API 获取
      // const response = await fetch('/api/user/profile')
      // if (response.ok) {
      //   const data = await response.json()
      //   userInfo.value = {
      //     ...userInfo.value,
      //     name: data.name || '用户',
      //     avatar: data.avatar || '',
      //     isOnline: data.isOnline || true
      //   }
      // }

      // 方案3：从 Vuex/Pinia Store 获取
      // userInfo.value = store.userInfo

      // 方案4：模拟用户头像（使用 UI Avatars API）
      // 如果没有头像，可以使用在线生成的头像
      if (!userInfo.value.avatar) {
        userInfo.value.avatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(userInfo.value.name)}&background=ff6b35&color=fff&size=40&rounded=true`
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  // ============================================
  // 6. 核心功能：发送消息
  // ============================================

  const sendMessage = (text: string): void => {
    if (!text.trim() || isLoading.value) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      time: getCurrentTime()
    }
    messages.value.push(userMessage)
    inputText.value = ''
    scrollToBottom()

    callAIApi(text.trim())
  }

  // ============================================
  // 7. AI API 调用
  // ============================================

  const callAIApi = async (userInput: string): Promise<void> => {
    isLoading.value = true

    try {
      const API_URL = '/api/chat'

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userInput,
          userId: userInfo.value.id, // 可选：发送用户ID
          userName: userInfo.value.name // 可选：发送用户名
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const assistantContent = data.content || data.message || data.reply || '收到回复'

      messages.value.push({
        id: Date.now() + 1,
        role: 'assistant',
        content: assistantContent,
        time: getCurrentTime()
      })

    } catch (error) {
      console.error('AI 调用失败:', error)

      messages.value.push({
        id: Date.now() + 1,
        role: 'assistant',
        content: '抱歉，我暂时无法回答，请稍后再试。',
        time: getCurrentTime()
      })
    } finally {
      isLoading.value = false
      await scrollToBottom()
    }
  }

  // ============================================
  // 8. 生命周期钩子
  // ============================================

  onMounted(() => {
    getUserInfo()
  })
  </script>

  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .chat-view {
    display: flex;
    width: 100%;
    height: 100vh;
    height: 100dvh;
    background: #f1f5f9;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  /* ============================================
     电脑端侧边栏（默认显示）
     ============================================ */
  .chat-sidebar {
    width: 280px;
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 1.2rem 1.2rem;
    border-bottom: 1px solid #f1f5f9;
  }

  .sidebar-back-btn {
    background: #f1f5f9;
    border: none;
    color: #1e293b;
    font-size: 1rem;
    cursor: pointer;
    padding: 0.4rem 0.8rem;
    border-radius: 0.5rem;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .sidebar-back-btn:hover {
    background: #e2e8f0;
  }

  .btn-label {
    font-size: 0.85rem;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    .btn-label {
      display: none;
    }
  }

  .sidebar-title {
    flex: 1;
    font-weight: 650;
    color: #1e293b;
    font-size: 1.05rem;
  }

  /* 对话列表 */
  .conversation-list {
    flex: 1;
    padding: 0.8rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    overflow-y: auto;
  }

  .conv-item {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem 1rem;
    border-radius: 0.7rem;
    cursor: pointer;
    transition: all 0.15s;
    position: relative;
  }

  .conv-item:hover {
    background: #f8fafc;
  }

  .conv-item.active {
    background: #eff6ff;
  }

  .conv-item i {
    color: #94a3b8;
    font-size: 0.9rem;
    width: 1.2rem;
    text-align: center;
  }

  .conv-item.active i {
    color: #2563eb;
  }

  .conv-info {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    min-width: 0;
    flex: 1;
  }

  .conv-title {
    font-size: 0.85rem;
    color: #334155;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .conv-item.active .conv-title {
    color: #1e293b;
    font-weight: 600;
  }

  .conv-time {
    font-size: 0.7rem;
    color: #94a3b8;
  }

  /* 删除单个对话按钮 */
  .delete-conv-btn {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 0.7rem;
    cursor: pointer;
    padding: 0.2rem 0.4rem;
    border-radius: 0.3rem;
    opacity: 0;
    transition: all 0.2s;
  }

  .conv-item:hover .delete-conv-btn {
    opacity: 1;
  }

  .delete-conv-btn:hover {
    background: #fef2f2;
    color: #dc2626;
  }

  /* ============================================
     清空历史记录按钮
     ============================================ */
  .clear-history-wrapper {
    padding: 0.8rem 1.2rem;
    border-top: 1px solid #f1f5f9;
    border-bottom: 1px solid #f1f5f9;
    flex-shrink: 0;
  }

  .clear-history-btn {
    width: 100%;
    padding: 0.6rem 1rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.5rem;
    color: #dc2626;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.2s ease;
  }

  .clear-history-btn:hover {
    background: #fee2e2;
    border-color: #f87171;
    transform: scale(1.02);
  }

  .clear-history-btn:active {
    transform: scale(0.98);
  }

  .clear-history-btn i {
    font-size: 0.9rem;
  }

  @media (max-width: 768px) {
    .clear-history-wrapper {
      display: none;
    }
  }

  /* ============================================
     侧边栏底部用户信息 - 修改样式
     ============================================ */
  .sidebar-footer {
    padding: 1rem 1.2rem;
    border-top: 1px solid #f1f5f9;
  }

  .user-card {
    display: flex;
    align-items: center;
    gap: 0.7rem;
  }

  /* 用户头像图片 */
  .user-avatar-img {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #e2e8f0;
  }

  /* 当没有头像时使用图标 */
  .user-card > i {
    font-size: 2.2rem;
    color: #94a3b8;
  }

  .user-detail {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .user-name {
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
  }

  .user-status {
    font-size: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }

  .status-dot-small {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #22c55e;
    display: inline-block;
  }

  .user-status:not(.online) .status-dot-small {
    background: #94a3b8;
  }

  /* ============================================
     主对话区域
     ============================================ */
  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    background: #ffffff;
  }

  /* ============================================
     头部
     ============================================ */
  .chat-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: linear-gradient(135deg, #ff6b35 0%, #ff8c5a 100%);
    color: white;
    flex-shrink: 0;
  }

  .mobile-back-btn {
    display: none;
    background: none;
    border: none;
    color: white;
    font-size: 1.2rem;
    cursor: pointer;
    padding: 0.3rem;
  }

  .header-info {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex: 1;
  }

  .header-info > i {
    font-size: 1.3rem;
  }

  .header-title {
    font-size: 1.1rem;
    font-weight: 650;
  }

  .status-badge {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.7rem;
    background: rgba(255, 255, 255, 0.2);
    padding: 0.2rem 0.7rem;
    border-radius: 1rem;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #94a3b8;
  }

  .status-badge.online .status-dot {
    background: #4ade80;
  }

  /* 清空对话按钮（头部） */
  .desktop-clear-btn {
    background: rgba(255, 255, 255, 0.15);
    border: none;
    color: white;
    padding: 0.4rem 0.8rem;
    border-radius: 0.5rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: all 0.15s;
    font-size: 0.85rem;
  }

  .desktop-clear-btn:hover {
    background: rgba(255, 255, 255, 0.25);
  }

  .desktop-clear-btn i {
    font-size: 0.9rem;
  }

  .clear-label {
    font-size: 0.8rem;
  }

  @media (max-width: 768px) {
    .clear-label {
      display: none;
    }
    .desktop-clear-btn {
      padding: 0.4rem 0.6rem;
    }
  }

  /* ============================================
     快捷提问
     ============================================ */
  .quick-questions {
    padding: 0.8rem 1.5rem;
    background: #fafbfd;
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
    border-bottom: 1px solid #f1f5f9;
    flex-shrink: 0;
  }

  .quick-questions::-webkit-scrollbar {
    height: 0;
  }

  .question-btn {
    padding: 0.4rem 1rem;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 1.5rem;
    font-size: 0.8rem;
    color: #475569;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
  }

  .question-btn:hover {
    background: #ff6b35;
    color: white;
    border-color: #ff6b35;
  }

  /* ============================================
     对话容器
     ============================================ */
  .chat-container {
    flex: 1;
    padding: 1.5rem 2rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    background: #fafbfd;
    background-image:
      radial-gradient(circle at 30% 20%, #f1f5f9 1px, transparent 1px),
      radial-gradient(circle at 70% 80%, #f1f5f9 1px, transparent 1px);
    background-size: 40px 40px, 50px 50px;
  }

  /* 空状态 */
  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
    margin: auto;
    max-width: 450px;
    background: white;
    border-radius: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    border: 1px solid #e2e8f0;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 0.8rem;
  }

  .empty-title {
    font-size: 1.3rem;
    font-weight: 650;
    color: #1e293b;
    margin-bottom: 0.4rem;
  }

  .empty-hint {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  /* 消息行 */
  .message-row {
    display: flex;
    gap: 0.8rem;
    align-items: flex-end;
    animation: fadeIn 0.3s ease;
  }

  .message-row.user {
    justify-content: flex-end;
  }

  .message-row.assistant {
    justify-content: flex-start;
  }

  /* 头像 */
  .avatar {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 1rem;
    overflow: hidden;
  }

  /* 头像图片 */
  .avatar-img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
  }

  .assistant-avatar {
    background: #fff7ed;
    font-size: 1.2rem;
  }

  .user-avatar {
    background: #ff6b35;
    color: white;
  }

  /* 消息气泡 */
  .message-bubble {
    max-width: 65%;
    padding: 0.8rem 1.2rem;
    border-radius: 1rem;
    word-wrap: break-word;
    white-space: pre-wrap;
    line-height: 1.6;
    font-size: 0.9rem;
  }

  .message-bubble.user {
    background: #ff6b35;
    color: white;
    border-bottom-right-radius: 0.3rem;
  }

  .message-bubble.assistant {
    background: white;
    color: #334155;
    border-bottom-left-radius: 0.3rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    border: 1px solid #f1f5f9;
  }

  .message-content {
    line-height: 1.6;
  }

  .message-time {
    font-size: 0.65rem;
    opacity: 0.6;
    margin-top: 0.3rem;
    text-align: right;
  }

  /* 加载动画 */
  .loading-dots {
    display: flex;
    gap: 4px;
    padding: 0.2rem 0;
  }

  .loading-dots span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #94a3b8;
    animation: dotPulse 1.4s infinite;
  }

  .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
  .loading-dots span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes dotPulse {
    0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
    30% { opacity: 1; transform: scale(1); }
  }

  /* ============================================
     输入区域
     ============================================ */
  .input-area {
    padding: 1rem 1.5rem 1.2rem;
    border-top: 1px solid #e2e8f0;
    background: white;
    flex-shrink: 0;
    padding-bottom: calc(1.2rem + env(safe-area-inset-bottom, 0px));
  }

  .input-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #f8fafc;
    border: 2px solid #e2e8f0;
    border-radius: 1.5rem;
    padding: 0.3rem 0.5rem;
    transition: border-color 0.2s;
  }

  .input-container:focus-within {
    border-color: #ff6b35;
    background: white;
  }

  .tool-btn {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1rem;
    padding: 0.5rem;
    border-radius: 0.5rem;
    cursor: pointer;
    flex-shrink: 0;
    transition: color 0.15s;
  }

  .tool-btn:hover {
    color: #64748b;
  }

  .chat-input {
    flex: 1;
    padding: 0.5rem 0.3rem;
    border: none;
    outline: none;
    font-size: 0.9rem;
    background: transparent;
    color: #334155;
    min-width: 0;
  }

  .chat-input::placeholder {
    color: #94a3b8;
  }

  /* 发送按钮 - 带箭头指示 */
  .send-btn {
    background: #ff6b35;
    border: none;
    color: white;
    padding: 0.4rem 0.8rem;
    border-radius: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.2s;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .send-btn::after {
    content: '→';
    font-size: 1.1rem;
    transition: transform 0.2s;
  }

  .send-btn:hover:not(:disabled)::after {
    transform: translateX(3px);
  }

  .send-btn:hover:not(:disabled) {
    background: #e55a2b;
    transform: scale(1.02);
  }

  .send-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .send-btn i {
    font-size: 0.9rem;
  }

  .send-label {
    font-size: 0.85rem;
  }

  /* 手机端优化 */
  @media (max-width: 768px) {
    .send-btn {
      padding: 0.3rem 0.6rem;
    }

    .send-label {
      display: none;
    }

    .send-btn::after {
      content: '→';
    }
  }

  .disclaimer {
    text-align: center;
    font-size: 0.65rem;
    color: #94a3b8;
    margin-top: 0.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
  }

  /* ============================================
     动画
     ============================================ */
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* ============================================
     滚动条
     ============================================ */
  .chat-container::-webkit-scrollbar {
    width: 4px;
  }

  .chat-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .chat-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
  }

  /* ============================================
     平板端 (768px - 1024px)
     ============================================ */
  @media (max-width: 1024px) {
    .chat-sidebar {
      width: 240px;
    }

    .chat-container {
      padding: 1.2rem 1.5rem;
    }

    .message-bubble {
      max-width: 75%;
    }
  }

  /* ============================================
     手机端 (最大768px) - 隐藏侧边栏
     ============================================ */
  @media (max-width: 768px) {
    .chat-sidebar {
      display: none;
    }

    .mobile-back-btn {
      display: block;
    }

    .desktop-clear-btn {
      display: flex;
    }

    .chat-header {
      padding: 0.8rem 1rem;
    }

    .header-title {
      font-size: 1rem;
    }

    .quick-questions {
      padding: 0.6rem 0.8rem;
      gap: 0.4rem;
    }

    .question-btn {
      font-size: 0.75rem;
      padding: 0.35rem 0.8rem;
    }

    .chat-container {
      padding: 0.8rem;
      gap: 0.8rem;
    }

    .message-bubble {
      max-width: 85%;
      padding: 0.7rem 1rem;
      font-size: 0.85rem;
    }

    .message-bubble.user {
      max-width: 80%;
    }

    .avatar {
      width: 1.8rem;
      height: 1.8rem;
      font-size: 0.8rem;
    }

    .assistant-avatar {
      font-size: 1rem;
    }

    .empty-state {
      padding: 2rem 1.2rem;
      margin: 0.5rem;
    }

    .empty-icon {
      font-size: 3rem;
    }

    .empty-title {
      font-size: 1.1rem;
    }

    .input-area {
      padding: 0.7rem 0.8rem 0.9rem;
      padding-bottom: calc(0.9rem + env(safe-area-inset-bottom, 0px));
    }

    .input-container {
      border-radius: 1.2rem;
      padding: 0.2rem 0.3rem;
    }

    .chat-input {
      font-size: 0.85rem;
    }
  }

  /* ============================================
     小屏手机 (最大480px)
     ============================================ */
  @media (max-width: 480px) {
    .chat-header {
      padding: 0.6rem 0.8rem;
    }

    .header-title {
      font-size: 0.9rem;
    }

    .quick-questions {
      padding: 0.5rem 0.6rem;
    }

    .question-btn {
      font-size: 0.7rem;
      padding: 0.3rem 0.7rem;
    }

    .chat-container {
      padding: 0.6rem;
      gap: 0.6rem;
    }

    .message-bubble {
      max-width: 90%;
      padding: 0.6rem 0.8rem;
      font-size: 0.8rem;
    }

    .empty-state {
      padding: 1.5rem 1rem;
    }

    .empty-icon {
      font-size: 2.5rem;
    }

    .send-btn {
      padding: 0.2rem 0.5rem;
    }
  }

  /* ============================================
     横屏手机优化
     ============================================ */
  @media (max-height: 500px) and (orientation: landscape) {
    .chat-header {
      padding: 0.5rem 1rem;
    }

    .quick-questions {
      display: none;
    }

    .chat-container {
      padding: 0.5rem 1rem;
    }

    .empty-state {
      padding: 1rem;
    }

    .empty-icon {
      font-size: 2rem;
    }

    .input-area {
      padding: 0.5rem 1rem 0.6rem;
    }
  }
  </style>
