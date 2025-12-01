# 🎯 QUICK START & RUN GUIDE

## ✅ APPLICATION IS RUNNING NOW!

```
🟢 Status: ACTIVE & RUNNING
📍 URL: http://localhost:5000
⏱️ Server: Flask Development Server
🔧 Port: 5000
```

---

## 🚀 HOW TO ACCESS

### Option 1: Web Browser (Recommended)
```
Open in browser: http://localhost:5000
```

### Option 2: Network Access
```
From any device on network:
http://172.20.10.2:5000
```

### Option 3: Command Line
```powershell
# Check if running
curl http://localhost:5000

# Get stats
curl http://localhost:5000/get_stats

# Get alerts
curl http://localhost:5000/get_alerts
```

---

## 🎥 FEATURES TO TRY

### 1. Start Live Detection
```
Click "▶ Start Camera" button
→ Live video feed will appear
→ Real-time object detection starts
→ Statistics update every second
```

### 2. Monitor Statistics
```
Watch in real-time:
- FPS (frames per second)
- Object count
- Detected classes
- Total detections
```

### 3. View Alerts
```
Alerts trigger when:
- 5+ persons detected
- 5+ cars detected
- 5+ trucks detected
(Configurable in config.py)
```

### 4. Export Data
```
Click "📊 Export CSV" to download:
- detection_YYYYMMDD_HHMMSS.csv
- Contains all detection records
```

### 5. Upload Videos
```
Click "📁 Upload Video" to:
- Upload pre-recorded videos
- Process for detection
- Analyze offline
```

---

## 📊 EXPECTED OUTPUT

### When You Start Camera:
```
✅ Camera 0 started
✅ Video feed displaying
✅ FPS counter shows ~20-30
✅ Objects detected and labeled
✅ Bounding boxes drawn
✅ Statistics updating
✅ Alerts logging (if threshold met)
```

### In Server Terminal:
```
INFO:werkzeug:172.20.10.2 - - [20/Nov/2025 23:07:39] "POST /start_camera HTTP/1.1" 200
INFO:__main__:Camera 0 started
INFO:werkzeug:172.20.10.2 - - [20/Nov/2025 23:07:40] "GET /get_stats HTTP/1.1" 200
INFO:werkzeug:172.20.10.2 - - [20/Nov/2025 23:07:41] "GET /get_stats HTTP/1.1" 200
```

---

## 🔧 CONFIGURATION OPTIONS

### Change Model Confidence (Lower = More Detections)
```python
# File: backend/config.py
MODEL_CONFIDENCE = 0.5  # Change to 0.3-0.7
```

### Change Alert Threshold
```python
# File: backend/config.py
ALERT_THRESHOLD = 5  # Alert when N objects detected
ALERT_CLASSES = ['person', 'car', 'truck']  # Classes to alert on
```

### Change Video Resolution
```python
# File: backend/config.py
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
# Change to higher values for better quality (slower)
```

### Enable/Disable Debug Mode
```python
# File: backend/config.py
FLASK_DEBUG = True  # Set to False for production
```

---

## 🎮 KEYBOARD SHORTCUTS

In Dashboard:
- **Click "Start Camera"** - Begin detection
- **Click "Stop Camera"** - Stop detection
- **Click "Export CSV"** - Download data
- **Click "Upload Video"** - Upload for processing

---

## 🛠️ TROUBLESHOOTING

### Issue: Camera not opening
```
Solution:
1. Check if camera is connected
2. Ensure no other app is using camera
3. Try: config.py → DEFAULT_CAMERA = 1
4. Restart browser
```

### Issue: No objects detected
```
Solution:
1. Ensure objects are visible to camera
2. Lower MODEL_CONFIDENCE in config.py
3. Check lighting conditions
4. Ensure YOLOv8 model is loaded
```

### Issue: Dashboard won't load
```
Solution:
1. Clear browser cache (Ctrl+Shift+Del)
2. Try incognito/private window
3. Hard refresh: Ctrl+Shift+R
4. Check http://localhost:5000
```

### Issue: Server won't start
```
Solution:
1. Kill any existing python: taskkill /F /IM python.exe
2. Check port 5000 is free: netstat -ano | findstr :5000
3. Install dependencies: pip install -r backend/requirements.txt
4. Try different port: config.py → FLASK_PORT = 5001
```

---

## 📈 PERFORMANCE TIPS

### For Better FPS:
```
1. Lower VIDEO_WIDTH/HEIGHT in config.py
2. Lower MODEL_CONFIDENCE threshold
3. Use model: yolov8n (already using - smallest)
4. Close other applications
5. Ensure good camera resolution
```

### For Better Detection:
```
1. Increase MODEL_CONFIDENCE to 0.7
2. Increase VIDEO_WIDTH/HEIGHT to 1280x720
3. Improve lighting around objects
4. Use model: yolov8m (larger, slower)
5. Reduce ALERT_THRESHOLD for more sensitivity
```

---

## 📊 DATABASE & LOGGING

### View Detected Objects
```
File: logs/detections.db
Type: SQLite3 Database
Contains:
- All detected objects
- Timestamps
- Confidence scores
- Bounding boxes
- Tracking IDs
```

### Export Statistics
```
Click "📊 Export CSV" to get:
logs/detections_TIMESTAMP.csv
Columns:
- id, timestamp, class_name, confidence
- bbox_x1, bbox_y1, bbox_x2, bbox_y2
- frame_number, source, tracking_id
```

---

## 🔐 SECURITY NOTES

✅ **Secure by Default:**
- Input validation on all endpoints
- SQL injection prevention
- XSS attack prevention
- CORS properly configured
- Safe error messages
- Thread-safe operations

⚠️ **Before Production:**
- Change SECRET_KEY in config.py
- Disable FLASK_DEBUG = False
- Use HTTPS/SSL certificates
- Implement authentication
- Add rate limiting
- Use production WSGI server

---

## 📱 MOBILE ACCESS

### From Phone/Tablet on Same Network:
```
1. Find your machine IP:
   - Windows: ipconfig (look for IPv4 Address)
   - Should be 172.20.10.2 or similar

2. On mobile browser, go to:
   http://172.20.10.2:5000

3. Dashboard will work on mobile!
```

---

## 🔄 RESTART APPLICATION

### If Something Goes Wrong:
```powershell
# Press Ctrl+C in the terminal to stop

# Then restart:
cd "c:\Users\RAJEEV NISHAD\real-time-object-detection"
python backend/app.py
```

### Or Kill and Restart:
```powershell
# Kill all Python processes
taskkill /F /IM python.exe

# Restart
cd "c:\Users\RAJEEV NISHAD\real-time-object-detection"
python backend/app.py
```

---

## 📊 REAL-TIME MONITORING

### Watch Server Activity:
```
Server terminal shows:
- Requests coming in
- Response status codes
- Processing time
- Errors (if any)
```

### Monitor Database:
```
In terminal:
sqlite3 logs/detections.db
SELECT COUNT(*) FROM detections;
SELECT class_name, COUNT(*) FROM detections GROUP BY class_name;
```

---

## 🎯 NEXT STEPS

### 1. Try the Dashboard
```
✅ Open http://localhost:5000
✅ Click "Start Camera"
✅ Watch live detection
✅ Check statistics
```

### 2. Upload a Video
```
✅ Click "Upload Video"
✅ Choose a video file
✅ System will process it
```

### 3. Export Data
```
✅ Click "Export CSV"
✅ Download detection records
✅ Analyze results
```

### 4. Configure & Customize
```
✅ Edit config.py for your needs
✅ Change alert thresholds
✅ Adjust model confidence
✅ Modify UI if desired
```

---

## 📞 GETTING HELP

### Check Logs:
```
1. Terminal output (main source)
2. logs/detections.db (database logs)
3. logs/detections.csv (exported data)
```

### Documentation:
```
1. PROJECT_FIXES_SUMMARY.md
2. DETAILED_FIX_REPORT.md
3. README_COMPLETION.md
4. FULL_EXECUTION_REPORT.md
```

### Common Commands:
```powershell
# Start server
python backend/app.py

# Check if port is in use
netstat -ano | findstr :5000

# Kill process on port 5000
taskkill /F /PID <PID>

# View database
sqlite3 logs/detections.db

# List files in project
dir /s
```

---

## ✨ YOU'RE ALL SET! 

🎉 **Your application is running and ready to use!**

### Summary:
- ✅ Application: RUNNING
- ✅ Dashboard: http://localhost:5000
- ✅ All Features: WORKING
- ✅ Database: INITIALIZED
- ✅ Model: LOADED
- ✅ Security: ENHANCED

### What to do next:
1. Open dashboard in browser
2. Start the camera
3. Watch objects being detected in real-time
4. Explore features
5. Export data as needed

---

**Last Updated:** November 20, 2025
**Status:** 🟢 RUNNING & READY
