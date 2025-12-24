# 学生信息与人脸库管理API路由
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import sqlite3
import os
import base64
from datetime import datetime
from PIL import Image
import io

from src.databaseBuild.db import DB_PATH, register_student_to_db
from src.register import register_faces

students_bp = Blueprint('students', __name__, url_prefix='/api/students')

# 配置路径
KNOWN_FACES_FOLDER = project_root / "data" / "train"
UPLOAD_FOLDER = project_root / "data" / "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

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

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@students_bp.route('/', methods=['GET'])
def get_students_list():
    """
    获取学生列表
    Query参数：
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20)
        - search: 搜索关键词（姓名或学号）
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        base_query = "FROM students WHERE 1=1"
        params = []
        
        if search:
            base_query += " AND (name LIKE ? OR student_id LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) as total {base_query}", params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        query = f"""
            SELECT 
                id,
                name,
                student_id,
                created_at
            {base_query}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        cursor.execute(query, params)
        
        students = []
        for row in cursor.fetchall():
            # 检查是否有人脸数据
            student_face_dir = KNOWN_FACES_FOLDER / row['name']
            has_face = student_face_dir.exists() and any(student_face_dir.iterdir())
            
            # 获取人脸图片数量
            face_count = 0
            if has_face:
                face_count = len([f for f in student_face_dir.iterdir() 
                                 if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])
            
            students.append({
                "id": row['id'],
                "name": row['name'],
                "student_id": row['student_id'],
                "created_at": row['created_at'],
                "has_face": has_face,
                "face_count": face_count,
                "status": "已激活" if has_face else "未录入"
            })
        
        conn.close()
        
        return format_response(True, "获取成功", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "students": students
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@students_bp.route('/<int:student_id>', methods=['GET'])
def get_student_detail(student_id):
    """获取单个学生详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if not student:
            return format_response(False, "学生不存在", code=404)
        
        # 获取人脸图片信息
        student_face_dir = KNOWN_FACES_FOLDER / student['name']
        face_images = []
        if student_face_dir.exists():
            for img_file in student_face_dir.iterdir():
                if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                    face_images.append({
                        "filename": img_file.name,
                        "path": str(img_file.relative_to(project_root)),
                        "size": img_file.stat().st_size,
                        "created_at": datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                    })
        
        return format_response(True, "获取成功", {
            "id": student['id'],
            "name": student['name'],
            "student_id": student['student_id'],
            "created_at": student['created_at'],
            "face_images": face_images,
            "has_face": len(face_images) > 0,
            "status": "已激活" if len(face_images) > 0 else "未录入"
        })
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@students_bp.route('/', methods=['POST'])
def create_student():
    """
    创建新学生
    Body参数：
        - name: 姓名 (必填)
        - student_id: 学号 (可选)
    """
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        student_id = data.get('student_id', '').strip()
        
        if not name:
            return format_response(False, "姓名不能为空", code=400)
        
        # 注册到数据库
        register_student_to_db(name, student_id if student_id else None)
        
        # 创建人脸文件夹
        student_face_dir = KNOWN_FACES_FOLDER / name
        student_face_dir.mkdir(parents=True, exist_ok=True)
        
        return format_response(True, f"学生 {name} 创建成功", {
            "name": name,
            "student_id": student_id
        })
    except Exception as e:
        return format_response(False, f"创建失败: {str(e)}", code=500)

@students_bp.route('/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """
    更新学生信息
    Body参数：
        - name: 姓名
        - student_id: 学号
    """
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        new_student_id = data.get('student_id', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查学生是否存在
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            conn.close()
            return format_response(False, "学生不存在", code=404)
        
        old_name = student['name']
        
        # 更新数据库
        update_fields = []
        params = []
        
        if name and name != old_name:
            update_fields.append("name = ?")
            params.append(name)
        
        if new_student_id:
            update_fields.append("student_id = ?")
            params.append(new_student_id)
        
        if update_fields:
            params.append(student_id)
            cursor.execute(f"""
                UPDATE students 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
            conn.commit()
            
            # 如果姓名改变，需要重命名人脸文件夹
            if name and name != old_name:
                old_face_dir = KNOWN_FACES_FOLDER / old_name
                new_face_dir = KNOWN_FACES_FOLDER / name
                if old_face_dir.exists():
                    old_face_dir.rename(new_face_dir)
        
        conn.close()
        
        return format_response(True, "更新成功")
    except Exception as e:
        return format_response(False, f"更新失败: {str(e)}", code=500)

@students_bp.route('/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """删除学生（包括人脸数据）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取学生信息
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            conn.close()
            return format_response(False, "学生不存在", code=404)
        
        student_name = student['name']
        
        # 删除数据库记录
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        cursor.execute("DELETE FROM attendance_records WHERE student_name = ?", (student_name,))
        conn.commit()
        conn.close()
        
        # 删除人脸文件夹
        student_face_dir = KNOWN_FACES_FOLDER / student_name
        if student_face_dir.exists():
            import shutil
            shutil.rmtree(student_face_dir)
        
        return format_response(True, f"学生 {student_name} 已删除")
    except Exception as e:
        return format_response(False, f"删除失败: {str(e)}", code=500)

@students_bp.route('/<int:student_id>/face', methods=['POST'])
def upload_face_image(student_id):
    """
    上传学生人脸图片
    支持两种方式：
    1. multipart/form-data: file字段
    2. application/json: base64编码的图片数据
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if not student:
            return format_response(False, "学生不存在", code=404)
        
        student_name = student['name']
        student_face_dir = KNOWN_FACES_FOLDER / student_name
        student_face_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return format_response(False, "未选择文件", code=400)
            
            if not allowed_file(file.filename):
                return format_response(False, "不支持的文件格式", code=400)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = secure_filename(f"{student_name}_{timestamp}.jpg")
            filepath = student_face_dir / filename
            
            file.save(str(filepath))
            
        # 处理base64编码的图片
        elif request.is_json:
            data = request.get_json()
            image_data = data.get('image')
            if not image_data:
                return format_response(False, "缺少图片数据", code=400)
            
            # 解码base64
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 保存图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{student_name}_{timestamp}.jpg"
            filepath = student_face_dir / filename
            image.save(str(filepath))
        else:
            return format_response(False, "未找到图片数据", code=400)
        
        # 上传成功后自动更新该学生的人脸数据库（增量更新）
        try:
            register_faces(student_names=student_name)
            print(f"✓ Updated face database for {student_name}")
        except Exception as e:
            print(f"Warning: Failed to update face database for {student_name}: {e}")
        
        return format_response(True, "人脸图片上传成功", {
            "filename": filename,
            "path": str(filepath.relative_to(project_root))
        })
    except Exception as e:
        return format_response(False, f"上传失败: {str(e)}", code=500)

@students_bp.route('/<int:student_id>/face/<filename>', methods=['DELETE'])
def delete_face_image(student_id, filename):
    """删除指定的人脸图片"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if not student:
            return format_response(False, "学生不存在", code=404)
        
        student_name = student['name']
        student_face_dir = KNOWN_FACES_FOLDER / student_name
        filepath = student_face_dir / secure_filename(filename)
        
        if not filepath.exists():
            return format_response(False, "图片不存在", code=404)
        
        filepath.unlink()
        
        # 删除成功后自动更新该学生的人脸数据库（增量更新）
        try:
            register_faces(student_names=student_name)
            print(f"✓ Updated face database for {student_name}")
        except Exception as e:
            print(f"Warning: Failed to update face database for {student_name}: {e}")
        
        return format_response(True, "图片已删除")
    except Exception as e:
        return format_response(False, f"删除失败: {str(e)}", code=500)

@students_bp.route('/<int:student_id>/face/<filename>', methods=['GET'])
def get_face_image(student_id, filename):
    """获取人脸图片"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if not student:
            return format_response(False, "学生不存在", code=404)
        
        student_name = student['name']
        student_face_dir = KNOWN_FACES_FOLDER / student_name
        filepath = student_face_dir / secure_filename(filename)
        
        if not filepath.exists():
            return format_response(False, "图片不存在", code=404)
        
        return send_file(str(filepath), mimetype='image/jpeg')
    except Exception as e:
        return format_response(False, f"获取失败: {str(e)}", code=500)

@students_bp.route('/update-face-database', methods=['POST'])
def update_face_database():
    """
    手动更新人脸数据库 (students.pkl)
    扫描所有学生的人脸图片并重新生成特征数据库
    """
    try:
        register_faces()
        return format_response(True, "人脸数据库已更新")
    except Exception as e:
        return format_response(False, f"更新失败: {str(e)}", code=500)

@students_bp.route('/batch', methods=['POST'])
def batch_create_students():
    """
    批量创建学生
    Body参数：
        - students: 学生列表 [{"name": "张三", "student_id": "001"}, ...]
    """
    try:
        data = request.get_json()
        students_data = data.get('students', [])
        
        if not students_data:
            return format_response(False, "学生列表不能为空", code=400)
        
        success_count = 0
        failed_list = []
        
        for student in students_data:
            name = student.get('name', '').strip()
            student_id = student.get('student_id', '').strip()
            
            if not name:
                failed_list.append({"student": student, "reason": "姓名为空"})
                continue
            
            try:
                register_student_to_db(name, student_id if student_id else None)
                student_face_dir = KNOWN_FACES_FOLDER / name
                student_face_dir.mkdir(parents=True, exist_ok=True)
                success_count += 1
            except Exception as e:
                failed_list.append({"student": student, "reason": str(e)})
        
        return format_response(True, f"批量创建完成，成功 {success_count} 个", {
            "success_count": success_count,
            "failed_count": len(failed_list),
            "failed_list": failed_list
        })
    except Exception as e:
        return format_response(False, f"批量创建失败: {str(e)}", code=500)
