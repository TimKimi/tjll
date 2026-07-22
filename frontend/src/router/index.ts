// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../view/HomeView.vue'
import ChatView from '../view/ChatView.vue'
import LoginView from '../view/LoginView.vue'
import RegisterView from '../view/RegisterView.vue'
import PersonalProfileView from '../view/PersonalProfileView.vue'
import RestaurantView from '../view/RestaurantView.vue'
import AdminLoginView from '../view/AdminLoginView.vue'
import AdminView from '../view/AdminView.vue'
import RestaurantListView from '../view/RestaurantListView.vue'
import ForgotPassword from '../view/ForgotPassword.vue'
import ResetPassword from '../view/ResetPassword.vue'
import { getGlobalToast } from '@/composables/useToast'

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
        requiresAuth: false,  // 必须登录才能访问(?)
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
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: ForgotPassword
    },
    {
      path: '/reset-password',
      name: 'ResetPassword',
      component: ResetPassword
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLoginView,
      meta: {
        title: '管理员登录',
        requiresAuth: false,
      }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: {
        title: '探店助手 - 管理后台',
        requiresAuth: true,
        requiresAdmin: true,  //需要管理员权限
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
      path: '/restaurant/:id',
      name: 'restaurant',
      component: RestaurantView,
      meta: {
        title: '探店助手 - 餐厅信息',
        requiresAuth: true,  // 必须登录才能访问
      }
    },
    {
      path: '/restaurants',
      name: 'reataurants',
      component: RestaurantListView,
      meta: {
        title: '发现餐厅',
        requiresAuth: false,
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

//路由守卫
router.beforeEach((to, from, next) => {
  // ====== 1. 放行登录页 ======
  if (to.path === '/login' || to.path === '/admin/login') {
    next()
    return
  }

  // ====== 2. 设置标题 ======
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }

  // ====== 3. 获取凭证 ======
  const requiresAuth = to.meta?.requiresAuth as boolean
  const requiresAdmin = to.meta?.requiresAdmin as boolean

  const token = localStorage.getItem('token')
  const role = localStorage.getItem('userRole')
  const adminToken = localStorage.getItem('admin_token')
  const adminRole = localStorage.getItem('admin_role')

  // ====== 4. 先处理管理员权限 ======
  if (requiresAdmin) {
    if (!adminToken || adminRole !== 'admin') {
      getGlobalToast()?.error('您没有管理员权限')
      next('/')
      return
    }
    // 管理员权限通过，直接放行（不再检查普通 token）
    next()
    return
  }

  // ====== 5. 再处理普通需要登录的页面 ======
  if (requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // ====== 6. 普通用户已登录，访问登录/注册页 → 跳转首页 ======
  if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
    return
  }

  // ====== 7. 管理员已登录，访问 /admin/login → 跳转 /admin ======
  if (to.path === '/admin/login' && adminToken && adminRole === 'admin') {
    next('/admin')
    return
  }

  // ====== 8. 普通用户（无管理员权限）访问 /admin/*（除 /admin/login 外）→ 跳转首页 ======
  // 此条其实已被第4条覆盖，但作为双重保险保留
  if (to.path.startsWith('/admin') && to.path !== '/admin/login' && token && role !== 'admin') {
    next('/')
    return
  }

  // ====== 9. 其他情况放行 ======
  next()
})
export default router
