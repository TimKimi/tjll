<template>
    <div class="forgot-view">
      <div class="forgot-container">
        <!-- 返回按钮 -->
        <button class="back-btn" @click="goLogin">
          <i class="fas fa-arrow-left"></i>
          <span>返回登录</span>
        </button>

        <!-- 卡片 -->
        <div class="forgot-card">
          <div class="forgot-header">
            <div class="logo-icon">
              <img
                src="/images/2.png"
                alt="探店助手"
                style="width: 56px; height: 56px; object-fit: contain;"
              />
            </div>
            <h1 class="forgot-title">找回密码</h1>
            <p class="forgot-subtitle">
              输入注册邮箱，我们将发送重置密钥
            </p>
          </div>

          <!-- 表单 -->
          <form class="forgot-form" @submit.prevent="handleForgot">
            <div class="form-group">
              <label for="email">
                <i class="fas fa-envelope"></i>
                邮箱
              </label>
              <div class="input-wrapper">
                <i class="fas fa-envelope input-icon"></i>
                <input
                  id="email"
                  v-model="email"
                  type="email"
                  placeholder="请输入注册邮箱"
                  autocomplete="email"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              class="forgot-btn"
              :disabled="isLoading"
            >
              <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>发送重置邮件</span>
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

        <div class="forgot-footer">
          <p>&copy; 2026 探店助手 · 让选择更简单</p>
        </div>
      </div>
    </div>
  </template>

  <script setup lang="ts">
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const email = ref('')
  const isLoading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const goLogin = () => {
    router.push('/login')
  }

  const handleForgot = async () => {
    errorMessage.value = ''
    successMessage.value = ''

    if (!email.value.trim()) {
      errorMessage.value = '请输入邮箱地址'
      return
    }
    // 简单邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email.value.trim())) {
      errorMessage.value = '请输入有效的邮箱地址'
      return
    }

    isLoading.value = true

    try {
      const response = await fetch('http://localhost:8000/api/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.value.trim() }),
      })

      if (response.ok) {
  const result = await response.json()
  if (result.code === 200) {
    successMessage.value = result.message || '重置邮件已发送，请检查您的邮箱'
    email.value = '' // 清空邮箱

    // ✅ 发送成功后跳转到重置密码页面
    setTimeout(() => {
      router.push('/reset-password')
    }, 2000) // 2 秒后跳转，让用户看到成功提示
  } else {
    errorMessage.value = result.message || '请求失败'
  }
}
    } catch (error) {
      console.error('忘记密码请求异常:', error)
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
     全局布局（与 LoginView 一致）
     ============================================ */
  .forgot-view {
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

  .forgot-container {
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

  .forgot-card {
    background: #ffffff;
    border-radius: 1.5rem;
    padding: 2.5rem 2rem 2rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
    position: relative;
    overflow: hidden;
  }

  .forgot-card::before {
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

  .forgot-card::after {
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

  .forgot-header {
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

  .forgot-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.3rem;
  }

  .forgot-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 400;
  }

  .forgot-form {
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

  .forgot-btn {
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

  .forgot-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s ease;
  }

  .forgot-btn:hover:not(:disabled)::before {
    left: 100%;
  }

  .forgot-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3);
  }

  .forgot-btn:disabled {
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

  .forgot-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.7rem;
    color: #94a3b8;
    position: relative;
    z-index: 1;
  }

  /* 响应式 与 LoginView 一致 */
  @media (max-width: 768px) {
    .forgot-view { padding: 1rem; align-items: flex-start; padding-top: 2rem; }
    .forgot-container { max-width: 100%; }
    .back-btn span { display: none; }
    .back-btn { padding: 0.4rem 0.8rem; font-size: 0.8rem; margin-bottom: 1rem; }
    .forgot-card { padding: 1.8rem 1.2rem 1.5rem; border-radius: 1.2rem; }
    .forgot-title { font-size: 1.4rem; }
    .forgot-subtitle { font-size: 0.8rem; }
    .form-group { margin-bottom: 1rem; }
    .input-wrapper { padding: 0 0.6rem; border-radius: 0.7rem; }
    .input-wrapper input { padding: 0.6rem 0.4rem; font-size: 0.85rem; }
    .forgot-btn { padding: 0.7rem; font-size: 0.95rem; border-radius: 0.7rem; }
    .footer-links { margin-top: 1.2rem; font-size: 0.85rem; }
  }

  @media (max-width: 480px) {
    .forgot-view { padding: 0.8rem; padding-top: 1.5rem; }
    .forgot-card { padding: 1.5rem 1rem 1.2rem; border-radius: 1rem; }
    .logo-icon img { width: 44px; height: 44px; }
    .forgot-title { font-size: 1.2rem; }
    .forgot-subtitle { font-size: 0.75rem; }
    .input-wrapper input { font-size: 0.8rem; }
    .forgot-btn { font-size: 0.9rem; padding: 0.6rem; }
  }

  @media (max-height: 500px) and (orientation: landscape) {
    .forgot-view { padding: 0.8rem; align-items: center; }
    .forgot-card { padding: 1.2rem 1.5rem; border-radius: 1rem; }
    .forgot-header { margin-bottom: 1rem; }
    .logo-icon img { width: 36px; height: 36px; }
    .forgot-title { font-size: 1.2rem; }
    .forgot-subtitle { display: none; }
    .form-group { margin-bottom: 0.6rem; }
    .footer-links { margin-top: 0.8rem; }
    .forgot-footer { display: none; }
  }
  </style>
