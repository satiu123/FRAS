# 实时人脸识别API
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Blueprint, request, jsonify, Response
import cv2
import numpy as np
import pickle
from datetime import datetime, timedelta
import base64
import time

from src.config import SIMILARITY_THRESHOLD, CAPTURE_DIR
from src.realtime_utils import draw_faces_with_names
from src.attendance import record_attendance
from insightface.app import FaceAnalysis
import os

realtime_recognition_bp = Blueprint('realtime_recognition', __name__, url_prefix='/api/realtime')

# 全局变量
face_app = None
known_names = []
known_feats = None
last_attendance = {}
camera_active = False
camera_instance = None

def initialize_face_app():
    """初始化人脸识别模型"""
    global face_app
    if face_app is None:
        face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=0, det_size=(320, 320))
    return face_app

def load_known_faces():
    """加载已注册的学生特征"""
    global known_names, known_feats
    pkl_path = project_root / "data" / "students.pkl"
    if not pkl_path.exists():
        return False, "未找到 students.pkl，请先注册学生"
    
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        known_names = list(data.keys())
        known_feats = np.array(list(data.values()))
        return True, f"成功加载 {len(known_names)} 名学生"
    except Exception as e:
        return False, f"加载失败: {str(e)}"

@realtime_recognition_bp.route('/start-camera', methods=['POST'])
def start_camera():
    """启动摄像头"""
    global camera_active, camera_instance
    
    try:
        print("📷 收到启动摄像头请求")
        
        if camera_active:
            print("⚠️ 摄像头已在运行")
            return jsonify({"success": False, "message": "摄像头已在运行"}), 400
        
        # 加载人脸数据库
        print("📚 正在加载人脸数据库...")
        success, message = load_known_faces()
        print(f"📚 加载结果: {message}")
        if not success:
            return jsonify({"success": False, "message": message}), 400
        
        # 初始化模型
        print("🤖 正在初始化人脸识别模型...")
        initialize_face_app()
        print("✓ 模型初始化完成")
        
        # 打开摄像头
        data = request.get_json() if request.is_json else {}
        camera_index = data.get('camera_index', 0) if data else 0
        print(f"📹 正在打开摄像头 (索引: {camera_index})...")
        camera_instance = cv2.VideoCapture(camera_index)
        
        if not camera_instance.isOpened():
            print("❌ 无法打开摄像头")
            return jsonify({"success": False, "message": "无法打开摄像头"}), 500
        
        camera_active = True
        print(f"✓ 摄像头已启动，共加载 {len(known_names)} 名学生")
        return jsonify({
            "success": True,
            "message": "摄像头已启动",
            "students_count": len(known_names)
        })
    except Exception as e:
        import traceback
        print(f"❌ 启动摄像头失败: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"启动失败: {str(e)}"}), 500

@realtime_recognition_bp.route('/stop-camera', methods=['POST'])
def stop_camera():
    """停止摄像头"""
    global camera_active, camera_instance
    
    try:
        if camera_instance:
            camera_instance.release()
            camera_instance = None
        camera_active = False
        return jsonify({"success": True, "message": "摄像头已停止"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@realtime_recognition_bp.route('/camera-status', methods=['GET'])
def camera_status():
    """获取摄像头状态"""
    return jsonify({
        "success": True,
        "active": camera_active,
        "students_count": len(known_names)
    })

@realtime_recognition_bp.route('/process-frame', methods=['POST'])
def process_frame():
    """处理单帧图像并返回识别结果"""
    global last_attendance
    
    try:
        # 获取base64图像
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({"success": False, "message": "缺少图像数据"}), 400
        
        # 解码base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"success": False, "message": "无效的图像数据"}), 400
        
        # 确保模型和数据已加载
        if face_app is None:
            initialize_face_app()
        
        if len(known_names) == 0:
            success, message = load_known_faces()
            if not success:
                return jsonify({"success": False, "message": message}), 400
        
        # 检测人脸
        if face_app is None or known_feats is None or len(known_names) == 0:
            return jsonify({"success": False, "message": "人脸识别系统未初始化"}), 400
            
        faces = face_app.get(frame)
        current_time = datetime.now()
        
        results = []
        should_record = data.get('record', True)  # 是否记录考勤
        
        for face in faces:
            feat = face.normed_embedding
            sims = np.dot(known_feats, feat)
            max_idx = np.argmax(sims)
            max_sim = float(sims[max_idx])
            name = known_names[max_idx]
            
            recognized = max_sim >= SIMILARITY_THRESHOLD
            recorded = False
            
            if recognized and should_record:
                # 检查冷却期（5分钟）
                can_record = True
                if name in last_attendance:
                    if current_time - last_attendance[name] < timedelta(minutes=5):
                        can_record = False
                
                if can_record:
                    last_attendance[name] = current_time
                    
                    # 保存截图
                    os.makedirs(CAPTURE_DIR, exist_ok=True)
                    timestamp = current_time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{name}_{timestamp}.jpg"
                    capture_path = os.path.join(CAPTURE_DIR, filename)
                    
                    bbox = face.bbox.astype(int)
                    x1, y1, x2, y2 = bbox
                    face_img = frame[y1:y2, x1:x2]
                    if face_img.size > 0:
                        cv2.imwrite(capture_path, face_img)
                    
                    # 记录考勤
                    record_attendance(
                        name=name,
                        course_date=current_time.date(),
                        image_path=capture_path,
                        confidence=max_sim,
                        status="present",
                        remark="实时摄像头签到"
                    )
                    recorded = True
                    
                    # 广播WebSocket事件（在应用上下文中）
                    try:
                        from src.api.app import socketio
                        socketio.emit('new_signin', {
                            'student_name': name,
                            'confidence': round(max_sim, 4),
                            'status': 'present',
                            'timestamp': current_time.isoformat(),
                            'message': f'{name} 签到成功'
                        })
                        print(f"📢 广播签到事件: {name} (置信度: {max_sim:.4f})")
                    except Exception as e:
                        print(f"⚠️ WebSocket广播失败: {e}")
            
            # 构建人脸框信息
            bbox = face.bbox.astype(int).tolist()
            results.append({
                "name": name if recognized else "Unknown",
                "confidence": max_sim,
                "recognized": recognized,
                "recorded": recorded,
                "bbox": bbox
            })
        
        # 绘制标注
        annotated_frame = frame.copy()
        for idx, face in enumerate(faces):
            result = results[idx]
            bbox = result['bbox']
            x1, y1, x2, y2 = bbox
            
            color = (0, 255, 0) if result['recognized'] else (0, 0, 255)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            label = f"{result['name']} ({result['confidence']:.2f})"
            cv2.putText(annotated_frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 编码返回
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        annotated_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        
        return jsonify({
            "success": True,
            "faces": results,
            "annotated_image": f"data:image/jpeg;base64,{annotated_base64}"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@realtime_recognition_bp.route('/reload-database', methods=['POST'])
def reload_database():
    """重新加载人脸数据库"""
    try:
        success, message = load_known_faces()
        return jsonify({
            "success": success,
            "message": message,
            "students_count": len(known_names) if success else 0
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
