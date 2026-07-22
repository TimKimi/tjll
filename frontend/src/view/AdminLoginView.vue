<template>
  <div class="admin-login-view">
    <div class="login-container">
      <!-- 返回按钮（与普通登录页一致） -->
      <button
        class="back-btn"
        @click="goHome"
      >
        <i class="fas fa-arrow-left" />
        <span>返回首页</span>
      </button>

      <!-- 登录卡片 -->
      <div class="login-card">
        <!-- 头部 -->
        <div class="login-header">
          <div class="logo-icon">
            <img
              src="/images/2.png"
              alt="探店助手"
              style="width: 56px; height: 56px; object-fit: contain;"
            >
          </div>
          <h1 class="login-title">
            管理后台登录
          </h1>
          <p class="login-subtitle">
            请输入管理员账号密码
          </p>
        </div>

        <!-- 登录表单 -->
        <form
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <!-- 账号输入 -->
          <div class="form-group">
            <label for="username">
              <i class="fas fa-user" />
              用户名
            </label>
            <div class="input-wrapper">
              <i class="fas fa-user input-icon" />
              <input
                id="username"
                v-model="form.username"
                type="text"
                placeholder="请输入管理员用户名"
                autocomplete="username"
                required
              >
            </div>
          </div>

          <!-- 密码输入 -->
          <div class="form-group">
            <label for="password">
              <i class="fas fa-lock" />
              密码
            </label>
            <div class="input-wrapper">
              <i class="fas fa-lock input-icon" />
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                autocomplete="current-password"
                required
              >
              <button
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
              >
                <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'" />
              </button>
            </div>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            class="login-btn"
            :disabled="loading"
          >
            <i
              v-if="loading"
              class="fas fa-spinner fa-spin"
            />
            <span v-else>登录</span>
          </button>

          <!-- 错误提示 -->
          <div
            v-if="errorMessage"
            class="error-message"
          >
            <i class="fas fa-exclamation-circle" />
            {{ errorMessage }}
          </div>
        </form>

        <!-- 普通用户登录入口 -->
        <div class="register-section">
          <span>普通用户？</span>
          <router-link to="/login">
            点击这里登录
          </router-link>
        </div>

        <!-- 底部版权 -->
        <div class="login-footer">
          <p>&copy; 2026 探店助手 · 让选择更简单</p>
        </div>
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
  const form = reactive({
    username: '',
    password: '',
  })

  const showPassword = ref(false)
  const loading = ref(false)
  const errorMessage = ref('')

  // ============================================
  // 登录逻辑（调用管理员接口）
  // ============================================
  const handleLogin = async () => {
    errorMessage.value = ''

    if (!form.username.trim() || !form.password.trim()) {
      errorMessage.value = '请填写完整信息'
      return
    }

    loading.value = true

    try {
      const response = await fetch('/api/auth/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: form.username.trim(),
          password: form.password.trim(),
          // 管理员登录默认不记住（可根据需要添加 remember 字段）
        }),
      })

      if (response.ok) {
        const result = await response.json()

        if (result.code !== 200) {
          errorMessage.value = result.message || '登录失败'
          return
        }

        const { token, user } = result.data

        if (token) {
  localStorage.setItem('admin_token', token)
}
if (user) {
  localStorage.setItem('admin_userInfo', JSON.stringify(user))
  localStorage.setItem('admin_role', 'admin')
}

        // 跳转到管理后台
        router.push('/admin')
      } else {
        let errorMsg = '管理员登录失败，请检查账号和密码'
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
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        errorMessage.value = '网络连接失败，请检查网络后重试'
      } else {
        errorMessage.value = '登录失败，请稍后重试'
      }
    } finally {
      loading.value = false
    }
  }

  // ============================================
  // 导航函数
  // ============================================
  const goHome = () => {
    router.push('/')
  }
  </script>

  <style scoped>
  /* ============================================
     全局布局（与普通登录页完全一致）
     ============================================ */
  .admin-login-view {
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
     注册入口（普通用户跳转）
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
     响应式 (与普通登录页完全一致)
     ============================================ */
  @media (max-width: 1024px) {
    .admin-login-view {
      padding: 1.5rem;
    }
    .login-card {
      padding: 2rem 1.8rem 1.8rem;
    }
  }

  @media (max-width: 768px) {
    .admin-login-view {
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
    .login-btn {
      padding: 0.7rem;
      font-size: 0.95rem;
      border-radius: 0.7rem;
    }
    .register-section {
      margin-top: 1.2rem;
      font-size: 0.85rem;
    }
    .login-footer {
      margin-top: 1rem;
      font-size: 0.65rem;
    }
  }

  @media (max-width: 480px) {
    .admin-login-view {
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

  @media (max-height: 500px) and (orientation: landscape) {
    .admin-login-view {
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
    .login-footer {
      display: none;
    }
  }
  </style>
