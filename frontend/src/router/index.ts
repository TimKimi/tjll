// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../view/HomeView.vue'
import ChatView from '../view/ChatView.vue'
import LoginView from '../view/LoginView.vue'
import RegisterView from '../view/RegisterView.vue'
import PersonalProfileView from '../view/PersonalProfileView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: '探店助手 - 首页',
        requiresAuth: false,
      }
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
      meta: {
        title: '探店助手 - 智能对话',
        requiresAuth: false,
      }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        title: '探店助手 - 登录',
        requiresAuth: false,
      }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: {
        title: '探店助手 - 注册',
        requiresAuth: false,
      }
    },
    {
      path: '/profile',
      name: 'profile',
      component: PersonalProfileView,
      meta: {
        title: '探店助手 - 个人中心',
        requiresAuth: true,  // 必须登录才能访问
      }
    },

    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../view/NotFoundView.vue'),
      meta: {
        title: '页面未找到',
        requiresAuth: false,
      }
    }
  ]
})

// 路由守卫：设置页面标题 + 登录验证
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }

  // 检查是否需要登录
  const requiresAuth = to.meta?.requiresAuth as boolean
  const token = localStorage.getItem('token')

  if (requiresAuth && !token) {
    // 需要登录但未登录，跳转到登录页，并保存原路径
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  } else {
    // 如果已登录且访问登录页或注册页，跳转到首页（可选）
    if ((to.path === '/login' || to.path === '/register') && token) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
