<template>
    <div class="profile-view">
      <div class="profile-container">
        <!-- ============================================
             侧边栏 (与 ChatView 风格一致)
             ============================================ -->
        <aside class="profile-sidebar">
          <!-- 侧边栏头部 -->
          <div class="sidebar-header">
            <button class="sidebar-back-btn" @click="goHome">
              <i class="fas fa-arrow-left"></i>
              <span class="btn-label">返回</span>
            </button>
            <span class="sidebar-title">个人中心</span>
          </div>
  
          <!-- 用户信息卡片 -->
          <div class="profile-user-card">
            <div class="profile-avatar-wrapper">
              <img
                v-if="userInfo.avatar"
                :src="userInfo.avatar"
                alt="用户头像"
                class="profile-avatar"
              />
              <i v-else class="fas fa-user-circle profile-avatar-icon"></i>
              <button class="avatar-upload-btn" @click="triggerAvatarUpload">
                <i class="fas fa-camera"></i>
              </button>
            </div>
            <h3 class="profile-username">{{ userInfo.name || '用户' }}</h3>
            <span class="profile-user-status" :class="{ online: userInfo.isOnline }">
              <span class="status-dot-small"></span>
              {{ userInfo.isOnline ? '在线' : '离线' }}
            </span>
          </div>
  
          <!-- 菜单列表 -->
          <nav class="profile-menu">
            <div
              v-for="item in menuItems"
              :key="item.key"
              :class="['menu-item', { active: activeMenu === item.key }]"
              @click="activeMenu = item.key"
            >
              <i :class="item.icon"></i>
              <span>{{ item.label }}</span>
              <i v-if="item.badge" class="fas fa-chevron-right menu-arrow"></i>
            </div>
          </nav>
  
          <!-- 退出登录 -->
          <div class="sidebar-footer">
            <button class="logout-btn" @click="handleLogout">
              <i class="fas fa-sign-out-alt"></i>
              <span>退出登录</span>
            </button>
          </div>
        </aside>
  
        <!-- ============================================
             主内容区域
             ============================================ -->
        <main class="profile-main">
          <!-- 头部 -->
          <header class="profile-header">
            <div class="header-info">
              <i class="fas fa-user-circle"></i>
              <h2 class="header-title">{{ getMenuTitle }}</h2>
            </div>
          </header>
  
          <!-- 内容区 -->
          <div class="profile-content">
            <!-- 个人信息 -->
            <div v-if="activeMenu === 'profile'" class="content-panel">
              <div class="panel-header">
                <h3>基本信息</h3>
                <button class="edit-btn" @click="toggleEdit">
                  <i :class="isEditing ? 'fas fa-save' : 'fas fa-pen'"></i>
                  {{ isEditing ? '保存' : '编辑' }}
                </button>
              </div>
  
              <div class="info-grid">
                <div class="info-item">
                  <label>用户名</label>
                  <div class="info-value">
                    <input
                      v-if="isEditing"
                      v-model="editForm.username"
                      type="text"
                      placeholder="请输入用户名"
                    />
                    <span v-else>{{ userInfo.name || '未设置' }}</span>
                  </div>
                </div>
  
                <div class="info-item">
                  <label>手机号</label>
                  <div class="info-value">
                    <input
                      v-if="isEditing"
                      v-model="editForm.phone"
                      type="tel"
                      placeholder="请输入手机号"
                    />
                    <span v-else>{{ userInfo.phone || '未绑定' }}</span>
                  </div>
                </div>
  
                <div class="info-item">
                  <label>邮箱</label>
                  <div class="info-value">
                    <input
                      v-if="isEditing"
                      v-model="editForm.email"
                      type="email"
                      placeholder="请输入邮箱"
                    />
                    <span v-else>{{ userInfo.email || '未绑定' }}</span>
                  </div>
                </div>
  
                <div class="info-item">
                  <label>个性签名</label>
                  <div class="info-value">
                    <input
                      v-if="isEditing"
                      v-model="editForm.bio"
                      type="text"
                      placeholder="写一句话介绍自己"
                      maxlength="50"
                    />
                    <span v-else>{{ userInfo.bio || '这个人很懒，什么都没写~' }}</span>
                  </div>
                </div>
  
                <div class="info-item full-width">
                  <label>注册时间</label>
                  <div class="info-value">
                    <span class="info-meta">{{ userInfo.registerTime || '2026-01-01' }}</span>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 对话历史 -->
            <div v-if="activeMenu === 'history'" class="content-panel">
              <div class="panel-header">
                <h3>对话历史</h3>
                <span class="panel-count">
                  {{ conversationList.length }} 条记录
                  <span v-if="isLoadingConversations" class="loading-text">加载中...</span>
                </span>
              </div>
  
              <!-- 加载状态 -->
              <div v-if="isLoadingConversations" class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>加载对话记录...</p>
              </div>
  
              <!-- 空状态 -->
              <div v-else-if="conversationList.length === 0" class="empty-state">
                <i class="fas fa-comment-slash"></i>
                <p>暂无对话历史</p>
                <span class="empty-hint">去探索发现好店吧！</span>
              </div>
  
              <!-- 对话列表 -->
              <div v-else class="history-list">
                <div
                  v-for="conv in conversationList"
                  :key="conv.id"
                  class="history-item"
                  @click="goToChat(conv.id)"
                >
                  <div class="history-info">
                    <span class="history-title">{{ conv.title }}</span>
                    <span class="history-time">{{ conv.time }}</span>
                  </div>
                  <div class="history-actions">
                    <button class="delete-history-btn" @click.stop="deleteConversation(conv.id)">
                      <i class="fas fa-times"></i>
                    </button>
                    <i class="fas fa-chevron-right"></i>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 设置 -->
            <div v-if="activeMenu === 'settings'" class="content-panel">
              <div class="panel-header">
                <h3>设置</h3>
              </div>
  
              <div class="settings-list">
                <!-- 隐私设置 -->
                <div class="setting-item">
                  <div class="setting-info">
                    <i class="fas fa-lock"></i>
                    <span>隐私设置</span>
                  </div>
                  <button class="setting-action-btn" @click="showPrivacySettings">
                    <span>管理</span>
                    <i class="fas fa-chevron-right"></i>
                  </button>
                </div>
  
                <!-- 关于探店助手 -->
                <div class="setting-item">
                  <div class="setting-info">
                    <i class="fas fa-info-circle"></i>
                    <span>关于探店助手</span>
                  </div>
                  <button class="setting-action-btn" @click="showAbout">
                    <span>v1.0.0</span>
                    <i class="fas fa-chevron-right"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
  
      <!-- 隐藏的文件上传 -->
      <input
        ref="avatarInput"
        type="file"
        accept="image/*"
        style="display: none"
        @change="handleAvatarUpload"
      />
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  
  // ============================================
  // 类型定义
  // ============================================
  interface UserInfo {
    id: number
    name: string
    avatar: string
    phone: string
    email: string
    bio: string
    isOnline: boolean
    registerTime: string
  }
  
  interface Conversation {
    id: number
    title: string
    time: string
    icon?: string
    active?: boolean
  }
  
  // ============================================
  // 状态
  // ============================================
  const activeMenu = ref('profile')
  const isEditing = ref(false)
  const avatarInput = ref<HTMLInputElement | null>(null)
  const isLoadingConversations = ref(false)
  
  // 用户信息
  const userInfo = ref<UserInfo>({
    id: 1,
    name: '用户',
    avatar: '',
    phone: '',
    email: '',
    bio: '',
    isOnline: true,
    registerTime: '2026-01-01',
  })
  
  // 编辑表单
  const editForm = reactive({
    username: '',
    phone: '',
    email: '',
    bio: '',
  })
  
  // 菜单项
  const menuItems = [
    { key: 'profile', label: '个人信息', icon: 'fas fa-user' },
    { key: 'history', label: '对话历史', icon: 'fas fa-comment-dots', badge: true },
    { key: 'settings', label: '设置', icon: 'fas fa-cog' },
  ]
  
  // 对话列表（与 ChatView 共享数据源）
  const conversationList = ref<Conversation[]>([])
  
  // ============================================
  // 计算属性
  // ============================================
  const getMenuTitle = computed(() => {
    const item = menuItems.find(m => m.key === activeMenu.value)
    return item?.label || '个人中心'
  })
  
  // ============================================
  // 生命周期
  // ============================================
  onMounted(() => {
    loadUserInfo()
    loadConversations()
  })
  
  // ============================================
  // 加载用户信息
  // ============================================
  const loadUserInfo = () => {
    const userStr = localStorage.getItem('userInfo')
    if (userStr) {
      try {
        const data = JSON.parse(userStr)
        userInfo.value = { ...userInfo.value, ...data }
        // 同步到编辑表单
        editForm.username = userInfo.value.name
        editForm.phone = userInfo.value.phone
        editForm.email = userInfo.value.email
        editForm.bio = userInfo.value.bio
      } catch (e) {
        console.error('解析用户信息失败:', e)
      }
    }
  }
  
  // ============================================
  // 获取对话列表（与 ChatView 中的 loadConversations 完全一致）
  // ============================================
  const loadConversations = async (): Promise<void> => {
    isLoadingConversations.value = true
    try {
      const response = await fetch('/api/conversations', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
        },
      })
  
      if (response.ok) {
        const data = await response.json()
        const list = data.data || data || []
  
        if (Array.isArray(list) && list.length > 0) {
          conversationList.value = list.map((item: any, index: number) => ({
            id: item.id || index + 1,
            title: item.title || '未命名对话',
            time: item.time || '刚刚',
            icon: item.icon || 'fas fa-comment',
            active: item.active || index === 0,
          }))
        } else {
          // 没有历史对话，设置为空数组
          conversationList.value = []
        }
      } else {
        console.warn('获取对话列表失败')
        // 如果 API 失败，使用默认数据（降级方案）
        setDefaultConversations()
      }
    } catch (error) {
      console.error('获取对话列表异常:', error)
      // 如果 API 异常，使用默认数据（降级方案）
      setDefaultConversations()
    } finally {
      isLoadingConversations.value = false
    }
  }
  
  // ============================================
  // 设置默认对话（降级方案，与 ChatView 一致）
  // ============================================
  const setDefaultConversations = (): void => {
    // 尝试从 localStorage 读取缓存
    try {
      const cached = localStorage.getItem('conversations')
      if (cached) {
        const parsed = JSON.parse(cached)
        if (Array.isArray(parsed) && parsed.length > 0) {
          conversationList.value = parsed
          return
        }
      }
    } catch (e) {
      console.warn('读取缓存对话失败:', e)
    }
  
    // 如果没有缓存，使用空数组
    conversationList.value = []
  }
  
  // ============================================
  // 删除对话（与 ChatView 中的 deleteConversation 保持一致）
  // ============================================
  const deleteConversation = async (conversationId: number): Promise<void> => {
    const conversation = conversationList.value.find(c => c.id === conversationId)
    if (!conversation) return
  
    if (confirm(`确定要删除"${conversation.title}"吗？此操作不可恢复！`)) {
      try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          },
        })
  
        if (response.ok || response.status === 204) {
          // 从列表中移除
          conversationList.value = conversationList.value.filter(c => c.id !== conversationId)
          
          // 更新缓存
          try {
            localStorage.setItem('conversations', JSON.stringify(conversationList.value))
          } catch (e) {
            console.warn('更新缓存失败:', e)
          }
        } else {
          throw new Error('删除失败')
        }
      } catch (error) {
        console.error('删除对话失败:', error)
        alert('删除失败，请稍后重试')
      }
    }
  }
  
  // ============================================
  // 头像上传
  // ============================================
  const triggerAvatarUpload = () => {
    avatarInput.value?.click()
  }
  
  const handleAvatarUpload = (event: Event) => {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return
  
    if (file.size > 2 * 1024 * 1024) {
      alert('图片大小不能超过2MB')
      return
    }
  
    const reader = new FileReader()
    reader.onload = (e) => {
      userInfo.value.avatar = e.target?.result as string
      saveUserInfo()
    }
    reader.readAsDataURL(file)
  }
  
  // ============================================
  // 保存用户信息
  // ============================================
  const saveUserInfo = () => {
    const data = {
      ...userInfo.value,
      name: editForm.username,
      phone: editForm.phone,
      email: editForm.email,
      bio: editForm.bio,
    }
    localStorage.setItem('userInfo', JSON.stringify(data))
  }
  
  // ============================================
  // 编辑切换
  // ============================================
  const toggleEdit = () => {
    if (isEditing.value) {
      // 保存
      if (!editForm.username.trim()) {
        alert('用户名不能为空')
        return
      }
      userInfo.value.name = editForm.username.trim()
      userInfo.value.phone = editForm.phone.trim()
      userInfo.value.email = editForm.email.trim()
      userInfo.value.bio = editForm.bio.trim()
      saveUserInfo()
    }
    isEditing.value = !isEditing.value
  }
  
  // ============================================
  // 导航函数
  // ============================================
  const goHome = () => {
    router.push('/')
  }
  
  const goToChat = (convId?: number) => {
    router.push({
      path: '/chat',
      query: convId ? { id: String(convId) } : undefined,
    })
  }
  
  // ============================================
  // 设置操作
  // ============================================
  const showPrivacySettings = () => {
    alert('隐私设置页面开发中...')
  }
  
  const showAbout = () => {
    alert('探店助手 v1.0.0\n让选择更简单')
  }
  
  // ============================================
  // 退出登录
  // ============================================
  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      router.push('/')
    }
  }
  </script>
  
  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .profile-view {
    display: flex;
    width: 100%;
    height: 100vh;
    height: 100dvh;
    background: #f1f5f9;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  .profile-container {
    display: flex;
    width: 100%;
    height: 100%;
  }
  
  /* ============================================
     侧边栏
     ============================================ */
  .profile-sidebar {
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
  
  .sidebar-title {
    flex: 1;
    font-weight: 650;
    color: #1e293b;
    font-size: 1.05rem;
  }
  
  /* ============================================
     用户信息卡片
     ============================================ */
  .profile-user-card {
    padding: 1.5rem 1.2rem;
    text-align: center;
    border-bottom: 1px solid #f1f5f9;
  }
  
  .profile-avatar-wrapper {
    position: relative;
    display: inline-block;
    margin-bottom: 0.8rem;
  }
  
  .profile-avatar {
    width: 4.5rem;
    height: 4.5rem;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid #e2e8f0;
  }
  
  .profile-avatar-icon {
    font-size: 4.5rem;
    color: #94a3b8;
  }
  
  .avatar-upload-btn {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 2rem;
    height: 2rem;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border: 2px solid white;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    transition: all 0.2s;
  }
  
  .avatar-upload-btn:hover {
    transform: scale(1.1);
  }
  
  .profile-username {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.2rem;
  }
  
  .profile-user-status {
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    color: #94a3b8;
  }
  
  .profile-user-status.online {
    color: #22c55e;
  }
  
  .status-dot-small {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #94a3b8;
    display: inline-block;
  }
  
  .profile-user-status.online .status-dot-small {
    background: #22c55e;
  }
  
  /* ============================================
     菜单
     ============================================ */
  .profile-menu {
    flex: 1;
    padding: 0.8rem;
    overflow-y: auto;
  }
  
  .menu-item {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.7rem 1rem;
    border-radius: 0.7rem;
    cursor: pointer;
    transition: all 0.15s;
    color: #64748b;
  }
  
  .menu-item:hover {
    background: #f8fafc;
    color: #1e293b;
  }
  
  .menu-item.active {
    background: #eff6ff;
    color: #2563eb;
  }
  
  .menu-item i:first-child {
    font-size: 1rem;
    width: 1.2rem;
    text-align: center;
  }
  
  .menu-item span {
    flex: 1;
    font-size: 0.9rem;
    font-weight: 500;
  }
  
  .menu-arrow {
    font-size: 0.7rem;
    color: #94a3b8;
  }
  
  /* ============================================
     侧边栏底部
     ============================================ */
  .sidebar-footer {
    padding: 1rem 1.2rem;
    border-top: 1px solid #f1f5f9;
  }
  
  .logout-btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    padding: 0.7rem;
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 0.7rem;
    color: #dc2626;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .logout-btn:hover {
    background: #fee2e2;
    border-color: #f87171;
  }
  
  /* ============================================
     主内容区域
     ============================================ */
  .profile-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    background: #ffffff;
  }
  
  /* ============================================
     头部
     ============================================ */
  .profile-header {
    display: flex;
    align-items: center;
    padding: 1rem 2rem;
    background: linear-gradient(135deg, #2fb6e8 0%, #38b5eb 100%);
    color: white;
    flex-shrink: 0;
  }
  
  .header-info {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  
  .header-info > i {
    font-size: 1.3rem;
  }
  
  .header-title {
    font-size: 1.1rem;
    font-weight: 650;
  }
  
  /* ============================================
     内容区
     ============================================ */
  .profile-content {
    flex: 1;
    padding: 1.5rem 2rem;
    overflow-y: auto;
    background: #f8fafc;
  }
  
  .content-panel {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
  }
  
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #f1f5f9;
  }
  
  .panel-header h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #1e293b;
  }
  
  .panel-count {
    font-size: 0.8rem;
    color: #94a3b8;
  }
  
  .loading-text {
    color: #3b82f6;
    margin-left: 0.3rem;
  }
  
  .edit-btn {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 1rem;
    background: #f1f5f9;
    border: none;
    border-radius: 0.5rem;
    color: #475569;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .edit-btn:hover {
    background: #e2e8f0;
    color: #1e293b;
  }
  
  /* ============================================
     信息网格
     ============================================ */
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
  }
  
  .info-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  
  .info-item.full-width {
    grid-column: 1 / -1;
  }
  
  .info-item label {
    font-size: 0.8rem;
    color: #94a3b8;
    font-weight: 500;
  }
  
  .info-value {
    font-size: 0.95rem;
    color: #1e293b;
    padding: 0.4rem 0;
  }
  
  .info-value input {
    width: 100%;
    padding: 0.5rem 0.6rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    font-size: 0.9rem;
    color: #1e293b;
    background: #f8fafc;
    transition: all 0.2s;
  }
  
  .info-value input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
  }
  
  .info-meta {
    color: #94a3b8;
    font-size: 0.9rem;
  }
  
  /* ============================================
     加载状态
     ============================================ */
  .loading-state {
    text-align: center;
    padding: 2rem 1rem;
  }
  
  .loading-state i {
    font-size: 2rem;
    color: #3b82f6;
    margin-bottom: 0.5rem;
  }
  
  .loading-state p {
    color: #94a3b8;
    font-size: 0.9rem;
  }
  
  /* ============================================
     空状态
     ============================================ */
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
  }
  
  .empty-state i {
    font-size: 3rem;
    color: #cbd5e1;
    margin-bottom: 1rem;
  }
  
  .empty-state p {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 0.3rem;
  }
  
  .empty-hint {
    color: #94a3b8;
    font-size: 0.8rem;
  }
  
  /* ============================================
     对话历史列表
     ============================================ */
  .history-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  
  .history-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 1rem;
    border-radius: 0.6rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  
  .history-item:hover {
    background: #f8fafc;
  }
  
  .history-info {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    flex: 1;
  }
  
  .history-title {
    font-size: 0.9rem;
    color: #334155;
  }
  
  .history-time {
    font-size: 0.7rem;
    color: #94a3b8;
  }
  
  .history-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .delete-history-btn {
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
  
  .history-item:hover .delete-history-btn {
    opacity: 1;
  }
  
  .delete-history-btn:hover {
    background: #fef2f2;
    color: #dc2626;
  }
  
  .history-item i.fa-chevron-right {
    color: #94a3b8;
    font-size: 0.8rem;
  }
  
  /* ============================================
     设置列表
     ============================================ */
  .settings-list {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  
  .setting-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 1rem;
    border-radius: 0.6rem;
    transition: all 0.15s;
  }
  
  .setting-item:hover {
    background: #f8fafc;
  }
  
  .setting-info {
    display: flex;
    align-items: center;
    gap: 0.8rem;
  }
  
  .setting-info i {
    color: #94a3b8;
    font-size: 1rem;
    width: 1.2rem;
    text-align: center;
  }
  
  .setting-info span {
    font-size: 0.9rem;
    color: #334155;
  }
  
  .setting-action-btn {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 0.85rem;
    cursor: pointer;
    padding: 0.2rem 0.4rem;
    border-radius: 0.3rem;
    transition: all 0.2s;
  }
  
  .setting-action-btn:hover {
    color: #475569;
    background: #f1f5f9;
  }
  
  /* ============================================
     滚动条
     ============================================ */
  .profile-content::-webkit-scrollbar {
    width: 4px;
  }
  
  .profile-content::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .profile-content::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
  }
  
  /* ============================================
     平板端 (768px - 1024px)
     ============================================ */
  @media (max-width: 1024px) {
    .profile-sidebar {
      width: 240px;
    }
  
    .profile-content {
      padding: 1.2rem 1.5rem;
    }
  }
  
  /* ============================================
     手机端 (最大768px)
     ============================================ */
  @media (max-width: 768px) {
    .profile-sidebar {
      display: none;
    }
  
    .profile-main {
      width: 100%;
    }
  
    .profile-header {
      padding: 0.8rem 1rem;
    }
  
    .profile-content {
      padding: 0.8rem;
    }
  
    .content-panel {
      padding: 1rem;
      border-radius: 0.8rem;
    }
  
    .info-grid {
      grid-template-columns: 1fr;
      gap: 0.8rem;
    }
  
    .panel-header {
      flex-wrap: wrap;
      gap: 0.5rem;
    }
  
    .btn-label {
      display: none;
    }
  
    .history-actions .delete-history-btn {
      opacity: 1;
    }
  }
  
  /* ============================================
     小屏手机 (最大480px)
     ============================================ */
  @media (max-width: 480px) {
    .profile-header {
      padding: 0.6rem 0.8rem;
    }
  
    .header-title {
      font-size: 0.95rem;
    }
  
    .profile-content {
      padding: 0.6rem;
    }
  
    .content-panel {
      padding: 0.8rem;
    }
  
    .setting-item {
      padding: 0.5rem 0.6rem;
    }
  
    .setting-info span {
      font-size: 0.8rem;
    }
  }
  
  /* ============================================
     横屏手机优化
     ============================================ */
  @media (max-height: 500px) and (orientation: landscape) {
    .profile-sidebar {
      width: 200px;
    }
  
    .profile-user-card {
      padding: 0.8rem 0.8rem;
    }
  
    .profile-avatar {
      width: 3rem;
      height: 3rem;
    }
  
    .profile-avatar-icon {
      font-size: 3rem;
    }
  
    .profile-username {
      font-size: 0.9rem;
    }
  
    .profile-menu {
      padding: 0.4rem;
    }
  
    .menu-item {
      padding: 0.4rem 0.6rem;
      font-size: 0.8rem;
    }
  
    .profile-content {
      padding: 0.6rem 1rem;
    }
  
    .content-panel {
      padding: 0.8rem;
    }
  
    .info-grid {
      grid-template-columns: 1fr 1fr;
      gap: 0.4rem;
    }
  }
  </style>