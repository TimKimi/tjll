<template>
    <div class="restaurant-view">
      <!-- 顶部导航栏 -->
      <header class="restaurant-header">
        <button class="back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          <span>返回</span>
        </button>
        <div class="header-center">
          <h1 class="header-title">餐厅详情</h1>
        </div>
        <div class="header-actions">
          <button class="action-btn" @click="toggleFavorite" :class="{ favorited: isFavorited }">
            <i :class="isFavorited ? 'fas fa-heart' : 'far fa-heart'"></i>
          </button>
          <button class="action-btn" @click="shareRestaurant">
            <i class="fas fa-share-alt"></i>
          </button>
        </div>
      </header>
  
      <div class="restaurant-content" ref="restaurantContent">
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <p>加载餐厅信息...</p>
        </div>
  
        <!-- 餐厅信息 -->
        <div v-else-if="restaurantData" class="restaurant-detail">
          <!-- 图片轮播 -->
          <div class="restaurant-gallery">
            <div class="gallery-main" @click="openGallery(0)">
              <img :src="restaurantData.image" :alt="restaurantData.name" />
              <div class="gallery-badge">
                <i class="fas fa-images"></i>
                <span>{{ restaurantData.images?.length || 1 }} 张</span>
              </div>
            </div>
            <div class="gallery-thumbs" v-if="restaurantData.images && restaurantData.images.length > 1">
              <div
                v-for="(img, index) in restaurantData.images.slice(1, 4)"
                :key="index"
                class="thumb-item"
                @click="openGallery(index + 1)"
              >
                <img :src="img" :alt="restaurantData.name" />
              </div>
              <div v-if="restaurantData.images.length > 4" class="thumb-more" @click="openGallery(4)">
                <span>+{{ restaurantData.images.length - 4 }}</span>
              </div>
            </div>
          </div>
  
          <!-- 基本信息 -->
          <div class="restaurant-info-section">
            <div class="info-header">
              <div>
                <div class="name-wrapper">
                  <h1 class="restaurant-name">{{ restaurantData.name }}</h1>
                  <span class="rating-emoji">{{ getRatingEmoji(restaurantData.rating) }}</span>
                </div>
                <div class="restaurant-meta">
                  <span class="restaurant-rating">
                    <i class="fas fa-star"></i>
                    {{ restaurantData.rating }}
                    <span class="review-count">({{ restaurantData.reviewCount }}条评价)</span>
                  </span>
                  <span class="restaurant-price">¥{{ restaurantData.price }}/人</span>
                  <span class="restaurant-category">{{ restaurantData.category || '中餐' }}</span>
                </div>
              </div>
              <div class="restaurant-status" :class="{ open: restaurantData.isOpen }">
                <span class="status-dot"></span>
                {{ restaurantData.isOpen ? '营业中' : '已休息' }}
              </div>
            </div>
  
            <!-- 营业信息 -->
            <div class="restaurant-info-grid">
              <div class="info-item">
                <i class="fas fa-clock"></i>
                <div>
                  <span class="info-label">营业时间</span>
                  <span class="info-value">{{ restaurantData.hours }}</span>
                </div>
              </div>
              <div class="info-item">
                <i class="fas fa-map-pin"></i>
                <div>
                  <span class="info-label">地址</span>
                  <span class="info-value">{{ restaurantData.address }}</span>
                </div>
              </div>
              <div class="info-item">
                <i class="fas fa-phone"></i>
                <div>
                  <span class="info-label">电话</span>
                  <span class="info-value">{{ restaurantData.phone }}</span>
                </div>
              </div>
            </div>
  
            <!-- 操作按钮 -->
            <div class="action-buttons">
              <button class="action-btn-primary navigate" @click="navigateToRestaurant">
                <i class="fas fa-directions"></i>
                导航
              </button>
              <button class="action-btn-primary call" @click="callRestaurant">
                <i class="fas fa-phone"></i>
                打电话
              </button>
              <button class="action-btn-primary share" @click="shareRestaurant">
                <i class="fas fa-share-alt"></i>
                分享
              </button>
            </div>
  
            <!-- 特色标签 -->
            <div class="restaurant-tags-section" v-if="restaurantData.tags && restaurantData.tags.length">
              <h3 class="section-title">
                <i class="fas fa-tags"></i>
                特色标签
              </h3>
              <div class="restaurant-tags">
                <span v-for="tag in restaurantData.tags" :key="tag" class="tag">
                  {{ tag }}
                </span>
              </div>
            </div>
  
            <!-- 推荐理由 -->
            <div class="restaurant-reason" v-if="restaurantData.reason">
              <h3 class="section-title">
                <i class="fas fa-lightbulb"></i>
                推荐理由
              </h3>
              <div 
                class="reason-content" 
                :style="{
                  background: getReasonColor(restaurantData.rating).bg,
                  borderLeftColor: getReasonColor(restaurantData.rating).border
                }"
              >
                <i class="fas fa-quote-left" :style="{ color: getReasonColor(restaurantData.rating).icon }"></i>
                <p :style="{ color: getReasonColor(restaurantData.rating).text }">{{ restaurantData.reason }}</p>
              </div>
            </div>
  
            <!-- 用户评价摘要 -->
            <div class="restaurant-summary-section" v-if="restaurantData.summary">
              <h3 class="section-title">
                <i class="fas fa-comment-dots"></i>
                用户评价
              </h3>
              <div class="summary-content">
                <i class="fas fa-quote-left"></i>
                <p>{{ restaurantData.summary }}</p>
              </div>
            </div>
  
            <!-- 评价列表 -->
            <div class="reviews-section" v-if="restaurantData.reviews && restaurantData.reviews.length">
              <div class="reviews-header">
                <h3 class="section-title">
                  <i class="fas fa-star-half-alt"></i>
                  用户评价
                </h3>
                <span class="review-total">共 {{ restaurantData.reviews.length }} 条</span>
              </div>
              <div class="reviews-list">
                <div
                  v-for="review in displayedReviews"
                  :key="review.id"
                  class="review-item"
                >
                  <div class="review-user">
                    <img :src="review.avatar || 'https://ui-avatars.com/api/?name=' + review.userName + '&background=3b82f6&color=fff'" :alt="review.userName" />
                    <div>
                      <span class="review-name">{{ review.userName }}</span>
                      <span class="review-time">{{ review.time }}</span>
                    </div>
                  </div>
                  <div class="review-rating">
                    <i v-for="i in 5" :key="i" class="fas fa-star" :class="{ active: i <= review.rating }"></i>
                  </div>
                  <p class="review-content">{{ review.content }}</p>
                </div>
              </div>
              
              <!-- 加载更多按钮 -->
              <div v-if="hasMoreReviews" class="load-more-wrapper">
                <button class="load-more-btn" @click="loadMoreReviews" :disabled="isLoadingMore">
                  <span v-if="!isLoadingMore">查看更多评论 ({{ remainingReviewsCount }} 条)</span>
                  <span v-else><i class="fas fa-spinner fa-spin"></i> 加载中...</span>
                </button>
              </div>
            </div>
          </div>
        </div>
  
        <!-- 空状态 -->
        <div v-else class="empty-state">
          <i class="fas fa-store-slash"></i>
          <p>餐厅不存在</p>
          <button class="empty-btn" @click="goBack">返回首页</button>
        </div>
      </div>
  
      <!-- 底部固定导航 -->
      <div class="bottom-nav" v-if="restaurantData">
        <div class="bottom-nav-content">
          <div class="nav-info">
            <span class="nav-price">¥{{ restaurantData.price }}/人</span>
            <span class="nav-rating">
              <i class="fas fa-star"></i>
              {{ restaurantData.rating }}
            </span>
          </div>
          <div class="nav-actions">
            <button class="nav-btn favorite" @click="toggleFavorite" :class="{ active: isFavorited }">
              <i :class="isFavorited ? 'fas fa-heart' : 'far fa-heart'"></i>
              <span>{{ isFavorited ? '已收藏' : '收藏' }}</span>
            </button>
            <button class="nav-btn book" @click="bookTable">
              <i class="fas fa-calendar-check"></i>
              预约
            </button>
            <button class="nav-btn navigate" @click="navigateToRestaurant">
              <i class="fas fa-directions"></i>
              导航
            </button>
          </div>
        </div>
      </div>
  
      <!-- 图片预览弹窗 -->
      <Teleport to="body">
        <div v-if="showGalleryModal" class="gallery-modal" @click="closeGallery">
          <div class="gallery-modal-content" @click.stop>
            <button class="gallery-close" @click="closeGallery">
              <i class="fas fa-times"></i>
            </button>
            <div class="gallery-image-wrapper">
              <img 
                :src="restaurantData?.images?.[currentImageIndex]" 
                :alt="restaurantData?.name"
                class="gallery-image"
              />
            </div>
            <div class="gallery-counter" v-if="restaurantData?.images && restaurantData.images.length > 1">
              {{ currentImageIndex + 1 }} / {{ restaurantData.images.length }}
            </div>
            <button 
              v-if="restaurantData?.images && restaurantData.images.length > 1"
              class="gallery-nav gallery-prev" 
              @click.stop="prevImage"
              :disabled="currentImageIndex === 0"
            >
              <i class="fas fa-chevron-left"></i>
            </button>
            <button 
              v-if="restaurantData?.images && restaurantData.images.length > 1"
              class="gallery-nav gallery-next" 
              @click.stop="nextImage"
              :disabled="currentImageIndex === (restaurantData?.images?.length || 0) - 1"
            >
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
      </Teleport>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, computed, nextTick, onUnmounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  
  const route = useRoute()
  const router = useRouter()
  
  // ============================================
  // 类型定义
  // ============================================
  interface Review {
    id: number
    userName: string
    avatar?: string
    rating: number
    content: string
    time: string
  }
  
  interface RestaurantData {
    id: number
    name: string
    image: string
    images?: string[]
    rating: number
    reviewCount: number
    price: number
    address: string
    hours: string
    phone: string
    category?: string
    isOpen: boolean
    reason?: string
    summary?: string
    tags: string[]
    reviews?: Review[]
    lat?: number
    lng?: number
  }
  
  // ============================================
  // 状态
  // ============================================
  const isLoading = ref(false)
  const restaurantData = ref<RestaurantData | null>(null)
  const isFavorited = ref(false)
  const restaurantContent = ref<HTMLElement | null>(null)
  
  // 评论分页状态
  const REVIEW_PAGE_SIZE = 10
  const reviewPage = ref(1)
  const isLoadingMore = ref(false)
  
  // 图片预览状态
  const showGalleryModal = ref(false)
  const currentImageIndex = ref(0)
  
  // ============================================
  // 评分表情映射
  // ============================================
  const getRatingEmoji = (rating: number): string => {
    if (rating >= 4.5) return '😍'
    if (rating >= 4.0) return '😊'
    if (rating >= 3.5) return '🙂'
    if (rating >= 3.0) return '😐'
    if (rating >= 2.5) return '😕'
    return '😞'
  }
  
  // ============================================
  // 推荐理由颜色映射
  // ============================================
  const getReasonColor = (rating: number) => {
    if (rating >= 4.5) {
      return {
        bg: '#f0fdf4',
        border: '#22c55e',
        text: '#166534',
        icon: '#22c55e'
      }
    } else if (rating >= 3.5) {
      return {
        bg: '#fffbeb',
        border: '#f59e0b',
        text: '#92400e',
        icon: '#f59e0b'
      }
    } else if (rating >= 2.5) {
      return {
        bg: '#fef2f2',
        border: '#ef4444',
        text: '#991b1b',
        icon: '#ef4444'
      }
    } else {
      return {
        bg: '#f1f5f9',
        border: '#94a3b8',
        text: '#475569',
        icon: '#94a3b8'
      }
    }
  }
  
  // ============================================
  // 生命周期
  // ============================================
  onMounted(() => {
    const restaurantId = route.params.id as string
    if (restaurantId) {
      loadRestaurantDetail(restaurantId)
    }
    window.addEventListener('keydown', handleKeydown)
  })
  
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
  
  // ============================================
  // 【API 接口1】获取餐厅详情
  // ============================================
  // 接口地址: GET /api/restaurants/{id}
  // 请求头: Authorization: Bearer {token}
  // 响应: { code: 200, data: RestaurantData }
  // ============================================
  const loadRestaurantDetail = async (id: string) => {
    isLoading.value = true
    try {
      // ========== 真实 API 调用（取消注释即可使用） ==========
      // const response = await fetch(`/api/restaurants/${id}`, {
      //   method: 'GET',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      //   }
      // })
      // if (!response.ok) throw new Error('获取餐厅详情失败')
      // const result = await response.json()
      // restaurantData.value = result.data
      // ======================================================
  
      // ========== 模拟数据（开发测试用，接入 API 后删除） ==========
      await new Promise(resolve => setTimeout(resolve, 500))
      restaurantData.value = {
        id: Number(id),
        name: '蜀九香火锅',
        image: 'https://picsum.photos/seed/restaurant1/800/400',
        images: [
          'https://picsum.photos/seed/restaurant1/800/400',
          'https://picsum.photos/seed/restaurant2/800/400',
          'https://picsum.photos/seed/restaurant3/800/400'
        ],
        rating: 4.8,
        reviewCount: 326,
        price: 120,
        address: '成都市锦江区春熙路88号',
        hours: '10:00 - 22:00',
        phone: '028-88888888',
        category: '火锅',
        isOpen: true,
        reason: '口碑极佳，环境舒适，性价比高，是成都必吃的火锅之一',
        summary: '"味道正宗，服务热情，排队也值得！"',
        tags: ['🫕 正宗川味', '👨‍👩‍👧‍👦 适合聚餐', '🏠 环境优雅', '📸 适合拍照'],
        lat: 30.6595,
        lng: 104.0786,
        reviews: [
          { id: 1, userName: '美食达人小王', rating: 5, content: '味道太棒了！强烈推荐！', time: '2026-07-15' },
          { id: 2, userName: '爱吃的小李', rating: 4, content: '环境很好，价格适中。', time: '2026-07-14' },
          { id: 3, userName: '探店达人张张', rating: 5, content: '强烈推荐！锅底香而不腻！', time: '2026-07-13' },
          { id: 4, userName: '火锅爱好者老李', rating: 5, content: '成都最好吃的火锅之一！', time: '2026-07-12' },
          { id: 5, userName: '美食探店小刘', rating: 4, content: '味道不错，价格合理。', time: '2026-07-11' },
          { id: 6, userName: '成都本地人老张', rating: 5, content: '从小吃到大的味道！', time: '2026-07-10' },
          { id: 7, userName: '旅游达人小美', rating: 5, content: '来成都必吃的火锅！', time: '2026-07-09' },
          { id: 8, userName: '美食博主阿杰', rating: 4, content: '整体不错，价格略贵。', time: '2026-07-08' },
          { id: 9, userName: '学生党小杨', rating: 4, content: '好吃，但有点贵。', time: '2026-07-07' },
          { id: 10, userName: '家庭聚餐代表', rating: 5, content: '很适合家庭聚餐！', time: '2026-07-06' },
          { id: 11, userName: '火锅控小刘', rating: 5, content: '成都火锅的天花板！', time: '2026-07-05' },
          { id: 12, userName: '美食评论家老王', rating: 4, content: '味道正宗，服务有待提升。', time: '2026-07-04' },
          { id: 13, userName: '情侣约会指南', rating: 5, content: '氛围很好，适合情侣约会！', time: '2026-07-03' },
          { id: 14, userName: '成都土著小赵', rating: 5, content: '吃了十年的老店！', time: '2026-07-02' },
          { id: 15, userName: '美食探店小分队', rating: 4, content: '整体不错，排队太久。', time: '2026-07-01' },
          { id: 16, userName: '吃货小胖', rating: 5, content: '好吃到哭！必点牛肉和毛肚！', time: '2026-06-30' },
          { id: 17, userName: '美食达人小陈', rating: 4, content: '味道不错，价格略高。', time: '2026-06-29' },
          { id: 18, userName: '旅游博主小刘', rating: 5, content: '来成都旅游必打卡！', time: '2026-06-28' },
          { id: 19, userName: '本地吃货老李', rating: 5, content: '成都最好吃的火锅！', time: '2026-06-27' },
          { id: 20, userName: '美食家小张', rating: 4, content: '味道正宗，价格偏贵。', time: '2026-06-26' }
        ]
      }
      // ======================================================
  
      reviewPage.value = 1
      checkFavorite()
    } catch (error) {
      console.error('加载餐厅详情失败:', error)
    } finally {
      isLoading.value = false
    }
  }
  
  // ============================================
  // 【API 接口2】收藏/取消收藏
  // ============================================
  // 添加收藏: POST /api/favorites
  // 请求体: { shopId: number }
  // 移除收藏: DELETE /api/favorites/{shopId}
  // 请求头: Authorization: Bearer {token}
  // ============================================
  const toggleFavorite = async () => {
    if (!restaurantData.value) return
    
    // ========== 真实 API 调用（取消注释即可使用） ==========
    // try {
    //   const url = isFavorited.value 
    //     ? `/api/favorites/${restaurantData.value.id}` 
    //     : '/api/favorites'
    //   const method = isFavorited.value ? 'DELETE' : 'POST'
    //   
    //   const response = await fetch(url, {
    //     method,
    //     headers: {
    //       'Content-Type': 'application/json',
    //       'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    //     },
    //     body: method === 'POST' ? JSON.stringify({ shopId: restaurantData.value.id }) : undefined
    //   })
    //   if (!response.ok) throw new Error('操作失败')
    //   isFavorited.value = !isFavorited.value
    // } catch (error) {
    //   console.error('收藏操作失败:', error)
    //   alert('操作失败，请稍后重试')
    // }
    // ======================================================
  
    // ========== 本地模拟（开发测试用，接入 API 后删除） ==========
    isFavorited.value = !isFavorited.value
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]')
    if (isFavorited.value) {
      if (!favorites.includes(restaurantData.value.id)) {
        favorites.push(restaurantData.value.id)
      }
    } else {
      const index = favorites.indexOf(restaurantData.value.id)
      if (index > -1) favorites.splice(index, 1)
    }
    localStorage.setItem('favorites', JSON.stringify(favorites))
    // ======================================================
  }
  
  // ============================================
  // 检查收藏状态
  // ============================================
  const checkFavorite = () => {
    if (!restaurantData.value) return
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]')
    isFavorited.value = favorites.includes(restaurantData.value.id)
  }
  
  // ============================================
  // 【API 接口3】加载更多评论
  // ============================================
  // 接口地址: GET /api/restaurants/{id}/reviews?page={page}&limit={limit}
  // 请求头: Authorization: Bearer {token}
  // 响应: { code: 200, data: { list: Review[], total: number, hasMore: boolean } }
  // ============================================
  const loadMoreReviews = async () => {
    if (isLoadingMore.value || !hasMoreReviews.value) return
    
    isLoadingMore.value = true
    
    // ========== 真实 API 调用（取消注释即可使用） ==========
    // try {
    //   const nextPage = reviewPage.value + 1
    //   const response = await fetch(
    //     `/api/restaurants/${restaurantData.value?.id}/reviews?page=${nextPage}&limit=${REVIEW_PAGE_SIZE}`,
    //     {
    //       headers: {
    //         'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    //       }
    //     }
    //   )
    //   if (!response.ok) throw new Error('加载评论失败')
    //   const result = await response.json()
    //   const newReviews = result.data.list
    //   restaurantData.value!.reviews = [...(restaurantData.value!.reviews || []), ...newReviews]
    //   reviewPage.value = nextPage
    // } catch (error) {
    //   console.error('加载评论失败:', error)
    //   alert('加载评论失败，请稍后重试')
    // } finally {
    //   isLoadingMore.value = false
    // }
    // ======================================================
  
    // ========== 本地模拟（开发测试用，接入 API 后删除） ==========
    await new Promise(resolve => setTimeout(resolve, 600))
    reviewPage.value++
    isLoadingMore.value = false
    // ======================================================
  
    await nextTick()
    const reviewItems = document.querySelectorAll('.review-item')
    if (reviewItems.length > 0) {
      const lastItem = reviewItems[reviewItems.length - 1]
      lastItem?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }
  
  // ============================================
  // 评论分页计算属性
  // ============================================
  const displayedReviews = computed(() => {
    if (!restaurantData.value?.reviews) return []
    const reviews = restaurantData.value.reviews
    const end = reviewPage.value * REVIEW_PAGE_SIZE
    return reviews.slice(0, end)
  })
  
  const hasMoreReviews = computed(() => {
    if (!restaurantData.value?.reviews) return false
    return restaurantData.value.reviews.length > displayedReviews.value.length
  })
  
  const remainingReviewsCount = computed(() => {
    if (!restaurantData.value?.reviews) return 0
    return restaurantData.value.reviews.length - displayedReviews.value.length
  })
  
  // ============================================
  // 图片预览功能
  // ============================================
  const openGallery = (index: number = 0) => {
    if (!restaurantData.value?.images || restaurantData.value.images.length === 0) {
      alert('暂无图片')
      return
    }
    currentImageIndex.value = index
    showGalleryModal.value = true
    document.body.style.overflow = 'hidden'
  }
  
  const closeGallery = () => {
    showGalleryModal.value = false
    document.body.style.overflow = ''
  }
  
  const prevImage = () => {
    if (!restaurantData.value?.images) return
    if (currentImageIndex.value > 0) {
      currentImageIndex.value--
    }
  }
  
  const nextImage = () => {
    if (!restaurantData.value?.images) return
    if (currentImageIndex.value < restaurantData.value.images.length - 1) {
      currentImageIndex.value++
    }
  }
  
  const handleKeydown = (e: KeyboardEvent) => {
    if (!showGalleryModal.value) return
    if (e.key === 'Escape') {
      closeGallery()
    } else if (e.key === 'ArrowLeft') {
      prevImage()
    } else if (e.key === 'ArrowRight') {
      nextImage()
    }
  }
  
  // ============================================
  // 导航功能 - 高德地图导航
  // ============================================
  const navigateToRestaurant = () => {
    const data = restaurantData.value
    if (!data) {
      alert('暂无地址信息')
      return
    }
    
    const name = encodeURIComponent(data.name)
    const address = encodeURIComponent(data.address)
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
    
    try {
      if (isMobile) {
        let amapUri = ''
        if (data.lat && data.lng) {
          amapUri = `androidamap://navi?sourceApplication=${name}&poiname=${name}&lat=${data.lat}&lon=${data.lng}&dev=0&style=2`
        } else {
          amapUri = `androidamap://navi?sourceApplication=${name}&poiname=${name}&dev=0&style=2`
        }
        
        const iframe = document.createElement('iframe')
        iframe.style.display = 'none'
        iframe.src = amapUri
        document.body.appendChild(iframe)
        
        setTimeout(() => {
          document.body.removeChild(iframe)
          let webUrl = `https://ditu.amap.com/dir?type=car&to=${address}&src=${name}`
          if (data.lat && data.lng) {
            webUrl = `https://ditu.amap.com/dir?type=car&to=${data.lng},${data.lat}&src=${name}`
          }
          window.open(webUrl, '_blank')
        }, 2500)
      } else {
        let webUrl = `https://ditu.amap.com/dir?type=car&to=${address}&src=${name}`
        if (data.lat && data.lng) {
          webUrl = `https://ditu.amap.com/dir?type=car&to=${data.lng},${data.lat}&src=${name}`
        }
        window.open(webUrl, '_blank')
      }
    } catch (error) {
      console.error('导航失败:', error)
      window.open(
        `https://api.map.baidu.com/direction?destination=${address}&output=html&src=webapp`,
        '_blank'
      )
    }
  }
  
  // ============================================
  // 其他导航功能
  // ============================================
  const goBack = () => {
    router.back()
  }
  
  const callRestaurant = () => {
    if (restaurantData.value) {
      window.location.href = `tel:${restaurantData.value.phone}`
    }
  }
  
  const shareRestaurant = () => {
    if (restaurantData.value) {
      if (navigator.share) {
        navigator.share({
          title: restaurantData.value.name,
          text: `推荐一家好店：${restaurantData.value.name}`,
          url: window.location.href
        }).catch(() => {})
      } else {
        navigator.clipboard.writeText(window.location.href)
        alert('链接已复制，快去分享给朋友吧！')
      }
    }
  }
  
  const bookTable = () => {
    if (restaurantData.value) {
      window.location.href = `tel:${restaurantData.value.phone}`
    }
  }
  </script>
  
  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .restaurant-view {
    width: 100%;
    min-height: 100vh;
    min-height: 100dvh;
    background: #f8fafc;
    display: flex;
    flex-direction: column;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  /* ============================================
     顶部导航栏
     ============================================ */
  .restaurant-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.2rem;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(8px);
  }
  
  .back-btn {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    color: #475569;
    font-size: 0.9rem;
    cursor: pointer;
    padding: 0.4rem 0.6rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
  }
  
  .back-btn:hover {
    background: #f1f5f9;
    color: #1e293b;
  }
  
  .back-btn i {
    font-size: 1rem;
  }
  
  .header-center {
    flex: 1;
    text-align: center;
  }
  
  .header-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: 0.3rem;
  }
  
  .header-actions .action-btn {
    width: 2.4rem;
    height: 2.4rem;
    border: none;
    background: none;
    border-radius: 50%;
    color: #64748b;
    font-size: 1.1rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .header-actions .action-btn:hover {
    background: #f1f5f9;
  }
  
  .header-actions .action-btn.favorited {
    color: #ef4444;
  }
  
  /* ============================================
     主内容
     ============================================ */
  .restaurant-content {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 80px;
  }
  
  /* ============================================
     加载状态
     ============================================ */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    color: #94a3b8;
  }
  
  .loading-state i {
    font-size: 2.5rem;
    color: #3b82f6;
    margin-bottom: 1rem;
  }
  
  /* ============================================
     图片区域
     ============================================ */
  .restaurant-gallery {
    position: relative;
  }
  
  .gallery-main {
    position: relative;
    width: 100%;
    height: 280px;
    overflow: hidden;
    cursor: pointer;
  }
  
  .gallery-main img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .gallery-badge {
    position: absolute;
    bottom: 1rem;
    right: 1rem;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    backdrop-filter: blur(4px);
  }
  
  .gallery-thumbs {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2px;
    padding: 2px;
    background: #f1f5f9;
  }
  
  .thumb-item {
    height: 80px;
    overflow: hidden;
    cursor: pointer;
  }
  
  .thumb-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.2s;
  }
  
  .thumb-item img:hover {
    transform: scale(1.05);
  }
  
  .thumb-more {
    height: 80px;
    background: #1e293b;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 600;
    cursor: pointer;
  }
  
  /* ============================================
     餐厅信息
     ============================================ */
  .restaurant-info-section {
    padding: 1.2rem 1.2rem 1.5rem;
    background: white;
  }
  
  .info-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }
  
  .name-wrapper {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.3rem;
  }
  
  .restaurant-name {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }
  
  .rating-emoji {
    font-size: 1.6rem;
    line-height: 1;
    cursor: default;
    transition: transform 0.2s;
  }
  
  .rating-emoji:hover {
    transform: scale(1.15);
  }
  
  .restaurant-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.85rem;
    color: #64748b;
  }
  
  .restaurant-rating {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    color: #f59e0b;
    font-weight: 600;
  }
  
  .restaurant-rating .review-count {
    color: #94a3b8;
    font-weight: 400;
  }
  
  .restaurant-price {
    color: #3b82f6;
    font-weight: 600;
  }
  
  .restaurant-category {
    background: #f1f5f9;
    padding: 0.1rem 0.6rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    color: #475569;
  }
  
  .restaurant-status {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    font-weight: 500;
    padding: 0.2rem 0.8rem;
    border-radius: 1rem;
    background: #fef2f2;
    color: #dc2626;
  }
  
  .restaurant-status.open {
    background: #f0fdf4;
    color: #22c55e;
  }
  
  .restaurant-status .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #dc2626;
  }
  
  .restaurant-status.open .status-dot {
    background: #22c55e;
  }
  
  /* ============================================
     信息网格
     ============================================ */
  .restaurant-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.8rem;
    padding: 1rem 0;
    border-top: 1px solid #f1f5f9;
    border-bottom: 1px solid #f1f5f9;
    margin-bottom: 1rem;
  }
  
  .info-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
  }
  
  .info-item i {
    color: #94a3b8;
    font-size: 0.9rem;
    margin-top: 0.1rem;
    width: 1rem;
  }
  
  .info-item div {
    display: flex;
    flex-direction: column;
  }
  
  .info-label {
    font-size: 0.7rem;
    color: #94a3b8;
  }
  
  .info-value {
    font-size: 0.85rem;
    color: #334155;
    word-break: break-all;
  }
  
  /* ============================================
     操作按钮
     ============================================ */
  .action-buttons {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 1.2rem;
  }
  
  .action-btn-primary {
    flex: 1;
    padding: 0.6rem;
    border: none;
    border-radius: 0.7rem;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
  }
  
  .action-btn-primary.navigate {
    background: #3b82f6;
    color: white;
  }
  
  .action-btn-primary.navigate:hover {
    background: #2563eb;
    transform: translateY(-1px);
  }
  
  .action-btn-primary.call {
    background: #f1f5f9;
    color: #334155;
  }
  
  .action-btn-primary.call:hover {
    background: #e2e8f0;
  }
  
  .action-btn-primary.share {
    background: #f1f5f9;
    color: #334155;
  }
  
  .action-btn-primary.share:hover {
    background: #e2e8f0;
  }
  
  /* ============================================
     内容区块
     ============================================ */
  .section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0 0 0.6rem 0;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  
  .section-title i {
    color: #3b82f6;
  }
  
  .restaurant-tags-section {
    margin-bottom: 1.2rem;
  }
  
  .restaurant-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
  
  .restaurant-tags .tag {
    background: #f1f5f9;
    padding: 0.3rem 0.8rem;
    border-radius: 1rem;
    font-size: 0.8rem;
    color: #475569;
  }
  
  .restaurant-reason {
    margin-bottom: 1.2rem;
  }
  
  .reason-content {
    display: flex;
    gap: 0.6rem;
    padding: 0.8rem 1rem;
    border-radius: 0.8rem;
    border-left: 3px solid;
    transition: all 0.3s ease;
  }
  
  .reason-content i {
    font-size: 0.8rem;
    margin-top: 0.1rem;
    flex-shrink: 0;
    transition: color 0.3s ease;
  }
  
  .reason-content p {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.6;
    transition: color 0.3s ease;
  }
  
  .restaurant-summary-section {
    margin-bottom: 1.2rem;
  }
  
  .summary-content {
    display: flex;
    gap: 0.6rem;
    background: #f8fafc;
    padding: 0.8rem 1rem;
    border-radius: 0.8rem;
    border-left: 3px solid #3b82f6;
  }
  
  .summary-content i {
    color: #3b82f6;
    font-size: 0.8rem;
    margin-top: 0.1rem;
  }
  
  .summary-content p {
    margin: 0;
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.6;
    font-style: italic;
  }
  
  /* ============================================
     评价列表
     ============================================ */
  .reviews-section {
    margin-bottom: 1.2rem;
  }
  
  .reviews-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8rem;
  }
  
  .review-total {
    font-size: 0.8rem;
    color: #94a3b8;
  }
  
  .reviews-list {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
  }
  
  .review-item {
    background: #f8fafc;
    padding: 0.8rem 1rem;
    border-radius: 0.8rem;
  }
  
  .review-user {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.4rem;
  }
  
  .review-user img {
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .review-user div {
    display: flex;
    flex-direction: column;
  }
  
  .review-name {
    font-size: 0.85rem;
    font-weight: 500;
    color: #334155;
  }
  
  .review-time {
    font-size: 0.7rem;
    color: #94a3b8;
  }
  
  .review-rating {
    display: flex;
    gap: 0.1rem;
    margin-bottom: 0.3rem;
  }
  
  .review-rating .fa-star {
    color: #e2e8f0;
    font-size: 0.7rem;
  }
  
  .review-rating .fa-star.active {
    color: #f59e0b;
  }
  
  .review-content {
    font-size: 0.85rem;
    color: #475569;
    line-height: 1.6;
    margin: 0;
  }
  
  .load-more-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
    padding-top: 0.8rem;
    border-top: 1px solid #f1f5f9;
  }
  
  .load-more-btn {
    padding: 0.5rem 1.5rem;
    background: #f1f5f9;
    border: none;
    border-radius: 0.7rem;
    font-size: 0.85rem;
    color: #475569;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .load-more-btn:hover:not(:disabled) {
    background: #e2e8f0;
    color: #1e293b;
  }
  
  .load-more-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .load-more-btn i {
    margin-right: 0.3rem;
  }
  
  /* ============================================
     图片预览弹窗
     ============================================ */
  .gallery-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.92);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: galleryFadeIn 0.3s ease;
  }
  
  @keyframes galleryFadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  
  .gallery-modal-content {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .gallery-image-wrapper {
    width: 90%;
    height: 85%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .gallery-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    animation: galleryZoomIn 0.3s ease;
  }
  
  @keyframes galleryZoomIn {
    from {
      transform: scale(0.95);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }
  
  .gallery-close {
    position: absolute;
    top: 1.5rem;
    right: 2rem;
    background: rgba(255, 255, 255, 0.15);
    border: none;
    color: white;
    font-size: 1.8rem;
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }
  
  .gallery-close:hover {
    background: rgba(255, 255, 255, 0.25);
    transform: rotate(90deg);
  }
  
  .gallery-counter {
    position: absolute;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
    background: rgba(0, 0, 0, 0.5);
    padding: 0.4rem 1rem;
    border-radius: 1.5rem;
    backdrop-filter: blur(4px);
  }
  
  .gallery-nav {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.12);
    border: none;
    color: white;
    font-size: 2rem;
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }
  
  .gallery-nav:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.25);
  }
  
  .gallery-nav:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
  
  .gallery-prev {
    left: 1.5rem;
  }
  
  .gallery-next {
    right: 1.5rem;
  }
  
  /* ============================================
     空状态
     ============================================ */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    color: #94a3b8;
  }
  
  .empty-state i {
    font-size: 4rem;
    color: #cbd5e1;
    margin-bottom: 1rem;
  }
  
  .empty-btn {
    margin-top: 1rem;
    padding: 0.6rem 2rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.7rem;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .empty-btn:hover {
    background: #2563eb;
  }
  
  /* ============================================
     底部导航
     ============================================ */
  .bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-top: 1px solid #e2e8f0;
    padding: 0.6rem 1.2rem;
    padding-bottom: calc(0.6rem + env(safe-area-inset-bottom, 0px));
    z-index: 100;
  }
  
  .bottom-nav-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1100px;
    margin: 0 auto;
  }
  
  .nav-info {
    display: flex;
    align-items: center;
    gap: 0.8rem;
  }
  
  .nav-price {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
  }
  
  .nav-rating {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    font-size: 0.9rem;
    color: #f59e0b;
    font-weight: 600;
  }
  
  .nav-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .nav-btn {
    padding: 0.4rem 1rem;
    border: none;
    border-radius: 0.7rem;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    transition: all 0.2s;
  }
  
  .nav-btn.favorite {
    background: #f1f5f9;
    color: #475569;
  }
  
  .nav-btn.favorite:hover {
    background: #e2e8f0;
  }
  
  .nav-btn.favorite.active {
    background: #fef2f2;
    color: #ef4444;
  }
  
  .nav-btn.favorite.active:hover {
    background: #fee2e2;
  }
  
  .nav-btn.book {
    background: #3b82f6;
    color: white;
  }
  
  .nav-btn.book:hover {
    background: #2563eb;
  }
  
  .nav-btn.navigate {
    background: #22c55e;
    color: white;
  }
  
  .nav-btn.navigate:hover {
    background: #16a34a;
  }
  
  /* ============================================
     滚动条
     ============================================ */
  .restaurant-content::-webkit-scrollbar {
    width: 4px;
  }
  
  .restaurant-content::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .restaurant-content::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
  }
  
  /* ============================================
     响应式
     ============================================ */
  @media (max-width: 768px) {
    .restaurant-header {
      padding: 0.6rem 0.8rem;
    }
  
    .back-btn span {
      display: none;
    }
  
    .gallery-main {
      height: 200px;
    }
  
    .thumb-item,
    .thumb-more {
      height: 60px;
    }
  
    .restaurant-info-section {
      padding: 1rem;
    }
  
    .restaurant-name {
      font-size: 1.3rem;
    }
  
    .rating-emoji {
      font-size: 1.3rem;
    }
  
    .restaurant-info-grid {
      grid-template-columns: 1fr 1fr;
      gap: 0.6rem;
    }
  
    .action-buttons {
      flex-wrap: wrap;
    }
  
    .action-btn-primary {
      flex: 1;
      min-width: calc(33.33% - 0.4rem);
    }
  
    .bottom-nav {
      padding: 0.4rem 0.8rem;
    }
  
    .nav-info {
      display: none;
    }
  
    .nav-actions {
      width: 100%;
      justify-content: space-around;
    }
  
    .nav-btn {
      flex: 1;
      justify-content: center;
      padding: 0.5rem;
    }
  
    .load-more-btn {
      width: 100%;
      padding: 0.6rem;
      font-size: 0.8rem;
    }
  
    .gallery-image-wrapper {
      width: 95%;
      height: 75%;
    }
    
    .gallery-close {
      top: 1rem;
      right: 1rem;
      font-size: 1.3rem;
      width: 2.8rem;
      height: 2.8rem;
    }
    
    .gallery-nav {
      width: 2.5rem;
      height: 2.5rem;
      font-size: 1.2rem;
    }
    
    .gallery-prev {
      left: 0.5rem;
    }
    
    .gallery-next {
      right: 0.5rem;
    }
    
    .gallery-counter {
      bottom: 1.2rem;
      font-size: 0.8rem;
      padding: 0.3rem 0.8rem;
    }
  }
  
  @media (max-width: 480px) {
    .gallery-main {
      height: 180px;
    }
  
    .thumb-item,
    .thumb-more {
      height: 50px;
    }
  
    .restaurant-meta {
      font-size: 0.75rem;
      gap: 0.4rem;
    }
  
    .restaurant-info-grid {
      grid-template-columns: 1fr;
      gap: 0.4rem;
    }
  
    .nav-btn {
      font-size: 0.75rem;
    }
  
    .nav-btn span {
      display: none;
    }
  
    .rating-emoji {
      font-size: 1.1rem;
    }
  }
  
  @media (max-width: 400px) {
    .header-title {
      font-size: 0.9rem;
    }
  
    .restaurant-name {
      font-size: 1.1rem;
    }
  
    .action-btn-primary {
      font-size: 0.75rem;
      padding: 0.4rem;
    }
  }
  </style>