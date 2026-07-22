import { inject } from 'vue'

let globalToast: ReturnType<typeof createToastApi> | null = null

const createToastApi = (toast: any) => ({
  showToast: toast.showToast,
  success: toast.success,
  error: toast.error,
  warning: toast.warning,
  info: toast.info,
  clearAll: toast.clearAll,
})

export const setGlobalToast = (toast: any) => {
  globalToast = createToastApi(toast)
}

export const getGlobalToast = () => globalToast

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
  const toast = (inject('toast') as any) ?? globalToast

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

  return createToastApi(toast)
}
