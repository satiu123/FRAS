# 非实时签到
import os
import argparse
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from numpy.linalg import norm
import config
import utils
import sys
from pathlib import Path
# 获取当前文件所在目录的父目录（即 FRAS-main 根目录）
project_root = Path(__file__).parent.parent  # src -> FRAS-main
sys.path.append(str(project_root))
# 导入 src 下的模块
from src.attendance import record_attendance
from datetime import date


def compute_sim(feat1, feat2):
    return np.dot(feat1, feat2) / (norm(feat1) * norm(feat2))

def run_inference(image_path):
    """
    Loads databases, detects faces in the image, and identifies them.
    """
    # Load database
    known_faces = utils.load_database(config.DB_PATH)
    if not known_faces:
        print("Warning: No known faces found in database. Please run register.py first.")
    
    # Initialize InsightFace
    app = FaceAnalysis(providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Load Image
    try:
        img = utils.load_image(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    # Detect faces
    faces = app.get(img)
    print(f"Detected {len(faces)} faces.")

    # # Identify faces
    # for face in faces:
    #     max_sim = -1
    #     best_name = "Unknown"
        
    #     # Compare with all known faces
    #     for name, embedding in known_faces.items():
    #         sim = compute_sim(face.embedding, embedding)
    #         if sim > max_sim:
    #             max_sim = sim
    #             best_name = name
        
    #     # Apply threshold
    #     final_name = None
    #     color = config.COLOR_UNKNOWN
    #     if max_sim >= config.MATCH_THRESHOLD:
    #         final_name = f"{best_name} ({max_sim:.2f})"
    #         color = config.COLOR_MATCH
        
    #     # Draw on image
    #     utils.draw_bbox(img, face.bbox, final_name, color)
    
    # Identify faces
    for face in faces:
        max_sim = -1
        best_name = "Unknown"
        
        for name, embedding in known_faces.items():
            sim = compute_sim(face.embedding, embedding)
            if sim > max_sim:
                max_sim = sim
                best_name = name
        
        # Apply threshold
        final_name = None
        color = config.COLOR_UNKNOWN
        if max_sim >= config.MATCH_THRESHOLD:
            final_name = f"{best_name} ({max_sim:.2f})"
            color = config.COLOR_MATCH
            
            # 自动签到！
            today = date.today()
            # # 可选：保存带人脸框的截图用于复核
            # capture_path = os.path.join(config.CAPTURE_DIR, f"capture_{today}_{best_name}.jpg")
            # utils.save_image(img, capture_path)  # 或只裁剪人脸区域
            
            # 调用签到函数
            record_attendance(
                name=best_name,
                course_date=today,
                image_path="",  # 可选：填写 capture_path
                confidence=float(max_sim),
                status="present",
                remark="自动签到"
            )
        
        utils.draw_bbox(img, face.bbox, final_name, color)

    # Save output
    filename = os.path.basename(image_path)
    output_path = os.path.join(config.OUTPUT_DIR, f"result_{filename}")
    utils.save_image(img, output_path)
    print(f"Result saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Recognition Inference")
    parser.add_argument("image_path", help="Path to the classroom image")
    args = parser.parse_args()
    
    run_inference(args.image_path)
