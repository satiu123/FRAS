import api from '@/utils/request'

export const systemAPI = {
  // 健康检查
  checkHealth() {
    return api.get('/health')
  }
}

export const realtimeAPI = {
  // 获取实时状态
  getStatus() {
    return api.get('/realtime/status')
  },
  
  // 获取最近签到
  getRecent(limit = 10) {
    return api.get('/realtime/recent', { params: { limit } })
  }
}

export const studentsAPI = {
  // 获取学生列表
  getList(params) {
    return api.get('/students/', { params })
  },
  
  // 获取学生详情
  getDetail(id) {
    return api.get(`/students/${id}`)
  },
  
  // 创建学生
  create(data) {
    return api.post('/students/', data)
  },
  
  // 更新学生
  update(id, data) {
    return api.put(`/students/${id}`, data)
  },
  
  // 删除学生
  delete(id) {
    return api.delete(`/students/${id}`)
  },
  
  // 上传人脸图片
  uploadFace(id, data) {
    return api.post(`/students/${id}/face`, data)
  },
  
  // 删除人脸图片
  deleteFace(id, filename) {
    return api.delete(`/students/${id}/face/${filename}`)
  },
  
  // 批量创建
  batchCreate(students) {
    return api.post('/students/batch', { students })
  }
}

export const attendanceAPI = {
  // 获取签到记录
  getRecords(params) {
    return api.get('/attendance/records', { params })
  },
  
  // 获取记录详情
  getDetail(id) {
    return api.get(`/attendance/records/${id}`)
  },
  
  // 手动补签
  manualSignin(data) {
    return api.post('/attendance/manual-signin', data)
  },
  
  // 批量补签
  batchSignin(data) {
    return api.post('/attendance/batch-signin', data)
  },
  
  // 更新记录
  updateRecord(id, data) {
    return api.put(`/attendance/records/${id}`, data)
  },
  
  // 删除记录
  deleteRecord(id) {
    return api.delete(`/attendance/records/${id}`)
  },
  
  // 获取签到汇总
  getSummary(params) {
    return api.get('/attendance/summary', { params })
  },
  
  // 获取缺勤名单
  getAbsentList(params) {
    return api.get('/attendance/absent-list', { params })
  }
}

export const statisticsAPI = {
  // 获取统计概览
  getOverview(params) {
    return api.get('/statistics/overview', { params })
  },
  
  // 获取出勤分布
  getDistribution(params) {
    return api.get('/statistics/distribution', { params })
  },
  
  // 获取出勤趋势
  getTrend(params) {
    return api.get('/statistics/trend', { params })
  },
  
  // 获取考勤预警
  getAlerts(params) {
    return api.get('/statistics/alerts', { params })
  },
  
  // 获取学生统计
  getStudentStats(name, params) {
    return api.get(`/statistics/student/${name}`, { params })
  }
}

export const exportAPI = {
  // 导出考勤数据
  exportAttendance(params) {
    return api.get('/export/attendance', { params })
  }
}

export const recognitionAPI = {
  // 上传图片进行识别签到
  uploadImage(data) {
    return api.post('/recognition/upload-image', data)
  },
  
  // 仅识别不签到（预览）
  recognizeOnly(data) {
    return api.post('/recognition/recognize-only', data)
  }
}

