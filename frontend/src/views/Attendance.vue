<template>
  <div class="attendance-page">
    <el-card shadow="hover">
      <!-- 筛选器 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
          />
        </el-form-item>
        
        <el-form-item label="学生姓名">
          <el-input
            v-model="filters.student_name"
            placeholder="输入姓名搜索"
            clearable
            @clear="loadRecords"
          />
        </el-form-item>
        
        <el-form-item label="签到状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="已到" value="present" />
            <el-option label="迟到" value="late" />
            <el-option label="缺勤" value="absent" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadRecords">
            查询
          </el-button>
          <el-button :icon="RefreshRight" @click="resetFilters">
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="showManualSigninDialog">
          手动补签
        </el-button>
        <el-button type="success" :icon="Download" @click="exportData">
          导出Excel
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="records"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="student_name" label="姓名" width="120" />
        <el-table-column prop="student_id" label="学号" width="140" />
        <el-table-column prop="course_date" label="日期" width="120" />
        <el-table-column prop="status_text" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round(row.confidence * 100)"
              :color="getConfidenceColor(row.confidence)"
              :show-text="false"
              :stroke-width="6"
            />
            <span style="font-size: 12px; color: #606266;">
              {{ (row.confidence * 100).toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="签到时间" width="180" />
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" :icon="Edit" @click="editRecord(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="deleteRecord(row)">
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
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadRecords"
        @current-change="loadRecords"
        class="pagination"
      />
    </el-card>

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
        <el-form-item label="签到日期">
          <el-date-picker
            v-model="manualSigninForm.course_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="manualSigninForm.remark"
            type="textarea"
            placeholder="补签原因"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="manualSigninVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualSignin" :loading="submitting">
          确认补签
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑记录对话框 -->
    <el-dialog
      v-model="editVisible"
      title="编辑签到记录"
      width="500px"
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="已到" value="present" />
            <el-option label="迟到" value="late" />
            <el-option label="缺勤" value="absent" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="editForm.remark"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, RefreshRight, Plus, Download, Edit, Delete
} from '@element-plus/icons-vue'
import { attendanceAPI, exportAPI } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const manualSigninVisible = ref(false)
const editVisible = ref(false)

const dateRange = ref([])
const filters = reactive({
  start_date: '',
  end_date: '',
  student_name: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const records = ref([])

const manualSigninForm = reactive({
  student_name: '',
  course_date: dayjs().format('YYYY-MM-DD'),
  remark: '手动补签'
})

const editForm = reactive({
  id: null,
  status: '',
  remark: ''
})

// 加载记录
async function loadRecords() {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    const res = await attendanceAPI.getRecords(params)
    records.value = res.data.records
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleDateChange(dates) {
  if (dates && dates.length === 2) {
    filters.start_date = dates[0]
    filters.end_date = dates[1]
  } else {
    filters.start_date = ''
    filters.end_date = ''
  }
  loadRecords()
}

function resetFilters() {
  dateRange.value = []
  filters.start_date = ''
  filters.end_date = ''
  filters.student_name = ''
  filters.status = ''
  pagination.page = 1
  loadRecords()
}

// 手动补签
function showManualSigninDialog() {
  manualSigninForm.student_name = ''
  manualSigninForm.course_date = dayjs().format('YYYY-MM-DD')
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
    loadRecords()
  } catch (error) {
    console.error('补签失败:', error)
  } finally {
    submitting.value = false
  }
}

// 编辑记录
function editRecord(row) {
  editForm.id = row.id
  editForm.status = row.status
  editForm.remark = row.remark
  editVisible.value = true
}

async function handleEdit() {
  submitting.value = true
  try {
    await attendanceAPI.updateRecord(editForm.id, {
      status: editForm.status,
      remark: editForm.remark
    })
    ElMessage.success('更新成功')
    editVisible.value = false
    loadRecords()
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    submitting.value = false
  }
}

// 删除记录
function deleteRecord(row) {
  ElMessageBox.confirm(
    `确定要删除 ${row.student_name} 在 ${row.course_date} 的签到记录吗？`,
    '删除确认',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    }
  ).then(async () => {
    try {
      await attendanceAPI.deleteRecord(row.id)
      ElMessage.success('删除成功')
      loadRecords()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 导出数据
async function exportData() {
  try {
    const res = await exportAPI.exportAttendance({
      start_date: filters.start_date,
      end_date: filters.end_date
    })
    
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

// 工具函数
function getStatusType(status) {
  const types = {
    present: 'success',
    late: 'warning',
    absent: 'danger'
  }
  return types[status] || 'info'
}

function getConfidenceColor(confidence) {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  // 默认查询今天的记录
  const today = dayjs().format('YYYY-MM-DD')
  dateRange.value = [today, today]
  filters.start_date = today
  filters.end_date = today
  loadRecords()
})
</script>

<style lang="scss" scoped>
.attendance-page {
  .filter-form {
    margin-bottom: 20px;
  }
  
  .toolbar {
    margin-bottom: 20px;
  }
  
  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>
