import { inject } from 'vue'

export interface ToastOptions {
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  detail?: string
  duration?: number
  showRetry?: boolean
  onRetry?: () => void | Promise<void>
}

export const useToast = () => {
  // 从 provide 中获取 toast 实例
  const toast = inject('toast') as any

  // 如果 toast 不存在，使用控制台警告
  if (!toast) {
    console.warn('Toast not initialized. Please make sure ToastNotification is registered.')
    return {
      showToast: (options: ToastOptions) => {
        console.log('[Toast]', options.message)
      },
      success: (message: string, options?: Partial<ToastOptions>) => {
        console.log('[Toast Success]', message)
      },
      error: (message: string, options?: Partial<ToastOptions>) => {
        console.log('[Toast Error]', message)
      },
      warning: (message: string, options?: Partial<ToastOptions>) => {
        console.log('[Toast Warning]', message)
      },
      info: (message: string, options?: Partial<ToastOptions>) => {
        console.log('[Toast Info]', message)
      },
    }
  }

  return {
    showToast: toast.showToast,
    success: toast.success,
    error: toast.error,
    warning: toast.warning,
    info: toast.info,
    clearAll: toast.clearAll,
  }
}