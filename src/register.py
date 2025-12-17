import os
import argparse
import numpy as np
from insightface.app import FaceAnalysis
import config
import utils

def register_faces():
    """
    Scans the KNOWN_FACES_DIR, extracts embeddings, and saves them to the database.
    """
    # Initialize InsightFace
    # providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if GPU is available
    app = FaceAnalysis(providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    known_faces = {}
    
    # Check if directory exists
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
                    print(f"  Warning: No face detected in {filename}. Skipping.")
                    continue
                
                # If multiple faces, pick the largest
                face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)[0]
                embeddings.append(face.embedding)

            except Exception as e:
                print(f"  Error processing {filename}: {e}")

        if embeddings:
            # Average the embeddings to get a stable prototype
            avg_embedding = np.mean(embeddings, axis=0)
            # Normalize the result
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            known_faces[person_name] = avg_embedding
            print(f"Registered {person_name} with {len(embeddings)} images.")
        else:
            print(f"Warning: No valid images for {person_name}")

    # Save to database
    utils.save_database(known_faces, config.DB_PATH)
    print(f"Successfully saved {len(known_faces)} students to {config.DB_PATH}")

if __name__ == "__main__":
    register_faces()
