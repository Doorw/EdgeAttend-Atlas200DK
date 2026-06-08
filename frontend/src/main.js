import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import './assets/css/style.css' // 全局样式

const app = createApp(App)
app.use(router)
app.mount('#app')
