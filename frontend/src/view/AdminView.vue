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
  <!-- 头像可点击 -->
  <div class="avatar-wrapper" @click="triggerAdminAvatarUpload" title="更换头像">
    <img
      v-if="adminInfo.avatar"
      :src="getFullAvatarUrl(adminInfo.avatar)"
      alt="管理员头像"
      class="admin-avatar"
      @error="adminInfo.avatar = ''"
    />
    <i v-else class="fas fa-user-circle admin-avatar-icon"></i>
    <!-- 小相机提示（可选） -->
    <span class="avatar-hover-tip">
      <i class="fas fa-camera"></i>
    </span>
  </div>
  <span class="admin-name">{{ adminInfo.name || '管理员' }}</span>
</div>

<!-- 隐藏的文件选择器 -->
<input
  ref="adminAvatarInput"
  type="file"
  accept="image/*"
  style="display: none"
  @change="handleAdminAvatarUpload"
/>
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
            <span class="table-count">共 {{ totalUsers }} 位用户</span>
          </div>
          <div class="table-header-right">
            <div class="search-box">
              <i class="fas fa-search"></i>
              <input
                v-model="searchKeyword"
                type="text"
                placeholder="搜索用户名"
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
                :class="{ 'row-active': user.is_online }"
              >
                <td class="col-id">#{{ user.id }}</td>
                <td class="col-name">
                  <div class="user-info-cell">
                    <img
  v-if="user.avatar"
  :src="getFullAvatarUrl(user.avatar)"
  alt="头像"
  class="user-avatar-small"
  @error="user.avatar = ''"
/>
                    <i v-else class="fas fa-user-circle user-avatar-small-icon"></i>
                    <span>{{ user.username }}</span>
                  </div>
                </td>
                <td class="col-email">{{ user.email || '无' }}</td>
                <td class="col-bio">{{ user.bio || '无' }}</td>
                <td class="col-status">
                  <span class="status-badge" :class="{ online: user.is_online }">
                    <span class="status-dot-small"></span>
                    {{ user.is_online ? '在线' : '离线' }}
                  </span>
                </td>
                <td class="col-time">{{ formatTime(user.register_time) }}</td>
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
const adminAvatarInput = ref<HTMLInputElement | null>(null)
// ============================================
// 类型定义（与后端返回字段完全一致）
// ============================================
interface User {
  id: number | string
  username: string
  avatar: string
  is_online: boolean
  email: string
  bio: string
  register_time: string  // ISO 8601 格式
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
const totalUsers = ref(0)
const adminInfo = ref<AdminInfo>({
  id: 0,
  name: '管理员',
  avatar: ''
})
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// ============================================
// 计算属性
// ============================================

// 搜索过滤（按用户名）
const filteredUsers = computed(() => {
  if (!searchKeyword.value.trim()) {
    return userList.value
  }
  const keyword = searchKeyword.value.trim().toLowerCase()
  return userList.value.filter(user =>
    user.username.toLowerCase().includes(keyword)
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
// 辅助函数
// ============================================
const formatTime = (isoString: string) => {
  if (!isoString) return '未知'
  try {
    const date = new Date(isoString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return isoString
  }
}

// ============================================
// 【API 接口1】获取所有用户列表
// ============================================
// 接口地址: GET /api/admin/users
// 请求头: Authorization: Bearer {token}
// 响应: { code: 0, message: 'success', data: User[] }
// ============================================
const loadUsers = async () => {
  isLoading.value = true
  try {
    const response = await fetch('/api/admin/users', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
      }
    })
    if (!response.ok) throw new Error('获取用户列表失败')
    const result = await response.json()

    if (result.code === 0) {
      // 从 data.items 提取列表，并映射字段名
      const items = result.data.items || []
      userList.value = items.map((item: any) => {
  const avatar = item.avatar || ''
  const fullAvatar = avatar ? (avatar.startsWith('http') ? avatar : `http://localhost:8000${avatar}`) : ''
  return {
    id: item.id || 0,
    username: item.username || '用户',
    avatar: fullAvatar,
    email: item.email || '',
    bio: item.bio || '',
    is_online: item.is_online ?? false,
    register_time: item.register_time || '未知',
    role: item.role || 'user',
  }
})

      // 保存总数用于显示
      totalUsers.value = result.data.total || 0
    } else {
      throw new Error(result.message || '获取用户列表失败')
    }

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
// 响应: { code: 0, data: AdminInfo }
// ============================================
const loadAdminInfo = async () => {
  try {
    const response = await fetch('/api/user/profile', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
      }
    })
    if (!response.ok) throw new Error('获取管理员信息失败')
    const result = await response.json()
    // 根据后端实际返回结构处理（示例：{ code: 0, data: { ... } }）
    if (result.code === 0) {
      const data = result.data
      const avatar = data.avatar || ''
      const fullAvatar = avatar ? (avatar.startsWith('http') ? avatar : `http://localhost:8000${avatar}`) : ''
      adminInfo.value = {
        id: data.id || 0,
        name: data.username || data.name || '管理员',   // 优先取 username
        avatar: fullAvatar
      }
    } else {
      throw new Error(result.message || '获取管理员信息失败')
    }
  } catch (error) {
    console.error('获取管理员信息失败:', error)
    // 降级方案：使用默认值
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
// 导航功能
// ============================================
const goHome = () => {
  router.push('/')
}

// ============================================
// 退出登录
// ============================================
const handleLogout = async () => {
  if (!confirm('确定要退出登录吗？')) return

  // 防止重复点击
  const logoutBtn = document.querySelector('.logout-btn') as HTMLButtonElement
  if (logoutBtn) logoutBtn.disabled = true

  try {
    const token = localStorage.getItem('admin_token')
    const response = await fetch('http://localhost:8000/api/auth/logout', {
      method: 'POST', // 根据 RESTful 规范，退出通常用 POST
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token || ''}`
      }
      // 如果后端需要传递其他数据，可在此添加 body
    })

    // 如果后端返回非 2xx，依然可以尝试清除本地（但最好根据业务决定）
    if (!response.ok) {
      console.warn('退出接口响应异常，仍清除本地登录态')
    }

    // 无论接口成功与否，都清除本地存储（但最好接口成功后再清除，这里我建议接口成功后清除）
    // 如果你希望接口成功后再清除，可将清除代码放在 response.ok 判断内
    // 但为了用户体验，一般不管接口是否成功，都清除本地
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_userInfo')
    localStorage.removeItem('admin_role')
    // 如果还有其他业务相关的本地存储，一并清除

    // 跳转到登录页
    router.push('/admin/login')
  } catch (error) {
    console.error('退出请求失败:', error)
    // 即使请求失败，也清除本地，以免用户卡住
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_userInfo')
    localStorage.removeItem('admin_role')
    router.push('/admin/login')
  } finally {
    if (logoutBtn) logoutBtn.disabled = false
  }
}

// ============================================
// 头像完整 URL 转换（带时间戳防缓存）
// ============================================

const getFullAvatarUrl = (avatar: string): string => {
  if (!avatar) return ''
  if (avatar.startsWith('http')) {
    return `${avatar}?t=${Date.now()}`
  }
  const baseURL = 'http://localhost:8000'
  return `${baseURL}${avatar}?t=${Date.now()}`
}

// ============================================
// admin头像上传
// ============================================
const triggerAdminAvatarUpload = () => {
  adminAvatarInput.value?.click()
}

const handleAdminAvatarUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    alert('图片大小不能超过2MB')
    return
  }

  const formData = new FormData()
  formData.append('avatar', file)

  try {
    const response = await fetch('http://localhost:8000/api/user/avatar', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
        // 不要设置 Content-Type
      },
      body: formData
    })

    if (!response.ok) throw new Error(`上传失败 (HTTP ${response.status})`)
    const result = await response.json()
    if (result.code !== 0) throw new Error(result.message || '上传失败')

    // 拼接完整 URL
    const avatarUrl = result.data.avatar
    const fullUrl = avatarUrl.startsWith('http') ? avatarUrl : `http://localhost:8000${avatarUrl}`
    adminInfo.value.avatar = fullUrl

    // 更新 localStorage（若其他地方使用了 admin_userInfo）
    const saved = JSON.parse(localStorage.getItem('admin_userInfo') || '{}')
    saved.avatar = fullUrl
    localStorage.setItem('admin_userInfo', JSON.stringify(saved))

    alert('头像更新成功')
  } catch (error) {
    console.error('管理员头像上传失败:', error)
    alert(error instanceof Error ? error.message : '上传失败，请重试')
  }

  // 清空 input 值，以便重复选择同一文件
  input.value = ''
}

// ============================================
// 生命周期
// ============================================
onMounted(() => {
  // 检查是否为管理员（生产环境取消注释）
  const role = localStorage.getItem('admin_role')
  if (role !== 'admin') {
    alert('您没有管理员权限')
    router.push('/')
    return
  }
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

.col-email {
  min-width: 150px;
}

.col-bio {
  min-width: 120px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-status {
  width: 80px;
}

.col-time {
  min-width: 150px;
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

  .col-status {
    width: 60px;
  }
}

.avatar-wrapper {
  position: relative;
  display: inline-block;
  cursor: pointer;
  border-radius: 50%;
  line-height: 0;
}

.avatar-wrapper:hover .avatar-hover-tip {
  opacity: 1;
}

.avatar-hover-tip {
  position: absolute;
  bottom: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 0.5rem;
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}
</style>
