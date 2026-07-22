<template>
  <div class="chat-view">
    <aside class="chat-sidebar">
      <!-- 侧边栏头部 -->
      <div class="sidebar-header">
        <button
          class="sidebar-back-btn"
          @click="goHome"
        >
          <i class="fas fa-arrow-left" />
          <span class="btn-label">返回</span>
        </button>
        <span class="sidebar-title">对话记录</span>
      </div>

      <!-- 对话列表 -->
      <div class="conversation-list">
        <!-- 加载状态 -->
        <div
          v-if="isLoadingConversations"
          class="loading-state"
        >
          <span>加载中...</span>
        </div>
        <!-- 空状态 -->
        <div
          v-else-if="conversationList.length === 0"
          class="empty-state-list"
        >
          <span>暂无对话记录</span>
        </div>
        <!-- 对话列表 -->
        <div
          v-for="(conv, index) in conversationList"
          v-else
          :key="conv.id || index"
          :class="['conv-item', { active: conv.active }]"
          @click="selectConversation(index)"
        >
          <i :class="conv.icon" />
          <div class="conv-info">
            <span class="conv-title">{{ conv.title }}</span>
            <span class="conv-time">{{ conv.time }}</span>
          </div>
          <!-- 删除单个对话按钮 -->
          <button
            class="delete-conv-btn"
            title="删除此对话"
            @click.stop="deleteConversation(index)"
          >
            <i class="fas fa-times" />
          </button>
        </div>
      </div>

      <!-- 清空历史记录 + 新建对话 -->
      <div class="clear-history-wrapper">
        <div class="action-buttons">
          <button
            class="new-conversation-btn"
            @click="handleNewConversation"
          >
            <span>新建对话</span>
          </button>
          <button
            class="clear-history-btn"
            @click="clearAllHistory"
          >
            <span>清空历史</span>
          </button>
        </div>
      </div>

      <!-- 侧边栏底部用户信息 - 修改为使用用户头像 -->
      <div class="sidebar-footer">
        <div class="user-card">
          <!-- 使用用户头像 -->
          <img
            v-if="userInfo.avatar"
            :src="userInfo.avatar"
            alt="用户头像"
            class="user-avatar-img"
          >
          <i
            v-else
            class="fas fa-user-circle"
          />
          <div class="user-detail">
            <span class="user-name">{{ userInfo.name || '用户' }}</span>
            <span
              class="user-status"
              :class="{ online: userInfo.isOnline }"
            >
              <span class="status-dot-small" />
              {{ userInfo.isOnline ? '在线' : '离线' }}
            </span>
          </div>
        </div>
      </div>
    </aside>

    <!-- ========================================== -->
    <!-- 主对话区域 -->
    <!-- ========================================== -->
    <main class="chat-main">
      <!-- 头部 -->
      <header class="chat-header">
        <!-- 手机端返回按钮（仅手机端显示） -->
        <button
          class="mobile-back-btn"
          @click="goHome"
        >
          <i class="fas fa-arrow-left" />
        </button>

        <div class="header-info">
          <i class="fas fa-robot" />
          <h2 class="header-title">
            探店助手
          </h2>
          <span :class="['status-badge', { online: isOnline }]">
            <span class="status-dot" />
            {{ isOnline ? '在线' : '离线' }}
          </span>
          <!-- 洞察开关（紧挨状态标签） -->
          <div class="insight-controls">
            <div
              class="insight-toggle-item"
              @click="toggleCreateInsight"
            >
              <span class="insight-label">创建洞察</span>
              <span
                class="toggle-slider"
                :class="{ active: createInsightEnabled }"
              />
            </div>
            <div
              class="insight-toggle-item"
              @click="toggleUseInsight"
            >
              <span class="insight-label">使用洞察</span>
              <span
                class="toggle-slider"
                :class="{ active: useInsightEnabled }"
              />
            </div>
          </div>
        </div>

        <!-- 清空对话按钮（只清空当前聊天内容） -->
        <button
          class="desktop-clear-btn"
          title="清空当前对话"
          @click="clearChat"
        >
          <i class="fas fa-trash-alt" />
          <span class="clear-label">清空对话</span>
        </button>
      </header>

      <!-- 快捷提问 -->
      <div class="quick-questions">
        <button
          v-for="q in quickQuestions"
          :key="q"
          class="question-btn"
          @click="sendMessage(q)"
        >
          {{ q }}
        </button>
      </div>

      <!-- 对话容器 -->
      <div
        ref="chatContainer"
        class="chat-container"
      >
        <!-- 空状态 -->
        <div
          v-if="messages.length === 0"
          class="empty-state"
        >
          <div class="empty-icon">
            <img
              src="/images/2.png"
              alt="探店助手"
              style="width: 64px; height: 64px; object-fit: contain;"
            >
          </div>
          <h3 class="empty-title">
            你好！我是探店助手
          </h3>
          <span class="empty-hint">输入你想找的餐厅或美食开始对话</span>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message-row', msg.role]"
        >
          <!-- AI 头像 -->
          <div
            v-if="msg.role === 'assistant'"
            class="avatar assistant-avatar"
          >
            🤖
          </div>

          <div :class="['message-bubble', msg.role]">
            <div class="message-content">
              {{ msg.content }}
            </div>

            <!-- 新增：文件附件列表（当消息包含文件时） -->
            <div
              v-if="msg.files && msg.files.length"
              class="file-attachments"
            >
              <div
                v-for="(file, index) in msg.files"
                :key="index"
                class="file-attachment-item"
              >
                <i class="fas fa-file-alt file-icon" />
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
              </div>
            </div>


            <!-- 选项区域（仅当有 options 且未处理） -->
            <div
              v-if="msg.options && msg.options.length && !msg.isOptionHandled"
              class="options-container"
            >
              <div class="options-list">
                <button
                  v-for="opt in msg.options"
                  :key="opt"
                  class="option-btn"
                  @click="selectOption(opt, msg.id)"
                >
                  {{ opt }}
                </button>
              </div>
              <button
                class="generate-btn"
                @click="generateFinal(msg.id)"
              >
                直接生成推荐
              </button>
            </div>

            <!-- 推荐卡片 - 点击进入详情页 -->
            <div
              v-if="msg.shop"
              class="recommend-card"
              @click="viewShopDetail(msg.shop.id)"
            >
              <div class="card-image">
                <img
                  :src="msg.shop.image"
                  :alt="msg.shop.name"
                  loading="lazy"
                >
                <span class="card-badge">推荐</span>
              </div>
              <div class="card-body">
                <div class="card-header-info">
                  <h3 class="shop-name">
                    {{ msg.shop.name }}
                  </h3>
                  <div class="shop-rating">
                    <i class="fas fa-star" />
                    <span>{{ msg.shop.rating }}</span>
                    <span class="review-count">({{ msg.shop.reviewCount }}条)</span>
                  </div>
                </div>

                <div class="reason">
                  <i class="fas fa-lightbulb" />
                  <span>{{ msg.shop.reason }}</span>
                </div>

                <div class="shop-info-grid">
                  <div class="info-item">
                    <i class="fas fa-coins" />
                    <span>人均 ¥{{ msg.shop.price }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-map-pin" />
                    <span>{{ msg.shop.address }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-clock" />
                    <span>{{ msg.shop.hours }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-phone" />
                    <span>{{ msg.shop.phone }}</span>
                  </div>
                </div>

                <div class="shop-tags">
                  <span
                    v-for="tag in msg.shop.tags"
                    :key="tag"
                    class="tag"
                  >
                    {{ tag }}
                  </span>
                </div>

                <div class="shop-summary">
                  <i class="fas fa-quote-left" />
                  <span>{{ msg.shop.summary }}</span>
                </div>

                <!-- 只有一个操作按钮 -->
                <div class="card-action">
                  <button class="detail-btn">
                    <i class="fas fa-arrow-right" />
                    查看餐厅详情
                  </button>
                </div>
              </div>
            </div>

            <div class="message-time">
              {{ msg.time }}
            </div>
          </div>

          <!-- 用户头像 - 修改为使用用户注册的头像 -->
          <div
            v-if="msg.role === 'user'"
            class="avatar user-avatar"
          >
            <img
              v-if="userInfo.avatar"
              :src="userInfo.avatar"
              alt="用户头像"
              class="avatar-img"
            >
            <i
              v-else
              class="fas fa-user"
            />
          </div>
        </div>

        <!-- 加载状态 -->
        <div
          v-if="isLoading"
          class="message-row assistant"
        >
          <div class="avatar assistant-avatar">
            🤖
          </div>
          <div class="message-bubble assistant">
            <div class="message-content loading-dots">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <!-- 待上传文件列表 -->
        <div
          v-if="pendingFiles.length > 0"
          class="pending-files"
        >
          <div
            v-for="(fileItem, index) in pendingFiles"
            :key="fileItem.id"
            class="pending-file-item"
            :class="{ error: fileItem.status === 'error' }"
          >
            <span class="file-name">
              <i class="fas fa-file" />
              {{ fileItem.file.name }}
            </span>
            <span class="file-size">{{ formatFileSize(fileItem.file.size) }}</span>
            <span
              v-if="fileItem.status === 'uploading'"
              class="file-status"
            >
              <i class="fas fa-spinner fa-spin" /> 上传中...
            </span>
            <span
              v-else-if="fileItem.status === 'success'"
              class="file-status success"
            >
              <i class="fas fa-check-circle" /> 已上传
            </span>
            <span
              v-else-if="fileItem.status === 'error'"
              class="file-status error"
            >
              <i class="fas fa-exclamation-circle" /> 上传失败
            </span>
            <button
              v-if="fileItem.status === 'error'"
              class="retry-file-btn"
              title="重试上传"
              @click="retryFile(index)"
            >
              <i class="fas fa-redo" />
            </button>
            <button
              class="remove-file-btn"
              title="移除文件"
              @click="removePendingFile(index)"
            >
              <i class="fas fa-times" />
            </button>
          </div>
        </div>

        <div class="input-container">
          <input
            v-model="inputText"
            type="text"
            placeholder="输入你想问的问题..."
            class="chat-input"
            @keyup.enter="sendMessage(inputText)"
          >

          <!-- 文件上传按钮 -->
          <button
            class="tool-btn"
            title="上传文件"
            @click="triggerFileUpload"
          >
            <i class="fas fa-plus" />
          </button>

          <!-- 隐藏的文件选择器 -->
          <input
            ref="fileInput"
            type="file"
            accept=".doc,.docx,.pdf,.txt,.md,.png,.jpg,"
            style="display: none"
            @change="handleFileUpload"
          >

          <!-- 语音按钮 -->
          <button
            class="tool-btn"
            title="语音输入"
            :class="{ recording: isRecording }"
            @click="toggleRecording"
          >
            <!-- ✅ 使用两个图标：一个作为背景，一个作为动态效果 -->
            <span class="mic-wrapper">
              <i class="fas fa-microphone mic-icon" />
              <span
                v-if="isRecording"
                class="mic-waves"
              >
                <span class="wave wave1" />
                <span class="wave wave2" />
                <span class="wave wave3" />
              </span>
            </span>
          </button>

          <button
            class="send-btn"
            :disabled="(!inputText.trim() && pendingFiles.length === 0) || isLoading"
            @click="sendMessage(inputText)"
          >
            <i class="fas fa-paper-plane" />
            <span class="send-label">发送</span>
          </button>
        </div>
        <p class="disclaimer">
          <i class="fas fa-shield-alt" />
          内容由AI生成，仅供参考
        </p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRouter , useRoute} from 'vue-router'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const toast = useToast()

// ============================================
// 1. 类型定义
// ============================================

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  time: string
  shop?: RecommendShop  // 添加推荐卡片数据
  options?: string[]   // 选项列表（仅 assistant 消息携带）
  isOptionHandled?: boolean // 标记该选项是否已被用户处理（点击后禁用）
  files?: { name: string; size: number }[]
}

interface Conversation {
  id: number
  title: string
  time: string
  icon: string
  active: boolean
}

interface UserInfo {
  id?: number
  name: string
  avatar: string
  isOnline: boolean
}

interface RecommendShop {
  id: number
  name: string
  image: string
  rating: number
  reviewCount: number
  reason: string
  price: number
  address: string
  hours: string
  phone: string
  tags: string[]
  summary: string
}

// ============================================
// 2. 响应式数据
// ============================================

const quickQuestions = [
  '推荐附近好吃的川菜',
  '适合约会的餐厅',
  '人均100以内的餐厅',
  '安静的咖啡馆推荐',
  '下雨天适合吃的热乎的'
]

const messages = ref<Message[]>([])
const inputText = ref('')
const isLoading = ref(false)
const isOnline = ref(true)
const isLoadingConversations = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const hasProcessedQuery = ref(false) // 防止重复处理

// 用户信息（从后端 API 获取）
const userInfo = ref<UserInfo>({
  id: 1,
  name: '用户',
  avatar: '',
  isOnline: true
})

// 对话列表（从后端 API 获取）
const conversationList = ref<Conversation[]>([])
// 当前激活的对话 ID（用于发送消息时关联）
const currentConversationId = ref<number | null>(null)

const isRecording = ref(false)  // 是否正在录音
const recognition = ref<any>(null)  // 语音识别实例
const audioLevel = ref(0) // 声音大小（0-100）

// 洞察开关状态
const createInsightEnabled = ref(false)
const useInsightEnabled = ref(false)
// 音频上下文
let audioContext: AudioContext | null = null
let analyser: AnalyserNode | null = null
let dataArray: Uint8Array | null = null
let animationId: number | null = null

const fileInput = ref<HTMLInputElement | null>(null)

// ============================================
// 3. 工具函数
// ============================================

const getCurrentTime = (): string => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

const scrollToBottom = async (): Promise<void> => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const goHome = (): void => {
  router.push('/')
}

// ============================================
// 4. 清空功能
// ============================================

// 清空当前对话（只清空聊天区域）
const clearChat = (): void => {
  if (messages.value.length === 0) return

  if (confirm('确定要清空当前对话内容吗？')) {
    messages.value = []
  }
}

// ============================================
// 5. 获取用户信息（从后端 API）
// ============================================

const getUserInfo = async (): Promise<void> => {
  try {
    const response = await fetch('/api/user/profile', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
    })

    if (response.ok) {
      const result = await response.json()
      const userData = result.data || result

      // 处理头像 URL
      let avatar = userData.avatar || ''
      if (avatar && !avatar.startsWith('http')) {
        const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const path = avatar.startsWith('/') ? avatar : `/${avatar}`
        avatar = `${baseURL}${path}`
      }

      userInfo.value = {
        id: userData.id ?? 1,
        name: userData.username || '用户',
        avatar: avatar,
        isOnline: userData.is_online ?? true,
      }
    } else {
      console.warn('获取用户信息失败，使用默认用户信息')
      setDefaultUserInfo()
    }
  } catch (error) {
    console.error('获取用户信息异常:', error)
    setDefaultUserInfo()
  }
}

// 设置默认用户信息（降级方案）
const setDefaultUserInfo = (): void => {
  userInfo.value = {
    id: 1,
    name: '用户',
    avatar: `https://ui-avatars.com/api/?name=用户&background=ff6b35&color=fff&size=40&rounded=true`,
    isOnline: true,
  }
}

// ============================================
// 6. 获取对话列表（从后端 API）
// ============================================

const loadConversations = async (): Promise<void> => {
  isLoadingConversations.value = true
  try {
    const response = await fetch('/api/conversations', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data = await response.json()
      const list = data.data || data || []

      if (Array.isArray(list) && list.length > 0) {
        conversationList.value = list.map((item: any, index: number) => ({
          id: item.id || index + 1,
          title: item.title || '未命名对话',
          time: item.time || '刚刚',
          icon: item.icon || 'fas fa-comment',
          active: item.active || index === 0,
        }))

        // 如果有激活的对话，加载其消息
        const activeConv = conversationList.value.find(conv => conv.active)
        if (activeConv) {
          currentConversationId.value = activeConv.id
          await loadConversationMessages(activeConv.id)
        }
      } else {
        // 没有历史对话，创建一个新的默认对话
        setDefaultConversation()
      }
    } else {
      console.warn('获取对话列表失败，使用默认对话')
      setDefaultConversation()
    }
  } catch (error) {
    console.error('获取对话列表异常:', error)
    setDefaultConversation()
  } finally {
    isLoadingConversations.value = false
  }
}

// 设置默认对话（降级方案）
const setDefaultConversation = (): void => {
  const defaultConv = {
    id: Date.now(),
    title: '当前对话',
    time: '刚刚',
    icon: 'fas fa-comment',
    active: true,
  }
  conversationList.value = [defaultConv]
  currentConversationId.value = defaultConv.id
}

// ============================================
// 7. 加载某个对话的消息
// ============================================

const loadConversationMessages = async (conversationId: number): Promise<void> => {
  try {
    const response = await fetch(`/api/conversations/${conversationId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data = await response.json()
      const conversationData = data.data || data
      const msgs = conversationData.messages || []

      if (Array.isArray(msgs) && msgs.length > 0) {
        messages.value = msgs.map((msg: any) => ({
          id: msg.id || Date.now(),
          role: msg.role || 'assistant',
          content: msg.content || '',
          time: msg.time || getCurrentTime(),
        }))
      } else {
        messages.value = []
      }

      await scrollToBottom()
    } else {
      console.warn('加载对话消息失败')
    }
  } catch (error) {
    console.error('加载对话消息异常:', error)
  }
}

// ============================================
// 8. 创建新对话（被 sendMessage 和 handleNewConversation 复用）
// ============================================

const createNewConversation = async (title?: string): Promise<number | null> => {
  try {
    const response = await fetch('/api/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: title || '新对话',
      }),
    })

    if (!response.ok) {
      throw new Error(`创建对话失败: ${response.status}`)
    }

    const data = await response.json()
    const newConv = data.data || data

    // 取消所有对话的激活状态
    conversationList.value.forEach(conv => (conv.active = false))

    const newConversation: Conversation = {
      id: newConv.id || Date.now(),
      title: newConv.title || '新对话',
      time: getCurrentTime(),
      icon: 'fas fa-comment',
      active: true,
    }
    conversationList.value.unshift(newConversation)
    currentConversationId.value = newConversation.id

    // 清空当前消息
    messages.value = []
    await scrollToBottom()

    return newConversation.id
  } catch (error) {
    console.error('创建新对话异常:', error)
    return null
  }
}


// ============================================
// 9. 选择对话
// ============================================

const selectConversation = async (index: number): Promise<void> => {
  if (index < 0 || index >= conversationList.value.length) {
    console.warn('无效的对话索引:', index)
    return
  }

  // 更新激活状态
  conversationList.value.forEach((conv, i) => {
    conv.active = i === index
  })

  const conversation = conversationList.value[index]
  if (conversation) {
    currentConversationId.value = conversation.id
    await loadConversationMessages(conversation.id)
  }
}

// ============================================
// 10. 删除对话
// ============================================

const deleteConversation = async (index: number): Promise<void> => {
  if (index < 0 || index >= conversationList.value.length) {
    console.warn('无效的对话索引:', index)
    return
  }

  const conversation = conversationList.value[index]
  if (!conversation) return

  if (confirm(`确定要删除"${conversation.title}"吗？此操作不可恢复！`)) {
    try {
      const response = await fetch(`/api/conversations/${conversation.id}`, {
        method: 'DELETE',
      })

      if (response.ok || response.status === 204) {
        // 如果删除的是当前激活的对话，清空消息
        if (conversation.active) {
          messages.value = []
          currentConversationId.value = null
        }

        // 从列表中移除
        conversationList.value.splice(index, 1)

        // 如果还有对话，激活第一个
        if (conversationList.value.length > 0) {
          const firstConv = conversationList.value[0]
          if (firstConv) {
            firstConv.active = true
            currentConversationId.value = firstConv.id
            await loadConversationMessages(firstConv.id)
          }
        } else {
          // 没有对话了，创建一个默认的
          setDefaultConversation()
          messages.value = []
        }
      } else {
        throw new Error('删除失败')
      }
    } catch (error) {
      console.error('删除对话失败:', error)
      toast.error('删除失败，请稍后重试')
    }
  }
}

// ============================================
// 11. 清空所有历史记录
// ============================================

const clearAllHistory = async (): Promise<void> => {
  if (conversationList.value.length === 0) {
    toast.info('暂无历史记录')
    return
  }

  if (confirm('确定要清空所有历史记录吗？此操作不可恢复！')) {
    try {
      const response = await fetch('/api/conversations', {
        method: 'DELETE',
      })

      if (response.ok || response.status === 204) {
        conversationList.value = []
        messages.value = []
        currentConversationId.value = null
        setDefaultConversation()
      } else {
        throw new Error('清空失败')
      }
    } catch (error) {
      console.error('清空历史失败:', error)
      toast.error('清空失败，请稍后重试')
    }
  }
}

// ============================================
// 12. 核心功能：发送消息
// ============================================

// 发送消息（整合文件和文字）
const sendMessage = async (
  text: string,
  extra?: { parentId?: string; action?: 'generate' }
) => {
  const trimmed = text.trim()
  if (!trimmed && pendingFiles.value.length === 0) return
  if (trimmed && trimmed.length < 2 && pendingFiles.value.length === 0) {
    toast.warning('请输入更完整的问题')
    return
  }
  if (isLoading.value) return

  // 处理文件上传
  const hasPending = pendingFiles.value.some(
    item => item.status === 'pending' || item.status === 'error'
  )
  if (hasPending) {
    const allSuccess = await uploadPendingFiles()
    if (!allSuccess) {
      toast.warning('存在上传失败的文件，请重试后再发送')
      return
    }
  }

  // 收集成功上传的文件信息
  const successFiles = pendingFiles.value.filter(item => item.status === 'success')
  const fileList = successFiles.map(item => ({
    name: item.file.name,
    size: item.file.size,
  }))

  // 构建消息内容
  let messageContent = trimmed || ''
  // 如果有文件，在内容中添加文件列表（文本形式，用于显示）
  if (fileList.length > 0) {
    if (messageContent) messageContent += '\n'
    messageContent += fileList.map(f => `📎 ${f.name}`).join('\n')
  }

  // 如果有文字或文件，发送消息
  if (messageContent || fileList.length > 0) {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: messageContent || '文件',
      time: getCurrentTime(),
      files: fileList, // ✅ 保存文件列表到消息对象
    }
    messages.value.push(userMsg)
    inputText.value = ''
    await scrollToBottom()

    // 如果有文字，调用 AI
    if (trimmed) {
      await callAIApi(trimmed, extra?.parentId, extra?.action)
    }
  }

  // 清空待上传列表（成功文件已发送）
  pendingFiles.value = []
}
// ============================================
// 13. AI API 调用
// ============================================

const callAIApi = async (
  userInput: string,
  parentId?: string,
  action?: 'generate'
) => {
  isLoading.value = true
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userInput,
        conversationId: currentConversationId.value,
        userId: userInfo.value.id,
        userName: userInfo.value.name,
        parentId,          // 关联到哪条选项消息
        action,            // 是否请求直接生成
      }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()

    // ========== 接口标注 ==========
    // 【推荐卡片接口】/api/chat POST
    // 当 data.type === 'final' 时返回最终推荐，data.shop 为卡片数据
    // 【选项接口】/api/chat POST
    // 当 data.type === 'options' 时返回选项列表，data.options 为 string[]
    // ===============================

    if (data.type === 'options') {
      // 添加带选项的 assistant 消息
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.content || '请选择以下选项：',
        time: getCurrentTime(),
        options: data.options || [],
        isOptionHandled: false,
      })
    } else {
      // 最终推荐（可能包含 shop）
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.content || '为您推荐：',
        time: getCurrentTime(),
        shop: data.shop,   // 推荐卡片数据
      })
    }

    // 刷新侧边栏对话列表（更新标题等）
    await loadConversations()
  } catch (error) {
    console.error('AI 调用失败:', error)
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '抱歉，我暂时无法回答，请稍后再试。',
      time: getCurrentTime(),
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// ============================================
// 14. 生命周期钩子
// ============================================

onMounted(async () => {
  // 并行获取用户信息和对话列表
  Promise.all([getUserInfo(), loadConversations()]).catch((error) => {
    console.error('初始化数据加载失败:', error)
  })
    // 处理查询参数
    await processQueryParam()
    // 新增：初始化语音识别
    initSpeechRecognition()
})

// ============================================
// 15. 新建对话
// ============================================

const handleNewConversation = async (): Promise<void> => {
  // 如果有当前对话且没有消息，提示用户
  if (messages.value.length === 0 && conversationList.value.length > 0) {
    const confirmNew = confirm('当前对话为空，确定要创建新对话吗？')
    if (!confirmNew) return
  }

  // 如果有未保存的消息，提示用户
  if (messages.value.length > 0) {
    const confirmNew = confirm('当前对话尚未保存，确定要创建新对话吗？')
    if (!confirmNew) return
  }

  await createNewConversation()
}

// ============================================
// 16. 处理从首页传递过来的查询参数
// ============================================
const processQueryParam = async (): Promise<void> => {
  // 防止重复处理
  if (hasProcessedQuery.value) return

  const query = route.query.q as string
  if (query && query.trim()) {
    hasProcessedQuery.value = true
    // 等待对话框加载完成
    await nextTick()
    // 延迟一点确保所有初始化完成
    setTimeout(() => {
      sendMessage(query.trim())
    }, 300)
  }
}

// ============================================
// 17. 监听路由变化（处理从其他页面跳转过来的查询参数）
// ============================================
watch(
  () => route.query.q,
  (newQuery) => {
    // 如果已经有消息或者正在加载，不处理
    if (messages.value.length > 0 || isLoading.value) return
    if (newQuery && typeof newQuery === 'string' && newQuery.trim()) {
      // 重置标记，允许处理新的查询
      hasProcessedQuery.value = false
      processQueryParam()
    }
  },
  { immediate: false }
)

// ============================================
// 18. 推荐卡片交互方法
// ============================================

// 查看商家详情 - 跳转到详情页
const viewShopDetail = (shopId: number): void => {
  // TODO: 跳转到商家详情页
  console.log('查看商家详情:', shopId)
  router.push(`/shop/${shopId}`)
}

// ============================================
// 19. 语音识别功能
// ============================================

// 初始化语音识别
const initSpeechRecognition = () => {
  // 检查浏览器是否支持
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    console.warn('当前浏览器不支持语音识别')
    return
  }

  recognition.value = new SpeechRecognition()
  recognition.value.lang = 'zh-CN'  // 中文
  recognition.value.continuous = false  // 单次识别
  recognition.value.interimResults = true  // 显示中间结果

// 识别结果
recognition.value.onresult = (event: any) => {
  const results = event.results
  const transcript = results[0][0].transcript
  inputText.value = transcript  // ✅ 只填入输入框

  // ✅ 如果是最终结果，只停止录音，不自动发送
  if (results[0].isFinal) {
    isRecording.value = false
  }
}

  // 识别结束
  recognition.value.onend = () => {
    isRecording.value = false
    stopAudioMonitoring()  // 停止声音监听
  }

  // 识别错误
  recognition.value.onerror = (event: any) => {
    console.error('语音识别错误:', event.error)
    isRecording.value = false
    if (event.error === 'not-allowed') {
      toast.warning('请允许浏览器使用麦克风权限')
    } else if (event.error === 'no-speech') {
      // 没有检测到语音，静默处理
    } else {
      toast.error('语音识别失败，请重试')
    }
  }
}

// 切换语音识别（点击麦克风按钮）
const toggleRecording = async () => {
  if (!recognition.value) {
    toast.warning('当前浏览器不支持语音识别，请使用 Chrome 浏览器')
    return
  }

  if (isRecording.value) {
    // 停止录音
    try {
      recognition.value.stop()
    } catch (e) {console.warn('停止录音时出错:', e)}
    isRecording.value = false
    stopAudioMonitoring()  // ✅ 停止声音监听
  } else {
    // 开始录音
    try {
      // ✅ 先获取音频权限并开始监听声音
      await startAudioMonitoring()
      recognition.value.start()
      isRecording.value = true
    } catch (e) {
      console.error('启动语音识别失败:', e)
      toast.error('启动语音识别失败，请重试')
      stopAudioMonitoring()
    }
  }
}

// ============================================
// 20. 声音波动效果
// ============================================

// 获取麦克风音频流
const getAudioStream = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext = new AudioContext()
    analyser = audioContext.createAnalyser()
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(analyser)
    analyser.fftSize = 256
    dataArray = new Uint8Array(analyser.frequencyBinCount)
    return true
  } catch (error) {
    console.error('获取麦克风失败:', error)
    return false
  }
}

// 更新声音大小
const updateAudioLevel = () => {
  if (!analyser || !dataArray || !isRecording.value) {
    audioLevel.value = 0
    return
  }

  // ✅ 使用类型断言 as Uint8Array<ArrayBuffer>
  analyser.getByteFrequencyData(dataArray as Uint8Array<ArrayBuffer>)
  let sum = 0
  for (let i = 0; i < dataArray.length; i++) {
    sum += dataArray[i] || 0  // ✅ 添加 || 0 防止 undefined
  }
  const avg = sum / dataArray.length
  audioLevel.value = Math.min((avg / 128) * 100, 100)

  animationId = requestAnimationFrame(updateAudioLevel)
}

// 开始监听声音
const startAudioMonitoring = async () => {
  const success = await getAudioStream()
  if (success) {
    updateAudioLevel()
  }
}

// 停止监听声音
const stopAudioMonitoring = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  audioLevel.value = 0
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
  analyser = null
  dataArray = null
}

// ============================================
// 21. AI选项
// ============================================

// 点击选项按钮
const selectOption = (option: string, parentId: string) => {
  // 将原选项消息标记为已处理，禁用按钮
  const parentMsg = messages.value.find(m => m.id === parentId)
  if (parentMsg) parentMsg.isOptionHandled = true

  // 发送用户的选择（不带 action，让后端继续返回选项或最终推荐）
  sendMessage(option, { parentId })
}

// 点击“直接生成推荐”
const generateFinal = (parentId: string) => {
  const parentMsg = messages.value.find(m => m.id === parentId)
  if (parentMsg) parentMsg.isOptionHandled = true

  // 发送特殊指令，携带 action: 'generate'
  sendMessage('直接生成', { parentId, action: 'generate' })
}

// ============================================
// 22.文件上传功能
// ============================================

// 触发文件选择器
const triggerFileUpload = () => {
  fileInput.value?.click()
}

// 处理文件上传（只添加到待上传列表）
const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 限制文件大小（10MB）
  if (file.size > 10 * 1024 * 1024) {
    toast.error('文件大小不能超过 10MB')
    input.value = ''
    return
  }

  // 添加到待上传列表，状态为 pending
  pendingFiles.value.push({
    id: crypto.randomUUID(),
    file: file,
    status: 'pending',
  })

  // 清空 input，以便再次选择
  input.value = ''
}

// 待上传文件列表
interface PendingFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  errorMsg?: string
}
const pendingFiles = ref<PendingFile[]>([])


//格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// 移除待上传文件
const removePendingFile = (index: number) => {
  pendingFiles.value.splice(index, 1)
}

// 重试失败的文件
const retryFile = (index: number) => {
  const fileItem = pendingFiles.value[index]
  if (!fileItem || fileItem.status !== 'error') return
  // 重置状态为 pending，然后触发上传
  fileItem.status = 'pending'
  // 自动触发上传（用户点击发送时会一并上传）
  toast.info('已加入上传队列，请点击发送')
}

// 批量上传待上传文件，返回是否全部成功
const uploadPendingFiles = async (): Promise<boolean> => {
  const toUpload = pendingFiles.value.filter(
    item => item.status === 'pending' || item.status === 'error'
  )
  if (toUpload.length === 0) return true

  toUpload.forEach(item => (item.status = 'uploading'))
  isLoading.value = true

  let allSuccess = true

  for (const fileItem of toUpload) {
    try {
      const formData = new FormData()
      formData.append('file', fileItem.file)

      const response = await fetch('http://localhost:8000/api/file/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: formData
      })

      if (!response.ok) {
        let errorMsg = `上传失败 (HTTP ${response.status})`
        try {
          const errorData = await response.json()
          // 支持多种错误格式
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMsg = errorData.detail.map((d: any) => d.msg || d.message || '').filter(Boolean).join(', ')
            } else {
              errorMsg = errorData.detail
            }
          } else if (errorData.message) {
            errorMsg = errorData.message
          } else if (errorData.msg) {
            errorMsg = errorData.msg
          } else if (typeof errorData === 'string') {
            errorMsg = errorData
          }
        } catch (e) {
          // 解析失败，使用状态文本
          errorMsg = `HTTP ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMsg)
      }

      const result = await response.json()
      if (result.code !== 200) {
        throw new Error(result.message || '上传失败')
      }

      fileItem.status = 'success'
    } catch (error) {
      console.error('文件上传失败:', error)
      fileItem.status = 'error'
      fileItem.errorMsg = error instanceof Error ? error.message : '上传失败'
      allSuccess = false
      toast.error(`文件 "${fileItem.file.name}" 上传失败: ${fileItem.errorMsg}`)
    }
  }

  isLoading.value = false
  return allSuccess
}

// ============================================
// 洞察功能（预留接口）
// ============================================

const toggleCreateInsight = () => {
  createInsightEnabled.value = !createInsightEnabled.value
  // TODO: 调用后端接口开启/关闭创建洞察
  console.log('创建洞察状态:', createInsightEnabled.value)
  toast.info(`创建洞察已${createInsightEnabled.value ? '开启' : '关闭'}`)
}

const toggleUseInsight = () => {
  useInsightEnabled.value = !useInsightEnabled.value
  // TODO: 调用后端接口开启/关闭使用洞察
  console.log('使用洞察状态:', useInsightEnabled.value)
  toast.info(`使用洞察已${useInsightEnabled.value ? '开启' : '关闭'}`)
}
</script>



<style scoped>
/* ============================================
   全局布局
   ============================================ */
.chat-view {
  display: flex;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  background: #f1f5f9;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* ============================================
   电脑端侧边栏（默认显示）
   ============================================ */
.chat-sidebar {
  width: 280px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1.2rem 1.2rem;
  border-bottom: 1px solid #f1f5f9;
}

.sidebar-back-btn {
  background: #f1f5f9;
  border: none;
  color: #1e293b;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.4rem 0.8rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.sidebar-back-btn:hover {
  background: #e2e8f0;
}

.btn-label {
  font-size: 0.85rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .btn-label {
    display: none;
  }
}

.sidebar-title {
  flex: 1;
  font-weight: 650;
  color: #1e293b;
  font-size: 1.05rem;
}

/* 对话列表 */
.conversation-list {
  flex: 1;
  padding: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  overflow-y: auto;
}

.loading-state,
.empty-state-list {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.8rem 1rem;
  border-radius: 0.7rem;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}

.conv-item:hover {
  background: #f8fafc;
}

.conv-item.active {
  background: #eff6ff;
}

.conv-item i {
  color: #94a3b8;
  font-size: 0.9rem;
  width: 1.2rem;
  text-align: center;
}

.conv-item.active i {
  color: #2563eb;
}

.conv-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  flex: 1;
}

.conv-title {
  font-size: 0.85rem;
  color: #334155;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-item.active .conv-title {
  color: #1e293b;
  font-weight: 600;
}

.conv-time {
  font-size: 0.7rem;
  color: #94a3b8;
}

/* 删除单个对话按钮 */
.delete-conv-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.7rem;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 0.3rem;
  opacity: 0;
  transition: all 0.2s;
}

.conv-item:hover .delete-conv-btn {
  opacity: 1;
}

.delete-conv-btn:hover {
  background: #fef2f2;
  color: #dc2626;
}

/* ============================================
   底部操作按钮（清空历史 + 新建对话）
   ============================================ */
   .clear-history-wrapper {
  padding: 0.8rem 1.2rem;
  border-top: 1px solid #e8f5e9;
  border-bottom: 1px solid #e8f5e9;
  flex-shrink: 0;
  background: linear-gradient(180deg, #fafffe 0%, #f5faf6 100%);
}

.action-buttons {
  display: flex;
  gap: 0.8rem;
}

/* ============================================
   新建对话按钮（淡绿色系）
   ============================================ */
/* ============================================
   新建对话按钮（蓝色系）
   ============================================ */
   .new-conversation-btn {
  flex: 1;
  padding: 0.7rem 1rem;
  background: linear-gradient(135deg, #e3f2fd 0%, #90caf9 100%);
  border: none;
  border-radius: 0.8rem;
  color: #1565c0;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(21, 101, 192, 0.12);
}

/* 按钮光效 */
.new-conversation-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  transition: left 0.6s ease;
}

.new-conversation-btn:hover::before {
  left: 100%;
}

.new-conversation-btn:hover {
  background: linear-gradient(135deg, #90caf9 0%, #64b5f6 100%);
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 6px 20px rgba(21, 101, 192, 0.25);
}

.new-conversation-btn:active {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 2px 8px rgba(21, 101, 192, 0.12);
}

.new-conversation-btn i {
  font-size: 1rem;
  transition: transform 0.3s ease;
}

.new-conversation-btn:hover i {
  transform: rotate(90deg);
}
/* ============================================
   清空历史按钮（淡红色系，保持对比）
   ============================================ */
.clear-history-btn {
  flex: 1;
  padding: 0.7rem 1rem;
  background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%);
  border: none;
  border-radius: 0.8rem;
  color: #c62828;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(198, 40, 40, 0.1);
}

/* 按钮光效 */
.clear-history-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.6s ease;
}

.clear-history-btn:hover::before {
  left: 100%;
}

.clear-history-btn:hover {
  background: linear-gradient(135deg, #f8bbd0 0%, #f48fb1 100%);
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 6px 20px rgba(198, 40, 40, 0.18);
}

.clear-history-btn:active {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 2px 8px rgba(198, 40, 40, 0.1);
}

.clear-history-btn i {
  font-size: 0.95rem;
  transition: transform 0.3s ease;
}

.clear-history-btn:hover i {
  transform: scale(1.1) rotate(-5deg);
}

@media (max-width: 768px) {
  .clear-history-wrapper {
    display: none;
  }
}

/* ============================================
   侧边栏底部用户信息 - 修改样式
   ============================================ */
.sidebar-footer {
  padding: 1rem 1.2rem;
  border-top: 1px solid #f1f5f9;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

/* 用户头像图片 */
.user-avatar-img {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e2e8f0;
}

/* 当没有头像时使用图标 */
.user-card > i {
  font-size: 2.2rem;
  color: #94a3b8;
}

.user-detail {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.user-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #334155;
}

.user-status {
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.status-dot-small {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
}

.user-status:not(.online) .status-dot-small {
  background: #94a3b8;
}

/* ============================================
   主对话区域
   ============================================ */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #ffffff;
  position: relative;
  overflow: hidden;
}

/* ============================================
   头部
   ============================================ */
.chat-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #2fb6e8 0%, #38b5eb 100%);
  color: white;
  flex-shrink: 0;
}

.mobile-back-btn {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.3rem;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
}

.header-info > i {
  font-size: 1.3rem;
}

.header-title {
  font-size: 1.1rem;
  font-weight: 650;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.2rem 0.7rem;
  border-radius: 1rem;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-badge.online .status-dot {
  background: #4ade80;
}

/* 清空对话按钮（头部） */
.desktop-clear-btn {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.15s;
  font-size: 0.85rem;
}

.desktop-clear-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.desktop-clear-btn i {
  font-size: 0.9rem;
}

.clear-label {
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .clear-label {
    display: none;
  }
  .desktop-clear-btn {
    padding: 0.4rem 0.6rem;
  }
}

/* ============================================
   快捷提问
   ============================================ */
.quick-questions {
  padding: 0.8rem 1.5rem;
  background: #fafbfd;
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.quick-questions::-webkit-scrollbar {
  height: 0;
}

.question-btn {
  padding: 0.4rem 1rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  font-size: 0.8rem;
  color: #475569;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.question-btn:hover {
  background: #5295ec;
  color: white;
  border-color: #1974d6;
}

/* ============================================
   对话容器
   ============================================ */
   .chat-container {
  flex: 1;
  padding: 1.5rem 2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  position: relative;
}

/* 用伪元素加载背景图 */
.chat-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  background:
    url('/images/1.png') center / cover no-repeat fixed;
  opacity: 0.4;  /* 控制透明度，0-1 之间调整 */
  pointer-events: none;
}

/* 所有子元素在背景之上 */
.chat-container > * {
  position: relative;
  z-index: 1;
}
/* 空状态 */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  margin: auto;
  max-width: 450px;
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 0.8rem;
}

.empty-title {
  font-size: 1.3rem;
  font-weight: 650;
  color: #1e293b;
  margin-bottom: 0.4rem;
}

.empty-hint {
  font-size: 0.75rem;
  color: #94a3b8;
}

/* 消息行 */
.message-row {
  display: flex;
  gap: 0.8rem;
  align-items: flex-end;
  animation: fadeIn 0.3s ease;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

/* 头像 */
.avatar {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1rem;
  overflow: hidden;
}

/* 头像图片 */
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.assistant-avatar {
  background: #fff7ed;
  font-size: 1.2rem;
}

.user-avatar {
  background: #ff6b35;
  color: white;
}

/* 消息气泡 */
.message-bubble {
  max-width: 65%;
  padding: 0.8rem 1.2rem;
  border-radius: 1rem;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 0.9rem;
}

.message-bubble.user {
  background: #4ee369;
  color: white;
  border-bottom-right-radius: 0.3rem;
}

.message-bubble.assistant {
  background: white;
  color: #334155;
  border-bottom-left-radius: 0.3rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
}

.message-content {
  line-height: 1.6;
}

.message-time {
  font-size: 0.65rem;
  opacity: 0.6;
  margin-top: 0.3rem;
  text-align: right;
}

/* 加载动画 */
.loading-dots {
  display: flex;
  gap: 4px;
  padding: 0.2rem 0;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: dotPulse 1.4s infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}
.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}

/* ============================================
   输入区域
   ============================================ */
.input-area {
  padding: 1rem 1.5rem 1.2rem;
  border-top: 1px solid #e2e8f0;
  background: white;
  flex-shrink: 0;
  padding-bottom: calc(1.2rem + env(safe-area-inset-bottom, 0px));
}

.input-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 1.5rem;
  padding: 0.3rem 0.5rem;
  transition: border-color 0.2s;
}

.input-container:focus-within {
  border-color: lab(76.95% -11.98 -29.62);
  background: white;
}

.tool-btn {
  position: relative;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.15s;
}

.tool-btn:hover {
  color: #64748b;
}

.chat-input {
  flex: 1;
  padding: 0.5rem 0.3rem;
  border: none;
  outline: none;
  font-size: 0.9rem;
  background: transparent;
  color:  #090909;
  min-width: 0;
  font-weight: 500;
}

.chat-input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

/* 发送按钮 - 带箭头指示 */
.send-btn {
  background: hsl(204, 81%, 42%);
  border: none;
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
  font-size: 0.85rem;
  font-weight: 500;
}

.send-btn::after {
  content: '→';
  font-size: 1.1rem;
  transition: transform 0.2s;
}

.send-btn:hover:not(:disabled)::after {
  transform: translateX(3px);
}

.send-btn:hover:not(:disabled) {
  background: #3387e8;
  transform: scale(1.02);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-btn i {
  font-size: 0.9rem;
}

.send-label {
  font-size: 0.85rem;
}

/* 手机端优化 */
@media (max-width: 768px) {
  .send-btn {
    padding: 0.3rem 0.6rem;
  }

  .send-label {
    display: none;
  }

  .send-btn::after {
    content: '→';
  }
}

.disclaimer {
  text-align: center;
  font-size: 0.65rem;
  color: #94a3b8;
  margin-top: 0.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
}

/* ============================================
   动画
   ============================================ */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ============================================
   滚动条
   ============================================ */
.chat-container::-webkit-scrollbar {
  width: 4px;
}

.chat-container::-webkit-scrollbar-track {
  background: transparent;
}

.chat-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

/* ============================================
   平板端 (768px - 1024px)
   ============================================ */
@media (max-width: 1024px) {
  .chat-sidebar {
    width: 240px;
  }

  .chat-container {
    padding: 1.2rem 1.5rem;
  }

  .message-bubble {
    max-width: 75%;
  }
}

/* ============================================
   手机端 (最大768px) - 隐藏侧边栏
   ============================================ */
@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }

  .mobile-back-btn {
    display: block;
  }

  .desktop-clear-btn {
    display: flex;
  }

  .chat-header {
    padding: 0.8rem 1rem;
  }

  .header-title {
    font-size: 1rem;
  }

  .quick-questions {
    padding: 0.6rem 0.8rem;
    gap: 0.4rem;
  }

  .question-btn {
    font-size: 0.75rem;
    padding: 0.35rem 0.8rem;
  }

  .chat-container {
    padding: 0.8rem;
    gap: 0.8rem;
  }

  .message-bubble {
    max-width: 85%;
    padding: 0.7rem 1rem;
    font-size: 0.85rem;
  }

  .message-bubble.user {
    max-width: 80%;
  }

  .avatar {
    width: 1.8rem;
    height: 1.8rem;
    font-size: 0.8rem;
  }

  .assistant-avatar {
    font-size: 1rem;
  }

  .empty-state {
    padding: 2rem 1.2rem;
    margin: 0.5rem;
  }

  .empty-icon {
    font-size: 3rem;
  }

  .empty-title {
    font-size: 1.1rem;
  }

  .input-area {
    padding: 0.7rem 0.8rem 0.9rem;
    padding-bottom: calc(0.9rem + env(safe-area-inset-bottom, 0px));
  }

  .input-container {
    border-radius: 1.2rem;
    padding: 0.2rem 0.3rem;
  }

  .chat-input {
    font-size: 0.85rem;
  }
}

/* ============================================
   小屏手机 (最大480px)
   ============================================ */
@media (max-width: 480px) {
  .chat-header {
    padding: 0.6rem 0.8rem;
  }

  .header-title {
    font-size: 0.9rem;
  }

  .quick-questions {
    padding: 0.5rem 0.6rem;
  }

  .question-btn {
    font-size: 0.7rem;
    padding: 0.3rem 0.7rem;
  }

  .chat-container {
    padding: 0.6rem;
    gap: 0.6rem;
  }

  .message-bubble {
    max-width: 90%;
    padding: 0.6rem 0.8rem;
    font-size: 0.8rem;
  }

  .empty-state {
    padding: 1.5rem 1rem;
  }

  .empty-icon {
    font-size: 2.5rem;
  }

  .send-btn {
    padding: 0.2rem 0.5rem;
  }
}

/* ============================================
   横屏手机优化
   ============================================ */
@media (max-height: 500px) and (orientation: landscape) {
  .chat-header {
    padding: 0.5rem 1rem;
  }

  .quick-questions {
    display: none;
  }

  .chat-container {
    padding: 0.5rem 1rem;
  }

  .empty-state {
    padding: 1rem;
  }

  .empty-icon {
    font-size: 2rem;
  }

  .input-area {
    padding: 0.5rem 1rem 0.6rem;
  }
}

/* ============================================
   推荐卡片样式
   ============================================ */
   .recommend-card {
  background: white;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin: 0.5rem 0;
  border: 1px solid #f1f5f9;
  transition: all 0.3s ease;
  max-width: 420px;
  cursor: pointer;
}

.recommend-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* 卡片图片 */
.card-image {
  position: relative;
  width: 100%;
  height: 160px;
  overflow: hidden;
  background: #f1f5f9;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recommend-card:hover .card-image img {
  transform: scale(1.03);
}

.card-badge {
  position: absolute;
  top: 0.8rem;
  left: 0.8rem;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  padding: 0.2rem 0.8rem;
  border-radius: 1rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 卡片主体 */
.card-body {
  padding: 1rem 1.2rem;
}

.card-header-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.shop-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.shop-rating {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.9rem;
  color: #f59e0b;
  flex-shrink: 0;
}

.shop-rating span {
  color: #334155;
  font-weight: 600;
}

.shop-rating .review-count {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 400;
}

/* 推荐理由 */
.reason {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  background: #f0fdf4;
  padding: 0.4rem 0.6rem;
  border-radius: 0.5rem;
  margin-bottom: 0.8rem;
  border-left: 3px solid #22c55e;
}

.reason i {
  color: #22c55e;
  font-size: 0.8rem;
  margin-top: 0.1rem;
  flex-shrink: 0;
}

.reason span {
  font-size: 0.85rem;
  color: #166534;
  line-height: 1.4;
}

/* 信息网格 */
.shop-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem 0.8rem;
  margin-bottom: 0.8rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: #475569;
}

.info-item i {
  color: #94a3b8;
  width: 0.9rem;
  font-size: 0.7rem;
  text-align: center;
  flex-shrink: 0;
}

.info-item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 特色标签 */
.shop-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.8rem;
}

.shop-tags .tag {
  background: #f1f5f9;
  padding: 0.15rem 0.6rem;
  border-radius: 1rem;
  font-size: 0.7rem;
  color: #475569;
  border: none;
  cursor: default;
}

.shop-tags .tag:hover {
  background: #e2e8f0;
  transform: none;
}

/* 用户摘要 */
.shop-summary {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  background: #f8fafc;
  padding: 0.5rem 0.6rem;
  border-radius: 0.5rem;
  margin-bottom: 0.8rem;
  border-left: 3px solid #3b82f6;
}

.shop-summary i {
  color: #3b82f6;
  font-size: 0.7rem;
  margin-top: 0.1rem;
  flex-shrink: 0;
}

.shop-summary span {
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.4;
  font-style: italic;
}

/* 操作按钮 */
.card-action {
  margin-top: 0.2rem;
}

.detail-btn {
  width: 100%;
  padding: 0.5rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.detail-btn:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  transform: scale(1.01);
}

.detail-btn i {
  font-size: 0.8rem;
}

/* ============================================
   语音输入按钮
   ============================================ */
   .tool-btn:hover {
  color: #64748b;
}

/* 麦克风包装器 */
.mic-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 麦克风图标 - 在波动圆环之上 */
.mic-icon {
  position: relative;
  z-index: 2;
  transition: color 0.2s;
  font-size: 1rem;
}

/* 录音状态 - 按钮变红*/
.tool-btn.recording {
  color: #ef4444;
}

.tool-btn.recording .mic-icon {
  color: #ef4444;
}

/* 波动圆环容器 */
.mic-waves {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 30px;
  height: 30px;
  z-index: 1;
  pointer-events: none;
}

/* 单个波动圆环 */
.wave {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 2px solid #ef4444;
  opacity: 0;
  width: 18px;
  height: 18px;
  animation: waveExpand 1.2s ease-out infinite;
}

/* 三个圆环不同延迟，形成连续波动 */
.wave1 {
  animation-delay: 0s;
}

.wave2 {
  animation-delay: 0.4s;
}

.wave3 {
  animation-delay: 0.8s;
}

/* 波动动画 - 从内向外扩散*/
@keyframes waveExpand {
  0% {
    width: 14px;
    height: 14px;
    opacity: 0.8;
    transform: translate(-50%, -50%) scale(0.5);
  }
  100% {
    width: 48px;
    height: 48px;
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.6);
  }
}

/* 选项样式*/
.options-container {
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px solid #e2e8f0;
}

.options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.option-btn {
  padding: 0.3rem 1rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  font-size: 0.8rem;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.2s;
}
.option-btn:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.generate-btn {
  padding: 0.3rem 1.2rem;
  background: #f59e0b;
  border: none;
  border-radius: 1.5rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}
.generate-btn:hover {
  background: #d97706;
}

/* 待上传文件列表 */
.pending-files {
  padding: 0.5rem 0.2rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 0.5rem;
}

.pending-file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8fafc;
  padding: 0.3rem 0.6rem 0.3rem 0.8rem;
  border-radius: 0.6rem;
  border: 1px solid #e2e8f0;
  font-size: 0.8rem;
}

.pending-file-item.error {
  border-color: #fca5a5;
  background: #fef2f2;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #334155;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #94a3b8;
  font-size: 0.7rem;
}

.file-status {
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.file-status.success {
  color: #22c55e;
}
.file-status.error {
  color: #ef4444;
}
.file-status.uploading {
  color: #3b82f6;
}

.remove-file-btn,
.retry-file-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 0.1rem 0.3rem;
  border-radius: 0.3rem;
  transition: all 0.2s;
}

.remove-file-btn:hover {
  background: #fef2f2;
  color: #dc2626;
}

.retry-file-btn:hover {
  background: #eff6ff;
  color: #2563eb;
}

/* 洞察控制区域 */
.insight-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 0 0.5rem;
}

.insight-toggle-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.9);
  user-select: none;
  transition: color 0.2s;
}

.insight-toggle-item:hover {
  color: #ffffff;
}

.insight-icon {
  font-size: 0.9rem;
}

.insight-label {
  white-space: nowrap;
}

/* 洞察控制区域 */
.insight-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 0 0.5rem;
}

.insight-toggle-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.9);
  user-select: none;
  transition: color 0.2s;
}

.insight-toggle-item:hover {
  color: #ffffff;
}

.insight-icon {
  font-size: 0.9rem;
}

.insight-label {
  white-space: nowrap;
}

/* 滑块样式（与个人中心风格一致） */
.header-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
}

/* 竖向开关容器 */
.insight-controls {
  display: flex;
  flex-direction: column;   /* 竖向排列 */
  gap: 2px;
  margin-left: 0.8rem;      /* 与状态标签保持一点间距 */
}

.insight-toggle-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;   /* 放大字体 */
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.insight-toggle-item .toggle-slider {
  width: 24px;
  height: 14px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 7px;
  position: relative;
  transition: background 0.25s;
  flex-shrink: 0;
}

.insight-toggle-item .toggle-slider::after {
  content: '';
  width: 10px;
  height: 10px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.25s;
}

.insight-toggle-item .toggle-slider.active {
  background: #4ade80;
}
.insight-toggle-item .toggle-slider.active::after {
  transform: translateX(10px);
}

/* 手机端隐藏 */
@media (max-width: 768px) {
  .insight-controls {
    display: none;
  }
}

</style>
