# 人脸识别课堂签到系统 (Face Recognition Attendance System)

这是一个基于 **InsightFace** 和 **OpenCV** 的智能课堂签到系统。不仅支持静态图片的批量识别，还集成了 **SQLite 数据库** 自动记录考勤状态，并提供了实时检测和考勤查询功能。

## ✅ 主要功能

1.  **高效人脸录入 (Register)**
    *   无需模型微调，仅需放入学生照片即可一键建立特征库。
    *   自动处理不同分辨率的照片（支持小图、证件照）。
    *   **自动同步**: 学生信息会自动注册到 SQLite 数据库中。

2.  **多场景识别 (Inference)**
    *   **批量识别**: 支持对课堂抓拍照片进行批量处理。
    *   **实时检测**: 提供 `realtime.py` 支持调用摄像头进行实时人脸签到。
    *   **抗遮挡优化**: 智能调整标签位置和透明度，避免遮挡人脸。

3.  **考勤管理 (Attendance)**
    *   **自动记录**: 识别成功通过后，自动将签到状态写入数据库。
    *   **记录查询**: 提供 `query.py` 脚本，可按姓名、日期查询出勤记录。

## 📂 目录结构

```
data/
├── train/              # 【注册区】学生照片文件夹 (e.g. data/train/ZhangSan/1.jpg)
├── test/               # 【测试区】课堂抓拍照片
└── outputs/            # 【结果区】识别后的可视化图片
src/
├── attendance.py       # 考勤逻辑核心 (记录/更新状态)
├── config.py           # 全局配置文件
├── inference.py        # 静态图片识别脚本
├── query.py            # 考勤查询脚本
├── realtime.py         # 实时摄像头签到脚本
├── register.py         # 学生注册脚本
├── utils.py            # 图像处理工具箱
└── databaseBuild/
    └── db.py           # 数据库初始化与操作
requirements.txt        # 项目依赖
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 学生注册
将学生照片整理到 `data/train` 目录下（每个学生一个文件夹）。
```bash
python src/register.py
```
> **提示**: 首次运行会自动下载 InsightFace 模型文件，请保持网络通畅。

### 3. 开始签到

#### 方式 A: 静态图片批量签到
将课堂照片放入 `data/test`，运行：
```bash
# Windows PowerShell
Get-ChildItem data\test | ForEach-Object { python src/inference.py $_.FullName }
```
结果将保存在 `data/outputs`，同时考勤记录会写入数据库。

#### 方式 B: 实时摄像头签到
```bash
python src/realtime.py
```
按 `q` 键退出实时检测。

### 4. 查询考勤
查看特定学生的出勤情况：
```bash
python src/query.py --name "ZhangSan"
```
（或者直接运行 `python src/query.py` 查看所有记录，具体用法取决于脚本实现）

## ⚙️ 配置说明 (`src/config.py`)

*   `MATCH_THRESHOLD`: 默认为 **0.45**。
    *   识别太严格（漏识） -> **调低**数值。
    *   识别太宽松（误识） -> **调高**数值。
*   `FONT_SCALE`: 控制人脸框文字大小（代码已实现动态调整，此处为基准值）。

## ❓ 常见问题

*   **Q: 注册时提示 Warning: No face detected？**
    *   A: 系统已针对小图进行了优化。如果仍检测不到，请尝试使用更清晰、正脸占比更大的照片。
*   **Q: 数据库文件在哪里？**
    *   A: 默认生成在 `data/` 目录下（如 `data/attendance.db` 或类似名称，详见配置）。
