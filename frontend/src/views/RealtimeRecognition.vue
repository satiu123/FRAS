<template>
  <div class="realtime-recognition">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><VideoCamera /></el-icon>
            实时摄像头识别
          </span>
          <div class="header-actions">
            <el-tag v-if="isRunning" type="success" effect="dark">
              <el-icon><CircleCheck /></el-icon>
              运行中
            </el-tag>
            <el-tag v-else type="info">
              <el-icon><VideoPause /></el-icon>
              已停止
            </el-tag>
          </div>
        </div>
      </template>

      <div class="camera-container">
        <!-- 摄像头画面 -->
        <div class="video-wrapper">
          <!-- 原始视频流（30fps流畅显示） -->
          <video
            v-show="isRunning"
            ref="videoElement"
            autoplay
            playsinline
            class="video-display"
          ></video>
          
          <!-- Canvas叠加层（绘制识别框） -->
          <canvas
            v-show="isRunning"
            ref="canvasElement"
            class="canvas-overlay"
          ></canvas>
          
          <!-- 未启动提示 -->
          <div v-if="!isRunning" class="placeholder">
            <el-icon :size="80" color="#909399"><VideoCamera /></el-icon>
            <p>点击下方按钮启动实时识别</p>
          </div>
        </div>

        <!-- 控制面板 -->
        <div class="control-panel">
          <el-button
            v-if="!isRunning"
            type="primary"
            size="large"
            :loading="starting"
            @click="startRecognition"
          >
            <el-icon><VideoPlay /></el-icon>
            启动识别
          </el-button>
          
          <el-button
            v-else
            type="danger"
            size="large"
            :loading="stopping"
            @click="stopRecognition"
          >
            <el-icon><VideoPause /></el-icon>
            停止识别
          </el-button>

          <el-switch
            v-model="autoRecord"
            active-text="自动签到"
            inactive-text="仅识别"
            :disabled="!isRunning"
            style="margin-left: 20px;"
          />

          <el-button
            :disabled="!isRunning"
            :icon="Refresh"
            @click="reloadDatabase"
            style="margin-left: 20px;"
          >
            重载数据库
          </el-button>
        </div>

        <!-- 识别统计 -->
        <div v-if="isRunning" class="stats-panel">
          <div class="stat-item">
            <span class="label">已加载学生:</span>
            <span class="value">{{ studentsCount }}</span>
          </div>
          <div class="stat-item">
            <span class="label">检测到人脸:</span>
            <span class="value">{{ detectedFaces }}</span>
          </div>
          <div class="stat-item">
            <span class="label">已识别:</span>
            <span class="value success">{{ recognizedCount }}</span>
          </div>
          <div class="stat-item">
            <span class="label">未识别:</span>
            <span class="value warning">{{ unknownCount }}</span>
          </div>
          <div class="stat-item">
            <span class="label">帧率:</span>
            <span class="value">{{ fps }} FPS</span>
          </div>
        </div>

        <!-- 识别详情列表 -->
        <div v-if="recognitionResults.length > 0" class="results-panel">
          <h4>当前识别结果</h4>
          <div class="result-list">
            <div
              v-for="(result, index) in recognitionResults"
              :key="index"
              class="result-item"
              :class="{ recognized: result.recognized }"
            >
              <el-avatar :size="40">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="result-info">
                <div class="name">{{ result.name }}</div>
                <div class="confidence">
                  置信度: {{ (result.confidence * 100).toFixed(1) }}%
                </div>
              </div>
              <el-tag
                v-if="result.recorded"
                type="success"
                size="small"
                effect="dark"
              >
                已签到
              </el-tag>
              <el-tag v-else-if="!result.recognized" type="danger" size="small">
                未识别
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoCamera,
  VideoPlay,
  VideoPause,
  CircleCheck,
  Refresh,
  User,
  Loading
} from '@element-plus/icons-vue'
import { realtimeAPI } from '@/api'

const videoElement = ref(null)
const canvasElement = ref(null)
const isRunning = ref(false)
const starting = ref(false)
const stopping = ref(false)
const autoRecord = ref(true)
const studentsCount = ref(0)
const detectedFaces = ref(0)
const recognizedCount = ref(0)
const unknownCount = ref(0)
const fps = ref(0)
const recognitionResults = ref([])

let stream = null
let processingInterval = null
let animationFrameId = null
let fpsCounter = 0
let fpsInterval = null
let lastRecognitionResults = []

async function startRecognition() {
  starting.value = true
  try {
    // 获取摄像头权限
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 }
    })
    
    if (videoElement.value) {
      videoElement.value.srcObject = stream
    }

    // 通知后端启动
    const res = await realtimeAPI.startCamera(0)
    studentsCount.value = res.students_count
    
    isRunning.value = true
    ElMessage.success('实时识别已启动')
    
    // 开始处理帧
    startProcessing()
    
  } catch (error) {
    console.error('启动失败:', error)
    ElMessage.error('启动失败: ' + (error.message || '无法访问摄像头'))
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      stream = null
    }
  } finally {
    starting.value = false
  }
}

async function stopRecognition() {
  stopping.value = true
  try {
    // 停止处理
    if (processingInterval) {
      clearInterval(processingInterval)
      processingInterval = null
    }
    if (fpsInterval) {
      clearInterval(fpsInterval)
      fpsInterval = null
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    
    // 停止摄像头流
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      stream = null
    }
    
    // 通知后端停止
    try {
      await realtimeAPI.stopCamera()
    } catch (error) {
      console.log('后端停止摄像头失败:', error)
    }
    
    isRunning.value = false
    recognitionResults.value = []
    lastRecognitionResults = []
    ElMessage.info('实时识别已停止')
    
  } catch (error) {
    console.error('停止失败:', error)
  } finally {
    stopping.value = false
  }
}

function startProcessing() {
  // 等待video准备好后设置canvas尺寸
  const setupCanvas = () => {
    if (canvasElement.value && videoElement.value) {
      // 使canvas与video显示区域完全匹配
      const rect = videoElement.value.getBoundingClientRect()
      canvasElement.value.width = rect.width
      canvasElement.value.height = rect.height
    }
  }
  
  // 延迟设置以确保video已加载
  setTimeout(setupCanvas, 500)
  
  // 启动绘制循环（30fps）
  drawLoop()
  
  // 每隔一段时间发送一帧到后端识别（降低后端压力）
  processingInterval = setInterval(async () => {
    if (!videoElement.value || !isRunning.value) return
    
    try {
      // 从视频捕获一帧
      const canvas = document.createElement('canvas')
      canvas.width = videoElement.value.videoWidth
      canvas.height = videoElement.value.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(videoElement.value, 0, 0)
      
      // 转为base64
      const imageData = canvas.toDataURL('image/jpeg', 0.7)
      
      // 发送到后端处理
      const res = await realtimeAPI.processFrame(imageData, autoRecord.value)
      
      if (res.faces) {
        lastRecognitionResults = res.faces
        recognitionResults.value = res.faces
        detectedFaces.value = res.faces.length
        recognizedCount.value = res.faces.filter(f => f.recognized).length
        unknownCount.value = res.faces.filter(f => !f.recognized).length
      }
      
      fpsCounter++
      
    } catch (error) {
      console.error('处理帧失败:', error)
    }
  }, 100) // 每100ms处理一帧 (10 FPS识别率)
  
  // 计算实际FPS
  fpsInterval = setInterval(() => {
    fps.value = fpsCounter * 10  // 因为每100ms统计一次
    fpsCounter = 0
  }, 1000)
}

function drawLoop() {
  if (!isRunning.value || !canvasElement.value || !videoElement.value) return
  
  const canvas = canvasElement.value
  const video = videoElement.value
  const ctx = canvas.getContext('2d')
  
  // 清空canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 绘制识别框
  if (lastRecognitionResults.length > 0) {
    // 获取video实际内容尺寸
    const videoWidth = video.videoWidth
    const videoHeight = video.videoHeight
    
    // 获取video显示尺寸
    const displayWidth = video.offsetWidth
    const displayHeight = video.offsetHeight
    
    // 计算video内容在显示区域的实际位置和大小（object-fit: contain）
    const videoAspect = videoWidth / videoHeight
    const displayAspect = displayWidth / displayHeight
    
    let renderWidth, renderHeight, offsetX, offsetY
    
    if (videoAspect > displayAspect) {
      // 视频更宽，以宽度为准
      renderWidth = displayWidth
      renderHeight = displayWidth / videoAspect
      offsetX = 0
      offsetY = (displayHeight - renderHeight) / 2
    } else {
      // 视频更高，以高度为准
      renderHeight = displayHeight
      renderWidth = displayHeight * videoAspect
      offsetX = (displayWidth - renderWidth) / 2
      offsetY = 0
    }
    
    // 计算从原始坐标到显示坐标的缩放比例
    const scaleX = renderWidth / videoWidth
    const scaleY = renderHeight / videoHeight
    
    lastRecognitionResults.forEach(result => {
      const [x1, y1, x2, y2] = result.bbox
      
      // 转换坐标
      const sx1 = x1 * scaleX + offsetX
      const sy1 = y1 * scaleY + offsetY
      const sx2 = x2 * scaleX + offsetX
      const sy2 = y2 * scaleY + offsetY
      
      // 设置样式
      const color = result.recognized ? '#67c23a' : '#f56c6c'
      ctx.strokeStyle = color
      ctx.lineWidth = 3
      ctx.fillStyle = color
      ctx.font = '16px Arial'
      
      // 绘制矩形框
      ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1)
      
      // 绘制标签背景
      const label = `${result.name} (${(result.confidence * 100).toFixed(1)}%)`
      const textWidth = ctx.measureText(label).width
      ctx.fillRect(sx1, sy1 - 25, textWidth + 10, 25)
      
      // 绘制文字
      ctx.fillStyle = '#fff'
      ctx.fillText(label, sx1 + 5, sy1 - 7)
    })
  }
  
  // 继续下一帧
  animationFrameId = requestAnimationFrame(drawLoop)
}

async function reloadDatabase() {
  try {
    const res = await realtimeAPI.reloadDatabase()
    studentsCount.value = res.students_count
    ElMessage.success(`数据库已重载，共 ${res.students_count} 名学生`)
  } catch (error) {
    ElMessage.error('重载数据库失败')
  }
}

onMounted(async () => {
  // 检查后端摄像头状态
  try {
    const res = await realtimeAPI.getCameraStatus()
    if (res.active) {
      // 后端摄像头已在运行，先停止它
      await realtimeAPI.stopCamera()
      console.log('已停止后端残留的摄像头')
    }
  } catch (error) {
    console.error('检查摄像头状态失败:', error)
  }
})

onBeforeUnmount(() => {
  if (isRunning.value) {
    stopRecognition()
  }
})
</script>

<style lang="scss" scoped>
.realtime-recognition {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .camera-container {
    .video-wrapper {
      position: relative;
      width: 100%;
      height: 480px;
      background: #000;
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;

      .video-display {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: contain;
      }

      .canvas-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
      }

      .placeholder {
        text-align: center;
        color: #909399;

        p {
          margin-top: 20px;
          font-size: 16px;
        }
      }
    }

    .control-panel {
      margin-top: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }

    .stats-panel {
      margin-top: 20px;
      padding: 15px;
      background: #f5f7fa;
      border-radius: 8px;
      display: flex;
      justify-content: space-around;
      flex-wrap: wrap;
      gap: 15px;

      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;

        .label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 5px;
        }

        .value {
          font-size: 24px;
          font-weight: 600;
          color: #303133;

          &.success {
            color: #67c23a;
          }

          &.warning {
            color: #e6a23c;
          }
        }
      }
    }

    .results-panel {
      margin-top: 20px;

      h4 {
        margin-bottom: 15px;
        color: #303133;
      }

      .result-list {
        display: flex;
        flex-direction: column;
        gap: 10px;

        .result-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: #f5f7fa;
          border-radius: 8px;
          border: 2px solid transparent;
          transition: all 0.3s;

          &.recognized {
            border-color: #67c23a;
            background: #f0f9ff;
          }

          .result-info {
            flex: 1;

            .name {
              font-size: 14px;
              font-weight: 600;
              color: #303133;
              margin-bottom: 4px;
            }

            .confidence {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }
}
</style>
