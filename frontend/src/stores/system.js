import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemAPI } from '@/api'

export const useSystemStore = defineStore('system', () => {
  const healthy = ref(true)
  const version = ref('')
  const isDark = ref(false)

  async function checkHealth() {
    try {
      const res = await systemAPI.checkHealth()
      healthy.value = res.data.status === 'healthy'
      version.value = res.data.version
    } catch (error) {
      healthy.value = false
      console.error('健康检查失败:', error)
    }
  }

  function toggleDark() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  return {
    healthy,
    version,
    isDark,
    checkHealth,
    toggleDark
  }
})
