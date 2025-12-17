import os
import argparse
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from numpy.linalg import norm
import config
import utils

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

    # Identify faces
    for face in faces:
        max_sim = -1
        best_name = "Unknown"
        
        # Compare with all known faces
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
        
        # Draw on image
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
