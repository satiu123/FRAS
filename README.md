# 人脸识别课堂签到系统 (Face Recognition Attendance System)

这是一个基于 Python 和 InsightFace 的轻量级课堂签到系统。它能够在一张包含多人的教室内照片中检测并识别特定的学生。

## 主要功能

*   **学生录入 (Fine-tuning)**: 只需要将学生的照片放入指定文件夹，系统即可自动提取特征并建立数据库（无需大规模训练）。
*   **课堂点名 (Inference)**: 对整张课堂照片进行人脸检测和识别。
*   **可视化输出**:
    *   自动识别学生并在其头部绘制人脸框和姓名。
    *   **动态字体**: 根据人脸远近（大小）自动调整字体大小。
    *   **防遮挡优化**: 只有识别出的学生才显示姓名标签，且标签背景半透明，最大限度减少对画面的遮挡。
    *   未知人员仅显示红色框标记。

## 目录结构

```
data/
├── train/           # 【注册区】存放学生照片的文件夹（每个学生一个文件夹）
├── test/            # 【测试区】存放待检测的课堂照片
└── outputs/         # 【结果区】存放识别后的结果图片
src/
├── register.py      # 注册脚本
├── inference.py     # 识别脚本
├── config.py        # 配置文件
└── utils.py         # 工具函数
requirements.txt     # 依赖列表
```

## 快速开始

### 1. 环境安装
确保安装了 Python 3.8+，然后安装依赖：
```bash
pip install -r requirements.txt
```
*注意：首次运行会通过 InsightFace 自动下载必要的模型文件。*

### 2. 准备数据
*   **注册学生**: 在 `data/train/` 下为每个学生创建一个文件夹，文件夹名为**学生姓名**（支持英文/拼音），放入该学生的单人照片（建议正脸清晰）。
    *   例如: `data/train/ZhangSan/photo.jpg`
*   **准备测试图**: 将课堂照片放入 `data/test/`。

### 3. 运行注册
建立学生人脸数据库：
```bash
python src/register.py
```
成功后会提示保存了多少个学生到 `data/students.pkl`。

### 4. 运行识别
对 `data/test` 中的图片进行识别：

**单张识别**:
```bash
python src/inference.py data/test/test1.jpg
```

**批量识别 (PowerShell)**:
```powershell
Get-ChildItem data\test | ForEach-Object { python src/inference.py $_.FullName }
```

识别结果图片将保存在 `data/outputs/` 目录中。

## 配置说明

文件: `src/config.py`

*   `MATCH_THRESHOLD` (默认 0.45): 相似度判定阈值。
    *   如果有学生**未被识别**，尝试**降低**此值 (如 0.40)。
    *   如果出现**张冠李戴**，尝试**提高**此值 (如 0.50)。
*   `FONT_SCALE` / `THICKNESS`: 字体缩放基准和粗细（代码中已启用根据人脸大小动态调整，此处为配置基准）。

## 常见问题

*   **Q: 识别出的框是红色的且没有名字？**
    *   A: 表示检测到了人脸，但与数据库中的学生匹配度低于阈值，判定为“未知”。
*   **Q: 名字显示乱码？**
    *   A:目前的 OpenCV 一般不支持直接绘制中文字符。建议学生文件夹名称使用**拼音**或**英文** (如 `ZhangSan`, `LiSi`)。
