# 人脸识别接口
import sys
from pathlib import Path
import base64
from datetime import datetime, date

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from numpy.linalg import norm

from src import config
from src import utils
from src.attendance import record_attendance
from src.query import student_exists, already_signed_today

recognition_bp = Blueprint('recognition', __name__, url_prefix='/api/recognition')

# 初始化人脸识别模型（全局单例）
face_app = None

def get_face_app():
    """获取人脸识别应用实例（单例模式）"""
    global face_app
    if face_app is None:
        face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=0, det_size=(640, 640))
    return face_app

def compute_sim(feat1, feat2):
    """计算两个特征向量的相似度"""
    return np.dot(feat1, feat2) / (norm(feat1) * norm(feat2))

def recognize_faces(image):
    """
    识别图片中的人脸
    
    Args:
        image: OpenCV格式的图片 (numpy array)
    
    Returns:
        dict: {
            success: bool,
            faces: list,  # 识别结果列表
            annotated_image: numpy.ndarray  # 带框标注的图片
        }
    """
    # 加载已知人脸数据库
    known_faces = utils.load_database(config.DB_PATH)
    if not known_faces:
        return {'success': False, 'message': '人脸库为空，请先注册学生人脸'}
    
    # 获取人脸识别应用
    app = get_face_app()
    
    # 检测人脸
    faces = app.get(image)
    
    if len(faces) == 0:
        return {'success': False, 'message': '未检测到人脸，请确保照片清晰且包含正脸'}
    
    # 复制图片用于绘制
    annotated_img = image.copy()
    
    # 识别每个人脸
    results = []
    for face in faces:
        max_sim = -1
        best_name = "Unknown"
        
        # 与已知人脸比对
        for name, embedding in known_faces.items():
            sim = compute_sim(face.embedding, embedding)
            if sim > max_sim:
                max_sim = sim
                best_name = name
        
        # 判断是否匹配
        if max_sim >= config.MATCH_THRESHOLD:
            final_name = f"{best_name} ({max_sim:.2f})"
            color = config.COLOR_MATCH
            results.append({
                'name': best_name,
                'confidence': float(max_sim),
                'status': 'matched',
                'bbox': face.bbox.tolist()
            })
        else:
            final_name = f"Unknown ({max_sim:.2f})"
            color = config.COLOR_UNKNOWN
            results.append({
                'name': 'Unknown',
                'confidence': float(max_sim),
                'status': 'unknown',
                'bbox': face.bbox.tolist()
            })
        
        # 在图片上绘制人脸框和标签
        utils.draw_bbox(annotated_img, face.bbox, final_name, color)
    
    return {
        'success': True, 
        'faces': results,
        'annotated_image': annotated_img
    }


@recognition_bp.route('/upload-image', methods=['POST'])
def upload_image_signin():
    """
    上传图片进行人脸识别签到
    
    支持两种方式:
    1. multipart/form-data 文件上传
    2. JSON base64 编码图片
    
    Returns:
        JSON: {
            success: bool,
            message: str,
            data: {
                detected_faces: int,
                recognized: list,  # 识别成功的学生
                unknown: list,      # 未识别的人脸
                signed_in: list     # 成功签到的学生
            }
        }
    """
    try:
        image = None
        
        # 方式1: 文件上传
        if 'file' in request.files:
            file = request.files['file']
            if not file or file.filename == '':
                return jsonify({'success': False, 'message': '未选择文件'}), 400
            
            # 检查文件类型
            allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp'}
            filename = file.filename or ''
            if not ('.' in filename and 
                    filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
            
            # 读取图片
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # 方式2: Base64编码
        elif request.is_json:
            data = request.get_json()
            if 'image' not in data:
                return jsonify({'success': False, 'message': '缺少image字段'}), 400
            
            # 解码base64图片
            try:
                img_data = data['image']
                # 移除data:image/xxx;base64,前缀（如果有）
                if ',' in img_data:
                    img_data = img_data.split(',')[1]
                
                img_bytes = base64.b64decode(img_data)
                nparr = np.frombuffer(img_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception as e:
                return jsonify({'success': False, 'message': f'图片解码失败: {str(e)}'}), 400
        else:
            return jsonify({'success': False, 'message': '请上传图片文件或提供base64编码'}), 400
        
        if image is None:
            return jsonify({'success': False, 'message': '图片读取失败'}), 400
        
        # 识别人脸
        result = recognize_faces(image)
        
        if not result['success']:
            return jsonify(result), 400
        
        faces = result['faces']
        annotated_image = result['annotated_image']
        
        # 将标注后的图片编码为base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{img_base64}"
        
        # 分类识别结果
        recognized = [f for f in faces if f['status'] == 'matched']
        unknown = [f for f in faces if f['status'] == 'unknown']
        
        # 自动签到（只签到识别成功的）
        signed_in = []
        today = date.today()
        
        for face in recognized:
            name = face['name']
            confidence = face['confidence']
            
            # 检查学生是否存在
            if not student_exists(name):
                continue
            
            # 检查今天是否已签到
            if already_signed_today(name, today):
                face['already_signed'] = True
                continue
            
            # 记录签到
            success = record_attendance(
                name=name,
                course_date=today,
                image_path='upload',
                confidence=confidence,
                status='present',
                remark='上传图片识别'
            )
            if success:
                signed_in.append({
                    'name': name,
                    'confidence': confidence,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                face['signed_in'] = True
        
        return jsonify({
            'success': True,
            'message': f'检测到 {len(faces)} 个人脸，识别成功 {len(recognized)} 人，签到成功 {len(signed_in)} 人',
            'data': {
                'detected_faces': len(faces),
                'recognized': recognized,
                'unknown': unknown,
                'signed_in': signed_in,
                'annotated_image': img_data_url  # 返回带框标注的图片
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理失败: {str(e)}'
        }), 500


@recognition_bp.route('/recognize-only', methods=['POST'])
def recognize_only():
    """
    仅识别图片中的人脸，不进行签到
    
    用于预览识别结果
    """
    try:
        image = None
        
        # 处理文件上传或base64
        if 'file' in request.files:
            file = request.files['file']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        elif request.is_json:
            data = request.get_json()
            img_data = data.get('image', '')
            if ',' in img_data:
                img_data = img_data.split(',')[1]
            img_bytes = base64.b64decode(img_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': '图片读取失败'}), 400
        
        # 识别人脸
        result = recognize_faces(image)
        
        if not result['success']:
            return jsonify(result), 400
        
        faces = result['faces']
        annotated_image = result['annotated_image']
        
        # 将标注后的图片编码为base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{img_base64}"
        
        recognized = [f for f in faces if f['status'] == 'matched']
        unknown = [f for f in faces if f['status'] == 'unknown']
        
        return jsonify({
            'success': True,
            'message': f'检测到 {len(faces)} 个人脸，识别成功 {len(recognized)} 人',
            'data': {
                'detected_faces': len(faces),
                'recognized': recognized,
                'unknown': unknown,
                'annotated_image': img_data_url  # 返回带框标注的图片
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
