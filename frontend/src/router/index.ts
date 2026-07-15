import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../view/HomeView.vue'
import ChatView from '../view/ChatView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: '探店助手 - 首页'
      }
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
      meta: {
        title: '探店助手 - 智能对话'
      }
    },
    // 404 重定向到首页
    {
      path: '/:pathMatch',
      name: 'not-found',
      component: () => import('../view/NotFoundView.vue'),
      meta: {
        title: '页面未找到'
      }
    }
  ]
})

// 路由守卫：设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }
  next()
})

export default router
