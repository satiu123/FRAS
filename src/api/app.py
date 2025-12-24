# Flask Web API 主应用
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import date, datetime, timedelta
import sqlite3
import os
from werkzeug.utils import secure_filename
import base64
import json

from src.databaseBuild.db import DB_PATH
from src.attendance import record_attendance as db_record_attendance
from src.query import manual_sign_in, student_exists, already_signed_today

# 导入蓝图
from src.api.statistics import statistics_bp
from src.api.students import students_bp
from src.api.attendance import attendance_bp
from src.api.recognition import recognition_bp
from src.api.realtime_recognition import realtime_recognition_bp

# Flask应用初始化
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'  # 生产环境需要更换
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 启用CORS（跨域资源共享）
CORS(app, resources={r"/api/*": {"origins": "*"}})

# WebSocket支持
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 注册蓝图
app.register_blueprint(statistics_bp)
app.register_blueprint(students_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(recognition_bp)
app.register_blueprint(realtime_recognition_bp)

# 配置上传文件夹
UPLOAD_FOLDER = project_root / "data" / "uploads"
KNOWN_FACES_FOLDER = project_root / "data" / "train"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# ==================== 辅助函数 ====================

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def format_response(success: bool, message: str = "", data=None, code: int = 200):
    """统一响应格式"""
    response = {
        "success": success,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(response), code

# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return format_response(True, "服务运行正常", {
        "version": "1.0.0",
        "status": "healthy"
    })

# ==================== 实时签到相关 ====================

@app.route('/api/realtime/status', methods=['GET'])
def get_realtime_status():
    """获取实时签到状态（当前课程信息）"""
    try:
        today = date.today().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取今日签到统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_signed,
                AVG(confidence) as avg_confidence
            FROM attendance_records 
            WHERE course_date = ? AND status = 'present'
        """, (today,))
        signed_stats = cursor.fetchone()
        
        # 获取总学生数
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "course_name": "当前课程",  # 可以从配置或参数获取
            "course_date": today,
            "total_students": total_students,
            "signed_count": signed_stats['total_signed'],
            "absent_count": total_students - signed_stats['total_signed'],
            "sign_rate": round((signed_stats['total_signed'] / total_students * 100) if total_students > 0 else 0, 2),
            "avg_confidence": round(signed_stats['avg_confidence'] or 0, 4)
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@app.route('/api/realtime/recent', methods=['GET'])
def get_recent_signins():
    """获取最近的签到记录（用于实时动态列表）"""
    try:
        limit = request.args.get('limit', 10, type=int)
        today = date.today().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ar.student_name,
                ar.course_date,
                ar.status,
                ar.confidence,
                ar.created_at,
                ar.remark,
                s.student_id
            FROM attendance_records ar
            LEFT JOIN students s ON ar.student_name = s.name
            WHERE ar.course_date = ?
            ORDER BY ar.created_at DESC
            LIMIT ?
        """, (today, limit))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "name": row['student_name'],
                "student_id": row['student_id'],
                "status": row['status'],
                "confidence": round(row['confidence'], 4),
                "time": row['created_at'],
                "remark": row['remark'] or ""
            })
        
        conn.close()
        return format_response(True, "获取成功", {"records": records})
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

# ==================== WebSocket事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f"✅ 客户端已连接: {request.sid}")
    emit('connection_response', {
        'status': 'connected', 
        'message': '已连接到实时签到服务',
        'sid': request.sid
    })

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f"❌ 客户端已断开: {request.sid}")

@socketio.on('ping')
def handle_ping(data):
    """处理心跳检测"""
    emit('pong', {'timestamp': datetime.now().isoformat()})

def broadcast_signin(student_name: str, confidence: float, status: str = "present", image_path: str = ""):
    """
    广播签到事件（供识别程序调用）
    这个函数应该被 realtime.py 或其他识别模块调用
    """
    try:
        # 记录到数据库
        db_record_attendance(
            name=student_name,
            course_date=date.today(),
            image_path=image_path,
            confidence=confidence,
            status=status
        )
        
        # 通过WebSocket广播
        socketio.emit('new_signin', {
            'student_name': student_name,
            'confidence': round(confidence, 4),
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'message': f'{student_name} 签到成功'
        })
        
        print(f"📢 广播签到事件: {student_name} (置信度: {confidence:.4f})")
    except Exception as e:
        print(f"❌ 广播签到失败: {e}")

# 提供给外部调用的接口
@app.route('/api/realtime/signin', methods=['POST'])
def receive_signin():
    """
    接收识别系统的签到通知
    Body参数：
        - student_name: 学生姓名
        - confidence: 置信度
        - status: 状态 (默认present)
        - image_path: 图片路径 (可选)
    """
    try:
        data = request.get_json()
        student_name = data.get('student_name')
        confidence = data.get('confidence', 0.0)
        status = data.get('status', 'present')
        image_path = data.get('image_path', '')
        
        if not student_name:
            return format_response(False, "缺少学生姓名", code=400)
        
        broadcast_signin(student_name, confidence, status, image_path)
        
        return format_response(True, "签到通知已发送")
    except Exception as e:
        return format_response(False, f"处理失败: {str(e)}", code=500)

# ==================== 导出功能 ====================

@app.route('/api/export/attendance', methods=['GET'])
def export_attendance():
    """导出考勤数据为CSV"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date', date.today().isoformat())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ar.student_name,
                s.student_id,
                ar.course_date,
                ar.status,
                ar.confidence,
                ar.created_at,
                ar.remark
            FROM attendance_records ar
            LEFT JOIN students s ON ar.student_name = s.name
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND ar.course_date >= ?"
            params.append(start_date)
        
        query += " AND ar.course_date <= ?"
        params.append(end_date)
        
        query += " ORDER BY ar.course_date DESC, ar.created_at DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        # 转换为CSV格式
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['学生姓名', '学号', '日期', '状态', '置信度', '签到时间', '备注'])
        
        for row in records:
            writer.writerow([
                row['student_name'],
                row['student_id'] or '',
                row['course_date'],
                '已到' if row['status'] == 'present' else '缺勤',
                f"{row['confidence']:.4f}",
                row['created_at'],
                row['remark'] or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return format_response(True, "导出成功", {
            "csv_content": csv_content,
            "filename": f"attendance_{start_date or 'all'}_{end_date}.csv"
        })
    except Exception as e:
        return format_response(False, f"导出失败: {str(e)}", code=500)

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return format_response(False, "接口不存在", code=404)

@app.errorhandler(500)
def internal_error(error):
    return format_response(False, "服务器内部错误", code=500)

# ==================== 启动服务 ====================

if __name__ == '__main__':
    print("🚀 Flask API 服务启动中...")
    print(f"📂 数据库路径: {DB_PATH}")
    print(f"📂 上传目录: {UPLOAD_FOLDER}")
    print("=" * 50)
    
    # 开发环境使用socketio.run，生产环境建议使用gunicorn + eventlet
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
