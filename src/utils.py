import cv2
import numpy as np
import os
import pickle
import config

def load_image(path):
    """
    Load an image from a file path, handling non-ASCII characters in the path.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    # Use numpy to read file validation unicode paths, then decode
    img_arr = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    return img

def save_image(img, path):
    """
    Save an image to a file path, handling non-ASCII characters.
    """
    is_success, im_buf_arr = cv2.imencode(".jpg", img)
    if is_success:
        im_buf_arr.tofile(path)
    else:
        print(f"Failed to save image to {path}")

def load_database(db_path):
    """
    Load the student embeddings database.
    """
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            return pickle.load(f)
    return {}

def save_database(database, db_path):
    """
    Save the student embeddings database.
    """
    with open(db_path, 'wb') as f:
        pickle.dump(database, f)

def draw_bbox(img, box, name, color=(0, 255, 0)):
    """
    Draw a bounding box and name on the image.
    """
    x1, y1, x2, y2 = box.astype(int)
    w = x2 - x1
    h = y2 - y1
    
    # Dynamic styling based on face height to handle different resolutions
    # Reduced scale as requested
    font_scale = max(0.35, h / 130.0)
    thickness = max(1, int(font_scale * 2))
    
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    
    if name:
        # Text settings
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Calculate text size
        (text_w, text_h), baseline = cv2.getTextSize(name, font, font_scale, thickness)
        
        # Text Background Position (above the box)
        back_x1 = x1
        back_y1 = y1 - text_h - 10
        back_x2 = x1 + text_w + 10
        back_y2 = y1
        
        # Ensure background is within image bounds
        img_h, img_w = img.shape[:2]
        back_x1 = max(0, back_x1)
        back_y1 = max(0, back_y1)
        back_x2 = min(img_w, back_x2)
        back_y2 = min(img_h, back_y2)
        
        # Draw semi-transparent background
        if back_y2 > back_y1 and back_x2 > back_x1:
            roi = img[back_y1:back_y2, back_x1:back_x2]
            color_rect = np.full(roi.shape, color, dtype=np.uint8)
            # Blend: 0.6 original + 0.4 color (semi-transparent)
            res = cv2.addWeighted(roi, 0.6, color_rect, 0.4, 1.0)
            img[back_y1:back_y2, back_x1:back_x2] = res
        
        # Draw text with Anti-Aliasing (LINE_AA) for sharpness
        text_x = x1 + 5
        text_y = y1 - 5
        # Ensure text is visible even if box is at the very top
        if text_y < 5:
            text_y = y1 + text_h + 5
        
        cv2.putText(img, name, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    
    return img
