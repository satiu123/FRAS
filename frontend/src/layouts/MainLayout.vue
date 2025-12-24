<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <el-icon :size="32" color="#409eff">
          <Camera />
        </el-icon>
        <span class="logo-text">FRAS</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item
          v-for="route in menuRoutes"
          :key="route.path"
          :index="route.path"
        >
          <el-icon>
            <component :is="route.meta.icon" />
          </el-icon>
          <span>{{ route.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ currentRoute?.meta?.title || '人脸识别考勤系统' }}</span>
        </div>
        
        <div class="header-right">
          <!-- 连接状态 -->
          <el-tooltip :content="wsConnected ? 'WebSocket已连接' : 'WebSocket未连接'" placement="bottom">
            <el-badge :is-dot="wsConnected" :type="wsConnected ? 'success' : 'danger'">
              <el-icon :size="20">
                <Connection />
              </el-icon>
            </el-badge>
          </el-tooltip>
          
          <!-- 暗黑模式切换 -->
          <el-tooltip content="切换主题" placement="bottom">
            <el-switch
              v-model="systemStore.isDark"
              inline-prompt
              :active-icon="Moon"
              :inactive-icon="Sunny"
              @change="systemStore.toggleDark"
            />
          </el-tooltip>
          
          <!-- 系统状态 -->
          <el-tooltip :content="`系统状态: ${systemStore.healthy ? '正常' : '异常'}`" placement="bottom">
            <el-icon :size="20" :color="systemStore.healthy ? '#67c23a' : '#f56c6c'">
              <CircleCheck v-if="systemStore.healthy" />
              <CircleClose v-else />
            </el-icon>
          </el-tooltip>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSystemStore } from '@/stores/system'
import websocket from '@/utils/websocket'
import {
  Camera, Monitor, Document, User, DataAnalysis,
  Connection, Moon, Sunny, CircleCheck, CircleClose
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const systemStore = useSystemStore()

const wsConnected = ref(false)

const menuRoutes = computed(() => {
  return router.options.routes[0].children || []
})

const currentRoute = computed(() => {
  return menuRoutes.value.find(r => r.path === route.path.substring(1))
})

onMounted(() => {
  // 连接 WebSocket
  websocket.connect()
  
  websocket.on('connect', () => {
    wsConnected.value = true
  })
  
  websocket.on('disconnect', () => {
    wsConnected.value = false
  })
})

onUnmounted(() => {
  websocket.disconnect()
})
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background-color: #304156;
  overflow-x: hidden;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: white;
    border-bottom: 1px solid #26333f;
    
    .logo-text {
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 2px;
    }
  }
  
  .menu {
    border-right: none;
    
    :deep(.el-menu-item) {
      &:hover {
        background-color: #263445 !important;
      }
    }
  }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  
  .header-left {
    .page-title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
  }
}

.main-content {
  background: #f5f7fa;
  overflow-y: auto;
  padding: 20px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
