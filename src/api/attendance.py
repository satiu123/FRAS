# 签到记录管理API路由
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
import sqlite3

from src.databaseBuild.db import DB_PATH
from src.attendance import record_attendance
from src.query import manual_sign_in, student_exists, already_signed_today

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

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

@attendance_bp.route('/records', methods=['GET'])
def get_attendance_records():
    """
    获取签到记录列表（支持筛选）
    Query参数：
        - date: 日期 (默认今天)
        - start_date: 开始日期
        - end_date: 结束日期
        - student_name: 学生姓名
        - status: 签到状态 (present/late/absent)
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20)
    """
    try:
        # 获取查询参数
        target_date = request.args.get('date')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date', date.today().isoformat())
        student_name = request.args.get('student_name')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        base_query = """
            FROM attendance_records ar
            LEFT JOIN students s ON ar.student_name = s.name
            WHERE 1=1
        """
        params = []
        
        # 日期筛选
        if target_date:
            base_query += " AND ar.course_date = ?"
            params.append(target_date)
        else:
            if start_date:
                base_query += " AND ar.course_date >= ?"
                params.append(start_date)
            base_query += " AND ar.course_date <= ?"
            params.append(end_date)
        
        # 学生筛选
        if student_name:
            base_query += " AND ar.student_name LIKE ?"
            params.append(f"%{student_name}%")
        
        # 状态筛选
        if status:
            base_query += " AND ar.status = ?"
            params.append(status)
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) as total {base_query}", params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        query = f"""
            SELECT 
                ar.id,
                ar.student_name,
                s.student_id,
                ar.course_date,
                ar.status,
                ar.confidence,
                ar.created_at,
                ar.remark,
                ar.image_path
            {base_query}
            ORDER BY ar.course_date DESC, ar.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row['id'],
                "student_name": row['student_name'],
                "student_id": row['student_id'],
                "course_date": row['course_date'],
                "status": row['status'],
                "status_text": {
                    "present": "已到",
                    "late": "迟到",
                    "absent": "缺勤"
                }.get(row['status'], row['status']),
                "confidence": round(row['confidence'], 4),
                "created_at": row['created_at'],
                "remark": row['remark'] or "",
                "has_image": bool(row['image_path'])
            })
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "records": records
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@attendance_bp.route('/records/<int:record_id>', methods=['GET'])
def get_attendance_record(record_id):
    """获取单条签到记录详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ar.*,
                s.student_id
            FROM attendance_records ar
            LEFT JOIN students s ON ar.student_name = s.name
            WHERE ar.id = ?
        """, (record_id,))
        
        record = cursor.fetchone()
        conn.close()
        
        if not record:
            return format_response(False, "记录不存在", code=404)
        
        return format_response(True, "获取成功", {
            "id": record['id'],
            "student_name": record['student_name'],
            "student_id": record['student_id'],
            "course_date": record['course_date'],
            "status": record['status'],
            "confidence": round(record['confidence'], 4),
            "created_at": record['created_at'],
            "remark": record['remark'] or "",
            "image_path": record['image_path'] or ""
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@attendance_bp.route('/manual-signin', methods=['POST'])
def manual_signin():
    """
    手动补签
    Body参数：
        - student_name: 学生姓名 (必填)
        - course_date: 日期 (可选，默认今天)
        - remark: 备注 (可选，默认"补签")
    """
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        course_date_str = data.get('course_date')
        remark = data.get('remark', '补签')
        
        if not student_name:
            return format_response(False, "学生姓名不能为空", code=400)
        
        # 检查学生是否存在
        if not student_exists(student_name):
            return format_response(False, f"学生 {student_name} 不存在，请先注册", code=400)
        
        # 处理日期
        if course_date_str:
            try:
                course_date = date.fromisoformat(course_date_str)
            except ValueError:
                return format_response(False, "日期格式错误，应为 YYYY-MM-DD", code=400)
        else:
            course_date = date.today()
        
        # 检查是否已签到
        if already_signed_today(student_name, course_date):
            return format_response(False, f"{student_name} 在 {course_date} 已经签到过了", code=400)
        
        # 执行补签
        success = manual_sign_in(student_name, course_date, remark)
        
        if success:
            return format_response(True, f"{student_name} 补签成功", {
                "student_name": student_name,
                "course_date": course_date.isoformat(),
                "remark": remark
            })
        else:
            return format_response(False, "补签失败", code=500)
    except Exception as e:
        return format_response(False, f"补签失败: {str(e)}", code=500)

@attendance_bp.route('/batch-signin', methods=['POST'])
def batch_manual_signin():
    """
    批量补签
    Body参数：
        - students: 学生姓名列表 ["张三", "李四", ...]
        - course_date: 日期 (可选，默认今天)
        - remark: 备注 (可选，默认"批量补签")
    """
    try:
        data = request.get_json()
        students = data.get('students', [])
        course_date_str = data.get('course_date')
        remark = data.get('remark', '批量补签')
        
        if not students:
            return format_response(False, "学生列表不能为空", code=400)
        
        # 处理日期
        if course_date_str:
            try:
                course_date = date.fromisoformat(course_date_str)
            except ValueError:
                return format_response(False, "日期格式错误，应为 YYYY-MM-DD", code=400)
        else:
            course_date = date.today()
        
        success_list = []
        failed_list = []
        
        for student_name in students:
            student_name = student_name.strip()
            
            # 检查学生是否存在
            if not student_exists(student_name):
                failed_list.append({"name": student_name, "reason": "学生不存在"})
                continue
            
            # 检查是否已签到
            if already_signed_today(student_name, course_date):
                failed_list.append({"name": student_name, "reason": "已经签到过"})
                continue
            
            # 执行补签
            if manual_sign_in(student_name, course_date, remark):
                success_list.append(student_name)
            else:
                failed_list.append({"name": student_name, "reason": "补签失败"})
        
        return format_response(True, f"批量补签完成，成功 {len(success_list)} 个", {
            "success_count": len(success_list),
            "success_list": success_list,
            "failed_count": len(failed_list),
            "failed_list": failed_list,
            "course_date": course_date.isoformat()
        })
    except Exception as e:
        return format_response(False, f"批量补签失败: {str(e)}", code=500)

@attendance_bp.route('/records/<int:record_id>', methods=['PUT'])
def update_attendance_record(record_id):
    """
    更新签到记录
    Body参数：
        - status: 状态 (present/late/absent)
        - remark: 备注
    """
    try:
        data = request.get_json()
        status = data.get('status')
        remark = data.get('remark')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查记录是否存在
        cursor.execute("SELECT * FROM attendance_records WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        if not record:
            conn.close()
            return format_response(False, "记录不存在", code=404)
        
        # 构建更新语句
        update_fields = []
        params = []
        
        if status:
            if status not in ['present', 'late', 'absent']:
                conn.close()
                return format_response(False, "状态值无效", code=400)
            update_fields.append("status = ?")
            params.append(status)
        
        if remark is not None:
            update_fields.append("remark = ?")
            params.append(remark)
        
        if not update_fields:
            conn.close()
            return format_response(False, "没有需要更新的字段", code=400)
        
        params.append(record_id)
        cursor.execute(f"""
            UPDATE attendance_records
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, params)
        conn.commit()
        conn.close()
        
        return format_response(True, "更新成功")
    except Exception as e:
        return format_response(False, f"更新失败: {str(e)}", code=500)

@attendance_bp.route('/records/<int:record_id>', methods=['DELETE'])
def delete_attendance_record(record_id):
    """删除签到记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查记录是否存在
        cursor.execute("SELECT * FROM attendance_records WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        if not record:
            conn.close()
            return format_response(False, "记录不存在", code=404)
        
        # 删除记录
        cursor.execute("DELETE FROM attendance_records WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        
        return format_response(True, "删除成功")
    except Exception as e:
        return format_response(False, f"删除失败: {str(e)}", code=500)

@attendance_bp.route('/summary', methods=['GET'])
def get_attendance_summary():
    """
    获取签到汇总（按日期和学生统计）
    Query参数：
        - start_date: 开始日期
        - end_date: 结束日期 (默认今天)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date', date.today().isoformat())
        
        if not start_date:
            # 默认最近30天
            start_date = (date.today() - timedelta(days=30)).isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有学生
        cursor.execute("SELECT name, student_id FROM students ORDER BY name")
        students = cursor.fetchall()
        
        # 获取日期范围内的所有日期（有签到记录的）
        cursor.execute("""
            SELECT DISTINCT course_date
            FROM attendance_records
            WHERE course_date BETWEEN ? AND ?
            ORDER BY course_date DESC
        """, (start_date, end_date))
        dates = [row['course_date'] for row in cursor.fetchall()]
        
        # 获取签到记录
        cursor.execute("""
            SELECT student_name, course_date, status
            FROM attendance_records
            WHERE course_date BETWEEN ? AND ?
        """, (start_date, end_date))
        
        # 构建签到矩阵
        attendance_map = {}
        for row in cursor.fetchall():
            key = f"{row['student_name']}_{row['course_date']}"
            attendance_map[key] = row['status']
        
        conn.close()
        
        # 构建汇总数据
        summary = []
        for student in students:
            student_data = {
                "name": student['name'],
                "student_id": student['student_id'],
                "records": []
            }
            
            present_count = 0
            late_count = 0
            absent_count = 0
            
            for date_str in dates:
                key = f"{student['name']}_{date_str}"
                status = attendance_map.get(key, 'absent')
                
                student_data["records"].append({
                    "date": date_str,
                    "status": status
                })
                
                if status == 'present':
                    present_count += 1
                elif status == 'late':
                    late_count += 1
                else:
                    absent_count += 1
            
            total_days = len(dates)
            student_data["statistics"] = {
                "total_days": total_days,
                "present_count": present_count,
                "late_count": late_count,
                "absent_count": absent_count,
                "attendance_rate": round((present_count / total_days * 100) if total_days > 0 else 0, 2)
            }
            
            summary.append(student_data)
        
        return format_response(True, "获取成功", {
            "start_date": start_date,
            "end_date": end_date,
            "dates": dates,
            "summary": summary
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@attendance_bp.route('/absent-list', methods=['GET'])
def get_absent_list():
    """
    获取缺勤名单
    Query参数：
        - date: 日期 (默认今天)
    """
    try:
        target_date = request.args.get('date', date.today().isoformat())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有学生
        cursor.execute("SELECT name, student_id FROM students")
        all_students = {row['name']: row['student_id'] for row in cursor.fetchall()}
        
        # 获取已签到学生
        cursor.execute("""
            SELECT student_name
            FROM attendance_records
            WHERE course_date = ? AND status IN ('present', 'late')
        """, (target_date,))
        signed_students = {row['student_name'] for row in cursor.fetchall()}
        
        conn.close()
        
        # 计算缺勤名单
        absent_list = []
        for name, student_id in all_students.items():
            if name not in signed_students:
                absent_list.append({
                    "name": name,
                    "student_id": student_id
                })
        
        return format_response(True, "获取成功", {
            "date": target_date,
            "total_students": len(all_students),
            "signed_count": len(signed_students),
            "absent_count": len(absent_list),
            "absent_list": absent_list
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)
