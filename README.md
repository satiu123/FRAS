# 🎓 人脸识别考勤系统 (FRAS)

基于 **InsightFace** 和 **OpenCV** 的智能课堂签到系统，提供完整的 Web 管理平台。

## ✨ 系统特色

### 🖥️ 现代化 Web 界面
- **实时监控大屏** - WebSocket 实时推送签到动态
- **考勤记录管理** - 多维筛选、手动补签、批量操作
- **学生信息管理** - 人脸库管理、图片上传预览
- **数据统计分析** - ECharts 可视化图表、考勤预警
- **拍照签到** 🆕 - 网页摄像头拍照、图片上传批量识别

### 🚀 核心功能

1.  **智能人脸识别**
    *   基于 InsightFace 高精度人脸识别
    *   支持批量识别和实时摄像头检测
    *   🆕 支持网页拍照签到和图片上传签到
    *   自动调整标签位置，避免遮挡人脸
    *   支持小图、证件照等多种照片格式

2.  **完整 Web API**
    *   RESTful API 接口（30+ 端点）
    *   WebSocket 实时通信
    *   统一响应格式
    *   完整的 CRUD 操作

3.  **考勤管理系统**
    *   自动记录签到状态到 SQLite 数据库
    *   支持手动补签和批量补签
    *   多维度数据筛选和查询
    *   Excel 数据导出功能

## 📂 项目结构

```
FRAS/
├── src/                        # 后端源代码
│   ├── api/                   # 🆕 Web API 服务
│   │   ├── app.py            # Flask 主应用（WebSocket）
│   │   ├── students.py       # 学生管理接口
│   │   ├── attendance.py     # 签到记录接口
│   │   └── statistics.py     # 数据统计接口
│   ├── databaseBuild/        # 数据库模块
│   │   └── db.py            # 数据库初始化与操作
│   ├── attendance.py         # 考勤逻辑核心
│   ├── config.py            # 全局配置文件
│   ├── inference.py         # 静态图片识别
│   ├── realtime.py          # 实时摄像头签到
│   ├── register.py          # 学生人脸注册
│   └── utils.py             # 图像处理工具箱
├── frontend/                  # 🆕 Web 前端（Vue 3）
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   │   ├── Dashboard.vue      # 实时监控大屏
│   │   │   ├── Attendance.vue     # 签到记录管理
│   │   │   ├── Students.vue       # 学生信息管理
│   │   │   └── Statistics.vue     # 数据统计分析
│   │   ├── api/             # API 接口封装
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.js
├── data/                      # 数据目录
│   ├── database/             # SQLite 数据库
│   ├── train/                # 人脸训练数据
│   ├── test/                 # 测试照片
│   ├── outputs/              # 识别结果
│   └── exports/              # 导出文件
├── docs/                      # 📚 文档
│   └── API_DOCUMENTATION.md  # 完整 API 文档
├── tests/                     # 测试脚本
│   └── test_api.py           # API 测试工具
├── requirements.txt           # Python 依赖
└── start.ps1                 # 🚀 一键启动脚本
```

## 🚀 快速启动（推荐）

### 使用启动脚本（一键启动）

```powershell
# 运行启动脚本
.\start.ps1

# 按照菜单选择：
# [4] 安装依赖（首次运行）
# [5] 初始化数据库（首次运行）
# [3] 同时启动前后端服务
```

### 访问系统
- 🌐 **Web 前端**: http://localhost:3000
- 🔌 **API 后端**: http://localhost:5000
- 📖 **API 文档**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

---

## 📝 使用方式

### 方式一：Web 界面管理（推荐 ⭐）

1. **启动 Web 服务**
   ```powershell
   .\start.ps1  # 选择 [3] 同时启动前后端
   ```

2. **访问管理界面**
   - 打开浏览器访问 http://localhost:3000
   - 在 **学生管理** 页面添加学生并上传人脸照片
   - 💡 **智能增量更新** - 上传/删除人脸图片后仅更新该学生的特征向量，快速高效
   - 🔄 **手动全量更新** - 点击"更新人脸数据库"按钮或运行 `python src/register.py` 重建所有学生特征
   - 在 **实时监控** 页面查看签到动态
   - 在 **签到记录** 页面管理考勤数据
   - 在 **数据统计** 页面查看图表分析

3. **开始人脸识别**
   🔧 技术栈

### 后端
- **Flask** 2.3.0+ - Web 框架
- **Flask-SocketIO** 5.3.0+ - WebSocket 实时通信
- **InsightFace** - 高精度人脸识别
- **OpenCV** - 图像处理
- **SQLite** - 数据库

### 前端
- **Vue 3** - 渐进式框架
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Socket.IO** - WebSocket 客户端
- **ECharts** - 数据可视化

## ⚙️ 配置说明

### 后端配置 ([src/config.py](src/config.py))
```python
MATCH_THRESHOLD = 0.45  # 人脸识别阈值
# 识别太严格（漏识） -> 调低数值
# 识别太宽松（误识） -> 调高数值

FONT_SCALE = 1.0  # 文字大小（自动动态调整）
```

### 前端配置 ([frontend/vite.config.js](frontend/vite.config.js))
```javascript
server: {
  port: 3000,           // 前端端口
  proxy: {
    '/api': 'http://localhost:5000'  // API 代理
  }
}
```

## 📚 文档

- � [拍照签到使用指南](docs/PHOTO_SIGNIN_GUIDE.md) - 拍照/上传识别签到教程 🆕
- �📘 [完整 API 文档](docs/API_DOCUMENTATION.md) - 30+ 接口详细说明
- 🚀 [快速开始指南](docs/QUICK_START.md) - 5 分钟上手教程
- 💻 [前端开发文档](frontend/README.md) - Vue 组件说明

## 🧪 测试

```bash
# 运行 API 测试
python tests/test_api.py
```

## ❓ 常见问题

**Q: 首次启动报错？**
- A: 确保已安装依赖 `pip install -r requirements.txt` 和 `cd frontend && npm install`

**Q: 上传人脸图片后无法识别？**
- A: 系统会**自动增量更新**相关学生的人脸数据库，无需手动操作。也可以在学生管理页面点击"更新人脸数据库"按钮进行全量更新，或运行启动脚本选择选项 [6]

**Q: 注册时提示 No face detected？**
- A: 使用更清晰的正面照片，确保人脸占比足够大

**Q: WebSocket 连接失败？**
- A: 检查后端是否启动（http://localhost:5000/api/health）

**Q: 前端页面空白？**
- A: 检查前端是否启动（http://localhost:3000）和 API 代理配置

**Q: 数据库文件在哪里？**
- A: 默认位置 `data/database/attendance.db`，人脸数据库为 `students.pkl`

## 📄 License

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！
