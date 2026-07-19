<template>
    <div class="login-view">
      <div class="login-container">
        <!-- 返回按钮 -->
        <button class="back-btn" @click="goHome">
          <i class="fas fa-arrow-left"></i>
          <span>返回首页</span>
        </button>

        <!-- 登录卡片 -->
        <div class="login-card">
          <!-- Logo 区域 -->
<div class="login-header">
  <div class="logo-icon">
    <img
      src="/images/2.png"
      alt="探店助手"
      style="width: 56px; height: 56px; object-fit: contain;"
    />
  </div>
  <h1 class="login-title">欢迎回来</h1>
  <p class="login-subtitle">{{ isAdminMode ? '管理员登录' : '登录你的探店助手账号，开启智能探店之旅' }}</p>

  <!-- ✅ 新增：角色切换 -->
  <div class="role-toggle">
    <button
      type="button"
      class="role-btn"
      :class="{ active: !isAdminMode }"
      @click="isAdminMode = false"
    >
      <i class="fas fa-user"></i>
      用户
    </button>
    <button
      type="button"
      class="role-btn"
      :class="{ active: isAdminMode }"
      @click="isAdminMode = true"
    >
      <i class="fas fa-user-shield"></i>
      管理员
    </button>
  </div>
</div>

          <!-- 登录表单 -->
          <form class="login-form" @submit.prevent="handleLogin">
            <!-- 账号输入 -->
            <div class="form-group">
              <label for="username">
                <i class="fas fa-user"></i>
                用户名
              </label>
              <div class="input-wrapper">
                <i class="fas fa-user input-icon"></i>
                <input
                  id="username"
                  v-model="loginForm.username"
                  type="text"
                  placeholder="请输入用户名"
                  autocomplete="username"
                  required
                />
              </div>
            </div>

            <!-- 密码输入 -->
            <div class="form-group">
              <label for="password">
                <i class="fas fa-lock"></i>
                密码
              </label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input
                  id="password"
                  v-model="loginForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入密码"
                  autocomplete="current-password"
                  required
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
                <!-- ✅ 新增：管理员提示 -->
  <div v-if="isAdminMode" class="admin-hint">
    <i class="fas fa-info-circle"></i>
    <span>管理员账号：admin，密码：admin123</span>
  </div>
            </div>

            <!-- 选项 -->
            <div class="form-options">
              <label class="remember-me">
                <input type="checkbox" v-model="loginForm.remember" />
                <span>记住我</span>
              </label>
              <a href="#" class="forgot-link" @click.prevent="handleForgotPassword">
                忘记密码？
              </a>
            </div>

            <!-- 登录按钮 -->
            <button
              type="submit"
              class="login-btn"
              :disabled="isLoading"
            >
              <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>登录</span>
            </button>

            <!-- 错误提示 -->
            <div v-if="errorMessage" class="error-message">
              <i class="fas fa-exclamation-circle"></i>
              {{ errorMessage }}
            </div>
          </form>

          <!-- 注册入口 -->
          <div class="register-section">
            <span>还没有账号？</span>
            <a href="#" @click.prevent="goToRegister">立即注册</a>
          </div>

          <!-- 社交登录 -->
          <div class="social-login">
            <div class="divider">
              <span>其他登录方式</span>
            </div>
            <div class="social-buttons">
              <button class="social-btn wechat" @click="handleSocialLogin('wechat')">
                <i class="fab fa-weixin"></i>
              </button>
              <button class="social-btn qq" @click="handleSocialLogin('qq')">
                <i class="fab fa-qq"></i>
              </button>
              <button class="social-btn weibo" @click="handleSocialLogin('weibo')">
                <i class="fab fa-weibo"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 底部版权 -->
        <div class="login-footer">
          <p>&copy; 2026 探店助手 · 让选择更简单</p>
        </div>
      </div>
    </div>
  </template>

  <script setup lang="ts">
  import { ref, reactive } from 'vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  // ============================================
  // 表单数据
  // ============================================
  const loginForm = reactive({
    username: '',
    password: '',
    remember: false,
  })

  const showPassword = ref(false)
  const isLoading = ref(false)
  const errorMessage = ref('')
  const isAdminMode = ref(false)

// ============================================
// 登录逻辑（只调用真实 API，无模拟）
// ============================================
const handleLogin = async () => {
  errorMessage.value = ''

  if (!loginForm.username.trim() || !loginForm.password.trim()) {
    errorMessage.value = '请输入用户名'
    return
  }

  isLoading.value = true

  try {
    // ✅ 根据模式选择不同的登录接口
    const loginUrl = isAdminMode.value ? '/api/auth/admin/login' : '/api/auth/login'

    const response = await fetch(loginUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: loginForm.username.trim(),
        password: loginForm.password.trim(),
        remember: loginForm.remember,
      }),
    })

    if (response.ok) {
      const result = await response.json()


        // ✅ 检查业务状态码（约定 code === 0 表示成功）
  if (result.code !== 0) {
    errorMessage.value = result.message || '登录失败'
    return
  }
    // 从 result.data 中解构
    const { token, user } = result.data

if (token) {
  localStorage.setItem('token', token)
}
console.log("token:", token)  // 现在会正确输出

if (user) {
    localStorage.setItem('userInfo', JSON.stringify(user))
    localStorage.setItem('userRole', user.role || 'user')
        // ✅ 如果是管理员，标记角色
        if (isAdminMode.value) {
          localStorage.setItem('userRole', 'admin')
        } else {
          localStorage.setItem('userRole', 'user')
        }
      }

      // 获取重定向地址并跳转
      const redirect = router.currentRoute.value.query.redirect as string || '/'
      router.push(redirect)
    } else {
      // 处理错误响应
      let errorMsg = isAdminMode.value ? '管理员登录失败，请检查账号和密码' : '登录失败，请检查账号和密码'
      try {
        const error = await response.json()
        errorMsg = error.message || errorMsg
      } catch (e) {
        errorMsg = `登录失败 (${response.status})`
      }
      errorMessage.value = errorMsg
    }
  } catch (error) {
    console.error('登录请求异常:', error)

    // 判断是否为网络错误
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      errorMessage.value = '网络连接失败，请检查网络后重试'
    } else {
      errorMessage.value = isAdminMode.value ? '管理员登录失败，请稍后重试' : '登录失败，请稍后重试'
    }
  } finally {
    isLoading.value = false
  }
}

  // ============================================
  // 导航函数
  // ============================================
  const goHome = () => {
    router.push('/')
  }

  const goToRegister = () => {
    router.push('/register')
  }

  const handleForgotPassword = () => {
  // 跳转到找回密码页面
   alert('请联系管理员重置密码')
  }

  const handleSocialLogin = (platform: string) => {
    console.log(`使用 ${platform} 登录`)
    // 跳转到第三方授权
    alert(`${platform} 登录功能开发中...`)
  }
  </script>

  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .login-view {
    width: 100%;
    min-height: 100vh;
    min-height: 100dvh;
    background: #f1f5f9;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 1.5rem;
    box-sizing: border-box;
    background-image:
      radial-gradient(circle at 20% 30%, #e2e8f0 1px, transparent 1px),
      radial-gradient(circle at 80% 70%, #e2e8f0 1px, transparent 1px);
    background-size: 40px 40px, 50px 50px;
  }

  .login-container {
    width: 100%;
    max-width: 440px;
    position: relative;
  }

  /* ============================================
     返回按钮
     ============================================ */
  .back-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid #e2e8f0;
    color: #475569;
    padding: 0.5rem 1rem;
    border-radius: 0.7rem;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 10;
  }

  .back-btn:hover {
    background: white;
    border-color: #3b82f6;
    color: #1e293b;
    transform: translateX(-2px);
    box-shadow: 0 2px 12px rgba(59, 130, 246, 0.15);
  }

  .back-btn i {
    font-size: 0.9rem;
  }

  /* ============================================
     登录卡片
     ============================================ */
  .login-card {
    background: #ffffff;
    border-radius: 1.5rem;
    padding: 2.5rem 2rem 2rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
    position: relative;
    overflow: hidden;
  }

  /* 顶部装饰光晕 */
  .login-card::before {
    content: '';
    position: absolute;
    top: -80px;
    right: -80px;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.06) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }

  .login-card::after {
    content: '';
    position: absolute;
    bottom: -60px;
    left: -60px;
    width: 160px;
    height: 160px;
    background: radial-gradient(circle, rgba(251, 191, 36, 0.05) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }

  /* ============================================
     头部
     ============================================ */
  .login-header {
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    z-index: 1;
  }

  .logo-icon {
    display: flex;
    justify-content: center;
    margin-bottom: 0.8rem;
  }

  .logo-icon img {
    filter: drop-shadow(0 4px 12px rgba(59, 130, 246, 0.15));
  }

  .login-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.3rem;
  }

  .login-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 400;
  }

  /* ============================================
     表单
     ============================================ */
  .login-form {
    position: relative;
    z-index: 1;
  }

  .form-group {
    margin-bottom: 1.2rem;
  }

  .form-group label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
    margin-bottom: 0.4rem;
  }

  .form-group label i {
    color: #94a3b8;
    font-size: 0.8rem;
  }

  .input-wrapper {
    display: flex;
    align-items: center;
    background: #f8fafc;
    border: 2px solid #e2e8f0;
    border-radius: 0.8rem;
    padding: 0 0.8rem;
    transition: all 0.2s ease;
  }

  .input-wrapper:focus-within {
    border-color: #3b82f6;
    background: white;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
  }

  .input-icon {
    color: #94a3b8;
    font-size: 0.9rem;
    flex-shrink: 0;
  }

  .input-wrapper input {
    flex: 1;
    padding: 0.7rem 0.6rem;
    border: none;
    outline: none;
    background: transparent;
    font-size: 0.9rem;
    color: #1e293b;
    min-width: 0;
  }

  .input-wrapper input::placeholder {
    color: #cbd5e1;
  }

  .toggle-password {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0.3rem;
    font-size: 0.9rem;
    flex-shrink: 0;
    transition: color 0.2s;
  }

  .toggle-password:hover {
    color: #64748b;
  }

  /* ============================================
     表单选项
     ============================================ */
  .form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .remember-me {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    color: #64748b;
    cursor: pointer;
  }

  .remember-me input[type="checkbox"] {
    width: 1rem;
    height: 1rem;
    accent-color: #3b82f6;
    cursor: pointer;
  }

  .remember-me span {
    user-select: none;
  }

  .forgot-link {
    font-size: 0.85rem;
    color: #3b82f6;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
  }

  .forgot-link:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }

  /* ============================================
     登录按钮
     ============================================ */
  .login-btn {
    width: 100%;
    padding: 0.8rem;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    border: none;
    border-radius: 0.8rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    position: relative;
    overflow: hidden;
  }

  .login-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s ease;
  }

  .login-btn:hover:not(:disabled)::before {
    left: 100%;
  }

  .login-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3);
  }

  .login-btn:active:not(:disabled) {
    transform: translateY(0);
  }

  .login-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .login-btn i {
    font-size: 1rem;
  }

  /* ============================================
     错误提示
     ============================================ */
  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.8rem;
    padding: 0.6rem 1rem;
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 0.6rem;
    color: #dc2626;
    font-size: 0.85rem;
  }

  .error-message i {
    font-size: 0.9rem;
    flex-shrink: 0;
  }

  /* ============================================
     注册入口
     ============================================ */
  .register-section {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.9rem;
    color: #64748b;
    position: relative;
    z-index: 1;
  }

  .register-section a {
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
  }

  .register-section a:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }

  /* ============================================
     社交登录
     ============================================ */
  .social-login {
    margin-top: 1.8rem;
    position: relative;
    z-index: 1;
  }

  .divider {
    display: flex;
    align-items: center;
    text-align: center;
    margin-bottom: 1.2rem;
  }

  .divider::before,
  .divider::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #e2e8f0;
  }

  .divider span {
    padding: 0 1rem;
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .social-buttons {
    display: flex;
    justify-content: center;
    gap: 1rem;
  }

  .social-btn {
    width: 2.8rem;
    height: 2.8rem;
    border-radius: 50%;
    border: 1px solid #e2e8f0;
    background: white;
    font-size: 1.2rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .social-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .social-btn.wechat {
    color: #07c160;
  }

  .social-btn.wechat:hover {
    background: #f0faf4;
    border-color: #07c160;
  }

  .social-btn.qq {
    color: #12b7f5;
  }

  .social-btn.qq:hover {
    background: #f0f7fe;
    border-color: #12b7f5;
  }

  .social-btn.weibo {
    color: #ff8200;
  }

  .social-btn.weibo:hover {
    background: #fff5ed;
    border-color: #ff8200;
  }

  /* ============================================
     底部版权
     ============================================ */
  .login-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.7rem;
    color: #94a3b8;
    position: relative;
    z-index: 1;
  }

  /* ============================================
     平板端 (768px - 1024px)
     ============================================ */
  @media (max-width: 1024px) {
    .login-view {
      padding: 1.5rem;
    }

    .login-card {
      padding: 2rem 1.8rem 1.8rem;
    }
  }

  /* ============================================
     手机端 (最大768px)
     ============================================ */
  @media (max-width: 768px) {
    .login-view {
      padding: 1rem;
      align-items: flex-start;
      padding-top: 2rem;
    }

    .login-container {
      max-width: 100%;
    }

    .back-btn {
      padding: 0.4rem 0.8rem;
      font-size: 0.8rem;
      margin-bottom: 1rem;
    }

    .back-btn span {
      display: none;
    }

    .login-card {
      padding: 1.8rem 1.2rem 1.5rem;
      border-radius: 1.2rem;
    }

    .login-title {
      font-size: 1.4rem;
    }

    .login-subtitle {
      font-size: 0.8rem;
    }

    .form-group {
      margin-bottom: 1rem;
    }

    .input-wrapper {
      padding: 0 0.6rem;
      border-radius: 0.7rem;
    }

    .input-wrapper input {
      padding: 0.6rem 0.4rem;
      font-size: 0.85rem;
    }

    .form-options {
      margin-bottom: 1.2rem;
      flex-wrap: wrap;
      gap: 0.4rem;
    }

    .login-btn {
      padding: 0.7rem;
      font-size: 0.95rem;
      border-radius: 0.7rem;
    }

    .register-section {
      margin-top: 1.2rem;
      font-size: 0.85rem;
    }

    .social-login {
      margin-top: 1.5rem;
    }

    .social-btn {
      width: 2.4rem;
      height: 2.4rem;
      font-size: 1rem;
    }

    .login-footer {
      margin-top: 1rem;
      font-size: 0.65rem;
    }
  }

  /* ============================================
     小屏手机 (最大480px)
     ============================================ */
  @media (max-width: 480px) {
    .login-view {
      padding: 0.8rem;
      padding-top: 1.5rem;
    }

    .login-card {
      padding: 1.5rem 1rem 1.2rem;
      border-radius: 1rem;
    }

    .logo-icon img {
      width: 44px;
      height: 44px;
    }

    .login-title {
      font-size: 1.2rem;
    }

    .login-subtitle {
      font-size: 0.75rem;
    }

    .input-wrapper input {
      font-size: 0.8rem;
    }

    .login-btn {
      font-size: 0.9rem;
      padding: 0.6rem;
    }
  }

  /* ============================================
     横屏手机优化
     ============================================ */
  @media (max-height: 500px) and (orientation: landscape) {
    .login-view {
      padding: 0.8rem;
      align-items: center;
    }

    .login-card {
      padding: 1.2rem 1.5rem;
      border-radius: 1rem;
    }

    .login-header {
      margin-bottom: 1rem;
    }

    .logo-icon img {
      width: 36px;
      height: 36px;
    }

    .login-title {
      font-size: 1.2rem;
      margin-bottom: 0.1rem;
    }

    .login-subtitle {
      display: none;
    }

    .form-group {
      margin-bottom: 0.6rem;
    }

    .form-options {
      margin-bottom: 0.8rem;
    }

    .social-login {
      margin-top: 1rem;
    }

    .login-footer {
      display: none;
    }
  }

  /* ============================================
   角色切换
   ============================================ */
.role-toggle {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 0.8rem;
  max-width: 220px;
  margin-left: auto;
  margin-right: auto;
}

.role-btn {
  flex: 1;
  padding: 0.4rem 1rem;
  border: none;
  border-radius: 0.6rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  background: transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}

.role-btn i {
  font-size: 0.8rem;
}

.role-btn:hover {
  color: #334155;
}

.role-btn.active {
  background: white;
  color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.role-btn.active i {
  color: #3b82f6;
}

/* ============================================
   响应式 - 角色切换
   ============================================ */
@media (max-width: 768px) {
  .role-toggle {
    max-width: 180px;
  }

  .role-btn {
    font-size: 0.7rem;
    padding: 0.3rem 0.6rem;
  }

  .role-btn i {
    font-size: 0.7rem;
  }
}
/* ============================================
   管理员提示
   ============================================ */
   .admin-hint {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.4rem;
  font-size: 0.75rem;
  color: #3b82f6;
  background: #eff6ff;
  padding: 0.3rem 0.6rem;
  border-radius: 0.4rem;
}

.admin-hint i {
  font-size: 0.7rem;
}

.admin-hint span {
  font-size: 0.75rem;
}

/* ============================================
   响应式 - 管理员提示
   ============================================ */
@media (max-width: 768px) {
  .admin-hint {
    font-size: 0.65rem;
    padding: 0.2rem 0.5rem;
  }

  .admin-hint span {
    font-size: 0.65rem;
  }
}
  </style>
