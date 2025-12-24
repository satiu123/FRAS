<template>
  <div class="dashboard">
    <!-- 状态卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card info">
          <div class="stat-icon">
            <el-icon :size="40"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ status.total_students }}</div>
            <div class="stat-label">应到人数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card success">
          <div class="stat-icon">
            <el-icon :size="40"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ status.signed_count }}</div>
            <div class="stat-label">实到人数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon :size="40"><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ status.absent_count }}</div>
            <div class="stat-label">缺勤人数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon :size="40"><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ status.sign_rate }}%</div>
            <div class="stat-label">签到率</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主要内容区 -->
    <el-row :gutter="20" class="content-row">
      <!-- 左侧：实时签到动态 -->
      <el-col :xs="24" :lg="12">
        <el-card class="realtime-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><Clock /></el-icon>
                实时签到动态
              </span>
              <el-tag :type="wsConnected ? 'success' : 'danger'" size="small">
                {{ wsConnected ? '实时更新' : '未连接' }}
              </el-tag>
            </div>
          </template>
          
          <div class="signin-list">
            <transition-group name="list">
              <div
                v-for="record in recentSignins"
                :key="record.time"
                class="signin-item"
              >
                <el-avatar :size="50" class="avatar">
                  <el-icon><UserFilled /></el-icon>
                </el-avatar>
                
                <div class="signin-info">
                  <div class="student-name">{{ record.name }}</div>
                  <div class="student-id">学号: {{ record.student_id || '未设置' }}</div>
                  <div class="signin-time">{{ formatTime(record.time) }}</div>
                </div>
                
                <div class="signin-meta">
                  <el-tag :type="getStatusType(record.status)" size="small">
                    {{ getStatusText(record.status) }}
                  </el-tag>
                  <div class="confidence">
                    <el-progress
                      :percentage="Math.round(record.confidence * 100)"
                      :color="getConfidenceColor(record.confidence)"
                      :show-text="false"
                      :stroke-width="6"
                    />
                    <span class="confidence-text">{{ (record.confidence * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
            </transition-group>
            
            <el-empty v-if="recentSignins.length === 0" description="暂无签到记录" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：今日签到进度 -->
      <el-col :xs="24" :lg="12">
        <el-card class="progress-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><DataAnalysis /></el-icon>
                今日签到进度
              </span>
              <el-button
                size="small"
                :icon="RefreshRight"
                circle
                @click="refreshData"
                :loading="loading"
              />
            </div>
          </template>
          
          <div class="progress-content">
            <!-- 圆环进度 -->
            <div class="circle-progress">
              <el-progress
                type="circle"
                :percentage="status.sign_rate"
                :width="180"
                :stroke-width="12"
                :color="progressColors"
              >
                <template #default="{ percentage }">
                  <span class="progress-value">{{ percentage }}%</span>
                  <span class="progress-label">签到率</span>
                </template>
              </el-progress>
            </div>
            
            <!-- 详细统计 -->
            <div class="detail-stats">
              <div class="stat-item">
                <div class="stat-bar">
                  <div class="bar-label">已签到</div>
                  <el-progress
                    :percentage="(status.signed_count / status.total_students * 100) || 0"
                    :format="() => status.signed_count"
                    color="#67c23a"
                  />
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-bar">
                  <div class="bar-label">未签到</div>
                  <el-progress
                    :percentage="(status.absent_count / status.total_students * 100) || 0"
                    :format="() => status.absent_count"
                    color="#f56c6c"
                  />
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-bar">
                  <div class="bar-label">平均置信度</div>
                  <el-progress
                    :percentage="status.avg_confidence * 100"
                    :format="() => (status.avg_confidence * 100).toFixed(1) + '%'"
                    color="#409eff"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 快捷操作 -->
        <el-card class="actions-card" shadow="hover" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><Operation /></el-icon>
                快捷操作
              </span>
            </div>
          </template>
          
          <div class="quick-actions">
            <el-button type="primary" :icon="DocumentAdd" @click="showManualSigninDialog">
              手动补签
            </el-button>
            <el-button type="success" :icon="Camera" @click="goToPhotoSignin">
              拍照签到
            </el-button>
            <el-button type="warning" :icon="VideoCamera" @click="goToRealtimeRecognition">
              实时识别
            </el-button>
            <el-button type="success" :icon="Download" @click="exportData">
              导出数据
            </el-button>
            <el-button :icon="View" @click="viewAbsentList">
              查看缺勤名单
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 手动补签对话框 -->
    <el-dialog
      v-model="manualSigninVisible"
      title="手动补签"
      width="500px"
    >
      <el-form :model="manualSigninForm" label-width="100px">
        <el-form-item label="学生姓名" required>
          <el-input v-model="manualSigninForm.student_name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="manualSigninForm.remark" placeholder="补签原因" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="manualSigninVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualSignin" :loading="submitting">
          确认补签
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  User, CircleCheck, CircleClose, TrendCharts, Clock, UserFilled,
  DataAnalysis, RefreshRight, Operation, DocumentAdd, Download, View, Camera, VideoCamera
} from '@element-plus/icons-vue'
import { realtimeAPI, attendanceAPI, exportAPI } from '@/api'
import websocket from '@/utils/websocket'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const wsConnected = ref(false)
const submitting = ref(false)
const manualSigninVisible = ref(false)

const status = reactive({
  total_students: 0,
  signed_count: 0,
  absent_count: 0,
  sign_rate: 0,
  avg_confidence: 0
})

const recentSignins = ref([])

const manualSigninForm = reactive({
  student_name: '',
  remark: '手动补签'
})

const progressColors = [
  { color: '#f56c6c', percentage: 60 },
  { color: '#e6a23c', percentage: 80 },
  { color: '#67c23a', percentage: 100 }
]

// 加载数据
async function loadData() {
  loading.value = true
  try {
    // 加载实时状态
    const statusRes = await realtimeAPI.getStatus()
    Object.assign(status, statusRes.data)
    
    // 加载最近签到
    const recentRes = await realtimeAPI.getRecent(15)
    recentSignins.value = recentRes.data.records
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function refreshData() {
  loadData()
}

// WebSocket 事件处理
function handleNewSignin(data) {
  console.log('新签到:', data)
  
  // 播放提示音（可选）
  playNotificationSound()
  
  // 更新签到列表
  recentSignins.value.unshift({
    name: data.student_name,
    student_id: '',
    status: data.status,
    confidence: data.confidence,
    time: data.timestamp,
    remark: ''
  })
  
  // 限制列表长度
  if (recentSignins.value.length > 15) {
    recentSignins.value.pop()
  }
  
  // 更新统计
  status.signed_count++
  status.absent_count = Math.max(0, status.absent_count - 1)
  status.sign_rate = ((status.signed_count / status.total_students) * 100).toFixed(2)
  
  // 显示通知
  ElMessage.success({
    message: `${data.student_name} 签到成功`,
    duration: 2000
  })
}

function playNotificationSound() {
  // 可以添加音效
  // const audio = new Audio('/sounds/success.mp3')
  // audio.play()
}

// 手动补签
function showManualSigninDialog() {
  manualSigninForm.student_name = ''
  manualSigninForm.remark = '手动补签'
  manualSigninVisible.value = true
}

async function handleManualSignin() {
  if (!manualSigninForm.student_name.trim()) {
    ElMessage.warning('请输入学生姓名')
    return
  }
  
  submitting.value = true
  try {
    await attendanceAPI.manualSignin(manualSigninForm)
    ElMessage.success('补签成功')
    manualSigninVisible.value = false
    refreshData()
  } catch (error) {
    console.error('补签失败:', error)
  } finally {
    submitting.value = false
  }
}

// 导出数据
async function exportData() {
  try {
    const res = await exportAPI.exportAttendance({
      date: dayjs().format('YYYY-MM-DD')
    })
    
    // 下载 CSV
    const blob = new Blob([res.data.csv_content], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = res.data.filename
    link.click()
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 查看缺勤名单
async function viewAbsentList() {
  try {
    const res = await attendanceAPI.getAbsentList()
    const list = res.data.absent_list
    
    if (list.length === 0) {
      ElMessage.success('今日全员已签到！')
      return
    }
    
    const content = list.map(s => `${s.name} (${s.student_id || '无学号'})`).join('<br>')
    ElMessageBox.alert(content, `缺勤名单 (共${list.length}人)`, {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '知道了'
    })
  } catch (error) {
    ElMessage.error('获取缺勤名单失败')
  }
}

// 跳转到拍照签到页面
function goToPhotoSignin() {
  router.push('/photo-signin')
}

// 跳转到实时识别页面
function goToRealtimeRecognition() {
  router.push('/realtime-recognition')
}

// 工具函数
function formatTime(time) {
  return dayjs(time).format('HH:mm:ss')
}

function getStatusType(status) {
  const types = {
    present: 'success',
    late: 'warning',
    absent: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    present: '已到',
    late: '迟到',
    absent: '缺勤'
  }
  return texts[status] || status
}

function getConfidenceColor(confidence) {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  loadData()
  
  // 连接 WebSocket
  if (!websocket.socket) {
    websocket.connect()
  }
  
  websocket.on('connect', () => {
    wsConnected.value = true
  })
  
  websocket.on('disconnect', () => {
    wsConnected.value = false
  })
  
  websocket.on('new_signin', handleNewSignin)
  
  // 定时刷新
  const timer = setInterval(refreshData, 60000) // 每分钟刷新
  
  onUnmounted(() => {
    clearInterval(timer)
    websocket.off('new_signin', handleNewSignin)
  })
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stats-row {
    margin-bottom: 20px;
  }
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 24px;
    border-radius: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: transform 0.3s ease;
    
    &:hover {
      transform: translateY(-4px);
    }
    
    &.success {
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    &.warning {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    &.info {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .stat-icon {
      flex-shrink: 0;
      opacity: 0.9;
    }
    
    .stat-content {
      flex: 1;
      
      .stat-value {
        font-size: 36px;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 8px;
      }
      
      .stat-label {
        font-size: 14px;
        opacity: 0.9;
      }
    }
  }
  
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .realtime-card {
    height: 580px;
    
    :deep(.el-card__body) {
      height: calc(100% - 60px);
      padding: 0;
    }
    
    .signin-list {
      height: 100%;
      overflow-y: auto;
      padding: 20px;
      
      .signin-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background: #f5f7fa;
        border-radius: 8px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        
        &:hover {
          background: #e6e9ed;
          transform: translateX(4px);
        }
        
        .avatar {
          flex-shrink: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .signin-info {
          flex: 1;
          min-width: 0;
          
          .student-name {
            font-size: 16px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .student-id {
            font-size: 13px;
            color: #909399;
            margin-bottom: 4px;
          }
          
          .signin-time {
            font-size: 12px;
            color: #a8abb2;
          }
        }
        
        .signin-meta {
          flex-shrink: 0;
          text-align: right;
          
          .confidence {
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            
            :deep(.el-progress) {
              width: 60px;
            }
            
            .confidence-text {
              font-size: 12px;
              color: #606266;
              min-width: 40px;
            }
          }
        }
      }
    }
  }
  
  .progress-card {
    :deep(.el-card__body) {
      padding: 30px;
    }
    
    .progress-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 30px;
      
      .circle-progress {
        :deep(.el-progress__text) {
          display: flex;
          flex-direction: column;
          align-items: center;
          
          .progress-value {
            font-size: 32px;
            font-weight: 700;
            color: #303133;
          }
          
          .progress-label {
            font-size: 14px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }
      
      .detail-stats {
        width: 100%;
        
        .stat-item {
          margin-bottom: 20px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .stat-bar {
            .bar-label {
              font-size: 14px;
              color: #606266;
              margin-bottom: 8px;
            }
          }
        }
      }
    }
  }
  
  .actions-card {
    .quick-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      
      .el-button {
        flex: 1;
        min-width: 120px;
      }
    }
  }
}

// 列表动画
.list-enter-active {
  animation: slideIn 0.5s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
