<template>
  <div class="photo-signin">
    <el-page-header @back="$router.back()" title="返回">
      <template #content>
        <span class="page-title">📷 拍照签到</span>
      </template>
    </el-page-header>

    <el-card class="main-card" shadow="hover">
      <!-- 选项卡 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 摄像头拍照 -->
        <el-tab-pane label="摄像头拍照" name="camera">
          <div class="camera-section">
            <!-- 摄像头预览 -->
            <div class="camera-preview">
              <video
                v-show="!capturedImage && cameraStarted"
                ref="videoElement"
                autoplay
                playsinline
              ></video>
              
              <img
                v-show="capturedImage"
                :src="capturedImage"
                alt="拍摄的照片"
              />
              
              <div v-show="!cameraStarted && !capturedImage" class="camera-placeholder">
                <el-icon :size="80"><Camera /></el-icon>
                <p>点击下方按钮开启摄像头</p>
              </div>
              
              <canvas ref="canvasElement" style="display: none;"></canvas>
            </div>

            <!-- 控制按钮 -->
            <div class="camera-controls">
              <el-button
                v-if="!cameraStarted"
                type="primary"
                size="large"
                :icon="VideoCamera"
                @click="startCamera"
                :loading="cameraLoading"
              >
                开启摄像头
              </el-button>

              <template v-else-if="!capturedImage">
                <el-button
                  type="success"
                  size="large"
                  :icon="Camera"
                  @click="capturePhoto"
                >
                  拍照
                </el-button>
                <el-button
                  size="large"
                  :icon="Close"
                  @click="stopCamera"
                >
                  关闭摄像头
                </el-button>
              </template>

              <template v-else>
                <el-button
                  type="primary"
                  size="large"
                  :icon="Check"
                  @click="recognizePhoto"
                  :loading="recognizing"
                >
                  确认识别签到
                </el-button>
                <el-button
                  size="large"
                  :icon="RefreshLeft"
                  @click="retakePhoto"
                >
                  重新拍照
                </el-button>
              </template>
            </div>
          </div>
        </el-tab-pane>

        <!-- 上传图片 -->
        <el-tab-pane label="上传图片" name="upload">
          <div class="upload-section">
            <el-upload
              ref="uploadRef"
              class="upload-demo"
              drag
              :auto-upload="false"
              :limit="1"
              accept="image/*"
              :on-change="handleFileChange"
              :on-exceed="handleExceed"
              :file-list="fileList"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                拖拽图片到此处 或 <em>点击选择</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 jpg/png/bmp 格式，文件大小不超过 10MB
                </div>
              </template>
            </el-upload>

            <!-- 预览图片 -->
            <div v-if="uploadedImage" class="upload-preview">
              <img :src="uploadedImage" alt="上传的图片" />
            </div>

            <!-- 上传按钮 -->
            <div v-if="uploadedImage" class="upload-controls">
              <el-button
                type="primary"
                size="large"
                :icon="Check"
                @click="recognizeUploadedImage"
                :loading="recognizing"
              >
                开始识别签到
              </el-button>
              <el-button
                size="large"
                :icon="Delete"
                @click="clearUpload"
              >
                清除
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 识别结果 -->
    <el-card v-if="recognitionResult" class="result-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">识别结果</span>
          <el-tag :type="recognitionResult.success ? 'success' : 'danger'">
            {{ recognitionResult.message }}
          </el-tag>
        </div>
      </template>

      <div v-if="recognitionResult.success && recognitionResult.data">
        <!-- 识别结果图片 -->
        <div v-if="recognitionResult.data.annotated_image" class="annotated-image">
          <h3>🎯 识别标注图</h3>
          <img :src="recognitionResult.data.annotated_image" alt="识别结果" />
        </div>

        <!-- 统计信息 -->
        <el-descriptions :column="3" border>
          <el-descriptions-item label="检测到人脸">
            {{ recognitionResult.data.detected_faces }}
          </el-descriptions-item>
          <el-descriptions-item label="识别成功">
            {{ recognitionResult.data.recognized.length }}
          </el-descriptions-item>
          <el-descriptions-item label="签到成功">
            {{ recognitionResult.data.signed_in.length }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 签到成功列表 -->
        <div v-if="recognitionResult.data.signed_in.length > 0" class="result-section">
          <h3>✅ 签到成功</h3>
          <el-table :data="recognitionResult.data.signed_in" style="width: 100%">
            <el-table-column prop="name" label="姓名" />
            <el-table-column label="置信度">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.round(row.confidence * 100)"
                  :color="getConfidenceColor(row.confidence)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="time" label="签到时间" />
          </el-table>
        </div>

        <!-- 识别成功但未签到列表 -->
        <div v-if="recognitionResult.data.recognized.length > recognitionResult.data.signed_in.length" class="result-section">
          <h3>⚠️ 识别成功（未签到）</h3>
          <el-table :data="getNotSignedInFaces()" style="width: 100%">
            <el-table-column prop="name" label="姓名" />
            <el-table-column label="置信度">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.round(row.confidence * 100)"
                  :color="getConfidenceColor(row.confidence)"
                />
              </template>
            </el-table-column>
            <el-table-column label="原因">
              <template #default="{ row }">
                <el-tag type="warning">
                  {{ row.already_signed ? '今日已签到' : '未知原因' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 未识别人脸 -->
        <div v-if="recognitionResult.data.unknown.length > 0" class="result-section">
          <h3>❌ 未识别</h3>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
          >
            检测到 {{ recognitionResult.data.unknown.length }} 个未识别的人脸，可能是未注册的学生或陌生人
          </el-alert>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Camera,
  VideoCamera,
  Close,
  Check,
  RefreshLeft,
  Delete,
  UploadFilled
} from '@element-plus/icons-vue'
import { recognitionAPI } from '@/api'

const activeTab = ref('camera')
const cameraStarted = ref(false)
const cameraLoading = ref(false)
const capturedImage = ref(null)
const uploadedImage = ref(null)
const recognizing = ref(false)
const recognitionResult = ref(null)
const fileList = ref([])

const videoElement = ref(null)
const canvasElement = ref(null)
const uploadRef = ref(null)
let mediaStream = null

// 开启摄像头
const startCamera = async () => {
  cameraLoading.value = true
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
      }
    })
    
    if (videoElement.value) {
      videoElement.value.srcObject = mediaStream
      cameraStarted.value = true
      ElMessage.success('摄像头已开启')
    }
  } catch (error) {
    console.error('摄像头开启失败:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  } finally {
    cameraLoading.value = false
  }
}

// 停止摄像头
const stopCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  cameraStarted.value = false
  capturedImage.value = null
}

// 拍照
const capturePhoto = () => {
  if (!videoElement.value || !canvasElement.value) return
  
  const video = videoElement.value
  const canvas = canvasElement.value
  
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  
  capturedImage.value = canvas.toDataURL('image/jpeg', 0.9)
  ElMessage.success('拍照成功')
}

// 重新拍照
const retakePhoto = () => {
  capturedImage.value = null
  recognitionResult.value = null
}

// 识别拍摄的照片
const recognizePhoto = async () => {
  if (!capturedImage.value) return
  
  recognizing.value = true
  recognitionResult.value = null
  
  try {
    const result = await recognitionAPI.uploadImage({ image: capturedImage.value })
    recognitionResult.value = result
    
    if (result.success) {
      ElMessage.success(result.message)
      // 如果有签到成功，停止摄像头
      if (result.data.signed_in.length > 0) {
        stopCamera()
      }
    } else {
      ElMessage.warning(result.message)
    }
  } catch (error) {
    ElMessage.error('识别失败: ' + error.message)
  } finally {
    recognizing.value = false
  }
}

// 处理文件选择
const handleFileChange = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

// 处理文件数量超限
const handleExceed = () => {
  ElMessage.warning('只能上传一张图片')
}

// 清除上传
const clearUpload = () => {
  uploadedImage.value = null
  fileList.value = []
  recognitionResult.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 识别上传的图片
const recognizeUploadedImage = async () => {
  if (!uploadedImage.value) return
  
  recognizing.value = true
  recognitionResult.value = null
  
  try {
    const result = await recognitionAPI.uploadImage({ image: uploadedImage.value })
    recognitionResult.value = result
    
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.warning(result.message)
    }
  } catch (error) {
    ElMessage.error('识别失败: ' + error.message)
  } finally {
    recognizing.value = false
  }
}

// 切换标签页
const handleTabChange = (tab) => {
  if (tab === 'upload') {
    stopCamera()
  }
  recognitionResult.value = null
}

// 获取未签到的识别成功人脸
const getNotSignedInFaces = () => {
  if (!recognitionResult.value?.data) return []
  
  const signedInNames = recognitionResult.value.data.signed_in.map(s => s.name)
  return recognitionResult.value.data.recognized.filter(
    f => !signedInNames.includes(f.name)
  )
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.7) return '#67c23a'
  if (confidence >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

// 组件卸载时清理
onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped lang="scss">
.photo-signin {
  .page-title {
    font-size: 20px;
    font-weight: 600;
  }

  .main-card {
    margin-top: 20px;
  }

  // 摄像头部分
  .camera-section {
    .camera-preview {
      width: 100%;
      max-width: 800px;
      height: 600px;
      margin: 0 auto 20px;
      background: #000;
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;

      video,
      img {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }

      .camera-placeholder {
        text-align: center;
        color: #fff;

        .el-icon {
          margin-bottom: 20px;
          opacity: 0.5;
        }

        p {
          font-size: 16px;
          opacity: 0.7;
        }
      }
    }

    .camera-controls {
      display: flex;
      justify-content: center;
      gap: 15px;
      flex-wrap: wrap;
    }
  }

  // 上传部分
  .upload-section {
    :deep(.upload-demo) {
      .el-upload {
        width: 100%;
      }

      .el-upload-dragger {
        width: 100%;
        height: 300px;
      }
    }

    .upload-preview {
      margin-top: 20px;
      text-align: center;

      img {
        max-width: 100%;
        max-height: 500px;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }
    }

    .upload-controls {
      margin-top: 20px;
      display: flex;
      justify-content: center;
      gap: 15px;
    }
  }

  // 结果卡片
  .result-card {
    margin-top: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .card-title {
        font-size: 16px;
        font-weight: 600;
      }
    }

    .annotated-image {
      margin-bottom: 20px;
      text-align: center;

      h3 {
        margin-bottom: 15px;
        font-size: 16px;
        font-weight: 600;
      }

      img {
        max-width: 100%;
        max-height: 600px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border: 2px solid #67c23a;
      }
    }

    .result-section {
      margin-top: 20px;

      h3 {
        margin-bottom: 15px;
        font-size: 16px;
        font-weight: 600;
      }

      .el-alert {
        margin-top: 10px;
      }
    }

    .el-descriptions {
      margin-bottom: 20px;
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .photo-signin {
    .camera-section .camera-preview {
      height: 400px;
    }
  }
}
</style>
