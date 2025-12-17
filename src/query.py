# 签到记录查询 + 手动补签功能

import sys
from pathlib import Path
from datetime import date
import sqlite3
import argparse
from tabulate import tabulate

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.databaseBuild.db import DB_PATH


def student_exists(name: str) -> bool:
    """检查学生是否已注册"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM students WHERE name = ?", (name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def already_signed_today(name: str, course_date: date) -> bool:
    """检查该学生当天是否已签到"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM attendance_records WHERE student_name = ? AND course_date = ?",
        (name, course_date.isoformat())
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def manual_sign_in(student_name: str, course_date: date, remark: str = "补签"):
    """执行手动补签（写入数据库）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO attendance_records 
            (student_name, course_date, status, image_path, confidence, remark)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_name, course_date.isoformat(), "present", "", 0.0, remark))
        conn.commit()
        print(f"✅ {student_name} 补签成功 ({course_date})")
        return True
    except Exception as e:
        print(f"❌ 补签失败: {e}")
        return False
    finally:
        conn.close()


def query_attendance(student_name: str = None, course_date: date = None) -> list:
    """
    查询考勤记录
    
    Args:
        student_name: 学生姓名（可选）
        course_date: 日期（默认今天）
    
    Returns:
        列表 of dict: [{'name', 'date', 'status', 'confidence', 'remark', 'time'}]
    """
    if course_date is None:
        course_date = date.today()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = '''
        SELECT 
            student_name AS name,
            course_date AS date,
            status,
            confidence,
            remark,
            created_at AS time
        FROM attendance_records
        WHERE 1=1
    '''
    params = []

    if student_name:
        query += " AND student_name = ?"
        params.append(student_name)
    
    query += " AND course_date = ?"
    params.append(course_date.isoformat())

    query += " ORDER BY time DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def print_results(results: list, student_name: str = None, course_date: date = None):
    if not results:
        if student_name:
            print(f"❌ {student_name} 在 {course_date} 无签到记录")
        else:
            print(f"❌ {course_date} 无人签到")
        return

    table = []
    for r in results:
        table.append([
            r['name'],
            r['date'],
            r['status'].upper(),
            f"{r['confidence']:.2f}" if r['confidence'] else "N/A",
            r['remark'] or "—",
            r['time'].split(' ')[1][:8]
        ])

    headers = ["姓名", "日期", "状态", "置信度", "备注", "时间"]
    title = f"📅 考勤查询结果（{course_date}）"
    if student_name:
        title += f" - {student_name}"

    print(f"\n{title}")
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="center"))


def main():
    parser = argparse.ArgumentParser(description="🔍 考勤状态查询与手动补签工具")
    parser.add_argument("--name", "-n", type=str, help="学生姓名（用于查询或补签）")
    parser.add_argument("--date", "-d", type=str, default=str(date.today()),
                        help="日期，格式 YYYY-MM-DD（默认今天）")
    parser.add_argument("--csv", action="store_true", help="导出查询结果为 CSV")
    parser.add_argument("--sign", action="store_true", help="手动补签（需配合 --name 使用）")

    args = parser.parse_args()

    try:
        q_date = date.fromisoformat(args.date)
    except ValueError:
        print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
        return

    # ========== 新增：手动补签逻辑 ==========
    if args.sign:
        if not args.name:
            print("❌ 补签必须指定学生姓名（使用 --name 或 -n）")
            return

        name = args.name

        # 检查学生是否存在
        if not student_exists(name):
            print(f"❌ 无法补签：学生 '{name}' 未注册，请先录入人脸信息。")
            return

        # 检查是否已签到
        if already_signed_today(name, q_date):
            print(f"❌ 无法补签：'{name}' 在 {q_date} 已有签到记录。")
            return

        # 执行补签
        success = manual_sign_in(name, q_date, remark="补签")
        if success:
            # 补签后自动查询显示
            results = query_attendance(student_name=name, course_date=q_date)
            print_results(results, student_name=name, course_date=q_date)
        return

    # ========== 原有：查询逻辑 ==========
    results = query_attendance(student_name=args.name, course_date=q_date)
    print_results(results, student_name=args.name, course_date=q_date)

    if args.csv and results:
        import csv
        from pathlib import Path
        export_dir = project_root / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        filename = f"attendance_{q_date.isoformat()}"
        if args.name:
            filename += f"_{args.name}"
        filename += ".csv"
        csv_path = export_dir / filename

        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            for r in results:
                writer.writerow(r)

        print(f"\n✅ 已导出 CSV: {csv_path.absolute()}")


if __name__ == "__main__":
    main()