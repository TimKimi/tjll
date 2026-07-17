<template>
  <div class="chat-view">
    <aside class="chat-sidebar">
      <!-- 侧边栏头部 -->
      <div class="sidebar-header">
        <button class="sidebar-back-btn" @click="goHome">
          <i class="fas fa-arrow-left"></i>
          <span class="btn-label">返回</span>
        </button>
        <span class="sidebar-title">对话记录</span>
      </div>

      <!-- 对话列表 -->
      <div class="conversation-list">
        <!-- 加载状态 -->
        <div v-if="isLoadingConversations" class="loading-state">
          <span>加载中...</span>
        </div>
        <!-- 空状态 -->
        <div v-else-if="conversationList.length === 0" class="empty-state-list">
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
          <i :class="conv.icon"></i>
          <div class="conv-info">
            <span class="conv-title">{{ conv.title }}</span>
            <span class="conv-time">{{ conv.time }}</span>
          </div>
          <!-- 删除单个对话按钮 -->
          <button class="delete-conv-btn" @click.stop="deleteConversation(index)" title="删除此对话">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

<!-- 清空历史记录 + 新建对话 -->
<div class="clear-history-wrapper">
  <div class="action-buttons">
    <button class="new-conversation-btn" @click="handleNewConversation">
      <span>新建对话</span>
    </button>
    <button class="clear-history-btn" @click="clearAllHistory">
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
          />
          <i v-else class="fas fa-user-circle"></i>
          <div class="user-detail">
            <span class="user-name">{{ userInfo.name || '用户' }}</span>
            <span class="user-status" :class="{ online: userInfo.isOnline }">
                <span class="status-dot-small"></span>
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
        <button class="mobile-back-btn" @click="goHome">
          <i class="fas fa-arrow-left"></i>
        </button>

        <div class="header-info">
          <i class="fas fa-robot"></i>
          <h2 class="header-title">探店助手</h2>
          <span :class="['status-badge', { online: isOnline }]">
            <span class="status-dot"></span>
            {{ isOnline ? '在线' : '离线' }}
          </span>
        </div>

          <!-- 清空对话按钮（只清空当前聊天内容） -->
          <button class="desktop-clear-btn" @click="clearChat" title="清空当前对话">
            <i class="fas fa-trash-alt"></i>
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
      <div class="chat-container" ref="chatContainer">
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">
    <img
      src="/images/2.png"
      alt="探店助手"
      style="width: 64px; height: 64px; object-fit: contain;"
    />
  </div>
          <h3 class="empty-title">你好！我是探店助手</h3>
          <span class="empty-hint">输入你想找的餐厅或美食开始对话</span>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message-row', msg.role]"
        >
          <!-- AI 头像 -->
          <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">
            🤖
          </div>

          <div :class="['message-bubble', msg.role]">
            <div class="message-content">{{ msg.content }}</div>
  
  <!-- 推荐卡片 - 点击进入详情页 -->
  <div v-if="msg.shop" class="recommend-card" @click="viewShopDetail(msg.shop.id)">
    <div class="card-image">
      <img :src="msg.shop.image" :alt="msg.shop.name" loading="lazy" />
      <span class="card-badge">推荐</span>
    </div>
    <div class="card-body">
      <div class="card-header-info">
        <h3 class="shop-name">{{ msg.shop.name }}</h3>
        <div class="shop-rating">
          <i class="fas fa-star"></i>
          <span>{{ msg.shop.rating }}</span>
          <span class="review-count">({{ msg.shop.reviewCount }}条)</span>
        </div>
      </div>
      
      <div class="reason">
        <i class="fas fa-lightbulb"></i>
        <span>{{ msg.shop.reason }}</span>
      </div>
      
      <div class="shop-info-grid">
        <div class="info-item">
          <i class="fas fa-coins"></i>
          <span>人均 ¥{{ msg.shop.price }}</span>
        </div>
        <div class="info-item">
          <i class="fas fa-map-pin"></i>
          <span>{{ msg.shop.address }}</span>
        </div>
        <div class="info-item">
          <i class="fas fa-clock"></i>
          <span>{{ msg.shop.hours }}</span>
        </div>
        <div class="info-item">
          <i class="fas fa-phone"></i>
          <span>{{ msg.shop.phone }}</span>
        </div>
      </div>
      
      <div class="shop-tags">
        <span v-for="tag in msg.shop.tags" :key="tag" class="tag">
          {{ tag }}
        </span>
      </div>
      
      <div class="shop-summary">
        <i class="fas fa-quote-left"></i>
        <span>{{ msg.shop.summary }}</span>
      </div>
      
      <!-- 只有一个操作按钮 -->
      <div class="card-action">
        <button class="detail-btn">
          <i class="fas fa-arrow-right"></i>
          查看餐厅详情
        </button>
      </div>
    </div>
  </div>
  
  <div class="message-time">{{ msg.time }}</div>
          </div>

          <!-- 用户头像 - 修改为使用用户注册的头像 -->
          <div v-if="msg.role === 'user'" class="avatar user-avatar">
            <img
              v-if="userInfo.avatar"
              :src="userInfo.avatar"
              alt="用户头像"
              class="avatar-img"
            />
            <i v-else class="fas fa-user"></i>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="message-row assistant">
          <div class="avatar assistant-avatar">🤖</div>
          <div class="message-bubble assistant">
            <div class="message-content loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-container">
          <button class="tool-btn" title="附件">
            <i class="fas fa-plus"></i>
          </button>

          <input
            v-model="inputText"
            type="text"
            placeholder="输入你想问的问题..."
            @keyup.enter="sendMessage(inputText)"
            class="chat-input"
          />

          <button class="tool-btn" title="语音">
            <i class="fas fa-microphone"></i>
          </button>

          <button
            @click="sendMessage(inputText)"
            class="send-btn"
            :disabled="!inputText.trim() || isLoading"
          >
            <i class="fas fa-paper-plane"></i>
            <span class="send-label">发送</span>
          </button>
        </div>
        <p class="disclaimer">
          <i class="fas fa-shield-alt"></i>
          内容由AI生成，仅供参考
        </p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRouter , useRoute} from 'vue-router'

const router = useRouter()
const route = useRoute()

// ============================================
// 1. 类型定义
// ============================================

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  time: string
  shop?: RecommendShop  // 添加推荐卡片数据
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
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data = await response.json()
      const userData = data.data || data
      userInfo.value = {
        id: userData.id ?? 1,
        name: userData.name || '用户',
        avatar: userData.avatar || '',
        isOnline: userData.isOnline ?? true,
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
      alert('删除失败，请稍后重试')
    }
  }
}

// ============================================
// 11. 清空所有历史记录
// ============================================

const clearAllHistory = async (): Promise<void> => {
  if (conversationList.value.length === 0) {
    alert('暂无历史记录')
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
      alert('清空失败，请稍后重试')
    }
  }
}

// ============================================
// 12. 核心功能：发送消息
// ============================================

const sendMessage = async (text: string): Promise<void> => {
  const trimmed = text.trim()
  if (!trimmed || isLoading.value) return

  // 如果没有当前对话，先创建一个
  let convId = currentConversationId.value
  if (!convId) {
    const newId = await createNewConversation()
    if (newId) {
      convId = newId
    } else {
      // 创建失败，使用本地临时 ID
      convId = Date.now()
      const tempConv: Conversation = {
        id: convId,
        title: '新对话',
        time: getCurrentTime(),
        icon: 'fas fa-comment',
        active: true,
      }
      conversationList.value.unshift(tempConv)
      currentConversationId.value = convId
    }
  }

  const userMessage: Message = {
    id: Date.now(),
    role: 'user',
    content: trimmed,
    time: getCurrentTime(),
  }
  messages.value.push(userMessage)
  inputText.value = ''
  await scrollToBottom()

  // 调用 AI API
  await callAIApi(trimmed, convId)
}

// ============================================
// 13. AI API 调用
// ============================================

const callAIApi = async (userInput: string, conversationId: number): Promise<void> => {
  isLoading.value = true

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userInput,
        conversationId: conversationId,
        userId: userInfo.value.id,
        userName: userInfo.value.name,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    const assistantContent = data.content || data.message || data.reply || '收到回复'

    // 生成推荐卡片
    let shopData: RecommendShop | undefined = undefined
    
    // 如果后端返回了商家数据
    if (data.shop) {
      shopData = data.shop
    } 

    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: assistantContent,
      time: getCurrentTime(),
      shop: shopData
    })

    await loadConversations()
  } catch (error) {
    console.error('AI 调用失败:', error)
    messages.value.push({
      id: Date.now() + 1,
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
  color: #334155;
  min-width: 0;
}

.chat-input::placeholder {
  color: #94a3b8;
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
</style>
