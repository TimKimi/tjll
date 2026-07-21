// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../view/HomeView.vue'
import ChatView from '../view/ChatView.vue'
import LoginView from '../view/LoginView.vue'
import RegisterView from '../view/RegisterView.vue'
import PersonalProfileView from '../view/PersonalProfileView.vue'
import RestaurantView from '../view/RestaurantView.vue'
import AdminView from '../view/AdminView.vue'
import RestaurantListView from '../view/RestaurantListView.vue'

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
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: {
        title: '探店助手 - 管理后台',
        // requiresAuth: true,
        // requiresAdmin: true,  // 新增：需要管理员权限
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

// //路由守卫
// router.beforeEach((to, from, next) => {
//   if (to.meta?.title) {
//     document.title = to.meta.title as string
//   }

//   const requiresAuth = to.meta?.requiresAuth as boolean
//   const requiresAdmin = to.meta?.requiresAdmin as boolean
//   const token = localStorage.getItem('token')
//   const role = localStorage.getItem('userRole')

//   if (requiresAuth && !token) {
//     next({
//       path: '/login',
//       query: { redirect: to.fullPath }
//     })
//     return
//   }

//   if (requiresAdmin && role !== 'admin') {
//     alert('您没有管理员权限')
//     next('/')
//     return
//   }

//   if ((to.path === '/login' || to.path === '/register') && token) {
//     next('/')
//     return
//   }

//   next()
// })

export default router
