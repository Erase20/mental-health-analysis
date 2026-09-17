import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/login/register.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    children: [
      // ===== 管理员/分析师路由 =====
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '数据概览', icon: 'DataLine', roles: ['admin', 'analyst'] }
      },
      {
        path: 'analysis',
        name: 'Analysis',
        component: () => import('@/views/analysis/index.vue'),
        meta: { title: '特征分析', icon: 'TrendCharts', roles: ['admin', 'analyst'] }
      },
      {
        path: 'clustering',
        name: 'Clustering',
        component: () => import('@/views/clustering/index.vue'),
        meta: { title: '聚类分析', icon: 'Share', roles: ['admin', 'analyst'] }
      },
      {
        path: 'classification',
        name: 'Classification',
        component: () => import('@/views/classification/index.vue'),
        meta: { title: '分类预测', icon: 'CircleCheck', roles: ['admin', 'analyst'] }
      },
      {
        path: 'profiles',
        name: 'Profiles',
        component: () => import('@/views/profiles/index.vue'),
        meta: { title: '用户画像', icon: 'UserFilled', roles: ['admin', 'analyst'] }
      },
      {
        path: 'profiles/:id',
        name: 'ProfileDetail',
        component: () => import('@/views/profiles/detail.vue'),
        meta: { title: '画像详情', hidden: true, roles: ['admin', 'analyst'] }
      },
      {
        path: 'data',
        name: 'Data',
        component: () => import('@/views/data/index.vue'),
        meta: { title: '数据管理', icon: 'Document', roles: ['admin', 'analyst'] }
      },
      {
        path: 'report',
        name: 'Report',
        component: () => import('@/views/report/index.vue'),
        meta: { title: '报告管理', icon: 'DocumentChecked', roles: ['admin', 'analyst'] }
      },
      {
        path: 'assessment-records',
        name: 'AssessmentRecords',
        component: () => import('@/views/assessment-records/index.vue'),
        meta: { title: '自评记录', icon: 'List', roles: ['admin', 'analyst'] }
      },
      {
        path: 'user-management',
        name: 'UserManagement',
        component: () => import('@/views/user-management/index.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin', 'analyst'] }
      },
      // ===== 普通用户路由 =====
      {
        path: 'self-assessment',
        name: 'SelfAssessment',
        component: () => import('@/views/self-assessment/index.vue'),
        meta: { title: '心理自评', icon: 'FirstAidKit', roles: ['user', 'admin', 'analyst'] }
      },
      {
        path: 'my-report',
        name: 'MyReport',
        component: () => import('@/views/user-report/index.vue'),
        meta: { title: '我的报告', icon: 'DocumentChecked', roles: ['user'] }
      },
      {
        path: 'my-analysis',
        name: 'MyAnalysis',
        component: () => import('@/views/user-analysis/index.vue'),
        meta: { title: '我的分析', icon: 'TrendCharts', roles: ['user'] }
      },
      // ===== 公共路由 =====
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = getToken()
  const userStore = useUserStore()

  if (token) {
    if (to.path === '/login') {
      // 已登录用户根据角色跳转到对应首页
      const role = userStore.userRole
      if (role === 'admin' || role === 'analyst') {
        next('/dashboard')
      } else {
        next('/self-assessment')
      }
    } else if (to.path === '/') {
      // 根路径根据角色重定向
      if (!userStore.userInfo) {
        try {
          await userStore.getUserInfoAction()
        } catch (error) {
          userStore.logoutAction()
          ElMessage.error('获取用户信息失败，请重新登录')
          next('/login')
          return
        }
      }
      const role = userStore.userRole
      if (role === 'admin' || role === 'analyst') {
        next('/dashboard')
      } else {
        next('/self-assessment')
      }
    } else {
      if (!userStore.userInfo) {
        try {
          await userStore.getUserInfoAction()
          // 获取用户信息后检查角色权限
          const role = userStore.userRole
          if (to.meta?.roles && !to.meta.roles.includes(role)) {
            // 没有权限，跳转到角色对应首页
            if (role === 'admin' || role === 'analyst') {
              next('/dashboard')
            } else {
              next('/self-assessment')
            }
          } else {
            next()
          }
        } catch (error) {
          userStore.logoutAction()
          ElMessage.error('获取用户信息失败，请重新登录')
          next('/login')
        }
      } else {
        // 已有用户信息，检查角色权限
        const role = userStore.userRole
        if (to.meta?.roles && !to.meta.roles.includes(role)) {
          if (role === 'admin' || role === 'analyst') {
            next('/dashboard')
          } else {
            next('/self-assessment')
          }
        } else {
          next()
        }
      }
    }
  } else {
    if (to.meta?.public) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router
