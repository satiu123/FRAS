# 实时签到
import sys
from pathlib import Path

# 添加项目根目录到 sys.path（兼容直接运行）
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import cv2
import numpy as np
import pickle
from datetime import datetime, timedelta
import os
import argparse

from src.config import (
    MODEL_NAME,
    SIMILARITY_THRESHOLD,
    CAPTURE_DIR,
    OUTPUTS_DIR
)
from src.realtime_utils import draw_faces_with_names
from src.attendance import record_attendance
from src.databaseBuild.db import DB_PATH
import insightface
from insightface.app import FaceAnalysis


def load_known_faces():
    """加载已注册的学生特征"""
    pkl_path = project_root / "data" / "students.pkl"
    if not pkl_path.exists():
        print("❌ 未找到 students.pkl，请先运行 register.py")
        return [], []
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    names = list(data.keys())
    feats = list(data.values())
    return names, feats


def realtime_attendance(camera_index=0, save_captures=True):
    # 初始化模型
    app = FaceAssistant(model_name=MODEL_NAME)
    
    # 加载已知人脸
    known_names, known_feats = load_known_faces()
    if not known_names:
        return

    # 转为 NumPy 数组便于计算
    known_feats = np.array(known_feats)

    # 打开摄像头
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ 无法打开摄像头 (索引: {camera_index})")
        return

    # 记录最近签到时间：{name: last_time}
    last_attendance = {}

    # 创建输出目录
    if save_captures:
        os.makedirs(CAPTURE_DIR, exist_ok=True)

    print("🎥 实时签到已启动！按 'q' 退出。")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ 无法读取摄像头帧")
            break

        # 检测并识别人脸
        faces = app.get(frame)
        current_time = datetime.now()

        results = []
        for face in faces:
            feat = face.normed_embedding
            sims = np.dot(known_feats, feat)
            max_idx = np.argmax(sims)
            max_sim = sims[max_idx]
            name = known_names[max_idx]

            if max_sim >= SIMILARITY_THRESHOLD:
                # 检查是否在冷却期内(默认1.5小时)
                can_record = True
                if name in last_attendance:
                    if current_time - last_attendance[name] < timedelta(seconds=5400):
                        can_record = False

                if can_record:
                    last_attendance[name] = current_time

                    # 保存截图（可选）
                    image_path = ""
                    if save_captures:
                        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
                        filename = f"{name}_{timestamp}.jpg"
                        capture_path = os.path.join(CAPTURE_DIR, filename)
                        # 裁剪人脸区域
                        bbox = face.bbox.astype(int)
                        x1, y1, x2, y2 = bbox
                        face_img = frame[y1:y2, x1:x2]
                        if face_img.size > 0:
                            cv2.imwrite(capture_path, face_img)
                            image_path = capture_path

                    # 记录考勤
                    record_attendance(
                        name=name,
                        course_date=current_time.date(),
                        image_path=image_path,
                        confidence=float(max_sim),
                        status="present",
                        remark="实时签到"
                    )

                results.append((name, max_sim, can_record))
            else:
                results.append(("Unknown", max_sim, False))

        # 绘制结果
        display_frame = draw_faces_with_names(frame.copy(), faces, results)

        # 显示画面
        cv2.imshow("Real-time Attendance (Press 'q' to quit)", display_frame)

        # 按 q 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 实时签到已关闭。")


class FaceAssistant:
    def __init__(self, model_name='buffalo_l'):
        self.app = FaceAnalysis(name=model_name, providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def get(self, img):
        return self.app.get(img)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="实时人脸签到系统")
    parser.add_argument("--camera", type=int, default=0, help="摄像头索引，默认 0")
    parser.add_argument("--no-save", action="store_true", help="不保存签到截图")
    args = parser.parse_args()

    realtime_attendance(
        camera_index=args.camera,
        save_captures=not args.no_save
    )