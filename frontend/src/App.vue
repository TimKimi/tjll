<template>
  <div id="app">
    <!-- 路由视图 -->
    <router-view v-slot="{ Component }">
      <transition
        name="fade"
        mode="out-in"
      >
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup lang="ts">
// 全局样式已在 main.ts 中导入
</script>

<style>
/* ============================================
   全局重置样式
   ============================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f8fafc;
  color: #0f172a;
}

#app {
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
}

/* ============================================
   路由过渡动画
   ============================================ */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ============================================
   Font Awesome 备用方案（如果 CDN 未加载）
   ============================================ */
.fas,
.far,
.fab {
  display: inline-block;
  font-style: normal;
  font-weight: 400;
  line-height: 1;
}

/* ============================================
   滚动条全局样式
   ============================================ */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* ============================================
   选中文本样式
   ============================================ */
::selection {
  background: #2563eb;
  color: white;
}

::-moz-selection {
  background: #2563eb;
  color: white;
}

/* ============================================
   响应式字体基础
   ============================================ */
@media (max-width: 768px) {
  html {
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  html {
    font-size: 14px;
  }
}
</style>
