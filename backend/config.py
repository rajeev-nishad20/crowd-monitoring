"""Configuration file for Real-Time Object Detection App"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Model Configuration
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolov8n.pt')
MODEL_CONFIDENCE = 0.35  # Optimized confidence threshold for accuracy
MODEL_IOU_THRESHOLD = 0.5  # Increased for better NMS filtering
MODEL_MAX_DET = 100  # Maximum detections per image
MODEL_AGNOSTIC_NMS = False  # Use class-specific NMS
MODEL_HALF = False  # Use FP16 precision (False for accuracy)

# Video Configuration
VIDEO_FPS = 30
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
MAX_UPLOAD_SIZE = 100 * 1024 * 1024

# Camera Configuration
DEFAULT_CAMERA = 0

# Database Configuration
DATABASE_PATH = os.path.join(BASE_DIR, 'logs', 'detections.db')
CSV_LOG_PATH = os.path.join(BASE_DIR, 'logs', 'detections.csv')

# Upload folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}

# Detection Classes (COCO dataset)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
]

# Alert Configuration
ALERT_CLASSES = ['person', 'car', 'truck']
ALERT_THRESHOLD = 5

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
SECRET_KEY = 'change-this-in-production'

# Create directories
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'models'), exist_ok=True)
