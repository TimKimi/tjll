import type { ToastOptions } from '@/composables/useToast'

export interface ApiErrorResponse {
  code?: number
  message?: string
  data?: any
}

export const getErrorMessage = (error: any, fallbackMessage: string = '操作失败，请稍后重试'): string => {
  // 网络错误
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return '网络连接失败，请检查网络后重试'
  }

  // API 响应错误
  if (error.response) {
    const status = error.response.status
    const data = error.response.data as ApiErrorResponse
    
    if (status === 401) {
      return '登录已过期，请重新登录'
    }
    if (status === 403) {
      return '您没有权限执行此操作'
    }
    if (status === 404) {
      return '请求的数据不存在'
    }
    if (status === 500) {
      return '服务器繁忙，请稍后重试'
    }
    
    return data?.message || `请求失败 (${status})`
  }

  // 其他错误
  if (error.message) {
    return error.message
  }

  return fallbackMessage
}

export const getToastOptions = (
  error: any,
  fallbackMessage: string = '操作失败，请稍后重试',
  onRetry?: () => void | Promise<void>
): ToastOptions => {
  const message = getErrorMessage(error, fallbackMessage)
  
  // 判断是否网络错误，可重试
  const isNetworkError = error instanceof TypeError && error.message === 'Failed to fetch'
  
  return {
    message,
    type: 'error',
    duration: isNetworkError ? 5000 : 3000,
    showRetry: !!onRetry,
    onRetry: onRetry,
  }
}

// 统一处理 API 错误
export const handleApiError = (
  error: any,
  fallbackMessage: string = '操作失败，请稍后重试',
  onRetry?: () => void | Promise<void>
): ToastOptions => {
  console.error('API Error:', error)
  return getToastOptions(error, fallbackMessage, onRetry)
}