# 注册人脸到数据库
import os
import sys
import argparse
import numpy as np
from insightface.app import FaceAnalysis

from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config
from src import utils

from src.databaseBuild.db import register_student_to_db

def register_faces(student_names=None):
    """
    Scans the KNOWN_FACES_DIR, extracts embeddings, and saves them to the database.
    Also registers each student into the SQLite attendance system.
    
    Args:
        student_names: Optional list of student names or single student name to update.
                      If None, updates all students (full scan).
                      If provided, only updates the specified student(s) incrementally.
    """
    # Initialize InsightFace
    app = FaceAnalysis(providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(320, 320))

    # Load existing database for incremental update
    if student_names is not None:
        try:
            known_faces = utils.load_database(config.DB_PATH)
        except:
            known_faces = {}
    else:
        known_faces = {}
    
    if not os.path.exists(config.KNOWN_FACES_DIR):
        print(f"Error: Directory {config.KNOWN_FACES_DIR} does not exist.")
        return

    # Convert single name to list
    if student_names is not None:
        if isinstance(student_names, str):
            student_names = [student_names]
        print(f"Incremental update for: {', '.join(student_names)}")
    else:
        print("Full scan update for all students")

    # Iterate over student folders
    students_to_process = student_names if student_names else os.listdir(config.KNOWN_FACES_DIR)
    
    for person_name in students_to_process:
        person_dir = os.path.join(config.KNOWN_FACES_DIR, person_name)
        if not os.path.isdir(person_dir):
            # If student folder doesn't exist, remove from database
            if person_name in known_faces:
                del known_faces[person_name]
                print(f"Removed {person_name} from database (folder not found)")
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

            # 同步写入 SQLite 数据库 
            register_student_to_db(person_name)

        else:
            print(f"Warning: No valid images for {person_name}")

    # Save face embeddings to .pkl
    utils.save_database(known_faces, config.DB_PATH)
    print(f"Successfully saved {len(known_faces)} students to {config.DB_PATH}")

if __name__ == "__main__":
    register_faces()