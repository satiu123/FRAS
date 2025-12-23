# FRAS 前端项目

人脸识别考勤系统 (Face Recognition Attendance System) Web 前端

## 🚀 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动，API 代理到 `http://localhost:5000`

### 构建生产版本

```bash
npm run build
```

## 📦 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Socket.IO** - WebSocket 实时通信
- **ECharts** - 数据可视化
- **Vite** - 构建工具

## 🌐 页面说明

### 1. 实时监控大屏 (`/dashboard`)
- 实时状态卡片（应到/实到/缺勤/签到率）
- 实时签到动态列表（WebSocket 推送）
- 签到进度可视化
- 快捷操作（手动补签、导出数据等）

### 2. 签到记录管理 (`/attendance`)
- 多维度筛选（日期、姓名、状态）
- 签到记录列表
- 手动补签功能
- 批量操作
- 导出 Excel

### 3. 学生信息管理 (`/students`)
- 学生列表（搜索、分页）
- 添加/编辑/删除学生
- 人脸图片管理（上传、删除）
- 人脸库预览

### 4. 数据统计分析 (`/statistics`)
- 统计概览卡片
- 出勤分布饼图
- 出勤率趋势折线图
- 考勤预警列表

## 🎨 主要功能

### WebSocket 实时推送
```javascript
// 在 Dashboard 页面自动连接 WebSocket
// 实时接收签到通知并更新界面
socket.on('new_signin', (data) => {
  // 新签到推送处理
})
```

### 响应式设计
- 支持桌面、平板、移动设备
- 自适应布局
- 触摸友好

### 暗黑模式
- 支持亮色/暗色主题切换
- 保护用户视力

## 📁 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口定义
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   ├── layouts/          # 布局组件
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理
│   ├── styles/           # 全局样式
│   ├── utils/            # 工具函数
│   ├── views/            # 页面组件
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html
├── package.json
└── vite.config.js
```

## 🔧 配置说明

### API 代理配置

修改 `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',  // 后端 API 地址
        changeOrigin: true
      }
    }
  }
})
```

### WebSocket 连接

修改 `src/utils/websocket.js`:

```javascript
connect(url = 'http://localhost:5000')
```

## 💡 开发建议

### 组件开发
- 使用 Composition API
- 遵循单一职责原则
- 合理使用组合式函数

### 状态管理
- 全局状态使用 Pinia
- 局部状态使用 ref/reactive
- 避免状态冗余

### 性能优化
- 使用虚拟滚动处理长列表
- 图片懒加载
- 路由懒加载
- 合理使用计算属性

## 🐛 常见问题

### Q: 无法连接到后端 API？
**A**: 检查后端服务是否启动（`python src/api/app.py`），确保端口为 5000。

### Q: WebSocket 连接失败？
**A**: 检查 WebSocket 配置，确保后端启用了 SocketIO。

### Q: 图表不显示？
**A**: 检查 ECharts 是否正确初始化，确保容器有明确的高度。

## 📄 许可证

MIT License
