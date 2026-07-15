<template>
    <div class="home-view">
      <div class="home-container">
        <!-- 顶部欢迎区域 -->
        <div class="hero-section">
          <div class="hero-content">
            <h1 class="hero-title">
              <i class="fas fa-map-pin"></i>
              探店助手
            </h1>
            <p class="hero-subtitle">
              基于真实评价 · 环境 · 菜单 · 营业状态
            </p>
            <p class="hero-subtitle-mobile">
              告诉你"推荐什么、为什么推荐"
            </p>
          </div>
        </div>

        <!-- 对话式交互入口卡片 -->
        <div class="chat-entry-card">
          <div class="card-header">
            <i class="fas fa-mug-hot"></i>
            <span>今天想探索什么？</span>
          </div>

          <!-- 输入框区域 -->
          <div class="input-wrapper">
            <div class="search-input">
              <i class="fas fa-search search-icon"></i>
              <span class="placeholder-text">
                例如："附近哪家咖啡馆适合写作业，比较安静？"
              </span>
            </div>
            <button class="send-btn" @click="goToChat">
              <i class="fas fa-arrow-right"></i>
            </button>
          </div>

          <!-- 示例问题标签 -->
          <div class="example-tags">
            <span class="tag">
              <i class="far fa-comment"></i>
              学校周边性价比高的聚餐点？
            </span>
            <span class="tag">
              <i class="fas fa-cloud-rain"></i>
              下雨天想吃点热乎的
            </span>
            <span class="tag">
              <i class="fas fa-wifi"></i>
              适合办公的安静茶馆
            </span>
          </div>
        </div>

        <!-- 推荐理由展示区域 -->
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-store-alt"></i>
            </div>
            <h3 class="feature-title">环境描述 · 评价提炼</h3>
            <div class="feature-placeholder">
              【空白】从周边商家环境描述、用户评价中检索的关键信息
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-utensils"></i>
            </div>
            <h3 class="feature-title">菜单 · 营业状态</h3>
            <div class="feature-placeholder">
              【空白】基于实时菜单与营业时间，匹配消费需求
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-star"></i>
            </div>
            <h3 class="feature-title">推荐理由生成</h3>
            <div class="feature-placeholder">
              【空白】检索增强生成建议，解释"为什么推荐"
            </div>
          </div>
        </div>

        <!-- 跳转按钮 -->
        <div class="navigate-section">
          <button class="navigate-btn" @click="goToChat">
            <i class="fas fa-comments"></i>
            进入完整对话
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>
  </template>

  <script setup>
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const goToChat = () => {
    router.push('/chat')
  }
  </script>

  <style scoped>
  /* ========== 重置与基础 ========== */
  .home-view {
    width: 100%;
    min-height: 100vh;
    min-height: 100dvh; /* 动态视口高度，适配移动端浏览器地址栏 */
    background: #f8fafc;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    overflow-x: hidden;
  }

  .home-container {
    width: 100%;
    max-width: 1100px;
    padding: 2rem 2.5rem;
    box-sizing: border-box;
  }

  /* ========== 顶部区域 ========== */
  .hero-section {
    text-align: center;
    margin-bottom: 2rem;
  }

  .hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
  }

  .hero-title i {
    color: #3b82f6;
  }

  .hero-subtitle {
    color: #64748b;
    font-size: 1rem;
    font-weight: 400;
  }

  .hero-subtitle-mobile {
    display: none;
    color: #64748b;
    font-size: 0.9rem;
    font-weight: 400;
  }

  /* ========== 对话入口卡片 ========== */
  .chat-entry-card {
    background: linear-gradient(135deg, #f8faff 0%, #f1f5fe 100%);
    border: 1px solid #e2e8f0;
    border-radius: 1.5rem;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.3rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1.2rem;
  }

  .card-header i {
    color: #f59e0b;
  }

  /* 输入框 */
  .input-wrapper {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 1rem;
    padding: 0.5rem 0.5rem 0.5rem 1.2rem;
    transition: box-shadow 0.2s, border-color 0.2s;
  }

  .input-wrapper:focus-within {
    border-color: #93c5fd;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .search-input {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 0;
    min-width: 0; /* 防止flex溢出 */
  }

  .search-icon {
    color: #94a3b8;
    font-size: 1rem;
    flex-shrink: 0;
  }

  .placeholder-text {
    color: #94a3b8;
    font-size: 0.95rem;
    user-select: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .send-btn {
    background: #2563eb;
    color: white;
    border: none;
    width: 2.8rem;
    height: 2.8rem;
    border-radius: 0.8rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.2s;
    font-size: 1rem;
    flex-shrink: 0;
  }

  .send-btn:hover {
    background: #1d4ed8;
  }

  .send-btn:active {
    transform: scale(0.95);
  }

  /* 示例标签 */
  .example-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
    margin-top: 1.2rem;
  }

  .tag {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    font-size: 0.85rem;
    color: #475569;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    cursor: default;
    transition: all 0.15s;
    white-space: nowrap;
  }

  .tag:hover {
    border-color: #3b82f6;
    background: #eff6ff;
  }

  .tag i {
    color: #94a3b8;
    font-size: 0.75rem;
  }

  /* ========== 功能卡片网格 ========== */
  .feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .feature-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 1.2rem;
    padding: 1.5rem;
    transition: box-shadow 0.2s, border-color 0.2s;
  }

  .feature-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
  }

  .feature-icon {
    font-size: 1.8rem;
    color: #2563eb;
    margin-bottom: 0.8rem;
  }

  .feature-title {
    font-size: 1rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.6rem;
  }

  .feature-placeholder {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 0.6rem;
    padding: 0.8rem;
    font-size: 0.8rem;
    color: #64748b;
    text-align: center;
    line-height: 1.5;
  }

  /* ========== 跳转按钮 ========== */
  .navigate-section {
    display: flex;
    justify-content: center;
  }

  .navigate-btn {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.9rem 2.2rem;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 0.8rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
  }

  .navigate-btn:hover {
    background: #1d4ed8;
    transform: translateY(-1px);
  }

  .navigate-btn:active {
    transform: translateY(0);
  }

  /* ========== 平板端 (768px - 1024px) ========== */
  @media (max-width: 1024px) {
    .home-container {
      padding: 1.5rem;
    }

    .feature-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }
  }

  /* ========== 手机端 (最大768px) ========== */
  @media (max-width: 768px) {
    .home-view {
      align-items: flex-start;
    }

    .home-container {
      padding: 1.2rem 1rem;
      max-width: 100%;
    }

    /* 顶部 */
    .hero-section {
      margin-bottom: 1.5rem;
    }

    .hero-title {
      font-size: 1.6rem;
      gap: 0.4rem;
    }

    .hero-subtitle {
      display: none;
    }

    .hero-subtitle-mobile {
      display: block;
    }

    /* 卡片 */
    .chat-entry-card {
      padding: 1.2rem;
      border-radius: 1rem;
      margin-bottom: 1.5rem;
    }

    .card-header {
      font-size: 1.1rem;
      margin-bottom: 1rem;
    }

    .input-wrapper {
      padding: 0.3rem 0.3rem 0.3rem 0.8rem;
      border-radius: 0.8rem;
    }

    .placeholder-text {
      font-size: 0.8rem;
    }

    .send-btn {
      width: 2.3rem;
      height: 2.3rem;
      border-radius: 0.6rem;
      font-size: 0.9rem;
    }

    .example-tags {
      gap: 0.5rem;
      margin-top: 0.8rem;
    }

    .tag {
      font-size: 0.75rem;
      padding: 0.4rem 0.8rem;
    }

    /* 功能卡片 - 单列 */
    .feature-grid {
      grid-template-columns: 1fr;
      gap: 0.8rem;
      margin-bottom: 1.5rem;
    }

    .feature-card {
      padding: 1.2rem;
      border-radius: 1rem;
    }

    .feature-icon {
      font-size: 1.5rem;
      margin-bottom: 0.5rem;
    }

    .feature-title {
      font-size: 0.95rem;
    }

    .feature-placeholder {
      font-size: 0.75rem;
      padding: 0.6rem;
    }

    /* 跳转按钮 */
    .navigate-btn {
      width: 100%;
      justify-content: center;
      padding: 0.8rem 1.5rem;
      font-size: 0.95rem;
      border-radius: 0.8rem;
    }
  }

  /* ========== 小屏手机 (最大480px) ========== */
  @media (max-width: 480px) {
    .home-container {
      padding: 1rem 0.8rem;
    }

    .hero-title {
      font-size: 1.4rem;
    }

    .chat-entry-card {
      padding: 1rem;
    }

    .placeholder-text {
      font-size: 0.75rem;
    }

    .tag {
      font-size: 0.7rem;
      padding: 0.3rem 0.6rem;
    }

    .example-tags {
      gap: 0.4rem;
    }
  }
  </style>
