# Deployment and Setup Guide

## Project Successfully Uploaded to GitHub! 🎉

Your complete Real-Time Object Detection System with Mobile Support has been successfully pushed to:
**https://github.com/rajeev-nishad20/crowd-monitoring**

---

## What's Included

### ✅ Core System
- **YOLOv8 Object Detection** - Real-time detection with tracking
- **Flask Web Application** - Full-featured dashboard
- **Mobile API** - 7 mobile-specific endpoints
- **Video Processing** - Support for images, videos, and live streams
- **Database** - SQLite logging for all detections
- **Analytics** - Comprehensive statistics and performance metrics

### ✅ Mobile Features
- Base64 image detection API
- Camera frame capture and detection
- Video file processing
- Batch image processing
- MJPEG streaming for live video
- Proper int32 data type handling
- Mobile-optimized compression

### ✅ Documentation
- `README.md` - Complete project overview
- `MOBILE_API_GUIDE.md` - Detailed API documentation
- `.gitignore` - Proper git configuration
- `requirements.txt` - All dependencies

---

## Quick Setup Instructions

### Step 1: Clone Repository
```bash
git clone https://github.com/rajeev-nishad20/crowd-monitoring.git
cd crowd-monitoring
```

### Step 2: Setup Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Run Application
```bash
python backend/app.py
```

The server will start at: **http://localhost:5000**

---

## Project Structure (Uploaded)

```
crowd-monitoring/
├── README.md                    # Complete project documentation
├── MOBILE_API_GUIDE.md         # Mobile API reference
├── .gitignore                  # Git configuration
│
├── backend/
│   ├── app.py                  # Flask application (main)
│   ├── detection.py            # YOLOv8 detection engine
│   ├── mobile_utils.py         # Mobile utilities (NEW)
│   ├── database.py             # Detection logging
│   ├── config.py               # Configuration settings
│   ├── video_processor.py      # Video processing
│   ├── requirements.txt        # Python dependencies
│   └── test_server.py          # Server testing
│
├── frontend/
│   ├── index.html              # Web dashboard
│   └── static/
│       ├── css/style.css       # Dashboard styling
│       └── js/main.js          # Frontend logic (with mobile functions)
│
├── models/
│   └── yolov8n.pt             # YOLOv8 nano model (auto-downloaded)
│
├── logs/
│   └── detections.csv         # Detection database
│
└── uploads/                    # Uploaded files storage
```

---

## Key Features Implemented

### 🎯 Core Detection
- Real-time YOLOv8 object detection
- 80 COCO dataset classes
- Configurable confidence thresholds
- Object tracking with unique IDs
- Performance monitoring (FPS, latency)

### 📱 Mobile APIs (NEW)
1. **POST /mobile/detect_image** - Base64 image detection
2. **POST /mobile/detect_camera** - Single frame capture
3. **POST /mobile/detect_video** - Video file processing
4. **POST /mobile/batch_detect** - Batch processing
5. **GET /mobile/available_cameras** - List cameras
6. **GET /mobile/stream_camera** - MJPEG streaming
7. **GET /mobile/stats** - Real-time statistics

### 🔄 Data Type Handling (NEW)
- Proper int32 array conversion
- Numpy type serialization
- JSON-compatible output
- Automatic type conversion

### 📊 Analytics & Monitoring
- Real-time statistics dashboard
- Detection history tracking
- Performance metrics
- Alert system
- CSV export

### 🎮 User Interface
- Live video feed display
- Real-time detection list
- Statistics cards
- Performance graphs
- Modal dialogs for results

---

## Mobile API Examples

### JavaScript - Detect Image
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

### JavaScript - Stream Camera
```javascript
// MJPEG streaming
document.getElementById('stream').src = '/mobile/stream_camera?camera_id=0';

// Or use mobileStreamCamera() helper
const streamUrl = mobileStreamCamera(0);
```

### JavaScript - Batch Processing
```javascript
async function batchDetect(files) {
  const images = await Promise.all(files.map(fileToBase64));
  const result = await mobileBatchDetect(images);
  console.log(`Processed ${result.total_images} images`);
}
```

---

## Configuration Options

Edit `backend/config.py` to customize:

```python
# Model Settings
MODEL_CONFIDENCE = 0.35          # Detection threshold (0-1)
MODEL_IOU_THRESHOLD = 0.5        # NMS IoU threshold
MODEL_MAX_DET = 100              # Max detections per image

# Video Settings
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
VIDEO_FPS = 30

# Alert Configuration
ALERT_CLASSES = ['person', 'car', 'truck']
ALERT_THRESHOLD = 5

# Server
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
```

---

## Testing the System

### Test Web Dashboard
1. Navigate to http://localhost:5000
2. Click "Start Camera"
3. See real-time detections
4. Upload photos or videos

### Test Mobile API with cURL

```bash
# Get available cameras
curl http://localhost:5000/mobile/available_cameras

# Detect camera frame
curl -X POST http://localhost:5000/mobile/detect_camera \
  -H "Content-Type: application/json" \
  -d '{"camera_id": 0}'

# Get stats
curl http://localhost:5000/mobile/stats
```

### Test with Python

```python
import requests
import json

# Get cameras
response = requests.get('http://localhost:5000/mobile/available_cameras')
print(response.json())

# Get stats
response = requests.get('http://localhost:5000/mobile/stats')
stats = response.json()
print(f"Current FPS: {stats['current_fps']}")
print(f"Objects detected: {stats['current_objects']}")
```

---

## Files Modified/Created

### New Files Created:
- ✅ `backend/mobile_utils.py` - Mobile utilities module
- ✅ `MOBILE_API_GUIDE.md` - Complete API documentation
- ✅ `test_mobile_api.py` - Mobile API tests

### Files Modified:
- ✅ `backend/app.py` - Added 7 mobile API endpoints
- ✅ `backend/detection.py` - Added int32 support
- ✅ `backend/requirements.txt` - Added python-dotenv
- ✅ `frontend/static/js/main.js` - Added mobile helper functions
- ✅ `README.md` - Complete project documentation

### Files Added to Git:
- ✅ `.gitignore` - Proper git configuration
- ✅ All 56 project files

---

## GitHub Repository Details

```
Repository: https://github.com/rajeev-nishad20/crowd-monitoring
Branch: main
Commits: 1
Files: 56
Size: ~170 KB

Latest Commit:
b3a0028 - Initial commit: Complete Real-Time Object Detection System 
         with Mobile Support
```

---

## System Requirements

### Minimum
- Python 3.8+
- 4GB RAM
- USB camera (optional)
- Windows/Linux/Mac

### Recommended
- Python 3.10+
- 8GB RAM
- NVIDIA GPU for faster processing
- Webcam or IP camera

---

## Troubleshooting

### 1. Camera Not Detected
```bash
# Check available cameras
curl http://localhost:5000/mobile/available_cameras

# Use different camera ID (0, 1, 2, etc.)
```

### 2. Import Errors
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

### 3. Model Download Issues
```bash
# Delete model and let it re-download
rm models/yolov8n.pt

# Run again - model will auto-download
python backend/app.py
```

### 4. Port Already in Use
```bash
# Change port in config.py
FLASK_PORT = 5001  # Change from 5000
```

---

## Performance Tips

1. **For faster detection**: Reduce image resolution
2. **For better accuracy**: Lower confidence threshold
3. **For mobile**: Use batch processing
4. **For real-time**: Use streaming endpoint

---

## Next Steps

1. ✅ Clone the repository
2. ✅ Set up virtual environment
3. ✅ Install dependencies
4. ✅ Run the application
5. 📱 Integrate with your mobile app
6. 🚀 Deploy to production

---

## Support Resources

- 📖 **Full Documentation**: See `MOBILE_API_GUIDE.md`
- 💻 **Code Examples**: Check `frontend/static/js/main.js`
- 🧪 **Test Scripts**: See `test_mobile_api.py`
- 📝 **Configuration**: Edit `backend/config.py`

---

## License

MIT License - Free to use and modify

---

## Contact

**Rajeev Nishad**
- GitHub: https://github.com/rajeev-nishad20
- Repository: https://github.com/rajeev-nishad20/crowd-monitoring

---

## Summary

✅ **All files successfully uploaded to GitHub!**

Your Real-Time Object Detection System with complete mobile support is now:
- Stored safely in version control
- Ready to share and collaborate
- Documented with comprehensive guides
- Set up for easy deployment

**Start using it now:**
```bash
git clone https://github.com/rajeev-nishad20/crowd-monitoring.git
cd crowd-monitoring
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python backend/app.py
```

Then visit: **http://localhost:5000**

---

**Happy coding! 🚀**
