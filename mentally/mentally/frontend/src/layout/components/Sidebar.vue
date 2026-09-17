<template>
  <div class="sidebar-container">
    <!-- Logo -->
    <div class="logo-container">
      <el-icon :size="32" color="#409eff" v-if="!isCollapse"><FirstAidKit /></el-icon>
      <span class="title" v-if="!isCollapse">心理健康分析</span>
      <el-icon :size="24" color="#fff" v-else><FirstAidKit /></el-icon>
    </div>
    
    <!-- 菜单 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      router
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
    >
      <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <template #title>{{ item.title }}</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

const isCollapse = computed(() => appStore.sidebarCollapsed)

const activeMenu = computed(() => {
  return route.path
})

// 管理员菜单
const adminMenuItems = [
  { path: '/dashboard', title: '数据概览', icon: 'DataLine' },
  { path: '/analysis', title: '特征分析', icon: 'TrendCharts' },
  { path: '/clustering', title: '聚类分析', icon: 'Share' },
  { path: '/classification', title: '分类预测', icon: 'CircleCheck' },
  { path: '/profiles', title: '用户画像', icon: 'UserFilled' },
  { path: '/self-assessment', title: '心理自评', icon: 'FirstAidKit' },
  { path: '/assessment-records', title: '自评记录', icon: 'List' },
  { path: '/user-management', title: '用户管理', icon: 'User' },
  { path: '/data', title: '数据管理', icon: 'Document' },
  { path: '/report', title: '报告管理', icon: 'DocumentChecked' },
  { path: '/settings', title: '系统设置', icon: 'Setting' }
]

// 普通用户菜单
const userMenuItems = [
  { path: '/self-assessment', title: '心理自评', icon: 'FirstAidKit' },
  { path: '/my-report', title: '我的报告', icon: 'DocumentChecked' },
  { path: '/my-analysis', title: '我的分析', icon: 'TrendCharts' },
  { path: '/settings', title: '个人设置', icon: 'Setting' }
]

// 根据角色动态显示菜单
const menuItems = computed(() => {
  const role = userStore.userRole
  if (role === 'admin' || role === 'analyst') {
    return adminMenuItems
  }
  return userMenuItems
})
</script>

<style lang="scss" scoped>
.sidebar-container {
  height: 100%;
  
  .logo-container {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #2b3649;
    
    .logo {
      width: 32px;
      height: 32px;
      margin-right: 10px;
    }
    
    .title {
      color: #fff;
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .el-menu {
    border-right: none;
    
    .el-menu-item {
      &:hover {
        background-color: #263445 !important;
      }
      
      &.is-active {
        background-color: #263445 !important;
      }
    }
  }
}
</style>
