<template>
    <div class="forgot-password-view">
      <div class="forgot-container">
        <!-- 返回按钮 -->
        <button class="back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          <span>返回</span>
        </button>
  
        <!-- 找回密码卡片 -->
        <div class="forgot-card">
          <!-- Logo 区域 -->
          <div class="forgot-header">
            <div class="logo-icon">
              <img
                src="/images/2.png"
                alt="探店助手"
                style="width: 56px; height: 56px; object-fit: contain;"
              />
            </div>
            <h1 class="forgot-title">找回密码</h1>
            <p class="forgot-subtitle">{{ currentStep === 1 ? '输入手机号，获取验证码' : '设置新密码' }}</p>
          </div>
  
          <!-- 步骤1：验证身份 -->
          <form v-if="currentStep === 1" class="forgot-form" @submit.prevent="sendCode">
            <div class="form-group">
              <label for="phone">
                <i class="fas fa-phone"></i>
                手机号
              </label>
              <div class="input-wrapper">
                <i class="fas fa-phone input-icon"></i>
                <input
                  id="phone"
                  v-model="forgotForm.phone"
                  type="tel"
                  placeholder="请输入绑定的手机号"
                  required
                />
              </div>
              <span v-if="phoneError" class="field-error">{{ phoneError }}</span>
            </div>
  
            <!-- 验证码 -->
            <div class="form-group">
              <label for="captcha">
                <i class="fas fa-shield-alt"></i>
                验证码
              </label>
              <div class="captcha-wrapper">
                <div class="input-wrapper captcha-input">
                  <i class="fas fa-shield-alt input-icon"></i>
                  <input
                    id="captcha"
                    v-model="forgotForm.captcha"
                    type="text"
                    placeholder="请输入验证码"
                    maxlength="6"
                    required
                  />
                </div>
                <button
                  type="button"
                  class="captcha-btn"
                  @click="sendCode"
                  :disabled="captchaCountdown > 0 || isLoading"
                >
                  {{ captchaCountdown > 0 ? `${captchaCountdown}s` : '获取验证码' }}
                </button>
              </div>
            </div>
  
            <div class="form-tip">
              <i class="fas fa-info-circle"></i>
              <span>验证码将发送至您的绑定手机号</span>
            </div>
  
            <button
              type="submit"
              class="submit-btn"
              :disabled="isLoading"
            >
              <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>验证身份</span>
            </button>
  
            <div v-if="errorMessage" class="error-message">
              <i class="fas fa-exclamation-circle"></i>
              {{ errorMessage }}
            </div>
          </form>
  
          <!-- 步骤2：重置密码 -->
          <form v-else class="forgot-form" @submit.prevent="resetPassword">
            <div class="form-group">
              <label for="newPassword">
                <i class="fas fa-lock"></i>
                新密码
              </label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input
                  id="newPassword"
                  v-model="forgotForm.newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请设置新密码（至少8位）"
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
              <div class="password-strength" v-if="forgotForm.newPassword">
                <div class="strength-bar">
                  <div
                    class="strength-fill"
                    :style="{ width: passwordStrength + '%', background: strengthColor }"
                  ></div>
                </div>
                <span class="strength-label" :style="{ color: strengthColor }">
                  {{ strengthText }}
                </span>
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
                  v-model="forgotForm.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="请再次输入新密码"
                  required
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <i :class="showConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
              <span v-if="confirmPasswordError" class="field-error">{{ confirmPasswordError }}</span>
            </div>
  
            <button
              type="submit"
              class="submit-btn"
              :disabled="isLoading"
            >
              <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>重置密码</span>
            </button>
  
            <div v-if="errorMessage" class="error-message">
              <i class="fas fa-exclamation-circle"></i>
              {{ errorMessage }}
            </div>
          </form>
  
          <!-- 成功状态 -->
          <div v-if="isSuccess" class="success-state">
            <i class="fas fa-check-circle"></i>
            <h3>密码重置成功</h3>
            <p>请使用新密码重新登录</p>
            <button class="login-now-btn" @click="goToLogin">立即登录</button>
          </div>
  
          <!-- 返回登录 -->
          <div class="back-to-login" v-if="!isSuccess">
            <a href="#" @click.prevent="goToLogin">返回登录</a>
          </div>
        </div>
  
        <!-- 底部版权 -->
        <div class="forgot-footer">
          <p>&copy; 2026 探店助手 · 让选择更简单</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, computed, watch } from 'vue'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  
  // ============================================
  // 表单数据
  // ============================================
  const forgotForm = reactive({
    phone: '',
    captcha: '',
    newPassword: '',
    confirmPassword: '',
  })
  
  const currentStep = ref(1) // 1: 验证身份, 2: 重置密码
  const isLoading = ref(false)
  const isSuccess = ref(false)
  const errorMessage = ref('')
  const captchaCountdown = ref(0)
  const showPassword = ref(false)
  const showConfirmPassword = ref(false)
  
  // ============================================
  // 表单验证
  // ============================================
  const phoneError = ref('')
  const confirmPasswordError = ref('')
  
  // 密码强度计算
  const passwordStrength = computed(() => {
    const pwd = forgotForm.newPassword
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
  watch(() => forgotForm.phone, (val) => {
    if (val && !/^1[3-9]\d{9}$/.test(val)) {
      phoneError.value = '请输入正确的手机号'
    } else {
      phoneError.value = ''
    }
  })
  
  watch(() => forgotForm.confirmPassword, (val) => {
    if (val && val !== forgotForm.newPassword) {
      confirmPasswordError.value = '两次密码输入不一致'
    } else {
      confirmPasswordError.value = ''
    }
  })
  
  // ============================================
  // 发送验证码
  // ============================================
  const sendCode = async () => {
    if (!forgotForm.phone) {
      errorMessage.value = '请输入手机号'
      return
    }
    if (phoneError.value) {
      errorMessage.value = '请输入正确的手机号'
      return
    }
  
    isLoading.value = true
    errorMessage.value = ''
  
    try {
      // 【API 接口1】发送验证码
      // 接口地址: POST /api/auth/forgot-password/send-code
      // 请求体: { phone: string }
      const response = await fetch('/api/auth/forgot-password/send-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: forgotForm.phone.trim(),
        }),
      })
  
      if (response.ok) {
        // 开始倒计时
        captchaCountdown.value = 60
        const timer = setInterval(() => {
          captchaCountdown.value--
          if (captchaCountdown.value <= 0) {
            clearInterval(timer)
          }
        }, 1000)
        alert('验证码已发送')
      } else {
        const error = await response.json()
        errorMessage.value = error.message || '发送验证码失败'
      }
    } catch (error) {
      console.error('发送验证码异常:', error)
      errorMessage.value = '网络异常，请稍后重试'
    } finally {
      isLoading.value = false
    }
  }
  
  // ============================================
  // 验证身份（步骤1提交）
  // ============================================
  const verifyIdentity = async () => {
    isLoading.value = true
    errorMessage.value = ''
  
    try {
      // 【API 接口2】验证身份
      // 接口地址: POST /api/auth/forgot-password/verify
      // 请求体: { phone: string, captcha: string }
      const response = await fetch('/api/auth/forgot-password/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: forgotForm.phone.trim(),
          captcha: forgotForm.captcha.trim(),
        }),
      })
  
      if (response.ok) {
        currentStep.value = 2
        errorMessage.value = ''
      } else {
        const error = await response.json()
        errorMessage.value = error.message || '验证失败，请重试'
      }
    } catch (error) {
      console.error('验证异常:', error)
      errorMessage.value = '网络异常，请稍后重试'
    } finally {
      isLoading.value = false
    }
  }
  
  // ============================================
  // 重置密码（步骤2提交）
  // ============================================
  const resetPassword = async () => {
    // 验证密码
    if (forgotForm.newPassword.length < 8) {
      errorMessage.value = '密码长度至少为8位'
      return
    }
  
    if (forgotForm.newPassword !== forgotForm.confirmPassword) {
      errorMessage.value = '两次密码输入不一致'
      return
    }
  
    isLoading.value = true
    errorMessage.value = ''
  
    try {
      // 【API 接口3】重置密码
      // 接口地址: POST /api/auth/forgot-password/reset
      // 请求体: { phone: string, password: string }
      const response = await fetch('/api/auth/forgot-password/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: forgotForm.phone.trim(),
          password: forgotForm.newPassword,
        }),
      })
  
      if (response.ok) {
        isSuccess.value = true
        // 清除表单
        forgotForm.newPassword = ''
        forgotForm.confirmPassword = ''
      } else {
        const error = await response.json()
        errorMessage.value = error.message || '重置密码失败，请重试'
      }
    } catch (error) {
      console.error('重置密码异常:', error)
      errorMessage.value = '网络异常，请稍后重试'
    } finally {
      isLoading.value = false
    }
  }
  
  // ============================================
  // 导航函数
  // ============================================
  const goBack = () => {
    router.back()
  }
  
  const goToLogin = () => {
    router.push('/login')
  }
  </script>
  
  <style scoped>
  /* ============================================
     全局布局（与 LoginView 风格一致）
     ============================================ */
  .forgot-password-view {
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
     找回密码卡片
     ============================================ */
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
  
  /* ============================================
     头部
     ============================================ */
  .forgot-header {
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
  
  .forgot-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.2rem;
  }
  
  .forgot-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 400;
  }
  
  /* ============================================
     表单
     ============================================ */
  .forgot-form {
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
  
  .field-error {
    display: block;
    font-size: 0.75rem;
    color: #ef4444;
    margin-top: 0.2rem;
  }
  
  /* ============================================
     验证码
     ============================================ */
  .captcha-wrapper {
    display: flex;
    gap: 0.6rem;
  }
  
  .captcha-input {
    flex: 1;
  }
  
  .captcha-btn {
    padding: 0 1rem;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border: none;
    border-radius: 0.8rem;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
    flex-shrink: 0;
  }
  
  .captcha-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  }
  
  .captcha-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
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
     提示文字
     ============================================ */
  .form-tip {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    color: #94a3b8;
    margin-bottom: 1rem;
  }
  
  .form-tip i {
    color: #3b82f6;
  }
  
  /* ============================================
     提交按钮
     ============================================ */
  .submit-btn {
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
  
  .submit-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s ease;
  }
  
  .submit-btn:hover:not(:disabled)::before {
    left: 100%;
  }
  
  .submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3);
  }
  
  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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
     成功状态
     ============================================ */
  .success-state {
    text-align: center;
    padding: 1.5rem 0;
  }
  
  .success-state i {
    font-size: 4rem;
    color: #22c55e;
    margin-bottom: 0.5rem;
  }
  
  .success-state h3 {
    font-size: 1.2rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.3rem;
  }
  
  .success-state p {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
  }
  
  .login-now-btn {
    padding: 0.6rem 2.5rem;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border: none;
    border-radius: 0.7rem;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .login-now-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  }
  
  /* ============================================
     返回登录
     ============================================ */
  .back-to-login {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.9rem;
    color: #64748b;
    position: relative;
    z-index: 1;
  }
  
  .back-to-login a {
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
  }
  
  .back-to-login a:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }
  
  /* ============================================
     底部版权
     ============================================ */
  .forgot-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.7rem;
    color: #94a3b8;
    position: relative;
    z-index: 1;
  }
  
  /* ============================================
     响应式
     ============================================ */
  @media (max-width: 768px) {
    .forgot-password-view {
      padding: 1rem;
      align-items: flex-start;
      padding-top: 2rem;
    }
  
    .forgot-container {
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
  
    .forgot-card {
      padding: 1.8rem 1.2rem 1.5rem;
      border-radius: 1.2rem;
    }
  
    .forgot-title {
      font-size: 1.4rem;
    }
  
    .forgot-subtitle {
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
  
    .captcha-btn {
      font-size: 0.75rem;
      padding: 0 0.8rem;
    }
  
    .submit-btn {
      padding: 0.7rem;
      font-size: 0.95rem;
    }
  
    .forgot-footer {
      margin-top: 1rem;
      font-size: 0.65rem;
    }
  }
  
  @media (max-width: 480px) {
    .forgot-password-view {
      padding: 0.8rem;
      padding-top: 1.5rem;
    }
  
    .forgot-card {
      padding: 1.5rem 1rem 1.2rem;
      border-radius: 1rem;
    }
  
    .logo-icon img {
      width: 44px;
      height: 44px;
    }
  
    .forgot-title {
      font-size: 1.2rem;
    }
  
    .captcha-wrapper {
      flex-direction: column;
      gap: 0.4rem;
    }
  
    .captcha-btn {
      padding: 0.5rem;
      border-radius: 0.6rem;
    }
  }
  
  @media (max-height: 500px) and (orientation: landscape) {
    .forgot-password-view {
      padding: 0.8rem;
      align-items: center;
    }
  
    .forgot-card {
      padding: 1rem 1.5rem;
      border-radius: 1rem;
    }
  
    .forgot-header {
      margin-bottom: 0.8rem;
    }
  
    .logo-icon img {
      width: 32px;
      height: 32px;
    }
  
    .forgot-title {
      font-size: 1.1rem;
      margin-bottom: 0;
    }
  
    .forgot-subtitle {
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
  
    .forgot-footer {
      display: none;
    }
  }
  </style>