<template>
  <div class="home-view">
    <!-- 顶部导航栏 -->
    <header class="home-header">
      <div class="header-left">
        <div class="brand" @click="goHome">
          <img
            src="/images/2.png"
            alt="探店助手"
            class="brand-logo"
          />
          <span class="brand-name">探店助手</span>
        </div>
      </div>

      <div class="header-right">
        <!-- 搜索框 (桌面端) -->
        <div class="header-search desktop-only">
          <i class="fas fa-search"></i>
          <input
            ref="searchInput"
            type="text"
            placeholder="搜索餐厅、美食..."
            @keyup.enter="handleSearch"
          />
        </div>

        <!-- 用户操作 -->
        <div class="user-actions">
          <button class="login-btn-header" @click="goToLogin" v-if="!isLoggedIn">
            <i class="fas fa-user"></i>
            <span>登录</span>
          </button>
          <div class="user-profile" v-else @click="goToProfile">
            <img
              v-if="userInfo.avatar"
              :src="userInfo.avatar"
              alt="用户头像"
              class="header-avatar"
            />
            <i v-else class="fas fa-user-circle"></i>
            <span class="user-name-display">{{ userInfo.name || '用户' }}</span>
          </div>
        </div>
      </div>
    </header>

    <div class="home-container">
      <!-- 移动端搜索 -->
      <div class="mobile-search mobile-only">
        <div class="mobile-search-input" @click="goToChat">
          <i class="fas fa-search"></i>
          <span>搜索餐厅、美食...</span>
        </div>
      </div>

      <!-- 英雄区域 -->
      <div class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">
            发现 <span class="highlight">附近</span> 的好店
          </h1>
          <p class="hero-subtitle">
            基于真实评价 · 环境 · 菜单 · 营业状态，告诉你「推荐什么、为什么推荐」
          </p>
        </div>
      </div>

      <!-- 对话式交互入口卡片 -->
      <div class="chat-entry-card">
        <div class="card-header">
          <div class="card-header-left">
            <i class="fas fa-mug-hot"></i>
            <span>今天想探索什么？</span>
          </div>
          <span class="card-badge">AI 智能</span>
        </div>

        <!-- 输入框区域 - 支持直接输入 -->
        <div class="input-wrapper">
          <div class="search-input">
            <i class="fas fa-search search-icon"></i>
            <input
              v-model="inputQuery"
              type="text"
              class="chat-input-field"
              placeholder="例如：附近哪家咖啡馆适合写作业，比较安静？"
              @keyup.enter="sendQuery"
              ref="queryInput"
            />
          </div>
          <button class="send-btn" @click="sendQuery" :disabled="!inputQuery.trim()">
            <i class="fas fa-arrow-right"></i>
          </button>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="quick-actions">
        <div class="quick-action-item" @click="goToChatWithQuery('附近餐厅推荐')">
          <i class="fas fa-utensils"></i>
          <span>找餐厅</span>
        </div>
        <div class="quick-action-item" @click="goToChatWithQuery('适合约会的餐厅')">
          <i class="fas fa-heart"></i>
          <span>约会推荐</span>
        </div>
        <div class="quick-action-item" @click="goToChatWithQuery('人均50以内的餐厅')">
          <i class="fas fa-coins"></i>
          <span>平价美食</span>
        </div>
        <div class="quick-action-item" @click="goToChatWithQuery('安静的咖啡馆')">
          <i class="fas fa-mug-saucer"></i>
          <span>咖啡馆</span>
        </div>
        <div class="quick-action-item" @click="goToChatWithQuery('附近火锅店')">
          <i class="fas fa-fire"></i>
          <span>火锅</span>
        </div>
        <div class="quick-action-item" @click="goToChatWithQuery('深夜食堂')">
          <i class="fas fa-moon"></i>
          <span>深夜食堂</span>
        </div>
      </div>

      <!-- 跳转按钮 -->
      <div class="navigate-section">
        <button class="navigate-btn" @click="goToChat">
          <i class="fas fa-comments"></i>
          进入完整对话
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ============================================
// 状态
// ============================================
const isLoggedIn = ref(false)
const inputQuery = ref('')
const queryInput = ref<HTMLInputElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)

const userInfo = ref({
  id: 0,
  name: '',
  avatar: '',
})

// ============================================
// 检查登录状态
// ============================================
const checkLoginStatus = () => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('userInfo')

  if (token && userStr) {
    try {
      userInfo.value = JSON.parse(userStr)
      isLoggedIn.value = true
    } catch (e) {
      console.error('解析用户信息失败:', e)
    }
  }
}

onMounted(() => {
  checkLoginStatus()
  // 聚焦到输入框
  nextTick(() => {
    queryInput.value?.focus()
  })
})

// ============================================
// 发送查询（输入框）
// ============================================
const sendQuery = () => {
  const query = inputQuery.value.trim()
  if (!query) return

  // 跳转到聊天页面并传递查询参数
  router.push({
    path: '/chat',
    query: { q: query }
  })
}

// ============================================
// 快捷入口点击 - 直接跳转到聊天并发送消息
// ============================================
const goToChatWithQuery = (query: string) => {
  router.push('/restaurants')
}

// ============================================
// 导航函数
// ============================================
const goHome = () => {
  router.push('/')
}

const goToChat = () => {
  router.push('/chat')
}

const goToLogin = () => {
  router.push('/login')
}

const goToProfile = () => {
  router.push('/profile')
}

const handleSearch = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.value.trim()) {
    router.push({
      path: '/chat',
      query: { q: input.value.trim() }
    })
  }
}
</script>

<style scoped>
/* ============================================
   重置与基础
   ============================================ */
.home-view {
  position: relative;
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

/* 用伪元素加载背景图 */
.home-view::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  background:
    url('/images/3.png') center / cover no-repeat fixed;
  opacity: 0.3;  /* 控制透明度，0-1 之间调整 */
}

/* 所有内容在背景之上 */
.home-header,
.home-container {
  position: relative;
  z-index: 1;
}
/* ============================================
   顶部导航栏
   ============================================ */
.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 2.5rem;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(8px);
}

.header-left {
  display: flex;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
}

.brand-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.brand-name {
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
}

.brand-name span {
  color: #3b82f6;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-search {
  display: flex;
  align-items: center;
  background: #f1f5f9;
  border-radius: 2rem;
  padding: 0.3rem 0.8rem;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.header-search:focus-within {
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}

.header-search i {
  color: #94a3b8;
  font-size: 0.85rem;
}

.header-search input {
  border: none;
  outline: none;
  background: transparent;
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
  color: #1e293b;
  width: 180px;
}

.header-search input::placeholder {
  color: #94a3b8;
}

.user-actions {
  display: flex;
  align-items: center;
}

.login-btn-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  padding: 0.4rem 1.2rem;
  border-radius: 2rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.login-btn-header:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.2rem 0.8rem 0.2rem 0.2rem;
  border-radius: 2rem;
  transition: background 0.2s;
}

.user-profile:hover {
  background: #f1f5f9;
}

.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e2e8f0;
}

.user-profile > i {
  font-size: 2rem;
  color: #94a3b8;
}

.user-name-display {
  font-size: 0.85rem;
  color: #334155;
  font-weight: 500;
}

/* ============================================
   主容器
   ============================================ */
.home-container {
  flex: 1;
  width: 100%;
  max-width: 1100px;
  padding: 2rem 2.5rem 3rem;
  margin: 0 auto;
  box-sizing: border-box;
}

/* ============================================
   移动端搜索
   ============================================ */
.mobile-search {
  margin-bottom: 1.5rem;
}

.mobile-search-input {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.8rem;
  padding: 0.7rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mobile-search-input:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.08);
}

.mobile-search-input i {
  color: #94a3b8;
}

.mobile-search-input span {
  color: #94a3b8;
  font-size: 0.9rem;
}

/* ============================================
   英雄区域
   ============================================ */
.hero-section {
  text-align: center;
  padding: 1.5rem 0 2.5rem;
}

.hero-title {
  font-size: 2.6rem;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 0.8rem;
  letter-spacing: -0.5px;
}

.hero-title .highlight {
  color: #3b82f6;
  position: relative;
}

.hero-title .highlight::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 0;
  width: 100%;
  height: 4px;
  background: rgba(59, 130, 246, 0.25);
  border-radius: 2px;
}

.hero-subtitle {
  color: #64748b;
  font-size: 1.05rem;
  font-weight: 400;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ============================================
   对话入口卡片
   ============================================ */
.chat-entry-card {
  background: linear-gradient(135deg, #f8faff 0%, #f1f5fe 100%);
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  padding: 2rem;
  margin-bottom: 2.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;
}

.chat-entry-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.2rem;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
}

.card-header-left i {
  color: #f59e0b;
}

.card-badge {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.7rem;
  border-radius: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 0.4rem 0.4rem 0.4rem 1.2rem;
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}

.search-input {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0;
  min-width: 0;
}

.search-icon {
  color: #94a3b8;
  font-size: 1rem;
  flex-shrink: 0;
}

.chat-input-field {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.95rem;
  color: #1e293b;
  min-width: 0;
  padding: 0;
}

.chat-input-field::placeholder {
  color: #94a3b8;
}

.send-btn {
  background: #2563eb;
  color: white;
  border: none;
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1rem;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #1d4ed8;
  transform: scale(1.02);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
}

.example-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin-top: 1.2rem;
}

.tag {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-size: 0.85rem;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.tag:hover {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1e293b;
  transform: translateY(-1px);
}

.tag i {
  color: #94a3b8;
  font-size: 0.75rem;
}

/* ============================================
   快捷入口
   ============================================ */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.8rem;
  margin-bottom: 2.5rem;
}

.quick-action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.2rem 0.5rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-action-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
  transform: translateY(-3px);
}

.quick-action-item:active {
  transform: scale(0.95);
}

.quick-action-item i {
  font-size: 1.6rem;
  color: #3b82f6;
  margin-bottom: 0.4rem;
}

.quick-action-item span {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

/* ============================================
   跳转按钮
   ============================================ */
.navigate-section {
  display: flex;
  justify-content: center;
}

.navigate-btn {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 2.5rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 0.8rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.navigate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3);
}

.navigate-btn:active {
  transform: translateY(0);
}

.navigate-btn i:last-child {
  transition: transform 0.2s;
}

.navigate-btn:hover i:last-child {
  transform: translateX(4px);
}

/* ============================================
   响应式工具类
   ============================================ */
.desktop-only {
  display: flex;
}

.mobile-only {
  display: none;
}

/* ============================================
   平板端 (768px - 1024px)
   ============================================ */
@media (max-width: 1024px) {
  .home-header {
    padding: 0.6rem 1.5rem;
  }

  .home-container {
    padding: 1.5rem;
  }

  .hero-title {
    font-size: 2.2rem;
  }

  .header-search input {
    width: 130px;
  }

  .quick-actions {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* ============================================
   手机端 (最大768px)
   ============================================ */
@media (max-width: 768px) {
  .home-header {
    padding: 0.6rem 1rem;
  }

  .brand-logo {
    width: 28px;
    height: 28px;
  }

  .brand-name {
    font-size: 1rem;
  }

  .desktop-only {
    display: none !important;
  }

  .mobile-only {
    display: block;
  }

  .home-container {
    padding: 1rem 1rem 2rem;
  }

  .hero-section {
    padding: 0 0 1.5rem;
  }

  .hero-title {
    font-size: 1.8rem;
  }

  .hero-subtitle {
    font-size: 0.9rem;
  }

  .chat-entry-card {
    padding: 1.2rem;
    border-radius: 1rem;
    margin-bottom: 1.5rem;
  }

  .card-header {
    margin-bottom: 0.8rem;
  }

  .card-header-left {
    font-size: 1rem;
  }

  .card-badge {
    font-size: 0.6rem;
    padding: 0.15rem 0.6rem;
  }

  .input-wrapper {
    padding: 0.3rem 0.3rem 0.3rem 0.8rem;
    border-radius: 0.8rem;
  }

  .chat-input-field {
    font-size: 0.85rem;
  }

  .chat-input-field::placeholder {
    font-size: 0.8rem;
  }

  .send-btn {
    width: 2.3rem;
    height: 2.3rem;
    border-radius: 0.6rem;
    font-size: 0.9rem;
  }

  .example-tags {
    gap: 0.5rem;
    margin-top: 0.8rem;
  }

  .tag {
    font-size: 0.75rem;
    padding: 0.4rem 0.8rem;
  }

  .quick-actions {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .quick-action-item {
    padding: 0.8rem 0.3rem;
  }

  .quick-action-item i {
    font-size: 1.3rem;
  }

  .quick-action-item span {
    font-size: 0.7rem;
  }

  .navigate-btn {
    width: 100%;
    justify-content: center;
    padding: 0.8rem 1.5rem;
    font-size: 0.95rem;
    border-radius: 0.8rem;
  }

  .user-name-display {
    display: none;
  }

  .login-btn-header span {
    display: none;
  }

  .login-btn-header {
    padding: 0.4rem 0.8rem;
  }

  .user-profile {
    padding: 0.2rem;
  }
}

/* ============================================
   小屏手机 (最大480px)
   ============================================ */
@media (max-width: 480px) {
  .home-header {
    padding: 0.4rem 0.8rem;
  }

  .brand-logo {
    width: 24px;
    height: 24px;
  }

  .brand-name {
    font-size: 0.9rem;
  }

  .home-container {
    padding: 0.8rem 0.8rem 1.5rem;
  }

  .hero-title {
    font-size: 1.5rem;
  }

  .hero-subtitle {
    font-size: 0.8rem;
  }

  .chat-entry-card {
    padding: 1rem;
  }

  .card-header-left {
    font-size: 0.9rem;
  }

  .chat-input-field {
    font-size: 0.8rem;
  }

  .tag {
    font-size: 0.7rem;
    padding: 0.3rem 0.6rem;
  }

  .quick-actions {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.4rem;
  }

  .quick-action-item {
    padding: 0.6rem 0.2rem;
    border-radius: 0.7rem;
  }

  .quick-action-item i {
    font-size: 1.1rem;
  }

  .quick-action-item span {
    font-size: 0.65rem;
  }
}

/* ============================================
   横屏手机优化
   ============================================ */
@media (max-height: 500px) and (orientation: landscape) {
  .home-header {
    padding: 0.4rem 1rem;
  }

  .hero-section {
    padding: 0.5rem 0 1rem;
  }

  .hero-title {
    font-size: 1.6rem;
  }

  .chat-entry-card {
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .example-tags {
    display: none;
  }

  .quick-actions {
    grid-template-columns: repeat(6, 1fr);
    gap: 0.4rem;
    margin-bottom: 1rem;
  }

  .quick-action-item {
    padding: 0.4rem 0.2rem;
  }

  .quick-action-item i {
    font-size: 1rem;
  }

  .quick-action-item span {
    font-size: 0.6rem;
  }
}
</style>
