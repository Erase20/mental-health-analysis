<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { getToken } from '@/utils/auth'

const userStore = useUserStore()

onMounted(() => {
  // 如果有token，自动获取用户信息
  if (getToken()) {
    userStore.fetchUserInfo().catch(() => {
      // 获取失败则清除token
      userStore.logout()
    })
  }
})
</script>

<style>
#app {
  height: 100%;
}
</style>
