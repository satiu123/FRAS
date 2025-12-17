# 注册人脸到数据库
import os
import sys
import argparse
import numpy as np
from insightface.app import FaceAnalysis

# ====== 新增：添加项目根目录到 sys.path ======
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# ============================================

import config
import utils

# ====== 新增：导入数据库注册函数 ======
from src.databaseBuild.db import register_student_to_db
# ====================================

def register_faces():
    """
    Scans the KNOWN_FACES_DIR, extracts embeddings, and saves them to the database.
    Also registers each student into the SQLite attendance system.
    """
    # Initialize InsightFace
    app = FaceAnalysis(providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(320, 320)) # Reducing det_size to better match small inputs, or remove it entirely. 
    # Actually, for small images, (640, 640) might be too large difference. Let's try (320, 320) or just auto. 
    # Let's try flexible mode first by removing it? No, det_size is required or defaults to something.
    # Let's set it to (320, 320) since user mentioned 278x270.
    # Wait, best practice is usually to try multiple sizes or use a size close to input. 
    # Let's start by removing the explicit argument to let library decide (usually defaults to larger, but let's see).
    # Re-reading: Removing it often defaults to (640, 640).
    # Let's try explicitly setting (320, 320) as a test for small images.
    app.prepare(ctx_id=0, det_size=(320, 320))

    known_faces = {}
    
    if not os.path.exists(config.KNOWN_FACES_DIR):
        print(f"Error: Directory {config.KNOWN_FACES_DIR} does not exist.")
        return

    # Iterate over student folders
    for person_name in os.listdir(config.KNOWN_FACES_DIR):
        person_dir = os.path.join(config.KNOWN_FACES_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue

        print(f"Processing {person_name}...")
        embeddings = []

        for filename in os.listdir(person_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                continue

            path = os.path.join(person_dir, filename)
            try:
                img = utils.load_image(path)
                faces = app.get(img)

                if len(faces) == 0:
                    h, w = img.shape[:2]
                    print(f"  Warning: No face detected in {filename} ({w}x{h}). Skipping.")
                    continue
                
                face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
                embeddings.append(face.embedding)

            except Exception as e:
                print(f"  Error processing {filename}: {e}")

        if embeddings:
            avg_embedding = np.mean(embeddings, axis=0)
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            known_faces[person_name] = avg_embedding
            print(f"Registered {person_name} with {len(embeddings)} images.")

            # ✅✅✅ 新增：同步写入 SQLite 数据库 ✅✅✅
            register_student_to_db(person_name)

        else:
            print(f"Warning: No valid images for {person_name}")

    # Save face embeddings to .pkl
    utils.save_database(known_faces, config.DB_PATH)
    print(f"Successfully saved {len(known_faces)} students to {config.DB_PATH}")

if __name__ == "__main__":
    register_faces()