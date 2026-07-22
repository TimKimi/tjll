<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="not-found-icon">
        🔍
      </div>
      <h1 class="not-found-title">
        404
      </h1>
      <p class="not-found-text">
        哎呀！页面走丢了...
      </p>
      <p class="not-found-hint">
        您访问的页面不存在，请返回首页
      </p>
      <button
        class="not-found-btn"
        @click="goHome"
      >
        <i class="fas fa-home" />
        返回首页
      </button>
    </div>
  </div>
</template>

  <script setup lang="ts">
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const goHome = () => {
    router.push('/')
  }
  </script>

  <style scoped>
  .not-found {
    width: 100%;
    height: 100vh;
    height: 100dvh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  }

  .not-found-content {
    text-align: center;
    padding: 2rem;
  }

  .not-found-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .not-found-title {
    font-size: 4rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .not-found-text {
    font-size: 1.2rem;
    color: #475569;
    margin-bottom: 0.3rem;
  }

  .not-found-hint {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
  }

  .not-found-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.8rem 2rem;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 0.8rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .not-found-btn:hover {
    background: #1d4ed8;
    transform: translateY(-2px);
  }
  </style>
