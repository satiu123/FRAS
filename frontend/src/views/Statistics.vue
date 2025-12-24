<template>
  <div class="statistics-page">
    <!-- 统计概览 -->
    <el-row :gutter="20" class="overview-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card info">
          <div class="stat-value">{{ overview.total_students }}</div>
          <div class="stat-label">总学生数</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card success">
          <div class="stat-value">{{ overview.signed_count }}</div>
          <div class="stat-label">今日签到</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card warning">
          <div class="stat-value">{{ overview.absent_count }}</div>
          <div class="stat-label">今日缺勤</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-value">{{ overview.sign_rate }}%</div>
          <div class="stat-label">签到率</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 出勤分布饼图 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><PieChart /></el-icon>
                今日出勤分布
              </span>
            </div>
          </template>
          <div ref="pieChartRef" style="height: 350px;"></div>
        </el-card>
      </el-col>

      <!-- 出勤趋势折线图 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><TrendCharts /></el-icon>
                出勤率趋势（近30天）
              </span>
            </div>
          </template>
          <div ref="lineChartRef" style="height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 考勤预警列表 -->
    <el-card shadow="hover" class="alerts-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Warning /></el-icon>
            考勤预警（连续缺勤3次以上）
          </span>
          <el-button size="small" :icon="RefreshRight" @click="loadAlerts">
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="alerts" border v-loading="alertsLoading">
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="student_id" label="学号" width="150" />
        <el-table-column prop="absent_days" label="缺勤天数" width="120" />
        <el-table-column prop="attended_days" label="出勤天数" width="120" />
        <el-table-column prop="total_days" label="统计天数" width="120" />
        <el-table-column prop="attendance_rate" label="出勤率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.attendance_rate"
              :color="getProgressColor(row.attendance_rate)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="alert_level" label="预警等级" width="100">
          <template #default="{ row }">
            <el-tag :type="row.alert_level === '严重' ? 'danger' : 'warning'">
              {{ row.alert_level }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { PieChart, TrendCharts, Warning, RefreshRight } from '@element-plus/icons-vue'
import { statisticsAPI } from '@/api'
import * as echarts from 'echarts'

const pieChartRef = ref(null)
const lineChartRef = ref(null)
const alertsLoading = ref(false)

const overview = reactive({
  total_students: 0,
  signed_count: 0,
  absent_count: 0,
  sign_rate: 0
})

const alerts = ref([])

let pieChart = null
let lineChart = null

// 加载统计概览
async function loadOverview() {
  try {
    const res = await statisticsAPI.getOverview()
    Object.assign(overview, res.data)
  } catch (error) {
    ElMessage.error('加载概览失败')
  }
}

// 加载出勤分布
async function loadDistribution() {
  try {
    const res = await statisticsAPI.getDistribution()
    const data = res.data.distribution
    
    await nextTick()
    if (!pieChart) {
      pieChart = echarts.init(pieChartRef.value)
    }
    
    pieChart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center'
      },
      series: [
        {
          name: '出勤分布',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}\n{c} 人'
          },
          data: data.map(item => ({
            name: item.name,
            value: item.value,
            itemStyle: {
              color: item.status === 'present' ? '#67c23a' :
                     item.status === 'late' ? '#e6a23c' : '#f56c6c'
            }
          }))
        }
      ]
    })
  } catch (error) {
    ElMessage.error('加载出勤分布失败')
  }
}

// 加载出勤趋势
async function loadTrend() {
  try {
    const res = await statisticsAPI.getTrend({ days: 30 })
    const data = res.data.trend
    
    await nextTick()
    if (!lineChart) {
      lineChart = echarts.init(lineChartRef.value)
    }
    
    lineChart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: '{b}<br/>签到率: {c}%'
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.date),
        axisLabel: {
          rotate: 45,
          formatter: (value) => value.substring(5) // 只显示月-日
        }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      series: [
        {
          name: '签到率',
          type: 'line',
          data: data.map(item => item.sign_rate),
          smooth: true,
          itemStyle: {
            color: '#409eff'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
              ]
            }
          }
        }
      ]
    })
  } catch (error) {
    ElMessage.error('加载趋势数据失败')
  }
}

// 加载预警列表
async function loadAlerts() {
  alertsLoading.value = true
  try {
    const res = await statisticsAPI.getAlerts({ days: 30, threshold: 3 })
    alerts.value = res.data.alerts
  } catch (error) {
    ElMessage.error('加载预警数据失败')
  } finally {
    alertsLoading.value = false
  }
}

function getProgressColor(percentage) {
  if (percentage >= 80) return '#67c23a'
  if (percentage >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 窗口大小改变时重绘图表
function handleResize() {
  pieChart?.resize()
  lineChart?.resize()
}

onMounted(() => {
  loadOverview()
  loadDistribution()
  loadTrend()
  loadAlerts()
  
  window.addEventListener('resize', handleResize)
  
  return () => {
    window.removeEventListener('resize', handleResize)
    pieChart?.dispose()
    lineChart?.dispose()
  }
})
</script>

<style lang="scss" scoped>
.statistics-page {
  .overview-row {
    margin-bottom: 20px;
    
    .stat-card {
      text-align: center;
      padding: 24px;
      border-radius: 12px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      
      &.success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      }
      
      &.warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }
      
      &.info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      }
      
      .stat-value {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      
      .stat-label {
        font-size: 14px;
        opacity: 0.9;
      }
    }
  }
  
  .charts-row {
    margin-bottom: 20px;
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
  
  .alerts-card {
    margin-top: 20px;
  }
}
</style>
