import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import '@fortawesome/fontawesome-free/css/all.min.css'
import ToastNotification from './components/ToastNotification.vue'

const app = createApp(App)

// 注册组件
app.component('ToastNotification', ToastNotification)

// 创建 Toast 容器
const toastContainer = document.createElement('div')
document.body.appendChild(toastContainer)

// 使用 createApp 挂载 Toast（修复类型错误）
import { createApp as createToastApp } from 'vue'
const toastVM = createToastApp(ToastNotification)
const toast = toastVM.mount(toastContainer)

// 提供全局 Toast
app.config.globalProperties.$toast = toast
app.provide('toast', toast)

app.use(router)

app.mount('#app')
