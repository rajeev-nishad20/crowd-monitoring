# Real-Time Object Detection System with Mobile Support

A comprehensive real-time object detection system powered by YOLOv8, with mobile API support, live video streaming, and advanced analytics.

## Features

✨ **Core Features:**
- Real-time object detection using YOLOv8
- Live video streaming with MJPEG
- Photo and video file analysis
- Object tracking with unique IDs
- Alert system for specific object classes
- Comprehensive statistics and analytics
- CSV export functionality

📱 **Mobile Support:**
- Base64 image detection API
- Single camera frame capture
- Video file processing
- Batch image detection
- Mobile-optimized MJPEG streaming
- Proper int32 data type handling
- Efficient compression and encoding

🎯 **Advanced Features:**
- High-confidence detection filtering
- Detection history and filtering
- Performance metrics tracking
- Real-time FPS and latency monitoring
- Database logging of all detections
- Web dashboard with live analytics
- Multi-camera support

## System Requirements

- **OS**: Windows 10+ (or any OS with Python support)
- **Python**: 3.8+
- **CUDA** (optional): For GPU acceleration
- **RAM**: 4GB+ recommended
- **Camera**: USB or built-in camera (optional)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/rajeev-nishad20/crowd-monitoring.git
cd crowd-monitoring
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate     # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Run the Application

```bash
python backend/app.py
```

The application will start at: `http://localhost:5000`

## Quick Start Guide

### Desktop Dashboard

1. Open browser and navigate to `http://localhost:5000`
2. Click **"Start Camera"** to begin detection
3. View real-time detections, statistics, and alerts
4. Upload photos or videos for analysis
5. Export detection history as CSV

### Mobile API Usage

#### Detect Image (Base64)

```javascript
async function detectImage(file) {
  const base64 = await fileToBase64(file);
  const response = await fetch('/mobile/detect_image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: base64 })
  });
  const result = await response.json();
  console.log('Detections:', result.detections);
}
```

#### Detect Camera Frame

```javascript
async function captureAndDetect() {
  const response = await fetch('/mobile/detect_camera', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ camera_id: 0 })
  });
  const result = await response.json();
  console.log('Objects detected:', result.objects_detected);
}
```

#### Stream Camera (MJPEG)

```javascript
// Display live stream in img or video element
document.getElementById('stream').src = '/mobile/stream_camera?camera_id=0';
```

For more API examples, see [MOBILE_API_GUIDE.md](MOBILE_API_GUIDE.md)

## Project Structure

```
crowd-monitoring/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── detection.py           # YOLOv8 detection logic
│   ├── mobile_utils.py        # Mobile API utilities
│   ├── database.py            # Detection logging
│   ├── config.py              # Configuration
│   ├── video_processor.py     # Video processing
│   ├── requirements.txt       # Python dependencies
│   └── __pycache__/
├── frontend/
│   ├── index.html             # Web dashboard
│   ├── static/
│   │   ├── css/style.css      # Dashboard styling
│   │   └── js/main.js         # Frontend logic
│   └── real-time-object-detection.code-workspace
├── models/
│   └── yolov8n.pt            # YOLOv8 nano model
├── logs/
│   └── detections.csv         # Detection log
├── uploads/                   # Uploaded files
├── MOBILE_API_GUIDE.md        # Mobile API documentation
└── README.md                  # This file
```

## API Endpoints

### Web Dashboard
- `GET /` - Dashboard page
- `POST /start_camera` - Start camera
- `POST /stop_camera` - Stop camera
- `GET /video_feed` - Live video stream

### Photo & Video
- `POST /detect_photo` - Analyze uploaded photo
- `POST /upload_video` - Upload video file
- `GET /get_result_image/<filename>` - Get detection result

### Analytics
- `GET /get_stats` - Current statistics
- `GET /get_alerts` - Recent alerts
- `GET /get_detection_history` - Full detection history
- `GET /get_analytics` - Comprehensive analytics

### Mobile APIs
- `POST /mobile/detect_image` - Base64 image detection
- `POST /mobile/detect_camera` - Single frame capture
- `POST /mobile/detect_video` - Video processing
- `POST /mobile/batch_detect` - Batch image processing
- `GET /mobile/available_cameras` - List cameras
- `GET /mobile/stream_camera` - MJPEG stream
- `GET /mobile/stats` - Statistics

## Configuration

Edit `backend/config.py` to customize:

```python
# Model Settings
MODEL_CONFIDENCE = 0.35          # Detection confidence threshold
MODEL_IOU_THRESHOLD = 0.5        # NMS IoU threshold
MODEL_MAX_DET = 100              # Max detections per image

# Video Settings
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
VIDEO_FPS = 30

# Alert Settings
ALERT_CLASSES = ['person', 'car', 'truck']
ALERT_THRESHOLD = 5

# Server Settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
```

## Performance Tips

1. **For Mobile**: Use batch processing for multiple images
2. **For Real-time**: Use streaming endpoint instead of repeated API calls
3. **For Accuracy**: Adjust `MODEL_CONFIDENCE` threshold
4. **For Speed**: Use `MODEL_IOU_THRESHOLD` to reduce NMS time

## Data Type Support

The system properly handles:
- **int32**: Bounding box coordinates, areas, counters
- **float32**: Confidence scores, FPS metrics
- **numpy arrays**: Image data and tensor operations
- **JSON serialization**: Automatic conversion for API responses

## Troubleshooting

### Camera Not Working
- Check `/mobile/available_cameras` endpoint
- Verify camera permissions
- Try different camera ID (0, 1, 2, etc.)

### Detection is Slow
- Reduce image resolution
- Adjust `MODEL_CONFIDENCE` threshold
- Use batch processing for multiple images

### Memory Issues
- Reduce `MODEL_MAX_DET` limit
- Process videos in chunks
- Close other applications

## Testing

### Manual Testing with cURL

```bash
# Test image detection
curl -X POST http://localhost:5000/mobile/detect_image \
  -H "Content-Type: application/json" \
  -d '{"image":"data:image/jpeg;base64,..."}'

# Get available cameras
curl http://localhost:5000/mobile/available_cameras

# Get statistics
curl http://localhost:5000/mobile/stats
```

## Development

### Project Setup
```bash
# Install development dependencies
pip install -r backend/requirements.txt
pytest                          # Run tests
```

### Code Structure
- `detection.py` - Core detection logic with int32 support
- `mobile_utils.py` - Mobile-specific utilities
- `app.py` - Flask API endpoints
- `database.py` - Detection logging

## Supported Object Classes

The system detects 80 COCO dataset classes including:
- person, bicycle, car, motorcycle, airplane, bus, train, truck
- boat, bird, cat, dog, horse, sheep, cow, elephant
- backpack, umbrella, handbag, tie, suitcase, skis, sports ball
- bottle, cup, fork, knife, spoon, bowl, banana, apple
- And 52 more...

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## Author

**Rajeev Nishad**
- GitHub: [@rajeev-nishad20](https://github.com/rajeev-nishad20)
- Email: rajeev.nishad20@example.com

## Support

For issues and questions:
1. Check [MOBILE_API_GUIDE.md](MOBILE_API_GUIDE.md)
2. Review existing issues on GitHub
3. Create a new issue with detailed description

## Acknowledgments

- YOLOv8 by Ultralytics
- Flask framework
- OpenCV library
- PyTorch

## Roadmap

- [ ] WebSocket support for real-time communication
- [ ] Custom model training UI
- [ ] Cloud storage integration
- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced filtering options
- [ ] Multi-GPU support

---

**Status**: ✅ Production Ready

Last Updated: December 1, 2025
