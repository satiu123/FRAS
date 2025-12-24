# 数据统计分析API路由
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
import sqlite3
from src.databaseBuild.db import DB_PATH

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

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

@statistics_bp.route('/overview', methods=['GET'])
def get_overview():
    """
    获取统计概览
    Query参数：
        - date: 日期 (默认今天)
    """
    try:
        target_date = request.args.get('date', date.today().isoformat())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总学生数
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        # 获取今日签到统计
        cursor.execute("""
            SELECT 
                COUNT(*) as signed_count,
                AVG(confidence) as avg_confidence
            FROM attendance_records 
            WHERE course_date = ? AND status = 'present'
        """, (target_date,))
        today_stats = cursor.fetchone()
        
        signed_count = today_stats['signed_count']
        absent_count = total_students - signed_count
        
        # 计算签到率
        sign_rate = round((signed_count / total_students * 100) if total_students > 0 else 0, 2)
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "date": target_date,
            "total_students": total_students,
            "signed_count": signed_count,
            "absent_count": absent_count,
            "sign_rate": sign_rate,
            "avg_confidence": round(today_stats['avg_confidence'] or 0, 4)
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@statistics_bp.route('/distribution', methods=['GET'])
def get_attendance_distribution():
    """
    获取出勤分布（用于饼图）
    Query参数：
        - date: 日期 (默认今天)
    """
    try:
        target_date = request.args.get('date', date.today().isoformat())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总学生数
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        # 获取各状态人数
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM attendance_records
            WHERE course_date = ?
            GROUP BY status
        """, (target_date,))
        
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # 计算各状态
        present_count = status_counts.get('present', 0)
        late_count = status_counts.get('late', 0)
        absent_count = total_students - present_count - late_count
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "date": target_date,
            "distribution": [
                {"name": "正常签到", "value": present_count, "status": "present"},
                {"name": "迟到", "value": late_count, "status": "late"},
                {"name": "缺勤", "value": absent_count, "status": "absent"}
            ]
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@statistics_bp.route('/trend', methods=['GET'])
def get_attendance_trend():
    """
    获取出勤率趋势（用于折线图）
    Query参数：
        - days: 天数 (默认30天)
    """
    try:
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取总学生数
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        # 获取每日签到统计
        cursor.execute("""
            SELECT 
                course_date,
                COUNT(*) as signed_count
            FROM attendance_records
            WHERE course_date BETWEEN ? AND ?
                AND status = 'present'
            GROUP BY course_date
            ORDER BY course_date ASC
        """, (start_date.isoformat(), end_date.isoformat()))
        
        daily_stats = {}
        for row in cursor.fetchall():
            daily_stats[row['course_date']] = row['signed_count']
        
        conn.close()
        
        # 构建完整的日期序列
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            signed_count = daily_stats.get(date_str, 0)
            sign_rate = round((signed_count / total_students * 100) if total_students > 0 else 0, 2)
            
            trend_data.append({
                "date": date_str,
                "signed_count": signed_count,
                "sign_rate": sign_rate
            })
            current_date += timedelta(days=1)
        
        return format_response(True, "获取成功", {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_students": total_students,
            "trend": trend_data
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@statistics_bp.route('/alerts', methods=['GET'])
def get_attendance_alerts():
    """
    获取考勤预警列表（频繁缺勤的学生）
    Query参数：
        - days: 统计天数 (默认30天)
        - threshold: 缺勤次数阈值 (默认3次)
    """
    try:
        days = request.args.get('days', 30, type=int)
        threshold = request.args.get('threshold', 3, type=int)
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有学生在统计期间内的总天数
        cursor.execute("""
            SELECT COUNT(DISTINCT course_date) as total_days
            FROM attendance_records
            WHERE course_date BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))
        total_days = cursor.fetchone()['total_days'] or 0
        
        # 获取每个学生的出勤情况
        cursor.execute("""
            SELECT 
                s.name,
                s.student_id,
                COUNT(DISTINCT ar.course_date) as attended_days
            FROM students s
            LEFT JOIN attendance_records ar 
                ON s.name = ar.student_name 
                AND ar.course_date BETWEEN ? AND ?
                AND ar.status = 'present'
            GROUP BY s.name, s.student_id
        """, (start_date.isoformat(), end_date.isoformat()))
        
        alerts = []
        for row in cursor.fetchall():
            attended_days = row['attended_days'] or 0
            absent_days = total_days - attended_days
            
            if absent_days >= threshold:
                attendance_rate = round((attended_days / total_days * 100) if total_days > 0 else 0, 2)
                alerts.append({
                    "name": row['name'],
                    "student_id": row['student_id'],
                    "absent_days": absent_days,
                    "attended_days": attended_days,
                    "total_days": total_days,
                    "attendance_rate": attendance_rate,
                    "alert_level": "严重" if absent_days >= threshold * 2 else "警告"
                })
        
        # 按缺勤天数排序
        alerts.sort(key=lambda x: x['absent_days'], reverse=True)
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "period": f"{start_date.isoformat()} 至 {end_date.isoformat()}",
            "threshold": threshold,
            "total_days": total_days,
            "alert_count": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@statistics_bp.route('/student/<student_name>', methods=['GET'])
def get_student_statistics(student_name):
    """
    获取单个学生的统计信息
    Query参数：
        - days: 统计天数 (默认30天)
    """
    try:
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取学生基本信息
        cursor.execute("SELECT * FROM students WHERE name = ?", (student_name,))
        student = cursor.fetchone()
        if not student:
            return format_response(False, "学生不存在", code=404)
        
        # 获取统计期间内的总天数
        cursor.execute("""
            SELECT COUNT(DISTINCT course_date) as total_days
            FROM attendance_records
            WHERE course_date BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))
        total_days = cursor.fetchone()['total_days'] or 0
        
        # 获取该学生的出勤记录
        cursor.execute("""
            SELECT 
                COUNT(*) as attended_days,
                AVG(confidence) as avg_confidence
            FROM attendance_records
            WHERE student_name = ?
                AND course_date BETWEEN ? AND ?
                AND status = 'present'
        """, (student_name, start_date.isoformat(), end_date.isoformat()))
        stats = cursor.fetchone()
        
        attended_days = stats['attended_days'] or 0
        absent_days = total_days - attended_days
        attendance_rate = round((attended_days / total_days * 100) if total_days > 0 else 0, 2)
        
        # 获取最近的签到记录
        cursor.execute("""
            SELECT 
                course_date,
                status,
                confidence,
                created_at,
                remark
            FROM attendance_records
            WHERE student_name = ?
                AND course_date BETWEEN ? AND ?
            ORDER BY course_date DESC
            LIMIT 10
        """, (student_name, start_date.isoformat(), end_date.isoformat()))
        
        recent_records = []
        for row in cursor.fetchall():
            recent_records.append({
                "date": row['course_date'],
                "status": row['status'],
                "confidence": round(row['confidence'], 4),
                "time": row['created_at'],
                "remark": row['remark'] or ""
            })
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "student": {
                "name": student['name'],
                "student_id": student['student_id'],
                "created_at": student['created_at']
            },
            "period": f"{start_date.isoformat()} 至 {end_date.isoformat()}",
            "statistics": {
                "total_days": total_days,
                "attended_days": attended_days,
                "absent_days": absent_days,
                "attendance_rate": attendance_rate,
                "avg_confidence": round(stats['avg_confidence'] or 0, 4)
            },
            "recent_records": recent_records
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)
