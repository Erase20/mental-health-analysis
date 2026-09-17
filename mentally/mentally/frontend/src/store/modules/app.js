import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const sidebarCollapsed = ref(false)
  const device = ref('desktop')
  const theme = ref('light')

  // Actions
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setSidebarCollapsed = (collapsed) => {
    sidebarCollapsed.value = collapsed
  }

  const setDevice = (deviceType) => {
    device.value = deviceType
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return {
    sidebarCollapsed,
    device,
    theme,
    toggleSidebar,
    setSidebarCollapsed,
    setDevice,
    toggleTheme
  }
})
