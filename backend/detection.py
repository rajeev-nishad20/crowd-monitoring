"""YOLOv8 Detection Module with Advanced Features"""
import cv2
import torch
import numpy as np
from ultralytics import YOLO
from collections import defaultdict, deque
import time
import config
import logging
from threading import Lock
from mobile_utils import DataTypeHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObjectDetector:
    def __init__(self):
        try:
            self.model = YOLO(config.MODEL_PATH)
            logger.info("YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise
        
        self.track_history = defaultdict(lambda: deque(maxlen=30))
        self.fps_history = deque(maxlen=30)
        self.frame_count = 0
        self.detection_counts = defaultdict(int)
        self.class_detection_history = defaultdict(list)  # Track detections per class
        self.confidence_threshold_history = deque(maxlen=100)  # Track thresholds
        
        # Performance metrics
        self.processing_times = deque(maxlen=100)
        self.frame_sizes = deque(maxlen=100)
        self.memory_usage = deque(maxlen=100)
        self.metrics_lock = Lock()
        
        # Detection quality metrics
        self.true_positive_estimates = 0
        self.false_positive_estimates = 0
        self.detection_quality_scores = deque(maxlen=50)
        
        # Performance optimization: Cache colors
        np.random.seed(42)
        self.colors = {cls: tuple(map(int, np.random.randint(0, 255, 3))) 
                      for cls in config.COCO_CLASSES}
    
    def detect_objects(self, frame, track=True):
        """Detect objects in frame with error handling and optimization"""
        try:
            if frame is None or frame.size == 0:
                logger.warning("Empty frame received")
                return frame.copy() if frame is not None else np.zeros((480, 640, 3), dtype=np.uint8), [], 0, 0
            
            start_time = time.time()
            self.frame_count += 1
            
            # Optimize: Convert to RGB once
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            try:
                if track:
                    results = self.model.track(
                        frame_rgb, 
                        persist=True, 
                        verbose=False, 
                        conf=config.MODEL_CONFIDENCE,
                        iou=config.MODEL_IOU_THRESHOLD,
                        max_det=config.MODEL_MAX_DET
                    )
                else:
                    results = self.model.predict(
                        frame_rgb, 
                        verbose=False, 
                        conf=config.MODEL_CONFIDENCE,
                        iou=config.MODEL_IOU_THRESHOLD,
                        max_det=config.MODEL_MAX_DET
                    )
            except Exception as track_error:
                logger.warning(f"Tracking error, falling back to predict: {track_error}")
                try:
                    results = self.model.predict(
                        frame_rgb, 
                        verbose=False, 
                        conf=config.MODEL_CONFIDENCE,
                        iou=config.MODEL_IOU_THRESHOLD,
                        max_det=config.MODEL_MAX_DET
                    )
                except Exception as e:
                    logger.error(f"Both tracking and predict failed: {e}")
                    results = None
            
            detections = []
            annotated_frame = frame.copy()
            
            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        try:
                            # Extract and convert to int32 properly
                            xyxy = box.xyxy[0]
                            x1 = int(np.int32(xyxy[0]))
                            y1 = int(np.int32(xyxy[1]))
                            x2 = int(np.int32(xyxy[2]))
                            y2 = int(np.int32(xyxy[3]))
                            
                            cls_id = int(np.int32(box.cls[0]))
                            confidence = float(box.conf[0])
                            
                            # Validate bounding box coordinates
                            x1 = max(0, min(x1, frame.shape[1] - 1))
                            y1 = max(0, min(y1, frame.shape[0] - 1))
                            x2 = max(0, min(x2, frame.shape[1]))
                            y2 = max(0, min(y2, frame.shape[0]))
                            
                            # Validate confidence is within bounds
                            if not (0 <= confidence <= 1):
                                continue
                            
                            class_name = config.COCO_CLASSES[cls_id] if cls_id < len(config.COCO_CLASSES) else f"class_{cls_id}"
                            track_id = int(np.int32(box.id[0])) if hasattr(box, 'id') and box.id is not None else None
                            
                            # Calculate bounding box area and aspect ratio
                            bbox_area = int(np.int32((x2 - x1) * (y2 - y1)))
                            aspect_ratio = float((x2 - x1) / (y2 - y1)) if (y2 - y1) > 0 else 0.0
                            
                            detection = {
                                'class': class_name,
                                'confidence': float(confidence),
                                'bbox': [x1, y1, x2, y2],
                                'track_id': track_id,
                                'area': bbox_area,
                                'aspect_ratio': aspect_ratio
                            }
                            detections.append(detection)
                            
                            # Update detection metrics
                            self.detection_counts[class_name] += 1
                            self.class_detection_history[class_name].append({
                                'confidence': confidence,
                                'timestamp': time.time()
                            })
                            self.confidence_threshold_history.append(confidence)
                            
                            # Draw bounding box with color-coding by confidence
                            color = self.colors.get(class_name, (0, 255, 0))
                            box_thickness = max(1, int(confidence * 3))
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, box_thickness)
                            
                            # Draw label with confidence score
                            label = f"{class_name}: {confidence:.2f}"
                            if track_id is not None:
                                label += f" (ID:{track_id})"
                            
                            # Draw label background for better visibility
                            (label_width, label_height), _ = cv2.getTextSize(
                                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                            )
                            cv2.rectangle(annotated_frame, (x1, y1 - label_height - 15),
                                        (x1 + label_width + 10, y1), color, -1)
                            cv2.putText(annotated_frame, label, (x1 + 5, y1 - 5),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            
                            # Draw tracking line if tracking ID exists
                            if track_id is not None:
                                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                                self.track_history[track_id].append(center)
                                points = list(self.track_history[track_id])
                                
                                # Draw trajectory line
                                for j in range(1, len(points)):
                                    if points[j - 1] and points[j]:
                                        cv2.line(annotated_frame, points[j - 1], points[j], color, 2)
                                
                                # Draw center point
                                cv2.circle(annotated_frame, center, 4, color, -1)
                        
                        except Exception as e:
                            logger.debug(f"Error processing detection box: {e}")
                            continue
            
            # Calculate processing time and FPS
            processing_time = time.time() - start_time
            
            # Update processing times for metrics
            with self.metrics_lock:
                self.processing_times.append(processing_time)
            
            # Calculate average FPS
            fps = 1.0 / processing_time if processing_time > 0 else 0
            self.fps_history.append(fps)
            avg_fps = np.mean(self.fps_history) if len(self.fps_history) > 0 else 0
            
            # Calculate average confidence
            avg_confidence = np.mean(self.confidence_threshold_history) if len(self.confidence_threshold_history) > 0 else 0
            
            # Draw info text on frame
            info_lines = [
                f"Frame: {self.frame_count} | FPS: {avg_fps:.1f} | Processing: {processing_time*1000:.1f}ms",
                f"Objects: {len(detections)} | Classes: {len(set(d['class'] for d in detections))} | Avg Conf: {avg_confidence:.2f}"
            ]
            
            y_offset = 30
            for line in info_lines:
                cv2.putText(annotated_frame, line, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 25
            
            return annotated_frame, detections, avg_fps, processing_time
            
        except Exception as e:
            logger.error(f"Error in detect_objects: {e}")
            return frame.copy() if frame is not None else np.zeros((480, 640, 3), dtype=np.uint8), [], 0, 0
    
    def get_statistics(self):
        """Get comprehensive detection statistics"""
        with self.metrics_lock:
            avg_processing_time = np.mean(self.processing_times) if len(self.processing_times) > 0 else 0
            avg_fps = np.mean(self.fps_history) if len(self.fps_history) > 0 else 0
            
            stats = {
                'total_detections': int(np.int32(sum(self.detection_counts.values()))),
                'unique_classes': int(np.int32(len(self.detection_counts))),
                'detection_counts': {k: int(np.int32(v)) for k, v in self.detection_counts.items()},
                'class_detection_history': dict(self.class_detection_history),
                'avg_confidence': float(np.mean(self.confidence_threshold_history)) if len(self.confidence_threshold_history) > 0 else 0,
                'frame_count': int(np.int32(self.frame_count)),
                'avg_processing_time': float(avg_processing_time),
                'avg_fps': float(avg_fps),
                'quality_score': self._calculate_quality_score()
            }
            
            # Convert to native Python types for JSON serialization
            return DataTypeHandler.convert_to_python_native(stats)
    
    def _calculate_quality_score(self):
        """Calculate overall detection quality (0-100)"""
        if len(self.confidence_threshold_history) == 0:
            return 0
        
        avg_conf = np.mean(self.confidence_threshold_history)
        var_conf = np.var(self.confidence_threshold_history) if len(self.confidence_threshold_history) > 1 else 0
        
        # Quality = average confidence (50%) + consistency (50%)
        consistency_score = max(0, 100 - (var_conf * 100))
        quality = (avg_conf * 100 * 0.5) + (consistency_score * 0.5)
        return float(min(100, max(0, quality)))
    
    def get_performance_metrics(self):
        """Get detailed performance metrics"""
        with self.metrics_lock:
            return {
                'avg_processing_time_ms': float(np.mean(self.processing_times) * 1000) if len(self.processing_times) > 0 else 0,
                'max_processing_time_ms': float(np.max(self.processing_times) * 1000) if len(self.processing_times) > 0 else 0,
                'min_processing_time_ms': float(np.min(self.processing_times) * 1000) if len(self.processing_times) > 0 else 0,
                'avg_fps': float(np.mean(self.fps_history)) if len(self.fps_history) > 0 else 0,
                'max_fps': float(np.max(self.fps_history)) if len(self.fps_history) > 0 else 0,
                'min_fps': float(np.min(self.fps_history)) if len(self.fps_history) > 0 else 0,
                'total_frames': self.frame_count,
                'quality_score': self._calculate_quality_score()
            }
    
    def filter_detections(self, detections, min_confidence=None, classes=None, min_area=None):
        """Filter detections by various criteria"""
        if min_confidence is None:
            min_confidence = config.MODEL_CONFIDENCE
        
        filtered = []
        for det in detections:
            # Confidence filter
            if det['confidence'] < min_confidence:
                continue
            
            # Class filter
            if classes and det['class'] not in classes:
                continue
            
            # Area filter (if min_area specified)
            if min_area and det.get('area', 0) < min_area:
                continue
            
            filtered.append(det)
        
        return filtered
    
    def reset_statistics(self):
        """Reset detection statistics"""
        with self.metrics_lock:
            self.detection_counts.clear()
            self.frame_count = 0
            self.track_history.clear()
            self.class_detection_history.clear()
            self.confidence_threshold_history.clear()
            self.processing_times.clear()
            self.detection_quality_scores.clear()

