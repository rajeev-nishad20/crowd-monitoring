"""Flask Application"""
from flask import Flask, render_template, Response, jsonify, request, send_file
from flask_cors import CORS
import cv2
import time
from datetime import datetime
import os
import config
from detection import ObjectDetector
from database import DetectionDatabase
import logging
import threading
import json
import numpy as np
from mobile_utils import (
    MobileImageProcessor, MobileVideoProcessor, DataTypeHandler,
    CameraHandler, MobileResponseFormatter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder for numpy types and int32
class NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        elif isinstance(o, np.bool_):
            return bool(o)
        return super().default(o)

app = Flask(__name__, 
            template_folder='../frontend',
            static_folder='../frontend/static')
CORS(app)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_SIZE

# Initialize components
try:
    detector = ObjectDetector()
    logger.info("Object detector initialized")
except Exception as e:
    logger.error(f"Failed to initialize detector: {e}")
    detector = None

db = DetectionDatabase()

# Global state with thread safety
camera = None
camera_id = None  # currently opened camera id
is_running = False
current_detections = []
current_fps = 0
state_lock = threading.Lock()

def generate_frames():
    """Generate video frames with detection - optimized for real-time streaming"""
    global camera, is_running, current_detections, current_fps, detector
    
    if detector is None:
        logger.error("Detector not initialized")
        return
    
    frame_count = 0
    error_count = 0
    max_errors = 10
    last_log_time = time.time()
    frame_skip = 0
    
    while is_running:
        if camera is None:
            logger.warning("Camera is None, stopping frame generation")
            break
        
        try:
            success, frame = camera.read()
            if not success:
                error_count += 1
                logger.warning(f"Failed to read frame from camera (error {error_count}/{max_errors})")
                if error_count >= max_errors:
                    logger.error("Max camera read errors reached, stopping")
                    with state_lock:
                        is_running = False
                    break
                time.sleep(0.1)
                continue
            
            error_count = 0  # Reset error count on success
            
            # Resize frame
            frame = cv2.resize(frame, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
            
            # Detect objects
            try:
                annotated_frame, detections, fps, processing_time = detector.detect_objects(frame, track=True)
            except Exception as detect_error:
                logger.warning(f"Detection error: {detect_error}")
                annotated_frame = frame.copy()
                detections = []
                fps = 0
                processing_time = 0
            
            # Update global state
            with state_lock:
                current_detections = detections
                current_fps = fps
            
            # Log detections with throttling
            if detections:
                for det in detections:
                    try:
                        db.log_detection(det['class'], det['confidence'], det['bbox'],
                                       frame_count, 'webcam', det.get('track_id'))
                    except Exception as e:
                        logger.debug(f"Error logging detection: {e}")
            
            # Check alerts
            check_alerts(detections)
            frame_count += 1
            
            # Log progress periodically
            current_time = time.time()
            if current_time - last_log_time >= 5:
                logger.info(f"Streaming: {frame_count} frames, {len(current_detections)} objects, {fps:.1f} FPS")
                last_log_time = current_time
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ret:
                logger.warning("Failed to encode frame")
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Stream frame with multipart boundary
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
                   b'\r\n' + frame_bytes + b'\r\n')
                   
        except GeneratorExit:
            logger.info("Generator exit requested")
            break
        except Exception as e:
            error_count += 1
            logger.error(f"Error in generate_frames: {e} (error {error_count}/{max_errors})")
            if error_count >= max_errors:
                logger.error("Max errors reached in generate_frames, stopping")
                with state_lock:
                    is_running = False
                break
            time.sleep(0.05)
            continue

def check_alerts(detections):
    """Check and trigger alerts"""
    try:
        if not detections:
            return
        
        class_counts = {}
        for det in detections:
            class_name = det['class']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        for alert_class in config.ALERT_CLASSES:
            if alert_class in class_counts and class_counts[alert_class] >= config.ALERT_THRESHOLD:
                message = f"Alert: {class_counts[alert_class]} {alert_class}(s) detected!"
                db.log_alert('threshold', message, alert_class, class_counts[alert_class])
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return jsonify({'error': 'Failed to load dashboard'}), 500

@app.route('/video_feed')
def video_feed():
    try:
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"Error in video_feed: {e}")
        return jsonify({'error': 'Failed to start video feed'}), 500

@app.route('/start_camera', methods=['POST'])
def start_camera():
    global camera, is_running
    
    try:
        data = request.get_json() or {}
        camera_id_raw = data.get('camera_id', config.DEFAULT_CAMERA)

        # Try to coerce camera_id to int when possible
        try:
            camera_id = int(camera_id_raw)
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid camera_id; must be an integer'}), 400

        if camera_id < 0:
            return jsonify({'success': False, 'message': 'camera_id must be >= 0'}), 400
        
        if detector is None:
            return jsonify({'success': False, 'message': 'Detector not initialized'}), 500
        
        with state_lock:
            # If the camera is already running with the same id, short-circuit
            if camera is not None and camera_id == globals().get('camera_id') and is_running and camera.isOpened():
                return jsonify({'success': True, 'message': f'Camera {camera_id} already running'})

            # Release any existing camera before opening new one
            if camera is not None:
                try:
                    camera.release()
                except Exception:
                    pass

            camera = cv2.VideoCapture(camera_id)
            if not camera.isOpened():
                camera = None
                return jsonify({'success': False, 'message': 'Failed to open camera'}), 400
            
            if not camera.isOpened():
                camera = None
                globals()['camera_id'] = None
                return jsonify({'success': False, 'message': 'Failed to open camera'}), 400

            is_running = True
            globals()['camera_id'] = camera_id
        
        logger.info(f"Camera {camera_id} started")
        return jsonify({'success': True, 'message': 'Camera started'})
    except Exception as e:
        logger.error(f"Error starting camera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    global camera, is_running
    
    try:
        with state_lock:
            is_running = False
            if camera is not None:
                camera.release()
                camera = None
        
        logger.info("Camera stopped")
        return jsonify({'success': True, 'message': 'Camera stopped'})
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_stats')
def get_stats():
    try:
        with state_lock:
            fps = current_fps
            objects = len(current_detections)
            classes = len(set(d['class'] for d in current_detections)) if current_detections else 0
        
        class_stats = db.get_class_statistics()
        recent_detections = db.get_recent_detections(limit=50)
        
        # Get detector statistics
        detector_stats = {}
        if detector:
            detector_stats = detector.get_statistics()
        
        stats = {
            'current_fps': round(fps, 2),
            'total_objects': objects,
            'unique_classes': classes,
            'class_distribution': class_stats.to_dict('records') if not class_stats.empty else [],
            'recent_detections': recent_detections.to_dict('records') if not recent_detections.empty else [],
            'detector_stats': detector_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_alerts')
def get_alerts():
    try:
        alerts = db.get_recent_alerts(limit=10)
        return jsonify(alerts.to_dict('records') if not alerts.empty else [])
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export_csv')
def export_csv():
    try:
        csv_path = db.export_to_csv()
        if csv_path and os.path.exists(csv_path):
            return send_file(csv_path, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to generate CSV'}), 500
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file extension
        filename = file.filename
        if filename and '.' in filename:
            file_ext = filename.rsplit('.', 1)[1].lower()
            allowed = {f.lower() for f in config.ALLOWED_EXTENSIONS}
            if file_ext not in allowed:
                return jsonify({'success': False, 'message': 'File type not allowed'}), 400
        else:
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Video uploaded: {filepath}")
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/detect_photo', methods=['POST'])
def detect_photo():
    """Detect objects in uploaded photo"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file extension for images
        filename = file.filename
        if filename and '.' in filename:
            file_ext = filename.rsplit('.', 1)[1].lower()
            allowed_images = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
            if file_ext not in allowed_images:
                return jsonify({'success': False, 'message': 'Image file type not allowed'}), 400
        else:
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        if detector is None:
            return jsonify({'success': False, 'message': 'Detector not initialized'}), 500
        
        # Read and process image
        file_bytes = file.read()
        import numpy as np
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Failed to read image'}), 400
        
        # Resize for processing
        image = cv2.resize(image, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        
        # Detect objects
        annotated_frame, detections, fps, processing_time = detector.detect_objects(image, track=False)
        
        # Log detections
        for det in detections:
            try:
                db.log_detection(det['class'], det['confidence'], det['bbox'],
                               0, 'photo_upload', None)
            except Exception as e:
                logger.warning(f"Error logging detection: {e}")
        
        # Check alerts
        check_alerts(detections)
        
        # Encode result image
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            return jsonify({'success': False, 'message': 'Failed to encode result'}), 500
        
        # Save result image
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        result_filename = f"detection_{int(time.time())}.jpg"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
        cv2.imwrite(result_path, annotated_frame)
        
        logger.info(f"Photo detection complete: {len(detections)} objects found")
        
        return jsonify({
            'success': True,
            'objects_detected': len(detections),
            'detections': detections,
            'result_image': result_filename,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error detecting photo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_result_image/<filename>')
def get_result_image(filename):
    """Get result image"""
    try:
        # Validate filename
        if '/' in filename or '\\' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error getting result image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_detection_history')
def get_detection_history():
    """Get full detection history from database"""
    try:
        limit = request.args.get('limit', 100, type=int)
        class_filter = request.args.get('class', None)
        
        if class_filter:
            detections = db.get_detections_by_class(class_filter, limit)
        else:
            detections = db.get_recent_detections(limit)
        
        return jsonify({
            'success': True,
            'total': len(detections),
            'detections': detections.to_dict('records') if not detections.empty else [],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting detection history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_class_details/<class_name>')
def get_class_details(class_name):
    """Get detailed statistics for a specific class"""
    try:
        detections = db.get_detections_by_class(class_name, limit=200)
        
        if detections.empty:
            return jsonify({'success': False, 'message': 'No detections found'}), 404
        
        stats = {
            'class_name': class_name,
            'total_count': len(detections),
            'avg_confidence': float(detections['confidence'].mean()),
            'min_confidence': float(detections['confidence'].min()),
            'max_confidence': float(detections['confidence'].max()),
            'detections': detections.to_dict('records')
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting class details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_high_confidence_detections')
def get_high_confidence_detections():
    """Get detections with high confidence scores"""
    try:
        min_conf = request.args.get('min_conf', 0.8, type=float)
        limit = request.args.get('limit', 50, type=int)
        
        detections = db.get_high_confidence_detections(min_confidence=min_conf, limit=limit)
        
        return jsonify({
            'success': True,
            'total': len(detections),
            'min_confidence': min_conf,
            'detections': detections.to_dict('records') if not detections.empty else []
        })
    except Exception as e:
        logger.error(f"Error getting high confidence detections: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_performance_metrics')
def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        if detector is None:
            return jsonify({'success': False, 'message': 'Detector not initialized'}), 500
        
        metrics = detector.get_performance_metrics()
        detector_stats = detector.get_statistics()
        
        return jsonify({
            'success': True,
            'performance': metrics,
            'statistics': detector_stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/filter_detections', methods=['POST'])
def filter_detections():
    """Filter detections by criteria"""
    try:
        data = request.get_json() or {}
        min_confidence = data.get('min_confidence', config.MODEL_CONFIDENCE)
        classes = data.get('classes', None)
        limit = data.get('limit', 100)
        
        # Get recent detections
        recent = db.get_recent_detections(limit=limit * 2)
        
        if recent.empty:
            return jsonify({'success': True, 'detections': []})
        
        # Convert to list of dicts for filtering
        filtered = []
        for _, row in recent.iterrows():
            if row['confidence'] < min_confidence:
                continue
            if classes and row['class_name'] not in classes:
                continue
            filtered.append(row.to_dict())
        
        return jsonify({
            'success': True,
            'total': len(filtered),
            'detections': filtered[:limit]
        })
    except Exception as e:
        logger.error(f"Error filtering detections: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_analytics')
def get_analytics():
    """Get comprehensive analytics"""
    try:
        # Get time range
        time_range_hours = request.args.get('hours', 24, type=int)
        
        # Get class statistics
        class_stats = db.get_class_statistics()
        
        # Get detector metrics
        if detector:
            perf_metrics = detector.get_performance_metrics()
            det_stats = detector.get_statistics()
        else:
            perf_metrics = {}
            det_stats = {}
        
        # Calculate additional metrics
        analytics = {
            'summary': {
                'total_detections': int(class_stats['count'].sum()) if not class_stats.empty else 0,
                'unique_classes': len(class_stats),
                'average_confidence': float(class_stats['avg_confidence'].mean()) if not class_stats.empty else 0
            },
            'performance': perf_metrics,
            'detector_stats': det_stats,
            'class_distribution': class_stats.to_dict('records') if not class_stats.empty else [],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== MOBILE API ENDPOINTS ====================

@app.route('/mobile/detect_image', methods=['POST'])
def mobile_detect_image():
    """Mobile endpoint: Detect objects in base64 encoded image"""
    try:
        data = request.get_json() or {}
        
        if 'image' not in data:
            return jsonify(MobileResponseFormatter.format_error_response(
                'No image provided', 'MISSING_IMAGE'
            )), 400
        
        if detector is None:
            return jsonify(MobileResponseFormatter.format_error_response(
                'Detector not initialized', 'DETECTOR_ERROR'
            )), 500
        
        # Decode base64 image
        try:
            image = MobileImageProcessor.decode_base64_image(data['image'])
        except Exception as e:
            return jsonify(MobileResponseFormatter.format_error_response(
                f'Failed to decode image: {str(e)}', 'DECODE_ERROR'
            )), 400
        
        # Resize for processing
        image = MobileImageProcessor.resize_for_processing(image)
        
        # Detect objects
        start_time = time.time()
        annotated_frame, detections, fps, processing_time = detector.detect_objects(image, track=False)
        
        # Serialize detections with proper type handling
        serialized_detections = DataTypeHandler.serialize_detections(
            detections, image.shape[1], image.shape[0]
        )
        
        # Log detections
        for det in detections:
            try:
                db.log_detection(det['class'], det['confidence'], det['bbox'],
                               0, 'mobile_image', None)
            except Exception as e:
                logger.warning(f"Error logging detection: {e}")
        
        # Format response with result image
        response = MobileResponseFormatter.format_detection_response(
            serialized_detections, processing_time, fps, annotated_frame
        )
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in mobile_detect_image: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.route('/mobile/detect_camera', methods=['POST'])
def mobile_detect_camera():
    """Mobile endpoint: Process single frame from camera"""
    try:
        data = request.get_json() or {}
        camera_id = data.get('camera_id', config.DEFAULT_CAMERA)
        
        if detector is None:
            return jsonify(MobileResponseFormatter.format_error_response(
                'Detector not initialized', 'DETECTOR_ERROR'
            )), 500
        
        try:
            camera_id = int(camera_id)
        except Exception:
            return jsonify(MobileResponseFormatter.format_error_response(
                'Invalid camera_id', 'INVALID_CAMERA_ID'
            )), 400
        
        # Open camera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            return jsonify(MobileResponseFormatter.format_error_response(
                'Cannot open camera', 'CAMERA_ERROR'
            )), 400
        
        # Read frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify(MobileResponseFormatter.format_error_response(
                'Failed to read camera frame', 'FRAME_READ_ERROR'
            )), 400
        
        # Resize for processing
        frame = MobileImageProcessor.resize_for_processing(frame)
        
        # Detect objects
        annotated_frame, detections, fps, processing_time = detector.detect_objects(frame, track=False)
        
        # Serialize detections
        serialized_detections = DataTypeHandler.serialize_detections(
            detections, frame.shape[1], frame.shape[0]
        )
        
        # Log detections
        for det in detections:
            try:
                db.log_detection(det['class'], det['confidence'], det['bbox'],
                               0, 'mobile_camera', None)
            except Exception as e:
                logger.warning(f"Error logging detection: {e}")
        
        # Format response
        response = MobileResponseFormatter.format_detection_response(
            serialized_detections, processing_time, fps, annotated_frame
        )
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in mobile_detect_camera: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.route('/mobile/available_cameras')
def mobile_available_cameras():
    """Mobile endpoint: Get list of available cameras"""
    try:
        cameras = CameraHandler.get_available_cameras()
        return jsonify(MobileResponseFormatter.format_camera_list_response(cameras))
    except Exception as e:
        logger.error(f"Error getting available cameras: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.route('/mobile/detect_video', methods=['POST'])
def mobile_detect_video():
    """Mobile endpoint: Process video file for detections"""
    try:
        if 'file' not in request.files:
            return jsonify(MobileResponseFormatter.format_error_response(
                'No file provided', 'MISSING_FILE'
            )), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify(MobileResponseFormatter.format_error_response(
                'No file selected', 'NO_FILE_SELECTED'
            )), 400
        
        if detector is None:
            return jsonify(MobileResponseFormatter.format_error_response(
                'Detector not initialized', 'DETECTOR_ERROR'
            )), 500
        
        # Save file temporarily
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 
                               f"temp_{int(time.time())}.mp4")
        file.save(filepath)
        
        try:
            # Get video properties
            video_props = MobileVideoProcessor.get_video_properties(filepath)
            
            # Extract frames
            frames = MobileVideoProcessor.extract_video_frames(filepath, max_frames=30)
            
            # Process frames
            all_detections = []
            total_processing_time = 0
            
            for frame_idx, frame in enumerate(frames):
                frame = MobileImageProcessor.resize_for_processing(frame)
                annotated_frame, detections, fps, proc_time = detector.detect_objects(frame, track=False)
                
                serialized = DataTypeHandler.serialize_detections(
                    detections, frame.shape[1], frame.shape[0]
                )
                
                all_detections.append({
                    'frame': frame_idx,
                    'detections': serialized,
                    'count': len(serialized)
                })
                
                total_processing_time += proc_time
                
                # Log detections
                for det in detections:
                    try:
                        db.log_detection(det['class'], det['confidence'], det['bbox'],
                                       frame_idx, 'mobile_video', None)
                    except Exception as e:
                        logger.warning(f"Error logging detection: {e}")
            
            avg_processing_time = total_processing_time / len(frames) if frames else 0
            
            response = {
                'success': True,
                'video_properties': video_props,
                'frames_processed': len(frames),
                'total_detections': sum(f['count'] for f in all_detections),
                'frame_detections': all_detections,
                'metrics': {
                    'avg_processing_time_ms': float(avg_processing_time * 1000),
                    'timestamp': int(time.time() * 1000)
                }
            }
            
            return jsonify(response)
        
        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    except Exception as e:
        logger.error(f"Error in mobile_detect_video: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.route('/mobile/batch_detect', methods=['POST'])
def mobile_batch_detect():
    """Mobile endpoint: Batch process multiple images"""
    try:
        data = request.get_json() or {}
        images = data.get('images', [])
        
        if not images:
            return jsonify(MobileResponseFormatter.format_error_response(
                'No images provided', 'MISSING_IMAGES'
            )), 400
        
        if detector is None:
            return jsonify(MobileResponseFormatter.format_error_response(
                'Detector not initialized', 'DETECTOR_ERROR'
            )), 500
        
        results = []
        total_time = 0
        
        for idx, img_data in enumerate(images):
            try:
                # Decode image
                image = MobileImageProcessor.decode_base64_image(img_data)
                image = MobileImageProcessor.resize_for_processing(image)
                
                # Detect
                start_time = time.time()
                annotated_frame, detections, fps, proc_time = detector.detect_objects(image, track=False)
                
                serialized = DataTypeHandler.serialize_detections(
                    detections, image.shape[1], image.shape[0]
                )
                
                results.append({
                    'image_index': idx,
                    'success': True,
                    'objects_detected': len(serialized),
                    'detections': serialized,
                    'processing_time_ms': float(proc_time * 1000)
                })
                
                total_time += proc_time
                
                # Log detections
                for det in detections:
                    try:
                        db.log_detection(det['class'], det['confidence'], det['bbox'],
                                       idx, 'mobile_batch', None)
                    except Exception as e:
                        logger.warning(f"Error logging detection: {e}")
            
            except Exception as e:
                results.append({
                    'image_index': idx,
                    'success': False,
                    'error': str(e)
                })
        
        response = {
            'success': True,
            'total_images': len(images),
            'results': results,
            'metrics': {
                'avg_processing_time_ms': float((total_time / len(images)) * 1000) if images else 0,
                'total_processing_time_ms': float(total_time * 1000),
                'timestamp': int(time.time() * 1000)
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in mobile_batch_detect: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.route('/mobile/stream_camera')
def mobile_stream_camera():
    """Mobile endpoint: Stream camera video with MJPEG"""
    try:
        camera_id = request.args.get('camera_id', config.DEFAULT_CAMERA, type=int)
        
        def generate_mobile_frames():
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                logger.error("Cannot open camera for streaming")
                return
            
            try:
                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame = MobileImageProcessor.resize_for_processing(frame)
                    
                    if detector:
                        try:
                            annotated_frame, detections, fps, _ = detector.detect_objects(frame, track=True)
                        except Exception as e:
                            logger.warning(f"Detection error: {e}")
                            annotated_frame = frame.copy()
                    else:
                        annotated_frame = frame.copy()
                    
                    ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if not ret:
                        continue
                    
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
                           b'\r\n' + frame_bytes + b'\r\n')
                    
                    frame_count += 1
            
            finally:
                cap.release()
        
        return Response(generate_mobile_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    except Exception as e:
        logger.error(f"Error in mobile_stream_camera: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.route('/mobile/stats')
def mobile_stats():
    """Mobile endpoint: Get current statistics"""
    try:
        with state_lock:
            fps = current_fps
            objects = len(current_detections)
            classes = len(set(d['class'] for d in current_detections)) if current_detections else 0
        
        stats = {
            'success': True,
            'current_fps': float(fps),
            'current_objects': int(np.int32(objects)),
            'unique_classes': int(np.int32(classes)),
            'detector_stats': detector.get_statistics() if detector else {},
            'timestamp': int(time.time() * 1000)
        }
        
        return jsonify(DataTypeHandler.convert_to_python_native(stats))
    
    except Exception as e:
        logger.error(f"Error getting mobile stats: {e}")
        return jsonify(MobileResponseFormatter.format_error_response(
            str(e), 'INTERNAL_ERROR'
        )), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        print("=" * 50)
        print("Real-Time Object Detection Server")
        print("=" * 50)
        print(f"Dashboard: http://localhost:{config.FLASK_PORT}")
        print(f"Debug Mode: {config.FLASK_DEBUG}")
        print("=" * 50)
        app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, 
                debug=config.FLASK_DEBUG, threaded=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
