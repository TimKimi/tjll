<template>
    <div class="shop-list-view">
      <!-- 顶部导航栏 -->
      <header class="shop-header">
        <div class="header-left">
          <button class="back-btn" @click="goHome">
            <i class="fas fa-arrow-left"></i>
            <span>返回</span>
          </button>
          <span class="header-title">发现餐厅</span>
        </div>
        <div class="header-right">
          <button class="filter-toggle-btn" @click="showFilters = !showFilters">
            <i class="fas fa-sliders-h"></i>
          </button>
        </div>
      </header>
  
      <!-- 搜索与筛选栏 -->
      <div class="search-bar">
        <div class="search-input-wrapper">
          <i class="fas fa-search"></i>
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索餐厅、美食..."
            @input="onSearchInput"
            @keyup.enter="fetchShops(1)"
          />
          <button v-if="searchKeyword" class="clear-btn" @click="clearSearch">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
  
      <!-- 筛选面板 -->
      <transition name="slide-down">
        <div v-if="showFilters" class="filter-panel">
          <div class="filter-row">
            <div class="filter-group">
              <label>分类</label>
              <select v-model="filters.category" @change="applyFilters">
                <option value="">全部分类</option>
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>排序</label>
              <select v-model="filters.sort_by" @change="applyFilters">
                <option value="rating">评分最高</option>
                <option value="review_count">评价最多</option>
              </select>
            </div>
            <div class="filter-group">
              <label>价格</label>
              <select v-model="filters.price" @change="applyFilters">
                <option value="">全部</option>
                <option value="1">¥ 50 以下</option>
                <option value="2">¥ 50 - 100</option>
                <option value="3">¥ 100 - 200</option>
                <option value="4">¥ 200 以上</option>
              </select>
            </div>
          </div>
          <div class="filter-actions">
            <button class="filter-reset-btn" @click="resetFilters">重置</button>
          </div>
        </div>
      </transition>
  
      <!-- 结果统计 -->
      <div class="result-info" v-if="total > 0">
        <span>共 {{ total }} 家餐厅</span>
        <span class="result-source" v-if="source">数据来源：{{ source }}</span>
      </div>
  
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        <p>加载餐厅中...</p>
      </div>
  
      <!-- 空状态 -->
      <div v-else-if="shops.length === 0" class="empty-state">
        <i class="fas fa-utensils"></i>
        <p>没有找到符合条件的餐厅</p>
        <button class="empty-btn" @click="resetFilters">重新搜索</button>
      </div>
  
      <!-- 餐厅卡片网格 -->
      <div v-else class="shop-grid">
        <div
          v-for="shop in shops"
          :key="shop.id"
          class="shop-card"
          @click="goToShop(shop.id)"
        >
          <div class="shop-image">
            <img :src="shop.image || defaultImage" :alt="shop.name" loading="lazy" />
            <span v-if="shop.isOpen === false" class="closed-badge">已休息</span>
            <span v-else-if="shop.isOpen === true" class="open-badge">营业中</span>
          </div>
          <div class="shop-info">
            <h3 class="shop-name">{{ shop.name }}</h3>
            <div class="shop-meta">
              <span class="shop-rating">
                <i class="fas fa-star"></i>
                {{ shop.rating || '暂无' }}
              </span>
              <span class="shop-price">¥{{ shop.price }}/人</span>
              <span class="shop-category">{{ shop.category || '中餐' }}</span>
            </div>
            <div class="shop-address">
              <i class="fas fa-map-pin"></i>
              <span>{{ shop.address || '地址待完善' }}</span>
            </div>
            <div class="shop-tags" v-if="shop.tags && shop.tags.length">
              <span v-for="tag in shop.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
  
      <!-- 分页 -->
      <div class="pagination" v-if="total > pageSize">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          <i class="fas fa-chevron-left"></i>
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, computed, onMounted, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { useToast } from '@/composables/useToast'
  import { handleApiError } from '@/utils/errorHandler'
  
  const router = useRouter()
  const toast = useToast()
  
  // ============================================
  // 类型定义
  // ============================================
  interface Shop {
    id: number
    name: string
    image: string
    rating: number
    reviewCount: number
    price: number
    address: string
    category: string
    isOpen: boolean
    tags: string[]
    // 可能还有其他字段，但列表不需要全部
  }
  
  // ============================================
  // 状态
  // ============================================
  const loading = ref(false)
  const shops = ref<Shop[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const source = ref('db')
  const defaultImage = 'https://picsum.photos/seed/default/400/300'
  
  // 搜索与筛选
  const searchKeyword = ref('')
  const showFilters = ref(false)
  const filters = reactive({
    category: '',
    sort_by: 'rating',
    price: '',
    location: '',   // 可留空或使用浏览器定位
  })
  
  // 分类列表（从接口返回的数据中提取，或静态定义）
  const categories = ref<string[]>([])
  
  // ============================================
  // 方法
  // ============================================
  
  // 获取餐厅列表
  const fetchShops = async (page: number = 1) => {
    loading.value = true
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize.value),
        sort_by: filters.sort_by,
        source: 'db', // 固定
      })
  
      if (searchKeyword.value.trim()) {
        params.append('keyword', searchKeyword.value.trim())
      }
      if (filters.category) {
        params.append('category', filters.category)
      }
      if (filters.price) {
        params.append('price', filters.price)
      }
      if (filters.location) {
        params.append('location', filters.location)
      }
  
      // 如果有经纬度可以添加，这里暂时不处理
  
      const response = await fetch(`/api/business/list?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      })
  
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
  
      const result = await response.json()
      // 假设后端返回格式为 { code, data: { items, total, page, page_size } }
      const data = result.data || result
      shops.value = data.items || data.list || []
      total.value = data.total || 0
      currentPage.value = data.page || page
      source.value = data.source || 'db'
  
      // 提取分类用于筛选
      if (shops.value.length) {
        const cats = shops.value.map(s => s.category).filter(Boolean)
        const uniqueCats = [...new Set(cats)]
        // 合并已有的分类，保留用户已选
        categories.value = [...new Set([...categories.value, ...uniqueCats])]
      }
  
    } catch (error) {
      console.error('获取餐厅列表失败:', error)
      const opts = handleApiError(error, '加载餐厅列表失败')
      toast.showToast(opts)
    } finally {
      loading.value = false
    }
  }
  
  // 切换页码
  const changePage = (page: number) => {
    if (page < 1 || page > totalPages.value) return
    fetchShops(page)
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  
  // 搜索输入（防抖）
  let searchTimer: ReturnType<typeof setTimeout> | null = null
  const onSearchInput = () => {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      fetchShops(1)
    }, 500)
  }
  
  const clearSearch = () => {
    searchKeyword.value = ''
    fetchShops(1)
  }
  
  // 应用筛选
  const applyFilters = () => {
    fetchShops(1)
  }
  
  // 重置筛选
  const resetFilters = () => {
    searchKeyword.value = ''
    filters.category = ''
    filters.sort_by = 'rating'
    filters.price = ''
    filters.location = ''
    fetchShops(1)
  }
  
  // 跳转到餐厅详情
  const goToShop = (id: number) => {
    router.push(`/restaurant/${id}`)
  }
  
  // 返回首页
  const goHome = () => {
    router.push('/')
  }
  
  // ============================================
  // 生命周期
  // ============================================
  onMounted(() => {
    fetchShops(1)
  })
  </script>
  
  <style scoped>
  /* ============================================
     全局布局
     ============================================ */
  .shop-list-view {
    min-height: 100vh;
    background: #f8fafc;
    padding-bottom: 2rem;
  }
  
  /* ============================================
     顶部导航栏
     ============================================ */
  .shop-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.2rem;
    background: white;
    border-bottom: 1px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 0.8rem;
  }
  
  .back-btn {
    background: none;
    border: none;
    font-size: 1rem;
    color: #475569;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.5rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
  }
  
  .back-btn:hover {
    background: #f1f5f9;
  }
  
  .header-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0f172a;
  }
  
  .filter-toggle-btn {
    background: none;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    padding: 0.4rem 0.7rem;
    color: #475569;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .filter-toggle-btn:hover {
    background: #f1f5f9;
  }
  
  /* ============================================
     搜索栏
     ============================================ */
  .search-bar {
    padding: 0.8rem 1.2rem;
    background: white;
    border-bottom: 1px solid #f1f5f9;
  }
  
  .search-input-wrapper {
    display: flex;
    align-items: center;
    background: #f1f5f9;
    border-radius: 0.8rem;
    padding: 0 0.8rem;
    border: 1px solid transparent;
    transition: all 0.2s;
  }
  
  .search-input-wrapper:focus-within {
    border-color: #3b82f6;
    background: white;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
  }
  
  .search-input-wrapper i {
    color: #94a3b8;
    font-size: 0.9rem;
  }
  
  .search-input-wrapper input {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    padding: 0.6rem 0.5rem;
    font-size: 0.9rem;
    color: #1e293b;
  }
  
  .search-input-wrapper input::placeholder {
    color: #94a3b8;
  }
  
  .clear-btn {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0.2rem 0.3rem;
    font-size: 0.8rem;
  }
  
  .clear-btn:hover {
    color: #64748b;
  }
  
  /* ============================================
     筛选面板
     ============================================ */
  .filter-panel {
    background: white;
    padding: 0.8rem 1.2rem 1rem;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .filter-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    margin-bottom: 0.6rem;
  }
  
  .filter-group {
    display: flex;
    flex-direction: column;
    flex: 1 0 120px;
  }
  
  .filter-group label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-bottom: 0.2rem;
  }
  
  .filter-group select {
    padding: 0.3rem 0.5rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.4rem;
    background: white;
    font-size: 0.85rem;
    color: #1e293b;
    outline: none;
    transition: border-color 0.2s;
  }
  
  .filter-group select:focus {
    border-color: #3b82f6;
  }
  
  .filter-actions {
    display: flex;
    justify-content: flex-end;
  }
  
  .filter-reset-btn {
    background: none;
    border: none;
    color: #3b82f6;
    font-size: 0.85rem;
    cursor: pointer;
    padding: 0.2rem 0.5rem;
  }
  
  .filter-reset-btn:hover {
    color: #2563eb;
    text-decoration: underline;
  }
  
  .slide-down-enter-active,
  .slide-down-leave-active {
    transition: all 0.25s ease;
  }
  .slide-down-enter-from,
  .slide-down-leave-to {
    opacity: 0;
    transform: translateY(-10px);
  }
  
  /* ============================================
     结果统计
     ============================================ */
  .result-info {
    padding: 0.8rem 1.2rem 0.2rem;
    font-size: 0.85rem;
    color: #64748b;
    display: flex;
    justify-content: space-between;
  }
  
  .result-source {
    color: #94a3b8;
    font-size: 0.75rem;
  }
  
  /* ============================================
     加载 & 空状态
     ============================================ */
  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1.5rem;
    color: #94a3b8;
  }
  
  .loading-state i {
    font-size: 2.5rem;
    color: #3b82f6;
    margin-bottom: 0.5rem;
  }
  
  .empty-state i {
    font-size: 3rem;
    color: #cbd5e1;
    margin-bottom: 0.5rem;
  }
  
  .empty-btn {
    margin-top: 1rem;
    padding: 0.5rem 1.5rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .empty-btn:hover {
    background: #2563eb;
  }
  
  /* ============================================
     餐厅卡片网格
     ============================================ */
  .shop-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.2rem;
    padding: 1rem 1.2rem;
  }
  
  .shop-card {
    background: white;
    border-radius: 0.8rem;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .shop-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  }
  
  .shop-image {
    position: relative;
    height: 160px;
    overflow: hidden;
    background: #f1f5f9;
  }
  
  .shop-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }
  
  .shop-card:hover .shop-image img {
    transform: scale(1.03);
  }
  
  .open-badge,
  .closed-badge {
    position: absolute;
    top: 0.6rem;
    left: 0.6rem;
    padding: 0.15rem 0.6rem;
    border-radius: 1rem;
    font-size: 0.7rem;
    font-weight: 500;
    color: white;
  }
  
  .open-badge {
    background: #22c55e;
  }
  
  .closed-badge {
    background: #94a3b8;
  }
  
  .shop-info {
    padding: 0.8rem 1rem;
  }
  
  .shop-name {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0 0 0.3rem 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .shop-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 0.3rem;
  }
  
  .shop-rating {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    color: #f59e0b;
    font-weight: 600;
  }
  
  .shop-price {
    color: #3b82f6;
  }
  
  .shop-category {
    background: #f1f5f9;
    padding: 0.1rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.7rem;
    color: #475569;
  }
  
  .shop-address {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.75rem;
    color: #94a3b8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .shop-address i {
    font-size: 0.6rem;
  }
  
  .shop-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin-top: 0.4rem;
  }
  
  .shop-tags .tag {
    background: #f1f5f9;
    padding: 0.1rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.65rem;
    color: #475569;
  }
  
  /* ============================================
     分页
     ============================================ */
  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.6rem;
    padding: 1.5rem 0;
  }
  
  .page-btn {
    width: 2.2rem;
    height: 2.2rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.4rem;
    background: white;
    color: #475569;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  
  .page-btn:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
  
  .page-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  
  .page-info {
    font-size: 0.85rem;
    color: #334155;
  }
  
  /* ============================================
     响应式
     ============================================ */
  @media (max-width: 768px) {
    .shop-grid {
      grid-template-columns: 1fr 1fr;
      gap: 0.8rem;
      padding: 0.8rem;
    }
  
    .shop-image {
      height: 130px;
    }
  
    .shop-name {
      font-size: 0.9rem;
    }
  
    .shop-meta {
      font-size: 0.7rem;
      gap: 0.4rem;
    }
  
    .filter-row {
      flex-direction: column;
      gap: 0.5rem;
    }
  
    .filter-group {
      flex: 1;
    }
  
    .result-info {
      font-size: 0.75rem;
    }
  }
  
  @media (max-width: 480px) {
    .shop-grid {
      grid-template-columns: 1fr;
      gap: 0.8rem;
    }
  
    .shop-image {
      height: 180px;
    }
  
    .header-title {
      font-size: 1rem;
    }
  }
  </style>