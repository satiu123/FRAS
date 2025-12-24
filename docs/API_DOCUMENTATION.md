# FRAS 后端 API 文档

人脸识别考勤系统 (Face Recognition Attendance System) 后端 API 接口文档

## 📋 目录

- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [认证与安全](#认证与安全)
- [响应格式](#响应格式)
- [接口详情](#接口详情)
  - [系统接口](#系统接口)
  - [实时签到接口](#实时签到接口)
  - [学生管理接口](#学生管理接口)
  - [签到记录接口](#签到记录接口)
  - [数据统计接口](#数据统计接口)
- [WebSocket 实时通信](#websocket-实时通信)
- [错误处理](#错误处理)

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 初始化数据库

```bash
python src/databaseBuild/db.py
```

### 启动服务

```bash
python src/api/app.py
```

服务将在 `http://localhost:5000` 启动

### 测试连接

```bash
curl http://localhost:5000/api/health
```

---

## 📊 API 概览

| 模块 | 端点前缀 | 功能描述 |
|------|---------|---------|
| 系统 | `/api` | 健康检查、导出等 |
| 实时签到 | `/api/realtime` | 实时签到状态、最近记录 |
| 学生管理 | `/api/students` | 学生信息、人脸库管理 |
| 签到记录 | `/api/attendance` | 签到记录查询、补签 |
| 数据统计 | `/api/statistics` | 统计分析、趋势图表 |

---

## 🔒 认证与安全

当前版本为开发版本，暂未启用认证。生产环境建议：

- 使用 JWT 令牌认证
- 启用 HTTPS
- 配置 CORS 白名单
- 实施 API 限流

---

## 📦 响应格式

所有接口返回统一的 JSON 格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2025-12-23T10:30:00"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 描述信息 |
| data | object | 返回的数据 |
| timestamp | string | 服务器时间戳 (ISO 8601) |

---

## 📡 接口详情

### 系统接口

#### 1. 健康检查

**端点**: `GET /api/health`

**描述**: 检查服务运行状态

**响应示例**:
```json
{
  "success": true,
  "message": "服务运行正常",
  "data": {
    "version": "1.0.0",
    "status": "healthy"
  }
}
```

#### 2. 导出考勤数据

**端点**: `GET /api/export/attendance`

**描述**: 导出指定日期范围的考勤数据为 CSV 格式

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期，默认今天 |

**响应示例**:
```json
{
  "success": true,
  "message": "导出成功",
  "data": {
    "csv_content": "学生姓名,学号,日期,...",
    "filename": "attendance_2025-12-01_2025-12-23.csv"
  }
}
```

---

### 实时签到接口

#### 1. 获取实时签到状态

**端点**: `GET /api/realtime/status`

**描述**: 获取当前课程的签到状态（总人数、已签到、签到率等）

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "course_name": "当前课程",
    "course_date": "2025-12-23",
    "total_students": 50,
    "signed_count": 45,
    "absent_count": 5,
    "sign_rate": 90.00,
    "avg_confidence": 0.8523
  }
}
```

#### 2. 获取最近签到记录

**端点**: `GET /api/realtime/recent`

**描述**: 获取最近的签到记录（用于实时动态列表）

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | integer | 否 | 返回记录数，默认10 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "records": [
      {
        "name": "张三",
        "student_id": "2021001",
        "status": "present",
        "confidence": 0.9123,
        "time": "2025-12-23T14:30:15",
        "remark": ""
      }
    ]
  }
}
```

#### 3. 接收签到通知

**端点**: `POST /api/realtime/signin`

**描述**: 识别系统调用此接口推送签到结果

**Body 参数**:
```json
{
  "student_name": "张三",
  "confidence": 0.9123,
  "status": "present",
  "image_path": "/path/to/capture.jpg"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "签到通知已发送"
}
```

---

### 学生管理接口

#### 1. 获取学生列表

**端点**: `GET /api/students/`

**描述**: 分页获取学生列表，支持搜索

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| search | string | 否 | 搜索关键词（姓名或学号） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "students": [
      {
        "id": 1,
        "name": "张三",
        "student_id": "2021001",
        "created_at": "2025-01-01T10:00:00",
        "has_face": true,
        "face_count": 5,
        "status": "已激活"
      }
    ]
  }
}
```

#### 2. 获取学生详情

**端点**: `GET /api/students/<student_id>`

**描述**: 获取单个学生的详细信息，包括人脸图片列表

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "id": 1,
    "name": "张三",
    "student_id": "2021001",
    "created_at": "2025-01-01T10:00:00",
    "face_images": [
      {
        "filename": "张三_20250101_100000.jpg",
        "path": "data/train/张三/张三_20250101_100000.jpg",
        "size": 45678,
        "created_at": "2025-01-01T10:00:00"
      }
    ],
    "has_face": true,
    "status": "已激活"
  }
}
```

#### 3. 创建学生

**端点**: `POST /api/students/`

**描述**: 创建新学生

**Body 参数**:
```json
{
  "name": "李四",
  "student_id": "2021002"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "学生 李四 创建成功",
  "data": {
    "name": "李四",
    "student_id": "2021002"
  }
}
```

#### 4. 更新学生信息

**端点**: `PUT /api/students/<student_id>`

**描述**: 更新学生信息

**Body 参数**:
```json
{
  "name": "李四",
  "student_id": "2021002"
}
```

#### 5. 删除学生

**端点**: `DELETE /api/students/<student_id>`

**描述**: 删除学生及其人脸数据

**响应示例**:
```json
{
  "success": true,
  "message": "学生 李四 已删除"
}
```

#### 6. 上传人脸图片

**端点**: `POST /api/students/<student_id>/face`

**描述**: 为学生上传人脸图片，支持两种方式

**方式1: 文件上传 (multipart/form-data)**
```
Content-Type: multipart/form-data
file: (binary)
```

**方式2: Base64 编码 (application/json)**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "人脸图片上传成功",
  "data": {
    "filename": "李四_20251223_143000.jpg",
    "path": "data/train/李四/李四_20251223_143000.jpg"
  }
}
```

#### 7. 删除人脸图片

**端点**: `DELETE /api/students/<student_id>/face/<filename>`

#### 8. 获取人脸图片

**端点**: `GET /api/students/<student_id>/face/<filename>`

**描述**: 返回图片文件

#### 9. 批量创建学生

**端点**: `POST /api/students/batch`

**Body 参数**:
```json
{
  "students": [
    {"name": "张三", "student_id": "2021001"},
    {"name": "李四", "student_id": "2021002"}
  ]
}
```

---

### 签到记录接口

#### 1. 获取签到记录列表

**端点**: `GET /api/attendance/records`

**描述**: 分页获取签到记录，支持多维度筛选

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 指定日期 (YYYY-MM-DD) |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期，默认今天 |
| student_name | string | 否 | 学生姓名（模糊搜索） |
| status | string | 否 | 状态 (present/late/absent) |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "records": [
      {
        "id": 1,
        "student_name": "张三",
        "student_id": "2021001",
        "course_date": "2025-12-23",
        "status": "present",
        "status_text": "已到",
        "confidence": 0.9123,
        "created_at": "2025-12-23T08:30:15",
        "remark": "",
        "has_image": true
      }
    ]
  }
}
```

#### 2. 获取签到记录详情

**端点**: `GET /api/attendance/records/<record_id>`

#### 3. 手动补签

**端点**: `POST /api/attendance/manual-signin`

**描述**: 为单个学生手动补签

**Body 参数**:
```json
{
  "student_name": "张三",
  "course_date": "2025-12-23",
  "remark": "补签"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "张三 补签成功",
  "data": {
    "student_name": "张三",
    "course_date": "2025-12-23",
    "remark": "补签"
  }
}
```

#### 4. 批量补签

**端点**: `POST /api/attendance/batch-signin`

**Body 参数**:
```json
{
  "students": ["张三", "李四", "王五"],
  "course_date": "2025-12-23",
  "remark": "批量补签"
}
```

#### 5. 更新签到记录

**端点**: `PUT /api/attendance/records/<record_id>`

**Body 参数**:
```json
{
  "status": "late",
  "remark": "迟到15分钟"
}
```

#### 6. 删除签到记录

**端点**: `DELETE /api/attendance/records/<record_id>`

#### 7. 获取签到汇总

**端点**: `GET /api/attendance/summary`

**描述**: 获取按日期和学生的签到矩阵

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期，默认30天前 |
| end_date | string | 否 | 结束日期，默认今天 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "start_date": "2025-11-23",
    "end_date": "2025-12-23",
    "dates": ["2025-12-23", "2025-12-22", "..."],
    "summary": [
      {
        "name": "张三",
        "student_id": "2021001",
        "records": [
          {"date": "2025-12-23", "status": "present"},
          {"date": "2025-12-22", "status": "absent"}
        ],
        "statistics": {
          "total_days": 30,
          "present_count": 28,
          "late_count": 1,
          "absent_count": 1,
          "attendance_rate": 93.33
        }
      }
    ]
  }
}
```

#### 8. 获取缺勤名单

**端点**: `GET /api/attendance/absent-list`

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 日期，默认今天 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "date": "2025-12-23",
    "total_students": 50,
    "signed_count": 45,
    "absent_count": 5,
    "absent_list": [
      {"name": "王五", "student_id": "2021003"}
    ]
  }
}
```

---

### 数据统计接口

#### 1. 获取统计概览

**端点**: `GET /api/statistics/overview`

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 日期，默认今天 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "date": "2025-12-23",
    "total_students": 50,
    "signed_count": 45,
    "absent_count": 5,
    "sign_rate": 90.00,
    "avg_confidence": 0.8523
  }
}
```

#### 2. 获取出勤分布（饼图数据）

**端点**: `GET /api/statistics/distribution`

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 日期，默认今天 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "date": "2025-12-23",
    "distribution": [
      {"name": "正常签到", "value": 43, "status": "present"},
      {"name": "迟到", "value": 2, "status": "late"},
      {"name": "缺勤", "value": 5, "status": "absent"}
    ]
  }
}
```

#### 3. 获取出勤率趋势（折线图数据）

**端点**: `GET /api/statistics/trend`

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | integer | 否 | 统计天数，默认30 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "start_date": "2025-11-23",
    "end_date": "2025-12-23",
    "total_students": 50,
    "trend": [
      {
        "date": "2025-11-23",
        "signed_count": 47,
        "sign_rate": 94.00
      },
      {
        "date": "2025-11-24",
        "signed_count": 45,
        "sign_rate": 90.00
      }
    ]
  }
}
```

#### 4. 获取考勤预警列表

**端点**: `GET /api/statistics/alerts`

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | integer | 否 | 统计天数，默认30 |
| threshold | integer | 否 | 缺勤次数阈值，默认3 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "period": "2025-11-23 至 2025-12-23",
    "threshold": 3,
    "total_days": 30,
    "alert_count": 5,
    "alerts": [
      {
        "name": "王五",
        "student_id": "2021003",
        "absent_days": 8,
        "attended_days": 22,
        "total_days": 30,
        "attendance_rate": 73.33,
        "alert_level": "严重"
      }
    ]
  }
}
```

#### 5. 获取学生个人统计

**端点**: `GET /api/statistics/student/<student_name>`

**Query 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | integer | 否 | 统计天数，默认30 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "student": {
      "name": "张三",
      "student_id": "2021001",
      "created_at": "2025-01-01T10:00:00"
    },
    "period": "2025-11-23 至 2025-12-23",
    "statistics": {
      "total_days": 30,
      "attended_days": 28,
      "absent_days": 2,
      "attendance_rate": 93.33,
      "avg_confidence": 0.8912
    },
    "recent_records": [
      {
        "date": "2025-12-23",
        "status": "present",
        "confidence": 0.9123,
        "time": "2025-12-23T08:30:15",
        "remark": ""
      }
    ]
  }
}
```

---

## 🔌 WebSocket 实时通信

### 连接地址

```
ws://localhost:5000
```

### 事件说明

#### 客户端 -> 服务器

**1. 连接（自动）**
```javascript
// 使用 socket.io-client
const socket = io('http://localhost:5000');
```

**2. 心跳检测**
```javascript
socket.emit('ping', {});
```

#### 服务器 -> 客户端

**1. 连接响应**
```javascript
socket.on('connection_response', (data) => {
  console.log(data);
  // { status: 'connected', message: '已连接到实时签到服务', sid: 'xxx' }
});
```

**2. 心跳响应**
```javascript
socket.on('pong', (data) => {
  console.log(data.timestamp);
});
```

**3. 新签到通知** ⭐
```javascript
socket.on('new_signin', (data) => {
  console.log(data);
  /*
  {
    student_name: '张三',
    confidence: 0.9123,
    status: 'present',
    timestamp: '2025-12-23T14:30:15',
    message: '张三 签到成功'
  }
  */
});
```

### 前端示例代码

#### Vue 3 + socket.io-client

```vue
<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { io } from 'socket.io-client';

const socket = ref(null);
const recentSignins = ref([]);

onMounted(() => {
  // 连接 WebSocket
  socket.value = io('http://localhost:5000');
  
  // 监听连接成功
  socket.value.on('connection_response', (data) => {
    console.log('✅ 已连接:', data.message);
  });
  
  // 监听新签到
  socket.value.on('new_signin', (data) => {
    console.log('📢 新签到:', data.student_name);
    
    // 添加到列表顶部
    recentSignins.value.unshift({
      name: data.student_name,
      confidence: data.confidence,
      time: data.timestamp
    });
    
    // 限制列表长度
    if (recentSignins.value.length > 10) {
      recentSignins.value.pop();
    }
    
    // 播放提示音
    playNotificationSound();
  });
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect();
  }
});

function playNotificationSound() {
  const audio = new Audio('/sounds/success.mp3');
  audio.play();
}
</script>
```

---

## 📸 人脸识别接口

### 6.1 上传图片识别签到

**端点**: `POST /api/recognition/upload-image`

**描述**: 上传图片进行人脸识别并自动签到

**支持方式**:
1. multipart/form-data 文件上传
2. JSON base64 编码

**请求示例 1 (文件上传)**:
```http
POST /api/recognition/upload-image
Content-Type: multipart/form-data

file=<图片文件>
```

**请求示例 2 (Base64)**:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**成功响应**:
```json
{
  "success": true,
  "message": "检测到 3 个人脸，识别成功 3 人，签到成功 2 人",
  "data": {
    "detected_faces": 3,
    "recognized": [
      {
        "name": "张三",
        "confidence": 0.85,
        "status": "matched",
        "bbox": [100, 200, 300, 400],
        "signed_in": true
      },
      {
        "name": "李四",
        "confidence": 0.78,
        "status": "matched",
        "bbox": [400, 200, 600, 400],
        "already_signed": true
      }
    ],
    "unknown": [
      {
        "name": "Unknown",
        "confidence": 0.35,
        "status": "unknown",
        "bbox": [700, 200, 900, 400]
      }
    ],
    "signed_in": [
      {
        "name": "张三",
        "confidence": 0.85,
        "time": "2025-12-23 14:30:00"
      }
    ]
  }
}
```

**失败响应**:
```json
{
  "success": false,
  "message": "未检测到人脸，请确保照片清晰且包含正脸"
}
```

### 6.2 仅识别（不签到）

**端点**: `POST /api/recognition/recognize-only`

**描述**: 识别图片中的人脸，但不记录签到（用于预览）

**请求/响应**: 与 `/upload-image` 相同，但 `data.signed_in` 始终为空

**使用场景**:
- 预览识别效果
- 测试识别准确度
- 查看图片中的人脸

**前端示例**:
```javascript
import { recognitionAPI } from '@/api'

// 文件上传方式
async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  const result = await recognitionAPI.uploadImage(formData)
  return result
}

// Base64方式
async function uploadBase64(base64Image) {
  const result = await recognitionAPI.uploadImage({
    image: base64Image
  })
  return result
}

// 使用摄像头拍照
async function captureAndRecognize() {
  const canvas = videoRef.value
  const base64 = canvas.toDataURL('image/jpeg', 0.9)
  const result = await recognitionAPI.uploadImage({ image: base64 })
  
  if (result.success) {
    console.log(`签到成功: ${result.data.signed_in.length} 人`)
  }
}
```

---

## ❌ 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "success": false,
  "message": "学生不存在",
  "data": {},
  "timestamp": "2025-12-23T14:30:00"
}
```

---

## 🛠️ 与识别系统集成

### 在 realtime.py 中集成 API

```python
import requests
from datetime import date

def on_face_recognized(student_name: str, confidence: float):
    """当识别到人脸时调用"""
    try:
        # 发送到 API
        response = requests.post('http://localhost:5000/api/realtime/signin', json={
            'student_name': student_name,
            'confidence': confidence,
            'status': 'present',
            'image_path': f'/captures/{student_name}_{date.today()}.jpg'
        })
        
        if response.status_code == 200:
            print(f"✅ {student_name} 签到成功")
        else:
            print(f"❌ 签到失败: {response.text}")
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
```

---

## 📝 开发建议

### 前端开发

1. **实时监控大屏**
   - 使用 WebSocket 接收实时签到
   - 调用 `/api/realtime/status` 获取课堂状态
   - 调用 `/api/realtime/recent` 显示最近签到列表

2. **签到记录管理**
   - 使用 `/api/attendance/records` 分页查询
   - 使用 `/api/attendance/manual-signin` 实现补签
   - 使用 `/api/export/attendance` 导出数据

3. **学生信息管理**
   - 使用 `/api/students/` 列表和搜索
   - 使用 `/api/students/<id>/face` 上传人脸照片
   - 支持拖拽上传、摄像头采集

4. **数据统计分析**
   - 使用 ECharts 渲染图表
   - `/api/statistics/distribution` → 饼图
   - `/api/statistics/trend` → 折线图
   - `/api/statistics/alerts` → 预警列表

### 生产环境部署

```bash
# 使用 gunicorn + eventlet
pip install gunicorn eventlet
gunicorn -w 4 -k eventlet -b 0.0.0.0:5000 src.api.app:app
```

---

## 📞 联系与支持

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]

---

**最后更新**: 2025-12-23
**API 版本**: v1.0.0
