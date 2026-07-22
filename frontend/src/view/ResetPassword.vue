<template>
    <div class="reset-view">
      <div class="reset-container">
        <!-- 返回按钮 -->
        <button class="back-btn" @click="goLogin">
          <i class="fas fa-arrow-left"></i>
          <span>返回登录</span>
        </button>

        <!-- 卡片 -->
        <div class="reset-card">
          <div class="reset-header">
            <div class="logo-icon">
              <img
                src="/images/2.png"
                alt="探店助手"
                style="width: 56px; height: 56px; object-fit: contain;"
              />
            </div>
            <h1 class="reset-title">重置密码</h1>
            <p class="reset-subtitle">输入收到的密钥和新密码</p>
          </div>

          <!-- 表单 -->
          <form class="reset-form" @submit.prevent="handleReset">
            <div class="form-group">
              <label for="token">
                <i class="fas fa-key"></i>
                密钥
              </label>
              <div class="input-wrapper">
                <i class="fas fa-key input-icon"></i>
                <input
                  id="token"
                  v-model="token"
                  type="text"
                  placeholder="请输入邮件中的密钥"
                  autocomplete="off"
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label for="newPassword">
                <i class="fas fa-lock"></i>
                新密码
              </label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input
                  id="newPassword"
                  v-model="newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入新密码（至少6位）"
                  autocomplete="new-password"
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
            </div>

            <div class="form-group">
              <label for="confirmPassword">
                <i class="fas fa-check-circle"></i>
                确认密码
              </label>
              <div class="input-wrapper">
                <i class="fas fa-check-circle input-icon"></i>
                <input
                  id="confirmPassword"
                  v-model="confirmPassword"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请再次输入新密码"
                  autocomplete="new-password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              class="reset-btn"
              :disabled="isLoading"
            >
              <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>重置密码</span>
            </button>

            <!-- 成功消息 -->
            <div v-if="successMessage" class="success-message">
              <i class="fas fa-check-circle"></i>
              {{ successMessage }}
            </div>

            <!-- 错误消息 -->
            <div v-if="errorMessage" class="error-message">
              <i class="fas fa-exclamation-circle"></i>
              {{ errorMessage }}
            </div>
          </form>

          <!-- 底部链接 -->
          <div class="footer-links">
            <a href="#" @click.prevent="goLogin">返回登录</a>
          </div>
        </div>

        <div class="reset-footer">
          <p>&copy; 2026 探店助手 · 让选择更简单</p>
        </div>
      </div>
    </div>
  </template>

  <script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'

  const router = useRouter()
  const route = useRoute()

  const token = ref('')
  const newPassword = ref('')
  const confirmPassword = ref('')
  const showPassword = ref(false)
  const isLoading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  // 如果 URL 中有 token 参数，自动填充
  onMounted(() => {
    const queryToken = route.query.token as string
    if (queryToken) {
      token.value = queryToken
    }
  })

  const goLogin = () => {
    router.push('/login')
  }

  const handleReset = async () => {
    errorMessage.value = ''
    successMessage.value = ''

    const trimmedToken = token.value.trim()
    const trimmedNew = newPassword.value.trim()
    const trimmedConfirm = confirmPassword.value.trim()

    if (!trimmedToken) {
      errorMessage.value = '请输入密钥'
      return
    }
    if (!trimmedNew || trimmedNew.length < 6) {
      errorMessage.value = '密码长度至少为6位'
      return
    }
    if (trimmedNew !== trimmedConfirm) {
      errorMessage.value = '两次输入的密码不一致'
      return
    }

    isLoading.value = true

    try {
      const response = await fetch('http://localhost:8000/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: trimmedToken,
          password: trimmedNew,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        if (result.code === 200) {
          successMessage.value = result.message || '密码重置成功，即将跳转到登录页'
          // 延迟跳转
          setTimeout(() => {
            router.push('/login')
          }, 3000)
        } else {
          errorMessage.value = result.message || '重置失败'
        }
      } else {
        let msg = '重置失败，请检查密钥是否正确'
        try {
          const err = await response.json()
          msg = err.message || msg
        } catch (e) { /* ignore */ }
        errorMessage.value = msg
      }
    } catch (error) {
      console.error('重置密码请求异常:', error)
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        errorMessage.value = '网络连接失败，请检查网络后重试'
      } else {
        errorMessage.value = '请求失败，请稍后重试'
      }
    } finally {
      isLoading.value = false
    }
  }
  </script>

  <style scoped>
  /* ============================================
     全局布局（与 LoginView / ForgotPassword 一致）
     ============================================ */
  .reset-view {
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

  .reset-container {
    width: 100%;
    max-width: 440px;
    position: relative;
  }

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

  .reset-card {
    background: #ffffff;
    border-radius: 1.5rem;
    padding: 2.5rem 2rem 2rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
    position: relative;
    overflow: hidden;
  }

  .reset-card::before {
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

  .reset-card::after {
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

  .reset-header {
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

  .reset-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.3rem;
  }

  .reset-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 400;
  }

  .reset-form {
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

  .reset-btn {
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

  .reset-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s ease;
  }

  .reset-btn:hover:not(:disabled)::before {
    left: 100%;
  }

  .reset-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3);
  }

  .reset-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .success-message,
  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.8rem;
    padding: 0.6rem 1rem;
    border-radius: 0.6rem;
    font-size: 0.85rem;
  }

  .success-message {
    background: #f0fdf4;
    border: 1px solid #86efac;
    color: #16a34a;
  }

  .error-message {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    color: #dc2626;
  }

  .success-message i,
  .error-message i {
    font-size: 0.9rem;
    flex-shrink: 0;
  }

  .footer-links {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.9rem;
    color: #64748b;
    position: relative;
    z-index: 1;
  }

  .footer-links a {
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
  }

  .footer-links a:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }

  .reset-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.7rem;
    color: #94a3b8;
    position: relative;
    z-index: 1;
  }

  /* 响应式 与 LoginView 一致 */
  @media (max-width: 768px) {
    .reset-view { padding: 1rem; align-items: flex-start; padding-top: 2rem; }
    .reset-container { max-width: 100%; }
    .back-btn span { display: none; }
    .back-btn { padding: 0.4rem 0.8rem; font-size: 0.8rem; margin-bottom: 1rem; }
    .reset-card { padding: 1.8rem 1.2rem 1.5rem; border-radius: 1.2rem; }
    .reset-title { font-size: 1.4rem; }
    .reset-subtitle { font-size: 0.8rem; }
    .form-group { margin-bottom: 1rem; }
    .input-wrapper { padding: 0 0.6rem; border-radius: 0.7rem; }
    .input-wrapper input { padding: 0.6rem 0.4rem; font-size: 0.85rem; }
    .reset-btn { padding: 0.7rem; font-size: 0.95rem; border-radius: 0.7rem; }
    .footer-links { margin-top: 1.2rem; font-size: 0.85rem; }
  }

  @media (max-width: 480px) {
    .reset-view { padding: 0.8rem; padding-top: 1.5rem; }
    .reset-card { padding: 1.5rem 1rem 1.2rem; border-radius: 1rem; }
    .logo-icon img { width: 44px; height: 44px; }
    .reset-title { font-size: 1.2rem; }
    .reset-subtitle { font-size: 0.75rem; }
    .input-wrapper input { font-size: 0.8rem; }
    .reset-btn { font-size: 0.9rem; padding: 0.6rem; }
  }

  @media (max-height: 500px) and (orientation: landscape) {
    .reset-view { padding: 0.8rem; align-items: center; }
    .reset-card { padding: 1.2rem 1.5rem; border-radius: 1rem; }
    .reset-header { margin-bottom: 1rem; }
    .logo-icon img { width: 36px; height: 36px; }
    .reset-title { font-size: 1.2rem; }
    .reset-subtitle { display: none; }
    .form-group { margin-bottom: 0.6rem; }
    .footer-links { margin-top: 0.8rem; }
    .reset-footer { display: none; }
  }
  </style>
