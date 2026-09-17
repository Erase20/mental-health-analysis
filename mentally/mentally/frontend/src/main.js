import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Vue ECharts
import VueECharts from 'vue-echarts'
import * as echarts from 'echarts'

// 全局样式
import '@/styles/index.scss'

// ECharts 已通过 import * as echarts 导入

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册 Vue ECharts 组件
app.component('v-chart', VueECharts)

// 将 echarts 挂载到全局
app.config.globalProperties.$echarts = echarts

app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')
