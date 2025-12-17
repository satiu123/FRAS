# 数据库表生成
# src/databaseBuild/db.py
import sqlite3
from pathlib import Path
from typing import Optional

# 数据库路径：data/attendance.db（相对于当前文件所在目录）
PROJECT_ROOT = Path(__file__).parent.parent.parent  # 上上层
DB_PATH = PROJECT_ROOT / "data" / "database" /"attendance.db"

def register_student_to_db(name: str, student_id: str = None):
    """将学生写入数据库"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO students (name, student_id) VALUES (?, ?)",
            (name, student_id)
        )
        conn.commit()
        print(f"[DB] 学生 {name} 已注册到数据库")
    except Exception as e:
        print(f"[DB ERROR] 注册失败: {e}")
    finally:
        conn.close()
        
def init_db():
    # 确保 data 目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        print(f"⚠️ 数据库已存在: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # 学生信息表：
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                student_id TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 考勤记录表：
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                course_date DATE NOT NULL,
                status TEXT DEFAULT 'absent',
                image_path TEXT,
                confidence REAL,
                remark TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_name, course_date)
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✅ 数据库创建成功: {DB_PATH.absolute()}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        raise

def get_student_id_by_name(name: str) -> Optional[int]:
    """根据姓名获取学生ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# 如果直接运行此脚本，则执行初始化
if __name__ == "__main__":
    init_db()