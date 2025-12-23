<template>
  <div class="students-page">
    <el-card shadow="hover">
      <!-- 搜索和操作栏 -->
      <div class="header-row">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索学生姓名或学号"
          style="width: 300px"
          clearable
          @change="loadStudents"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <div class="actions">
          <el-button type="primary" :icon="Plus" @click="showCreateDialog">
            添加学生
          </el-button>
        </div>
      </div>

      <!-- 学生列表 -->
      <el-table
        v-loading="loading"
        :data="students"
        border
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="student_id" label="学号" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.has_face ? 'success' : 'warning'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="face_count" label="人脸图片数" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="280">
          <template #default="{ row }">
            <el-button size="small" :icon="Picture" @click="manageFaces(row)">
              管理人脸
            </el-button>
            <el-button size="small" type="primary" :icon="Edit" @click="editStudent(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="deleteStudent(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadStudents"
        @current-change="loadStudents"
        class="pagination"
      />
    </el-card>

    <!-- 创建/编辑学生对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="form.student_id" placeholder="请输入学号" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 人脸管理对话框 -->
    <el-dialog
      v-model="faceDialogVisible"
      title="人脸图片管理"
      width="700px"
    >
      <div class="face-upload">
        <el-upload
          :action="`/api/students/${currentStudent?.id}/face`"
          :headers="{ 'Content-Type': 'multipart/form-data' }"
          :on-success="handleUploadSuccess"
          :before-upload="beforeUpload"
          accept="image/*"
          list-type="picture-card"
          :limit="10"
        >
          <el-icon><Plus /></el-icon>
          <template #tip>
            <div class="upload-tip">支持 jpg/png/bmp 格式，单个文件不超过 5MB</div>
          </template>
        </el-upload>
      </div>
      
      <div class="face-list">
        <div v-for="img in faceImages" :key="img.filename" class="face-item">
          <img :src="`/api/students/${currentStudent?.id}/face/${img.filename}`" />
          <div class="face-actions">
            <el-button size="small" type="danger" :icon="Delete" @click="deleteFaceImage(img.filename)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Picture, Edit, Delete } from '@element-plus/icons-vue'
import { studentsAPI } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const faceDialogVisible = ref(false)
const searchKeyword = ref('')
const dialogTitle = ref('添加学生')
const isEdit = ref(false)

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const students = ref([])
const currentStudent = ref(null)
const faceImages = ref([])

const form = reactive({
  id: null,
  name: '',
  student_id: ''
})

async function loadStudents() {
  loading.value = true
  try {
    const res = await studentsAPI.getList({
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchKeyword.value
    })
    students.value = res.data.students
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  dialogTitle.value = '添加学生'
  form.id = null
  form.name = ''
  form.student_id = ''
  dialogVisible.value = true
}

function editStudent(row) {
  isEdit.value = true
  dialogTitle.value = '编辑学生'
  form.id = row.id
  form.name = row.name
  form.student_id = row.student_id
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }
  
  submitting.value = true
  try {
    if (isEdit.value) {
      await studentsAPI.update(form.id, { name: form.name, student_id: form.student_id })
      ElMessage.success('更新成功')
    } else {
      await studentsAPI.create({ name: form.name, student_id: form.student_id })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadStudents()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

function deleteStudent(row) {
  ElMessageBox.confirm(
    `确定要删除学生 ${row.name} 吗？这将删除该学生的所有人脸数据！`,
    '删除确认',
    { type: 'warning' }
  ).then(async () => {
    try {
      await studentsAPI.delete(row.id)
      ElMessage.success('删除成功')
      loadStudents()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

async function manageFaces(row) {
  currentStudent.value = row
  try {
    const res = await studentsAPI.getDetail(row.id)
    faceImages.value = res.data.face_images || []
    faceDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载人脸数据失败')
  }
}

function beforeUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
  }
  return isImage && isLt5M
}

function handleUploadSuccess() {
  ElMessage.success('上传成功')
  manageFaces(currentStudent.value)
}

function deleteFaceImage(filename) {
  ElMessageBox.confirm('确定要删除这张人脸图片吗？', '删除确认', { type: 'warning' })
    .then(async () => {
      try {
        await studentsAPI.deleteFace(currentStudent.value.id, filename)
        ElMessage.success('删除成功')
        manageFaces(currentStudent.value)
      } catch (error) {
        ElMessage.error('删除失败')
      }
    })
}

onMounted(() => {
  loadStudents()
})
</script>

<style lang="scss" scoped>
.students-page {
  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
  
  .face-upload {
    margin-bottom: 20px;
    
    .upload-tip {
      font-size: 12px;
      color: #909399;
      margin-top: 8px;
    }
  }
  
  .face-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 16px;
    
    .face-item {
      position: relative;
      border-radius: 8px;
      overflow: hidden;
      
      img {
        width: 100%;
        height: 150px;
        object-fit: cover;
      }
      
      .face-actions {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, 0.6);
        padding: 8px;
        text-align: center;
        opacity: 0;
        transition: opacity 0.3s;
      }
      
      &:hover .face-actions {
        opacity: 1;
      }
    }
  }
}
</style>
