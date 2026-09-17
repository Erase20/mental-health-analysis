import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, register, getUserInfo } from '@/api/auth'
import { setToken, removeToken } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref('')
  const userInfo = ref(null)
  
  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const userRole = computed(() => userInfo.value?.role || '')
  
  // Actions
  const setUserToken = (newToken) => {
    token.value = newToken
    setToken(newToken)
  }
  
  const setUserInfo = (info) => {
    userInfo.value = info
  }
  
  const loginAction = async (credentials) => {
    const res = await login(credentials)
    if (res.code === 200) {
      setUserToken(res.data.access_token)
      setUserInfo(res.data.user)
      return res
    }
    throw new Error(res.message || '登录失败')
  }
  
  const registerAction = async (data) => {
    const res = await register(data)
    if (res.code === 201) {
      return res
    }
    throw new Error(res.message || '注册失败')
  }
  
  const fetchUserInfo = async () => {
    const res = await getUserInfo()
    if (res.code === 200) {
      setUserInfo(res.data)
      return res.data
    }
    throw new Error(res.message || '获取用户信息失败')
  }
  
  const logout = () => {
    token.value = ''
    userInfo.value = null
    removeToken()
  }
  
  // 为了兼容路由守卫中的调用
  const getUserInfoAction = async () => {
    return await fetchUserInfo()
  }
  
  const logoutAction = () => {
    logout()
  }
  
  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    userRole,
    setUserToken,
    setUserInfo,
    loginAction,
    registerAction,
    fetchUserInfo,
    logout,
    getUserInfoAction,
    logoutAction
  }
})
