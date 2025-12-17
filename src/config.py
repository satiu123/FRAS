import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
KNOWN_FACES_DIR = os.path.join(DATA_DIR, 'train')
CLASSROOM_DIR = os.path.join(DATA_DIR, 'test')
OUTPUT_DIR = os.path.join(DATA_DIR, 'outputs')
DB_PATH = os.path.join(DATA_DIR, 'students.pkl')

# Model Settings
# Cosine similarity threshold for face matching
# 0.4 - 0.6 is typical for ArcFace. Lower = looser matching, Higher = stricter.
MATCH_THRESHOLD = 0.45 

# Visualization
FONT_SCALE = 0.4
THICKNESS = 1
COLOR_MATCH = (0, 255, 0)    # Green
COLOR_UNKNOWN = (0, 0, 255)  # Red
