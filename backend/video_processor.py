"""Video Processing Module for Batch Detection"""
import cv2
import os
import logging
from detection import ObjectDetector
from database import DetectionDatabase
import config
from datetime import datetime
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process video files for object detection"""
    
    def __init__(self, detector, database):
        self.detector = detector
        self.db = database
        self.is_processing = False
        self.current_progress = 0
        self.processing_results = {}
        self.lock = threading.Lock()
    
    def process_video(self, video_path, output_path=None, progress_callback=None):
        """Process video file and detect objects"""
        try:
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return None
            
            with self.lock:
                self.is_processing = True
                self.current_progress = 0
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Failed to open video: {video_path}")
                return None
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Processing video: {frame_count} frames @ {fps} FPS, {width}x{height}")
            
            # Prepare output video if specified
            out = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Process video
            frame_num = 0
            detections_summary = {
                'total_objects': 0,
                'classes': {},
                'frames_with_detections': 0,
                'avg_confidence': 0,
                'processing_time': 0
            }
            all_confidences = []
            start_time = datetime.now()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detect objects
                annotated_frame, detections, fps_val, proc_time = self.detector.detect_objects(frame, track=False)
                
                # Log detections
                for det in detections:
                    try:
                        self.db.log_detection(
                            det['class'], 
                            det['confidence'], 
                            det['bbox'],
                            frame_num, 
                            'video_file'
                        )
                        all_confidences.append(det['confidence'])
                    except Exception as e:
                        logger.warning(f"Error logging detection: {e}")
                
                # Update summary
                detections_summary['total_objects'] += len(detections)
                if len(detections) > 0:
                    detections_summary['frames_with_detections'] += 1
                
                for det in detections:
                    class_name = det['class']
                    if class_name not in detections_summary['classes']:
                        detections_summary['classes'][class_name] = 0
                    detections_summary['classes'][class_name] += 1
                
                # Write output frame if needed
                if out:
                    out.write(annotated_frame)
                
                frame_num += 1
                
                # Update progress
                progress = int((frame_num / frame_count) * 100)
                with self.lock:
                    self.current_progress = progress
                
                if progress_callback and frame_num % int(fps) == 0:  # Call every second
                    progress_callback(progress, frame_num, frame_count)
            
            # Calculate statistics
            end_time = datetime.now()
            detections_summary['processing_time'] = (end_time - start_time).total_seconds()
            if all_confidences:
                detections_summary['avg_confidence'] = sum(all_confidences) / len(all_confidences)
            
            # Release resources
            cap.release()
            if out:
                out.release()
            
            with self.lock:
                self.is_processing = False
                self.current_progress = 100
                self.processing_results = detections_summary
            
            logger.info(f"Video processing completed: {detections_summary['total_objects']} objects detected")
            return detections_summary
        
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            with self.lock:
                self.is_processing = False
            return None
    
    def process_video_async(self, video_path, output_path=None, callback=None):
        """Process video asynchronously"""
        thread = threading.Thread(
            target=self.process_video,
            args=(video_path, output_path, callback)
        )
        thread.daemon = True
        thread.start()
        return thread
    
    def get_progress(self):
        """Get current processing progress"""
        with self.lock:
            return {
                'is_processing': self.is_processing,
                'progress': self.current_progress,
                'results': self.processing_results if self.current_progress == 100 else None
            }
    
    def stop_processing(self):
        """Stop current processing"""
        with self.lock:
            self.is_processing = False
