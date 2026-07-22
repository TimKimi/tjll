<template>
  <div class="register-view">
    <div class="register-container">
      <!-- 返回按钮 -->
      <button
        class="back-btn"
        @click="goHome"
      >
        <i class="fas fa-arrow-left" />
        <span>返回首页</span>
      </button>

      <!-- 注册卡片 -->
      <div class="register-card">
        <!-- Logo 区域 -->
        <div class="register-header">
          <div class="logo-icon">
            <img
              src="/images/2.png"
              alt="探店助手"
              style="width: 56px; height: 56px; object-fit: contain;"
            >
          </div>
          <h1 class="register-title">
            创建账号
          </h1>
          <p class="register-subtitle">
            加入探店助手，发现身边好店
          </p>
        </div>

        <!-- 注册表单 -->
        <form
          class="register-form"
          @submit.prevent="handleRegister"
        >
          <!-- 用户名 -->
          <div class="form-group">
            <label for="username">
              <i class="fas fa-user" />
              用户名
            </label>
            <div class="input-wrapper">
              <i class="fas fa-user input-icon" />
              <input
                id="username"
                v-model="registerForm.username"
                type="text"
                placeholder="请设置用户名（2-16位字母、数字或中文）"
                autocomplete="username"
                required
              >
            </div>
            <span
              v-if="usernameError"
              class="field-error"
            >{{ usernameError }}</span>
          </div>

          <!-- 邮箱 -->
          <div class="form-group">
            <label for="email">
              <i class="fas fa-envelope" />
              邮箱
            </label>
            <div class="input-wrapper">
              <i class="fas fa-envelope input-icon" />
              <input
                id="email"
                v-model="registerForm.email"
                type="email"
                placeholder="请输入邮箱地址"
                autocomplete="email"
                required
              >
            </div>
            <span
              v-if="emailError"
              class="field-error"
            >{{ emailError }}</span>
          </div>

          <!-- 密码 -->
          <div class="form-group">
            <label for="password">
              <i class="fas fa-lock" />
              密码
            </label>
            <div class="input-wrapper">
              <i class="fas fa-lock input-icon" />
              <input
                id="password"
                v-model="registerForm.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请设置密码（至少8位）"
                autocomplete="new-password"
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
            <div
              v-if="registerForm.password"
              class="password-strength"
            >
              <div class="strength-bar">
                <div
                  class="strength-fill"
                  :style="{ width: passwordStrength + '%', background: strengthColor }"
                />
              </div>
              <span
                class="strength-label"
                :style="{ color: strengthColor }"
              >
                {{ strengthText }}
              </span>
            </div>
          </div>

          <!-- 确认密码 -->
          <div class="form-group">
            <label for="confirmPassword">
              <i class="fas fa-check-circle" />
              确认密码
            </label>
            <div class="input-wrapper">
              <i class="fas fa-check-circle input-icon" />
              <input
                id="confirmPassword"
                v-model="registerForm.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="请再次输入密码"
                autocomplete="new-password"
                required
              >
              <button
                type="button"
                class="toggle-password"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <i :class="showConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'" />
              </button>
            </div>
            <span
              v-if="confirmPasswordError"
              class="field-error"
            >{{ confirmPasswordError }}</span>
          </div>

          <!-- 用户协议 -->
          <div class="form-agreement">
            <label class="agreement-checkbox">
              <input
                v-model="registerForm.agreed"
                type="checkbox"
                required
              >
              <span>
                我已阅读并同意
                <a
                  href="#"
                  @click.prevent="showTerms"
                >《用户协议》</a>
                和
                <a
                  href="#"
                  @click.prevent="showPrivacy"
                >《隐私政策》</a>
              </span>
            </label>
          </div>

          <!-- 注册按钮 -->
          <button
            type="submit"
            class="register-btn"
            :disabled="isLoading || !registerForm.agreed"
          >
            <i
              v-if="isLoading"
              class="fas fa-spinner fa-spin"
            />
            <span v-else>立即注册</span>
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

        <!-- 登录入口 -->
        <div class="login-section">
          <span>已有账号？</span>
          <a
            href="#"
            @click.prevent="goToLogin"
          >立即登录</a>
        </div>
      </div>

      <!-- 底部版权 -->
      <div class="register-footer">
        <p>&copy; 2026 探店助手 · 让选择更简单</p>
      </div>
    </div>
  </div>
</template>

  <script setup lang="ts">
  import { ref, reactive, computed, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { useToast } from '@/composables/useToast'

  const router = useRouter()
  const toast = useToast()

  // ============================================
  // 表单数据
  // ============================================
  const registerForm = reactive({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreed: false,
  })

  const showPassword = ref(false)
  const showConfirmPassword = ref(false)
  const isLoading = ref(false)
  const errorMessage = ref('')

  // ============================================
  // 表单验证
  // ============================================
  const usernameError = ref('')
  const emailError = ref('')
  const confirmPasswordError = ref('')

  // 密码强度计算
  const passwordStrength = computed(() => {
    const pwd = registerForm.password
    if (!pwd) return 0
    let strength = 0
    if (pwd.length >= 8) strength += 25
    if (/[a-z]/.test(pwd)) strength += 25
    if (/[A-Z]/.test(pwd)) strength += 25
    if (/[0-9]/.test(pwd) || /[^a-zA-Z0-9]/.test(pwd)) strength += 25
    return Math.min(strength, 100)
  })

  const strengthText = computed(() => {
    const s = passwordStrength.value
    if (s === 0) return ''
    if (s <= 30) return '弱'
    if (s <= 60) return '中'
    if (s <= 80) return '强'
    return '非常强'
  })

  const strengthColor = computed(() => {
    const s = passwordStrength.value
    if (s === 0) return '#94a3b8'
    if (s <= 30) return '#ef4444'
    if (s <= 60) return '#f59e0b'
    if (s <= 80) return '#3b82f6'
    return '#22c55e'
  })

  // 实时验证
  watch(() => registerForm.username, (val) => {
    if (val && !/^[a-zA-Z0-9\u4e00-\u9fa5]{2,16}$/.test(val)) {
      usernameError.value = '用户名需为2-16位字母、数字或中文'
    } else {
      usernameError.value = ''
    }
  })

  watch(() => registerForm.email, (val) => {
  if (val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
    emailError.value = '请输入正确的邮箱地址'
  } else {
    emailError.value = ''
  }
})

  watch(() => registerForm.confirmPassword, (val) => {
    if (val && val !== registerForm.password) {
      confirmPasswordError.value = '两次密码输入不一致'
    } else {
      confirmPasswordError.value = ''
    }
  })

  // ============================================
  // 工具函数：获取当前日期
  // ============================================
  const getCurrentDate = (): string => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  // ============================================
  // 注册逻辑
  // ============================================
  const handleRegister = async () => {
    errorMessage.value = ''

    // 验证用户名（支持中文）
    if (!/^[a-zA-Z0-9\u4e00-\u9fa5]{2,16}$/.test(registerForm.username)) {
      errorMessage.value = '用户名需为2-16位字母、数字或中文'
      return
    }

// 验证邮箱
if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
  errorMessage.value = '请输入正确的邮箱地址'
  return
}

    // 验证密码
    if (registerForm.password.length < 8) {
      errorMessage.value = '密码长度至少为8位'
      return
    }

    // 验证确认密码
    if (registerForm.password !== registerForm.confirmPassword) {
      errorMessage.value = '两次密码输入不一致'
      return
    }

    // 验证协议
    if (!registerForm.agreed) {
      errorMessage.value = '请先同意用户协议和隐私政策'
      return
    }

    isLoading.value = true

    try {
      // 调用注册 API
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: registerForm.username.trim(),
  email: registerForm.email.trim(),
  password: registerForm.password,
        }),
      })

      if (response.ok) {
        const data = await response.json()

        // ✅ 注册成功，跳转到登录页
        // 可以显示成功提示
        toast.success('注册成功！请登录')

        // 跳转到登录页
        router.push('/login')
      } else {
        const error = await response.json()
        errorMessage.value = error.message || '注册失败，请稍后重试'
      }
    } catch (error) {
      console.error('注册请求异常:', error)
      errorMessage.value = '网络异常，请稍后重试'
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

  const goToLogin = () => {
    router.push('/login')
  }

  const showTerms = () => {
    toast.info('用户协议内容...')
  }

  const showPrivacy = () => {
    toast.info('隐私政策内容...')
  }
  </script>

  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .register-view {
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

  .register-container {
    width: 100%;
    max-width: 460px;
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
     注册卡片
     ============================================ */
  .register-card {
    background: #ffffff;
    border-radius: 1.5rem;
    padding: 2.5rem 2rem 2rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
    position: relative;
    overflow: hidden;
    max-height: 90vh;
    overflow-y: auto;
  }

  .register-card::-webkit-scrollbar {
    width: 3px;
  }

  .register-card::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  /* 顶部装饰 */
  .register-card::before {
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

  .register-card::after {
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
  .register-header {
    text-align: center;
    margin-bottom: 1.8rem;
    position: relative;
    z-index: 1;
  }

  .logo-icon {
    display: flex;
    justify-content: center;
    margin-bottom: 0.6rem;
  }

  .logo-icon img {
    filter: drop-shadow(0 4px 12px rgba(59, 130, 246, 0.15));
  }

  .register-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.2rem;
  }

  .register-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 400;
  }

  /* ============================================
     表单
     ============================================ */
  .register-form {
    position: relative;
    z-index: 1;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
    margin-bottom: 0.3rem;
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

  .input-wrapper.error {
    border-color: #ef4444;
  }

  .input-icon {
    color: #94a3b8;
    font-size: 0.9rem;
    flex-shrink: 0;
  }

  .input-wrapper input {
    flex: 1;
    padding: 0.65rem 0.5rem;
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

  /* 字段错误 */
  .field-error {
    display: block;
    font-size: 0.75rem;
    color: #ef4444;
    margin-top: 0.2rem;
  }

  /* ============================================
     密码强度
     ============================================ */
  .password-strength {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-top: 0.4rem;
  }

  .strength-bar {
    flex: 1;
    height: 4px;
    background: #e2e8f0;
    border-radius: 2px;
    overflow: hidden;
  }

  .strength-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease, background 0.3s ease;
  }

  .strength-label {
    font-size: 0.7rem;
    font-weight: 500;
    min-width: 2.5rem;
    text-align: right;
  }

  /* ============================================
     用户协议
     ============================================ */
  .form-agreement {
    margin: 1rem 0 1.2rem;
  }

  .agreement-checkbox {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.8rem;
    color: #64748b;
    cursor: pointer;
    line-height: 1.5;
  }

  .agreement-checkbox input[type="checkbox"] {
    width: 1rem;
    height: 1rem;
    accent-color: #3b82f6;
    cursor: pointer;
    flex-shrink: 0;
    margin-top: 0.1rem;
  }

  .agreement-checkbox a {
    color: #3b82f6;
    text-decoration: none;
  }

  .agreement-checkbox a:hover {
    text-decoration: underline;
  }

  /* ============================================
     注册按钮
     ============================================ */
  .register-btn {
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

  .register-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s ease;
  }

  .register-btn:hover:not(:disabled)::before {
    left: 100%;
  }

  .register-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3);
  }

  .register-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .register-btn i {
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
     登录入口
     ============================================ */
  .login-section {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.9rem;
    color: #64748b;
    position: relative;
    z-index: 1;
  }

  .login-section a {
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
  }

  .login-section a:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }

  /* ============================================
     底部版权
     ============================================ */
  .register-footer {
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
    .register-view {
      padding: 1.5rem;
    }

    .register-card {
      padding: 2rem 1.8rem 1.8rem;
    }
  }

  /* ============================================
     手机端 (最大768px)
     ============================================ */
  @media (max-width: 768px) {
    .register-view {
      padding: 1rem;
      align-items: flex-start;
      padding-top: 2rem;
    }

    .register-container {
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

    .register-card {
      padding: 1.8rem 1.2rem 1.5rem;
      border-radius: 1.2rem;
      max-height: 85vh;
    }

    .register-title {
      font-size: 1.4rem;
    }

    .register-subtitle {
      font-size: 0.8rem;
    }

    .form-group {
      margin-bottom: 0.8rem;
    }

    .input-wrapper {
      padding: 0 0.6rem;
      border-radius: 0.7rem;
    }

    .input-wrapper input {
      padding: 0.55rem 0.4rem;
      font-size: 0.85rem;
    }

    .register-btn {
      padding: 0.7rem;
      font-size: 0.95rem;
    }

    .login-section {
      margin-top: 1.2rem;
      font-size: 0.85rem;
    }

    .register-footer {
      margin-top: 1rem;
      font-size: 0.65rem;
    }

    .form-agreement {
      margin: 0.8rem 0 1rem;
    }

    .agreement-checkbox {
      font-size: 0.75rem;
    }
  }

  /* ============================================
     小屏手机 (最大480px)
     ============================================ */
  @media (max-width: 480px) {
    .register-view {
      padding: 0.8rem;
      padding-top: 1.5rem;
    }

    .register-card {
      padding: 1.5rem 1rem 1.2rem;
      border-radius: 1rem;
      max-height: 80vh;
    }

    .logo-icon img {
      width: 44px;
      height: 44px;
    }

    .register-title {
      font-size: 1.2rem;
    }

    .register-subtitle {
      font-size: 0.75rem;
    }

    .input-wrapper input {
      font-size: 0.8rem;
    }

    .register-btn {
      font-size: 0.9rem;
      padding: 0.6rem;
    }
  }

  /* ============================================
     横屏手机优化
     ============================================ */
  @media (max-height: 500px) and (orientation: landscape) {
    .register-view {
      padding: 0.8rem;
      align-items: center;
    }

    .register-card {
      padding: 1rem 1.5rem;
      border-radius: 1rem;
      max-height: 90vh;
    }

    .register-header {
      margin-bottom: 0.8rem;
    }

    .logo-icon img {
      width: 32px;
      height: 32px;
    }

    .register-title {
      font-size: 1.1rem;
      margin-bottom: 0;
    }

    .register-subtitle {
      display: none;
    }

    .form-group {
      margin-bottom: 0.4rem;
    }

    .form-group label {
      font-size: 0.75rem;
      margin-bottom: 0.1rem;
    }

    .input-wrapper input {
      padding: 0.35rem 0.3rem;
      font-size: 0.8rem;
    }

    .password-strength {
      display: none;
    }

    .form-agreement {
      margin: 0.4rem 0 0.6rem;
    }

    .register-footer {
      display: none;
    }
  }
  </style>
