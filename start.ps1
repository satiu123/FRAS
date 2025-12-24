# 启动脚本

Write-Host "🚀 FRAS - 人脸识别考勤系统" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
Write-Host "检查 Python 环境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查Node.js
Write-Host "检查 Node.js 环境..." -ForegroundColor Yellow
node --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 未找到 Node.js，请先安装 Node.js 14+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "选择操作:" -ForegroundColor Green
Write-Host "1. 启动后端 API 服务" -ForegroundColor White
Write-Host "2. 启动前端开发服务器" -ForegroundColor White
Write-Host "3. 同时启动前后端（推荐）" -ForegroundColor White
Write-Host "4. 安装依赖" -ForegroundColor White
Write-Host "5. 初始化数据库" -ForegroundColor White
Write-Host "6. 更新人脸数据库 (students.pkl)" -ForegroundColor White
Write-Host "7. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-7)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🔧 启动后端 API 服务..." -ForegroundColor Cyan
        Write-Host "API 地址: http://localhost:5000" -ForegroundColor Green
        Write-Host ""
        python src/api/app.py
    }
    "2" {
        Write-Host ""
        Write-Host "🎨 启动前端开发服务器..." -ForegroundColor Cyan
        Write-Host "前端地址: http://localhost:3000" -ForegroundColor Green
        Write-Host ""
        Set-Location frontend
        npm run dev
    }
    "3" {
        Write-Host ""
        Write-Host "🚀 同时启动前后端服务..." -ForegroundColor Cyan
        Write-Host "后端地址: http://localhost:5000" -ForegroundColor Green
        Write-Host "前端地址: http://localhost:3000" -ForegroundColor Green
        Write-Host ""
        
        # 启动后端
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "python src/api/app.py"
        
        # 等待2秒
        Start-Sleep -Seconds 2
        
        # 启动前端
        Set-Location frontend
        npm run dev
    }
    "4" {
        Write-Host ""
        Write-Host "📦 安装依赖..." -ForegroundColor Cyan
        
        Write-Host "安装 Python 依赖..." -ForegroundColor Yellow
        pip install -r requirements.txt
        
        Write-Host ""
        Write-Host "安装前端依赖..." -ForegroundColor Yellow
        Set-Location frontend
        npm install
        
        Write-Host ""
        Write-Host "✅ 依赖安装完成!" -ForegroundColor Green
    }
    "5" {
        Write-Host ""
        Write-Host "🗄️  初始化数据库..." -ForegroundColor Cyan
        python src/databaseBuild/db.py
        Write-Host ""
        Write-Host "✅ 数据库初始化完成!" -ForegroundColor Green
    }
    "6" {
        Write-Host ""
        Write-Host "🔄 更新人脸数据库..." -ForegroundColor Cyan
        Write-Host "扫描 data/train 目录中的所有学生人脸图片" -ForegroundColor Yellow
        Write-Host "生成特征向量并更新到 students.pkl" -ForegroundColor Yellow
        Write-Host ""
        python src/register.py
        Write-Host ""
        Write-Host "✅ 人脸数据库更新完成!" -ForegroundColor Green
    }
    "7" {
        Write-Host "👋 再见!" -ForegroundColor Cyan
        exit 0
    }
    default {
        Write-Host "❌ 无效选项" -ForegroundColor Red
        exit 1
    }
}
