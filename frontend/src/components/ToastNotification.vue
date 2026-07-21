<!-- src/components/ToastNotification.vue -->
<template>
    <Teleport to="body">
      <TransitionGroup name="toast" tag="div" class="toast-container">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="[toast.type, { 'with-retry': toast.showRetry }]"
        >
          <!-- 图标 -->
          <div class="toast-icon">
            <i :class="getIcon(toast.type)"></i>
          </div>
  
          <!-- 内容 -->
          <div class="toast-content">
            <div class="toast-message">{{ toast.message }}</div>
            <div class="toast-detail" v-if="toast.detail">{{ toast.detail }}</div>
          </div>
  
          <!-- 重试按钮 -->
          <button
            v-if="toast.showRetry"
            class="toast-retry-btn"
            @click="handleRetry(toast)"
          >
            <i class="fas fa-redo"></i>
            重试
          </button>
  
          <!-- 关闭按钮 -->
          <button class="toast-close-btn" @click="removeToast(toast.id)">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </TransitionGroup>
    </Teleport>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, onUnmounted } from 'vue'
  
  // ============================================
  // 类型定义
  // ============================================
  type ToastType = 'success' | 'error' | 'warning' | 'info'
  
  interface ToastItem {
    id: string
    type: ToastType
    message: string
    detail?: string
    duration?: number
    showRetry?: boolean
    onRetry?: () => void | Promise<void>
  }
  
  // ============================================
  // 状态
  // ============================================
  const toasts = reactive<ToastItem[]>([])
  let timerMap = new Map<string, ReturnType<typeof setTimeout>>()
  
  // ============================================
  // 方法
  // ============================================
  
  // 生成唯一 ID
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7)
  }
  
  // 获取图标
  const getIcon = (type: ToastType): string => {
    const icons: Record<ToastType, string> = {
      success: 'fas fa-check-circle',
      error: 'fas fa-exclamation-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle',
    }
    return icons[type] || icons.info
  }
  
  // 添加 Toast
  const showToast = (options: {
    message: string
    type?: ToastType
    detail?: string
    duration?: number
    showRetry?: boolean
    onRetry?: () => void | Promise<void>
  }): void => {
    const {
      message,
      type = 'info',
      detail,
      duration = 3000,
      showRetry = false,
      onRetry,
    } = options
  
    const id = generateId()
    const toast: ToastItem = {
      id,
      type,
      message,
      detail,
      duration,
      showRetry,
      onRetry,
    }
  
    toasts.push(toast)
  
    // 自动关闭
    if (duration > 0) {
      const timer = setTimeout(() => {
        removeToast(id)
      }, duration)
      timerMap.set(id, timer)
    }
  }
  
  // 移除 Toast
  const removeToast = (id: string): void => {
    const index = toasts.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.splice(index, 1)
      if (timerMap.has(id)) {
        clearTimeout(timerMap.get(id))
        timerMap.delete(id)
      }
    }
  }
  
  // 清除所有 Toast
  const clearAll = (): void => {
    toasts.splice(0, toasts.length)
    timerMap.forEach(timer => clearTimeout(timer))
    timerMap.clear()
  }
  
  // 重试处理
  const handleRetry = async (toast: ToastItem): Promise<void> => {
    if (toast.onRetry) {
      try {
        await toast.onRetry()
        removeToast(toast.id)
      } catch (error) {
        console.error('重试失败:', error)
      }
    }
  }
  
  // 便捷方法
  const success = (message: string, options?: Partial<Omit<ToastItem, 'type' | 'message'>>) => {
    showToast({ ...options, message, type: 'success' })
  }
  
  const error = (message: string, options?: Partial<Omit<ToastItem, 'type' | 'message'>>) => {
    showToast({ ...options, message, type: 'error' })
  }
  
  const warning = (message: string, options?: Partial<Omit<ToastItem, 'type' | 'message'>>) => {
    showToast({ ...options, message, type: 'warning' })
  }
  
  const info = (message: string, options?: Partial<Omit<ToastItem, 'type' | 'message'>>) => {
    showToast({ ...options, message, type: 'info' })
  }
  
  // ============================================
  // 导出
  // ============================================
  defineExpose({
    showToast,
    success,
    error,
    warning,
    info,
    clearAll,
    removeToast,
  })
  
  // ============================================
  // 清理
  // ============================================
  onUnmounted(() => {
    clearAll()
  })
  </script>
  
  <style scoped>
  /* ============================================
     Toast 容器
     ============================================ */
  .toast-container {
    position: fixed;
    top: 1.5rem;
    right: 1.5rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    max-width: 420px;
    width: 100%;
    pointer-events: none;
  }
  
  .toast-container > * {
    pointer-events: auto;
  }
  
  /* ============================================
     Toast 卡片
     ============================================ */
  .toast {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    padding: 1rem 1.2rem;
    background: #ffffff;
    border-radius: 0.8rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    border: 1px solid #e2e8f0;
    backdrop-filter: blur(8px);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }
  
  /* 左侧彩色边框 */
  .toast::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 4px;
    border-radius: 0.8rem 0 0 0.8rem;
  }
  
  .toast.success::before {
    background: #22c55e;
  }
  .toast.error::before {
    background: #ef4444;
  }
  .toast.warning::before {
    background: #f59e0b;
  }
  .toast.info::before {
    background: #3b82f6;
  }
  
  /* ============================================
     Toast 图标
     ============================================ */
  .toast-icon {
    flex-shrink: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 1rem;
  }
  
  .toast.success .toast-icon {
    color: #22c55e;
    background: #f0fdf4;
  }
  .toast.error .toast-icon {
    color: #ef4444;
    background: #fef2f2;
  }
  .toast.warning .toast-icon {
    color: #f59e0b;
    background: #fffbeb;
  }
  .toast.info .toast-icon {
    color: #3b82f6;
    background: #eff6ff;
  }
  
  /* ============================================
     Toast 内容
     ============================================ */
  .toast-content {
    flex: 1;
    min-width: 0;
  }
  
  .toast-message {
    font-size: 0.9rem;
    font-weight: 500;
    color: #0f172a;
    line-height: 1.4;
  }
  
  .toast-detail {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 0.2rem;
  }
  
  /* ============================================
     重试按钮
     ============================================ */
  .toast-retry-btn {
    flex-shrink: 0;
    padding: 0.3rem 0.8rem;
    background: #f1f5f9;
    border: none;
    border-radius: 0.4rem;
    color: #475569;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    transition: all 0.2s;
    white-space: nowrap;
  }
  
  .toast-retry-btn:hover {
    background: #e2e8f0;
    color: #1e293b;
  }
  
  .toast-retry-btn:active {
    transform: scale(0.95);
  }
  
  /* ============================================
     关闭按钮
     ============================================ */
  .toast-close-btn {
    flex-shrink: 0;
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 0.8rem;
    cursor: pointer;
    padding: 0.2rem;
    transition: color 0.2s;
    margin-top: -0.1rem;
  }
  
  .toast-close-btn:hover {
    color: #64748b;
  }
  
  /* ============================================
     动画
     ============================================ */
  .toast-enter-active,
  .toast-leave-active {
    transition: all 0.3s ease;
  }
  
  .toast-enter-from {
    opacity: 0;
    transform: translateX(30px) scale(0.95);
  }
  
  .toast-leave-to {
    opacity: 0;
    transform: translateX(30px) scale(0.95);
  }
  
  /* ============================================
     移动端适配
     ============================================ */
  @media (max-width: 768px) {
    .toast-container {
      top: 1rem;
      right: 1rem;
      left: 1rem;
      max-width: none;
      gap: 0.6rem;
    }
  
    .toast {
      padding: 0.8rem 1rem;
      border-radius: 0.6rem;
    }
  
    .toast-message {
      font-size: 0.85rem;
    }
  
    .toast-detail {
      font-size: 0.75rem;
    }
  
    .toast-icon {
      width: 1.6rem;
      height: 1.6rem;
      font-size: 0.8rem;
    }
  
    .toast-retry-btn {
      font-size: 0.7rem;
      padding: 0.2rem 0.6rem;
    }
  }
  
  @media (max-width: 480px) {
    .toast-container {
      top: 0.6rem;
      right: 0.6rem;
      left: 0.6rem;
    }
  
    .toast {
      padding: 0.6rem 0.8rem;
      border-radius: 0.5rem;
    }
  
    .toast-message {
      font-size: 0.8rem;
    }
  }
  </style>