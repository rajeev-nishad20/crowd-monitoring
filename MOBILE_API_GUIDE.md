# Mobile API Guide

## Overview

This guide provides comprehensive documentation for using the Real-Time Object Detection system with mobile devices. The system now supports mobile-optimized APIs for image, video, and camera detection with proper handling of int32 data types and efficient data transfer.

## Quick Start

### Start the Server

```bash
# Activate Python environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run the application
python backend/app.py
```

Server will be available at: `http://localhost:5000`

---

## Mobile API Endpoints

### 1. Detect Image (Base64)

**Endpoint:** `POST /mobile/detect_image`

Detect objects in a base64-encoded image.

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA..."
}
```

**Response:**
```json
{
  "success": true,
  "objects_detected": 5,
  "detections": [
    {
      "class": "person",
      "confidence": 0.95,
      "bbox": [100, 150, 250, 450],
      "track_id": 1,
      "area": 45000,
      "aspect_ratio": 0.67
    }
  ],
  "metrics": {
    "processing_time_ms": 125.5,
    "fps": 7.9,
    "timestamp": 1700812345000
  },
  "image": "data:image/jpeg;base64,..."
}
```

**JavaScript Example:**
```javascript
// Convert file to base64
async function detectImage(file) {
  const base64 = await fileToBase64(file);
  const result = await mobileDetectImage(base64);
  console.log('Detections:', result.detections);
}
```

---

### 2. Detect Camera Frame

**Endpoint:** `POST /mobile/detect_camera`

Capture a single frame from camera and detect objects.

**Request:**
```json
{
  "camera_id": 0
}
```

**Response:**
```json
{
  "success": true,
  "objects_detected": 3,
  "detections": [
    {
      "class": "car",
      "confidence": 0.92,
      "bbox": [50, 100, 200, 250],
      "track_id": null,
      "area": 22500,
      "aspect_ratio": 1.33
    }
  ],
  "metrics": {
    "processing_time_ms": 95.3,
    "fps": 10.5,
    "timestamp": 1700812345000
  },
  "image": "data:image/jpeg;base64,..."
}
```

**JavaScript Example:**
```javascript
async function captureAndDetect() {
  const result = await mobileDetectCamera(0);
  displayDetections(result.detections);
}
```

---

### 3. Get Available Cameras

**Endpoint:** `GET /mobile/available_cameras`

Get list of all available cameras on the device.

**Response:**
```json
{
  "success": true,
  "cameras": [
    {
      "id": 0,
      "width": 1280,
      "height": 720,
      "fps": 30
    },
    {
      "id": 1,
      "width": 640,
      "height": 480,
      "fps": 30
    }
  ],
  "count": 2,
  "timestamp": 1700812345000
}
```

**JavaScript Example:**
```javascript
async function listCameras() {
  const cameras = await mobileGetAvailableCameras();
  cameras.forEach(cam => {
    console.log(`Camera ${cam.id}: ${cam.width}x${cam.height} @ ${cam.fps}fps`);
  });
}
```

---

### 4. Detect Video

**Endpoint:** `POST /mobile/detect_video`

Process video file and detect objects in frames.

**Request:** Multipart form data with video file

**Response:**
```json
{
  "success": true,
  "video_properties": {
    "fps": 30,
    "frame_count": 900,
    "width": 1280,
    "height": 720,
    "duration_seconds": 30
  },
  "frames_processed": 30,
  "total_detections": 156,
  "frame_detections": [
    {
      "frame": 0,
      "detections": [
        {
          "class": "person",
          "confidence": 0.88,
          "bbox": [100, 150, 250, 400],
          "track_id": 1,
          "area": 37500,
          "aspect_ratio": 0.67
        }
      ],
      "count": 1
    }
  ],
  "metrics": {
    "avg_processing_time_ms": 105.2,
    "timestamp": 1700812345000
  }
}
```

**JavaScript Example:**
```javascript
async function processVideo(file) {
  const result = await mobileDetectVideo(file);
  console.log(`Total detections: ${result.total_detections}`);
  result.frame_detections.forEach(frame => {
    console.log(`Frame ${frame.frame}: ${frame.count} objects`);
  });
}
```

---

### 5. Batch Detect Images

**Endpoint:** `POST /mobile/batch_detect`

Process multiple images in a single request.

**Request:**
```json
{
  "images": [
    "data:image/jpeg;base64,...",
    "data:image/jpeg;base64,...",
    "data:image/jpeg;base64,..."
  ]
}
```

**Response:**
```json
{
  "success": true,
  "total_images": 3,
  "results": [
    {
      "image_index": 0,
      "success": true,
      "objects_detected": 5,
      "detections": [...],
      "processing_time_ms": 95.2
    },
    {
      "image_index": 1,
      "success": true,
      "objects_detected": 3,
      "detections": [...],
      "processing_time_ms": 102.1
    },
    {
      "image_index": 2,
      "success": true,
      "objects_detected": 7,
      "detections": [...],
      "processing_time_ms": 98.5
    }
  ],
  "metrics": {
    "avg_processing_time_ms": 98.6,
    "total_processing_time_ms": 295.8,
    "timestamp": 1700812345000
  }
}
```

**JavaScript Example:**
```javascript
async function batchProcess(files) {
  const base64Images = await Promise.all(
    files.map(file => fileToBase64(file))
  );
  const result = await mobileBatchDetect(base64Images);
  console.log(`Processed ${result.total_images} images`);
}
```

---

### 6. Stream Camera (MJPEG)

**Endpoint:** `GET /mobile/stream_camera?camera_id=0`

Stream live camera video with real-time object detection.

**Response:** MJPEG stream (multipart/x-mixed-replace)

**JavaScript Example:**
```javascript
// Display stream in image element
const streamUrl = mobileStreamCamera(0);
document.getElementById('videoFeed').src = streamUrl;

// Or use in video element with custom streaming
const xhr = new XMLHttpRequest();
xhr.open('GET', '/mobile/stream_camera?camera_id=0', true);
xhr.responseType = 'arraybuffer';
xhr.onprogress = function() {
  // Handle streaming data
};
xhr.send();
```

---

### 7. Get Statistics

**Endpoint:** `GET /mobile/stats`

Get current detection statistics and performance metrics.

**Response:**
```json
{
  "success": true,
  "current_fps": 28.5,
  "current_objects": 5,
  "unique_classes": 3,
  "detector_stats": {
    "total_detections": 1250,
    "unique_classes": 80,
    "detection_counts": {
      "person": 450,
      "car": 350,
      "dog": 200
    },
    "avg_confidence": 0.88,
    "frame_count": 850,
    "avg_processing_time": 0.095,
    "avg_fps": 25.3,
    "quality_score": 87.5
  },
  "timestamp": 1700812345000
}
```

---

## JavaScript Mobile API Helper Functions

### 1. File to Base64
```javascript
async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
}
```

### 2. Canvas to Base64
```javascript
function canvasToBase64(canvas) {
  return canvas.toDataURL('image/jpeg', 0.85);
}
```

### 3. Process Image with Mobile API
```javascript
async function processImageWithMobileAPI(file) {
  try {
    const base64 = await fileToBase64(file);
    const result = await mobileDetectImage(base64);
    return result;
  } catch (error) {
    console.error('Error processing image:', error);
    return null;
  }
}
```

---

## Data Types and int32 Handling

The API properly handles and converts int32 values to standard JSON-compatible formats:

### Int32 Fields
- `objects_detected`: int32 → converted to int
- `frame_count`: int32 → converted to int
- `unique_classes`: int32 → converted to int
- `area`: int32 → bounding box area
- `bbox`: [int32, int32, int32, int32] → [x1, y1, x2, y2]
- `track_id`: int32 | null → object tracking ID

### Automatic Conversions
```python
# Python backend converts numpy types:
np.int32(value) → int(value)
np.float32(value) → float(value)
np.ndarray → list
np.bool_ → bool
```

---

## Error Handling

All mobile endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_TYPE",
  "timestamp": 1700812345000
}
```

### Common Error Codes
- `MISSING_IMAGE`: No image provided
- `DECODE_ERROR`: Failed to decode image
- `DETECTOR_ERROR`: Detector not initialized
- `CAMERA_ERROR`: Cannot open camera
- `FRAME_READ_ERROR`: Failed to read frame
- `MISSING_FILE`: No file uploaded
- `INVALID_CAMERA_ID`: Invalid camera ID format
- `INTERNAL_ERROR`: Server error

### JavaScript Error Handling
```javascript
async function detectWithErrorHandling(base64Image) {
  try {
    const result = await mobileDetectImage(base64Image);
    if (!result.success) {
      console.error(`Error: ${result.error_code} - ${result.error}`);
      return null;
    }
    return result;
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}
```

---

## Performance Tips

### 1. Image Compression
```javascript
// Compress before sending
function compressImage(canvas) {
  return canvas.toDataURL('image/jpeg', 0.75); // 75% quality
}
```

### 2. Batch Processing
For multiple images, use batch endpoint for efficiency:
```javascript
// Instead of:
for (const image of images) {
  await mobileDetectImage(image);
}

// Use:
await mobileBatchDetect(images); // More efficient
```

### 3. Camera Streaming
Use MJPEG stream for continuous real-time detection:
```javascript
// Instead of:
for (let i = 0; i < 100; i++) {
  await mobileDetectCamera();
}

// Use:
const streamUrl = mobileStreamCamera();
// Update display with stream
```

---

## Mobile Integration Example

### Complete Mobile App Example
```javascript
class MobileDetectionApp {
  constructor() {
    this.camera = 0;
    this.isStreaming = false;
  }
  
  async initialize() {
    const cameras = await mobileGetAvailableCameras();
    console.log('Available cameras:', cameras);
  }
  
  async detectFromFile(file) {
    showLoading(true);
    const result = await processImageWithMobileAPI(file);
    showLoading(false);
    
    if (result) {
      this.displayResults(result);
    }
  }
  
  startStream() {
    const streamUrl = mobileStreamCamera(this.camera);
    document.getElementById('stream').src = streamUrl;
    this.isStreaming = true;
  }
  
  stopStream() {
    document.getElementById('stream').src = '';
    this.isStreaming = false;
  }
  
  displayResults(result) {
    const html = `
      <div class="results">
        <h3>Detected Objects: ${result.objects_detected}</h3>
        <div class="detections">
          ${result.detections.map(det => `
            <div class="detection">
              <p>${det.class} - ${(det.confidence * 100).toFixed(1)}%</p>
            </div>
          `).join('')}
        </div>
        <p>Processing time: ${result.metrics.processing_time_ms.toFixed(1)}ms</p>
      </div>
    `;
    document.getElementById('results').innerHTML = html;
  }
}

// Usage
const app = new MobileDetectionApp();
app.initialize();

// File upload handler
document.getElementById('fileInput').addEventListener('change', (e) => {
  app.detectFromFile(e.target.files[0]);
});
```

---

## Testing the API

### Using cURL

**Test Image Detection:**
```bash
curl -X POST http://localhost:5000/mobile/detect_image \
  -H "Content-Type: application/json" \
  -d '{"image":"data:image/jpeg;base64,..."}'
```

**Test Camera Detection:**
```bash
curl -X POST http://localhost:5000/mobile/detect_camera \
  -H "Content-Type: application/json" \
  -d '{"camera_id":0}'
```

**Get Available Cameras:**
```bash
curl http://localhost:5000/mobile/available_cameras
```

---

## Statistics and Monitoring

### Real-time Stats Polling
```javascript
async function pollStats(interval = 1000) {
  setInterval(async () => {
    const stats = await mobileGetStats();
    updateStatsDisplay(stats);
  }, interval);
}

function updateStatsDisplay(stats) {
  document.getElementById('fps').textContent = stats.current_fps.toFixed(1);
  document.getElementById('objects').textContent = stats.current_objects;
  document.getElementById('quality').textContent = 
    stats.detector_stats.quality_score.toFixed(1) + '%';
}
```

---

## Support for Multiple Data Types

The system automatically handles:
- **Image Formats**: JPEG, PNG, BMP, GIF
- **Video Formats**: MP4, AVI, MOV, MKV
- **Data Types**: int32, int64, float32, float64, numpy arrays
- **Encoding**: Base64 for HTTP transmission, JPEG compression for streaming

---

## Deployment Considerations

### Production Setup
```bash
# Use gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app

# Or use environment variables
FLASK_ENV=production python backend/app.py
```

### Mobile Device Configuration
- Set appropriate `VIDEO_WIDTH` and `VIDEO_HEIGHT` in config
- Adjust `MODEL_CONFIDENCE` threshold for your use case
- Configure `ALERT_THRESHOLD` for event detection

---

## Troubleshooting

### Common Issues

**Issue: Camera not detected**
```
Solution: Check /mobile/available_cameras endpoint
  - Verify camera is connected
  - Check device permissions
```

**Issue: Detection takes too long**
```
Solution: 
  - Use batch processing for multiple images
  - Reduce image resolution
  - Adjust MODEL_CONFIDENCE threshold
```

**Issue: Memory issues with video processing**
```
Solution:
  - Process videos in chunks
  - Use streaming endpoint instead of batch
  - Reduce max_frames parameter
```

---

## API Limits

- **Max Upload Size**: 100 MB
- **Max Detections per Image**: 100
- **Max Batch Images**: Limited by server memory
- **Stream Frame Rate**: Configurable (default 30 FPS)

---

## Future Enhancements

- WebSocket support for real-time bidirectional communication
- Custom model support for domain-specific detection
- Advanced filtering and post-processing options
- Cloud integration for processing power sharing
