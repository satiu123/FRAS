# 考勤记录相关函数
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from src.databaseBuild.db import DB_PATH, register_student_to_db, get_student_id_by_name

def record_attendance(
    name: str,
    course_date: date,
    image_path: str,
    confidence: float,
    status: str = "present",
    remark: str = ""
):
    
    # from src.databaseBuild.db import get_student_id_by_name
    # if get_student_id_by_name(name) is None:
    #     print(f"❌ 未知学生: {name}，请先注册")
    #     return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO attendance_records 
            (student_name, course_date, status, image_path, confidence, remark)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_name, course_date) DO UPDATE SET
                status = excluded.status,
                image_path = excluded.image_path,
                confidence = excluded.confidence,
                remark = excluded.remark,
                created_at = CURRENT_TIMESTAMP
        ''', (name, course_date.isoformat(), status, image_path, confidence, remark))
        conn.commit()
        print(f"✅ {name} 签到成功 ({course_date})")
        return True
    except Exception as e:
        print(f"❌ 签到失败: {e}")
        return False
    finally:
        conn.close()

def manual_sign_in(student_name: str, course_date: date = None, remark: str = "补签"):
    """手动补签（管理员用）"""
    if course_date is None:
        course_date = date.today()
    # 补签时无图像和置信度
    return record_attendance(student_name, course_date, "", 0.0, "present", remark)

def query_attendance(student_name: Optional[str] = None, course_date: Optional[date] = None) -> List[dict]:
    """查询签到状态"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 只从 attendance_records 查询（因为学生信息已冗余在 student_name 中）
    query = '''
        SELECT 
            student_name AS name,
            '' AS student_id,          -- 如果需要，可后续通过 name 查 students 表补全
            course_date,
            status,
            remark,
            created_at
        FROM attendance_records
        WHERE 1=1
    '''
    params = []

    if student_name:
        query += " AND student_name = ?"
        params.append(student_name)
    
    if course_date:
        query += " AND course_date = ?"
        params.append(course_date.isoformat())

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]