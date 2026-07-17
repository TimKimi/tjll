<template>
    <div class="admin-view">
      <!-- 顶部导航栏 -->
      <header class="admin-header">
        <div class="header-left">
          <div class="brand" @click="goHome">
            <img
              src="/images/2.png"
              alt="探店助手"
              class="brand-logo"
            />
            <span class="brand-name">探店助手 · 管理后台</span>
          </div>
        </div>
  
        <div class="header-right">
          <div class="admin-info">
            <img
              v-if="adminInfo.avatar"
              :src="adminInfo.avatar"
              alt="管理员头像"
              class="admin-avatar"
            />
            <i v-else class="fas fa-user-circle admin-avatar-icon"></i>
            <span class="admin-name">{{ adminInfo.name || '管理员' }}</span>
          </div>
          <button class="logout-btn" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i>
            <span>退出</span>
          </button>
        </div>
      </header>
  
      <div class="admin-container">
        <!-- 用户列表 -->
        <div class="user-table-wrapper">
          <div class="table-header">
            <div class="table-header-left">
              <h2 class="table-title">
                <i class="fas fa-list"></i>
                用户列表
              </h2>
              <span class="table-count">共 {{ userList.length }} 位用户</span>
            </div>
            <div class="table-header-right">
              <div class="search-box">
                <i class="fas fa-search"></i>
                <input
                  v-model="searchKeyword"
                  type="text"
                  placeholder="搜索用户名、手机号"
                  @input="handleSearch"
                />
              </div>
              <button class="refresh-btn" @click="loadUsers" :disabled="isLoading">
                <i :class="isLoading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"></i>
                <span>{{ isLoading ? '刷新中...' : '刷新' }}</span>
              </button>
            </div>
          </div>
  
          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>加载用户数据...</p>
          </div>
  
          <!-- 空状态 -->
          <div v-else-if="filteredUsers.length === 0" class="empty-state">
            <i class="fas fa-users-slash"></i>
            <p>{{ searchKeyword ? '未找到匹配的用户' : '暂无注册用户' }}</p>
          </div>
  
          <!-- 用户表格 -->
          <div v-else class="table-responsive">
            <table class="user-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>手机号</th>
                  <th>密码</th>
                  <th>邮箱</th>
                  <th>个性签名</th>
                  <th>状态</th>
                  <th>注册时间</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="user in paginatedUsers"
                  :key="user.id"
                  :class="{ 'row-active': user.isOnline }"
                >
                  <td class="col-id">#{{ user.id }}</td>
                  <td class="col-name">
                    <div class="user-info-cell">
                      <img
                        v-if="user.avatar"
                        :src="user.avatar"
                        alt="头像"
                        class="user-avatar-small"
                      />
                      <i v-else class="fas fa-user-circle user-avatar-small-icon"></i>
                      <span>{{ user.name }}</span>
                    </div>
                  </td>
                  <td class="col-phone">{{ user.phone || '未绑定' }}</td>
                  <td class="col-password">
                    <span v-if="showPasswordIds.includes(user.id)" class="password-text">
                      {{ user.password }}
                    </span>
                    <span v-else class="password-mask">••••••••</span>
                    <button class="show-password-btn" @click="togglePassword(user.id)">
                      <i :class="showPasswordIds.includes(user.id) ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                    </button>
                  </td>
                  <td class="col-email">{{ user.email || '无' }}</td>
                  <td class="col-bio">{{ user.bio || '无' }}</td>
                  <td class="col-status">
                    <span class="status-badge" :class="{ online: user.isOnline }">
                      <span class="status-dot-small"></span>
                      {{ user.isOnline ? '在线' : '离线' }}
                    </span>
                  </td>
                  <td class="col-time">{{ user.registerTime || '未知' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
  
          <!-- 分页 -->
          <div v-if="filteredUsers.length > 0" class="pagination-wrapper">
            <div class="pagination-info">
              显示 {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, filteredUsers.length) }} 条，共 {{ filteredUsers.length }} 条
            </div>
            <div class="pagination-buttons">
              <button
                class="page-btn"
                :disabled="currentPage === 1"
                @click="currentPage--"
              >
                <i class="fas fa-chevron-left"></i>
              </button>
              <span class="page-current">{{ currentPage }} / {{ totalPages }}</span>
              <button
                class="page-btn"
                :disabled="currentPage === totalPages"
                @click="currentPage++"
              >
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  
  // ============================================
  // 类型定义
  // ============================================
  interface User {
    id: number
    name: string
    avatar: string
    phone: string
    password: string
    email: string
    bio: string
    isOnline: boolean
    registerTime: string
  }
  
  interface AdminInfo {
    id: number
    name: string
    avatar: string
  }
  
  // ============================================
  // 状态
  // ============================================
  const isLoading = ref(false)
  const userList = ref<User[]>([])
  const adminInfo = ref<AdminInfo>({
    id: 0,
    name: '管理员',
    avatar: ''
  })
  const searchKeyword = ref('')
  const currentPage = ref(1)
  const pageSize = ref(10)
  const showPasswordIds = ref<number[]>([])
  
  // ============================================
  // 计算属性
  // ============================================
  
  // 搜索过滤
  const filteredUsers = computed(() => {
    if (!searchKeyword.value.trim()) {
      return userList.value
    }
    const keyword = searchKeyword.value.trim().toLowerCase()
    return userList.value.filter(user =>
      user.name.toLowerCase().includes(keyword) ||
      user.phone.includes(keyword)
    )
  })
  
  // 总页数
  const totalPages = computed(() => {
    return Math.ceil(filteredUsers.value.length / pageSize.value)
  })
  
  // 分页数据
  const paginatedUsers = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredUsers.value.slice(start, end)
  })
  
  // ============================================
  // 【API 接口1】获取所有用户列表
  // ============================================
  // 接口地址: GET /api/admin/users
  // 请求头: Authorization: Bearer {token}
  // 响应: { code: 200, data: User[] }
  // ============================================
  const loadUsers = async () => {
    isLoading.value = true
    try {
      // ========== 真实 API 调用（取消注释即可使用） ==========
      // const response = await fetch('/api/admin/users', {
      //   method: 'GET',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      //   }
      // })
      // if (!response.ok) throw new Error('获取用户列表失败')
      // const result = await response.json()
      // userList.value = result.data
      // ======================================================
  
      // ========== 模拟数据（开发测试用，接入 API 后删除） ==========
      await new Promise(resolve => setTimeout(resolve, 600))
      userList.value = [
        {
          id: 1,
          name: '张三',
          avatar: 'https://ui-avatars.com/api/?name=张三&background=3b82f6&color=fff',
          phone: '13800138001',
          password: '12345678',
          email: 'zhangsan@example.com',
          bio: '这个人很懒，什么都没写~',
          isOnline: true,
          registerTime: '2026-07-15 14:30'
        }
      ]
      // ======================================================
  
      currentPage.value = 1
    } catch (error) {
      console.error('加载用户列表失败:', error)
      alert('加载用户列表失败，请稍后重试')
    } finally {
      isLoading.value = false
    }
  }
  
  // ============================================
  // 【API 接口2】获取管理员信息
  // ============================================
  // 接口地址: GET /api/admin/profile
  // 请求头: Authorization: Bearer {token}
  // 响应: { code: 200, data: AdminInfo }
  // ============================================
  const loadAdminInfo = async () => {
    try {
      // ========== 真实 API 调用（取消注释即可使用） ==========
      // const response = await fetch('/api/admin/profile', {
      //   method: 'GET',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      //   }
      // })
      // if (!response.ok) throw new Error('获取管理员信息失败')
      // const result = await response.json()
      // adminInfo.value = result.data
      // ======================================================
  
      // ========== 模拟数据（开发测试用，接入 API 后删除） ==========
      adminInfo.value = {
        id: 0,
        name: '管理员',
        avatar: 'https://ui-avatars.com/api/?name=管理员&background=3b82f6&color=fff'
      }
      // ======================================================
    } catch (error) {
      console.error('获取管理员信息失败:', error)
      // 降级方案：使用默认头像
      adminInfo.value = {
        id: 0,
        name: '管理员',
        avatar: 'https://ui-avatars.com/api/?name=管理员&background=3b82f6&color=fff'
      }
    }
  }
  
  // ============================================
  // 搜索功能
  // ============================================
  const handleSearch = () => {
    currentPage.value = 1
  }
  
  // ============================================
  // 密码可见切换
  // ============================================
  const togglePassword = (userId: number) => {
    const index = showPasswordIds.value.indexOf(userId)
    if (index > -1) {
      showPasswordIds.value.splice(index, 1)
    } else {
      showPasswordIds.value.push(userId)
    }
  }
  
  // ============================================
  // 导航功能
  // ============================================
  const goHome = () => {
    router.push('/')
  }
  
  // ============================================
  // 退出登录
  // ============================================
  const handleLogout = () => {
    if (confirm('确定要退出管理后台吗？')) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      localStorage.removeItem('userRole')
      router.push('/login')
    }
  }
  
  // ============================================
  // 生命周期
  // ============================================
  onMounted(() => {
//       // 检查是否为管理员，注释后可访问界面
//   const role = localStorage.getItem('userRole')
//   if (role !== 'admin') {
//     alert('您没有管理员权限')
//     router.push('/')
//     return
//   }
    loadAdminInfo()
    loadUsers()
  })
  </script>
  
  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .admin-view {
    width: 100%;
    min-height: 100vh;
    min-height: 100dvh;
    background: #f1f5f9;
    display: flex;
    flex-direction: column;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  /* ============================================
     顶部导航栏
     ============================================ */
  .admin-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 2rem;
    background: #ffffff;
    border-bottom: 2px solid #e2e8f0;
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
    width: 32px;
    height: 32px;
    object-fit: contain;
  }
  
  .brand-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .admin-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.2rem 0.6rem 0.2rem 0.2rem;
    border-radius: 2rem;
    background: #f8fafc;
  }
  
  .admin-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .admin-avatar-icon {
    font-size: 2rem;
    color: #94a3b8;
  }
  
  .admin-name {
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
  }
  
  .logout-btn {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 1rem;
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 0.6rem;
    color: #dc2626;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .logout-btn:hover {
    background: #fee2e2;
    border-color: #f87171;
  }
  
  .logout-btn i {
    font-size: 0.9rem;
  }
  
  /* ============================================
     主容器
     ============================================ */
  .admin-container {
    flex: 1;
    padding: 1.5rem 2rem;
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
  }
  
  /* ============================================
     用户表格
     ============================================ */
  .user-table-wrapper {
    background: white;
    border-radius: 1rem;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }
  
  .table-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #f1f5f9;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .table-header-left {
    display: flex;
    align-items: center;
    gap: 0.8rem;
  }
  
  .table-title {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  
  .table-count {
    font-size: 0.8rem;
    color: #94a3b8;
  }
  
  .table-header-right {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  
  .search-box {
    display: flex;
    align-items: center;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 0.6rem;
    padding: 0.3rem 0.8rem;
    transition: all 0.2s;
  }
  
  .search-box:focus-within {
    border-color: #3b82f6;
    background: white;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
  }
  
  .search-box i {
    color: #94a3b8;
    font-size: 0.8rem;
  }
  
  .search-box input {
    border: none;
    outline: none;
    background: transparent;
    padding: 0.3rem 0.5rem;
    font-size: 0.85rem;
    color: #1e293b;
    width: 180px;
  }
  
  .search-box input::placeholder {
    color: #94a3b8;
  }
  
  .refresh-btn {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 1rem;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 0.6rem;
    color: #475569;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .refresh-btn:hover:not(:disabled) {
    background: #e2e8f0;
  }
  
  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  /* ============================================
     表格
     ============================================ */
  .table-responsive {
    overflow-x: auto;
  }
  
  .user-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  
  .user-table thead {
    background: #f8fafc;
  }
  
  .user-table th {
    padding: 0.7rem 1rem;
    text-align: left;
    font-weight: 600;
    color: #475569;
    border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
    position: sticky;
    top: 0;
    background: #f8fafc;
  }
  
  .user-table td {
    padding: 0.7rem 1rem;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
    vertical-align: middle;
  }
  
  .user-table tbody tr:hover {
    background: #f8fafc;
  }
  
  .user-table tbody tr.row-active {
    background: #f0fdf4;
  }
  
  .user-table tbody tr.row-active:hover {
    background: #dcfce7;
  }
  
  /* 列宽 */
  .col-id {
    width: 60px;
    color: #94a3b8;
    font-weight: 500;
  }
  
  .col-name {
    min-width: 120px;
  }
  
  .col-phone {
    min-width: 130px;
  }
  
  .col-password {
    min-width: 130px;
  }
  
  .col-email {
    min-width: 150px;
  }
  
  .col-bio {
    min-width: 120px;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .col-status {
    width: 80px;
  }
  
  .col-time {
    min-width: 140px;
    font-size: 0.75rem;
    color: #94a3b8;
  }
  
  /* 用户信息单元格 */
  .user-info-cell {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .user-avatar-small {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .user-avatar-small-icon {
    font-size: 1.6rem;
    color: #94a3b8;
  }
  
  /* 密码列 */
  .password-mask {
    font-family: monospace;
    letter-spacing: 1px;
    color: #94a3b8;
  }
  
  .password-text {
    font-family: monospace;
    color: #334155;
    letter-spacing: 0.5px;
  }
  
  .show-password-btn {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0.1rem 0.4rem;
    font-size: 0.8rem;
    transition: color 0.2s;
    margin-left: 0.3rem;
  }
  
  .show-password-btn:hover {
    color: #3b82f6;
  }
  
  /* 状态标签 */
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.75rem;
    color: #94a3b8;
  }
  
  .status-badge.online {
    color: #22c55e;
  }
  
  .status-dot-small {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #94a3b8;
    display: inline-block;
  }
  
  .status-badge.online .status-dot-small {
    background: #22c55e;
  }
  
  /* ============================================
     加载/空状态
     ============================================ */
  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 2rem;
    color: #94a3b8;
  }
  
  .loading-state i {
    font-size: 2rem;
    color: #3b82f6;
    margin-bottom: 0.5rem;
  }
  
  .empty-state i {
    font-size: 3rem;
    color: #cbd5e1;
    margin-bottom: 0.5rem;
  }
  
  /* ============================================
     分页
     ============================================ */
  .pagination-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.5rem;
    border-top: 1px solid #f1f5f9;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .pagination-info {
    font-size: 0.8rem;
    color: #94a3b8;
  }
  
  .pagination-buttons {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  
  .page-btn {
    width: 2rem;
    height: 2rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.4rem;
    background: white;
    color: #475569;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  
  .page-btn:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
  
  .page-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  
  .page-current {
    font-size: 0.85rem;
    color: #334155;
    padding: 0 0.4rem;
  }
  
  /* ============================================
     响应式
     ============================================ */
  @media (max-width: 768px) {
    .admin-header {
      padding: 0.5rem 1rem;
    }
  
    .brand-name {
      font-size: 0.95rem;
    }
  
    .admin-info .admin-name {
      display: none;
    }
  
    .logout-btn span {
      display: none;
    }
  
    .admin-container {
      padding: 0.8rem;
    }
  
    .table-header {
      flex-direction: column;
      align-items: stretch;
      padding: 0.8rem 1rem;
    }
  
    .table-header-right {
      flex-wrap: wrap;
    }
  
    .search-box input {
      width: 120px;
    }
  
    .user-table {
      font-size: 0.75rem;
    }
  
    .user-table th,
    .user-table td {
      padding: 0.4rem 0.6rem;
    }
  
    .col-email,
    .col-bio,
    .col-time {
      display: none;
    }
  
    .pagination-wrapper {
      flex-direction: column;
      align-items: center;
      padding: 0.6rem 1rem;
    }
  }
  
  @media (max-width: 480px) {
    .user-table th,
    .user-table td {
      padding: 0.3rem 0.4rem;
      font-size: 0.7rem;
    }
  
    .col-id {
      width: 40px;
    }
  
    .col-name {
      min-width: 80px;
    }
  
    .col-phone {
      min-width: 100px;
    }
  
    .col-password {
      min-width: 90px;
    }
  
    .col-status {
      width: 60px;
    }
  }
  </style>