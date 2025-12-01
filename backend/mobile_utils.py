"""Mobile-optimized utilities for image and video processing"""
import cv2
import numpy as np
import base64
import io
from PIL import Image
import logging
import json

logger = logging.getLogger(__name__)

class MobileImageProcessor:
    """Handle image processing for mobile devices"""
    
    @staticmethod
    def decode_base64_image(base64_string):
        """Decode base64 image string to numpy array"""
        try:
            # Remove data:image/jpeg;base64, prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
            return image
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            raise
    
    @staticmethod
    def encode_image_to_base64(image):
        """Encode numpy array image to base64 string"""
        try:
            ret, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                raise ValueError("Failed to encode image")
            
            image_bytes = buffer.tobytes()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_string}"
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            raise
    
    @staticmethod
    def compress_image(image, quality=85, max_width=640, max_height=480):
        """Compress image for mobile transmission"""
        try:
            # Resize if necessary
            height, width = image.shape[:2]
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            # Compress
            ret, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if not ret:
                raise ValueError("Failed to compress image")
            
            return buffer.tobytes(), image.shape
        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            raise
    
    @staticmethod
    def resize_for_processing(image, target_width=640, target_height=480):
        """Resize image for model processing"""
        try:
            if image is None:
                raise ValueError("Image is None")
            
            height, width = image.shape[:2]
            
            # Maintain aspect ratio
            aspect_ratio = width / height
            target_aspect = target_width / target_height
            
            if aspect_ratio > target_aspect:
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
            
            resized = cv2.resize(image, (new_width, new_height))
            
            # Pad to target size
            top = (target_height - new_height) // 2
            bottom = target_height - new_height - top
            left = (target_width - new_width) // 2
            right = target_width - new_width - left
            
            padded = cv2.copyMakeBorder(resized, top, bottom, left, right, 
                                       cv2.BORDER_CONSTANT, value=(0, 0, 0))
            
            return padded
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise


class MobileVideoProcessor:
    """Handle video processing for mobile devices"""
    
    @staticmethod
    def get_video_properties(video_path):
        """Get video properties"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            properties = {
                'fps': int(cap.get(cv2.CAP_PROP_FPS)),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration_seconds': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
            }
            
            cap.release()
            return properties
        except Exception as e:
            logger.error(f"Error getting video properties: {e}")
            raise
    
    @staticmethod
    def extract_video_frames(video_path, max_frames=30, skip_frames=1):
        """Extract frames from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            frames = []
            frame_count = 0
            
            while len(frames) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % skip_frames == 0:
                    frames.append(frame)
                
                frame_count += 1
            
            cap.release()
            return frames
        except Exception as e:
            logger.error(f"Error extracting video frames: {e}")
            raise
    
    @staticmethod
    def stream_video_frames(video_path, target_fps=15):
        """Stream video frames for real-time processing"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            original_fps = int(cap.get(cv2.CAP_PROP_FPS))
            skip_frame_count = max(1, original_fps // target_fps)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % skip_frame_count == 0:
                    yield frame
                
                frame_count += 1
            
            cap.release()
        except Exception as e:
            logger.error(f"Error streaming video frames: {e}")
            raise


class DataTypeHandler:
    """Handle numpy data types for JSON serialization"""
    
    @staticmethod
    def convert_to_python_native(obj):
        """Convert numpy and other types to Python native types"""
        if isinstance(obj, np.integer):  # Covers int32, int64, etc.
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: DataTypeHandler.convert_to_python_native(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [DataTypeHandler.convert_to_python_native(item) for item in obj]
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return obj
    
    @staticmethod
    def validate_bbox_coordinates(bbox, frame_width, frame_height):
        """Validate and convert bbox coordinates"""
        try:
            x1, y1, x2, y2 = bbox
            
            # Convert to int32 if needed
            x1 = int(np.int32(x1))
            y1 = int(np.int32(y1))
            x2 = int(np.int32(x2))
            y2 = int(np.int32(y2))
            
            # Clamp to frame boundaries
            x1 = max(0, min(x1, frame_width - 1))
            y1 = max(0, min(y1, frame_height - 1))
            x2 = max(x1 + 1, min(x2, frame_width))
            y2 = max(y1 + 1, min(y2, frame_height))
            
            return [x1, y1, x2, y2]
        except Exception as e:
            logger.error(f"Error validating bbox: {e}")
            raise
    
    @staticmethod
    def serialize_detections(detections, frame_width, frame_height):
        """Serialize detections with proper type handling"""
        try:
            serialized = []
            for det in detections:
                item = {
                    'class': str(det['class']),
                    'confidence': float(det['confidence']),
                    'bbox': DataTypeHandler.validate_bbox_coordinates(
                        det['bbox'], frame_width, frame_height
                    ),
                    'track_id': int(det['track_id']) if det.get('track_id') is not None else None,
                    'area': int(det.get('area', 0)),
                    'aspect_ratio': float(det.get('aspect_ratio', 0))
                }
                serialized.append(item)
            
            return serialized
        except Exception as e:
            logger.error(f"Error serializing detections: {e}")
            raise
    
    @staticmethod
    def handle_json_serialization(obj):
        """Custom JSON encoder for numpy and opencv types"""
        try:
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            return str(obj)
        except Exception as e:
            logger.error(f"Error serializing object: {e}")
            return str(obj)


class CameraHandler:
    """Handle camera access and configuration"""
    
    @staticmethod
    def get_available_cameras(max_cameras=5):
        """Get list of available cameras"""
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append({
                    'id': i,
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    'fps': int(cap.get(cv2.CAP_PROP_FPS))
                })
                cap.release()
        
        return available
    
    @staticmethod
    def configure_camera(camera, width=640, height=480, fps=30):
        """Configure camera properties"""
        try:
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            camera.set(cv2.CAP_PROP_FPS, fps)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
            
            # Verify settings
            actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(camera.get(cv2.CAP_PROP_FPS))
            
            return {
                'width': actual_width,
                'height': actual_height,
                'fps': actual_fps,
                'buffer_size': int(camera.get(cv2.CAP_PROP_BUFFERSIZE))
            }
        except Exception as e:
            logger.error(f"Error configuring camera: {e}")
            raise


class MobileResponseFormatter:
    """Format responses for mobile applications"""
    
    @staticmethod
    def format_detection_response(detections, processing_time, fps, image=None):
        """Format detection response for mobile"""
        try:
            response = {
                'success': True,
                'objects_detected': len(detections),
                'detections': detections,
                'metrics': {
                    'processing_time_ms': float(processing_time * 1000),
                    'fps': float(fps),
                    'timestamp': int(__import__('time').time() * 1000)  # milliseconds
                }
            }
            
            if image is not None:
                response['image'] = MobileImageProcessor.encode_image_to_base64(image)
            
            return response
        except Exception as e:
            logger.error(f"Error formatting detection response: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def format_error_response(error_message, error_code='ERROR'):
        """Format error response for mobile"""
        return {
            'success': False,
            'error': str(error_message),
            'error_code': error_code,
            'timestamp': int(__import__('time').time() * 1000)
        }
    
    @staticmethod
    def format_camera_list_response(cameras):
        """Format camera list for mobile"""
        return {
            'success': True,
            'cameras': cameras,
            'count': len(cameras),
            'timestamp': int(__import__('time').time() * 1000)
        }
