// src/utils/errorHandler.ts

import type { ToastOptions } from '@/composables/useToast'

export interface ApiErrorResponse {
  code?: number
  message?: string
  data?: any
}

/**
 * 根据 HTTP 状态码和业务码生成友好错误信息
 */
export const getErrorMessage = (
  error: any,
  fallbackMessage: string = '操作失败，请稍后重试'
): string => {
  // 1. 网络错误
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return '网络连接失败，请检查网络后重试'
  }

  // 2. 如果有 response 属性（如 axios 错误对象），则处理
  if (error.response) {
    const status = error.response.status
    const data = error.response.data as ApiErrorResponse

    // 根据 HTTP 状态码
    switch (status) {
      case 400:
        return data?.message || '请求参数错误'
      case 401:
        return '未授权，请重新登录'
      case 403:
        return '权限不足，无法执行此操作'
      case 404:
        return '请求的资源不存在'
      case 409:
        return data?.message || '资源冲突，请检查后重试'
      case 500:
        return '服务器内部错误，请稍后重试'
      default:
        return data?.message || `请求失败 (${status})`
    }
  }

  // 3. 如果错误对象有 message 属性（例如我们自己抛出的 Error）
  if (error.message) {
    return error.message
  }

  // 4. 兜底
  return fallbackMessage
}

/**
 * 生成 Toast 选项（结合重试回调）
 */
export const getToastOptions = (
  error: any,
  fallbackMessage: string = '操作失败，请稍后重试',
  onRetry?: () => void | Promise<void>
): ToastOptions => {
  const message = getErrorMessage(error, fallbackMessage)
  const isNetworkError = error instanceof TypeError && error.message === 'Failed to fetch'

  return {
    message,
    type: 'error',
    duration: isNetworkError ? 5000 : 3000,
    showRetry: !!onRetry,
    onRetry: onRetry,
  }
}

/**
 * 统一处理 API 错误（打印日志 + 生成 Toast 配置）
 */
export const handleApiError = (
  error: any,
  fallbackMessage: string = '操作失败，请稍后重试',
  onRetry?: () => void | Promise<void>
): ToastOptions => {
  console.error('API Error:', error)
  return getToastOptions(error, fallbackMessage, onRetry)
}
