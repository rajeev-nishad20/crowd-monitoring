// Real-Time Object Detection Dashboard
// Enhanced with live updates, history tracking, and improved detection

let isRunning = false;
let updateInterval = null;
const UPDATE_INTERVAL = 500; // Update every 500ms for smoother live experience
let detectionHistory = []; // Store detection history
let currentPhotoData = null; // Store current photo results
const MAX_HISTORY = 100; // Limit history to 100 items
let lastStatsUpdate = 0;
const MIN_STATS_UPDATE_INTERVAL = 500; // Minimum interval between stat updates

// Initialize on document load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized with enhanced real-time features');
    initializeEventListeners();
    updateStatusIndicator();
    loadDetectionHistoryFromStorage();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Video upload handler
    const videoUpload = document.getElementById('videoUpload');
    if (videoUpload) {
        videoUpload.addEventListener('change', handleVideoUpload);
    }
    
    // Photo upload handler
    const photoUpload = document.getElementById('photoUpload');
    if (photoUpload) {
        photoUpload.addEventListener('change', handlePhotoUpload);
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('photoModal');
    if (modal) {
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                closePhotoModal();
            }
        });
    }
}

/**
 * Start camera and begin streaming
 */
async function startCamera() {
    try {
        const startBtn = document.getElementById('startCameraBtn');
        const stopBtn = document.getElementById('stopCameraBtn');
        const cameraInput = document.getElementById('cameraIdInput');
        
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.textContent = 'Starting...';
        }

        let cameraId = 0;
        if (cameraInput && cameraInput.value !== '') {
            cameraId = parseInt(cameraInput.value, 10);
            if (Number.isNaN(cameraId) || cameraId < 0) {
                showNotification('Invalid camera id. Please enter a non-negative integer.', 'error');
                if (startBtn) { startBtn.disabled = false; startBtn.textContent = '▶ Start Camera'; }
                return;
            }
        }

        const response = await fetch('/start_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ camera_id: cameraId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            isRunning = true;
            const videoFeed = document.getElementById('videoFeed');
            const placeholder = document.getElementById('placeholder');
            
            // Set video feed source
            if (videoFeed) {
                videoFeed.src = '/video_feed?t=' + Date.now();
                videoFeed.onload = () => {
                    console.log('Video feed loaded');
                };
                videoFeed.onerror = (e) => {
                    console.error('Video feed error:', e);
                    showNotification('Video feed error: ' + e.message, 'error');
                };
                videoFeed.style.display = 'block';
            }
            
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            // Update button states
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            
            updateStatusIndicator();
            
            // Start updating statistics
            if (!updateInterval) {
                updateInterval = setInterval(updateStats, UPDATE_INTERVAL);
            }
            
            showNotification('Camera started successfully! FPS and stats updating...', 'success');
            console.log('Camera started on ID:', cameraId);
        } else {
            showNotification('Failed to start camera: ' + data.message, 'error');
            console.error('Camera start failed:', data);
            if (startBtn) { 
                startBtn.disabled = false; 
                startBtn.textContent = '▶ Start Camera'; 
            }
        }
    } catch (error) {
        console.error('Error starting camera:', error);
        showNotification('Error: ' + error.message, 'error');
        const startBtn = document.getElementById('startCameraBtn');
        if (startBtn) { startBtn.disabled = false; startBtn.textContent = '▶ Start Camera'; }
    }
}

/**
 * Stop camera streaming
 */
async function stopCamera() {
    try {
        const response = await fetch('/stop_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            isRunning = false;
            const videoFeed = document.getElementById('videoFeed');
            const placeholder = document.getElementById('placeholder');
            const startBtn = document.getElementById('startCameraBtn');
            const stopBtn = document.getElementById('stopCameraBtn');
            
            // Clear video source
            if (videoFeed) {
                videoFeed.src = '';
                videoFeed.style.display = 'none';
            }
            
            if (placeholder) {
                placeholder.style.display = 'block';
            }
            
            // Update button states
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = '▶ Start Camera';
            }
            if (stopBtn) {
                stopBtn.disabled = true;
            }
            
            updateStatusIndicator();
            
            // Stop updating statistics
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
            
            showNotification('Camera stopped', 'info');
            console.log('Camera stopped');
        } else {
            showNotification('Failed to stop camera: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error stopping camera:', error);
        showNotification('Error: ' + error.message, 'error');
    }
}

/**
 * Update live statistics with improved performance
 */
async function updateStats() {
    if (!isRunning) {
        return;
    }
    
    try {
        const response = await fetch('/get_stats');
        if (!response.ok) {
            console.error('Stats fetch failed:', response.status);
            return;
        }
        
        const stats = await response.json();
        
        // Update FPS with color coding
        const fpsValue = document.getElementById('fpsValue');
        if (fpsValue) {
            fpsValue.textContent = stats.current_fps.toFixed(1);
            // Color code: Red < 15, Yellow < 25, Green >= 25
            if (stats.current_fps < 15) {
                fpsValue.style.color = '#ff6b6b';
            } else if (stats.current_fps < 25) {
                fpsValue.style.color = '#ffd93d';
            } else {
                fpsValue.style.color = '#6bcf7f';
            }
        }
        
        // Update object count with pulse animation
        const objectCount = document.getElementById('objectCount');
        if (objectCount) {
            const newCount = stats.total_objects;
            if (objectCount.textContent !== newCount.toString()) {
                objectCount.textContent = newCount;
                objectCount.style.animation = 'none';
                setTimeout(() => {
                    objectCount.style.animation = 'pulse 0.5s ease';
                }, 10);
            }
        }
        
        // Update class count
        const classCount = document.getElementById('classCount');
        if (classCount) {
            classCount.textContent = stats.unique_classes;
        }
        
        // Update recent detections list
        if (stats.recent_detections) {
            updateDetectionList(stats.recent_detections);
        }
        
        // Update class distribution chart
        if (stats.class_distribution) {
            updateClassStats(stats.class_distribution);
        }
        
        // Update total detections from database
        if (stats.class_distribution && stats.class_distribution.length > 0) {
            const total = stats.class_distribution.reduce((sum, cls) => sum + (cls.count || 0), 0);
            const totalDetections = document.getElementById('totalDetections');
            if (totalDetections) {
                totalDetections.textContent = total;
            }
        }
        
        // Update performance metrics if available
        if (stats.detector_stats) {
            updatePerformanceMetrics(stats.detector_stats);
        }
        
        // Update alerts
        await updateAlerts();
        
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

/**
 * Update detection list with live refresh
 */
function updateDetectionList(detections) {
    const detectionList = document.getElementById('detectionList');
    if (!detectionList) return;
    
    if (!detections || detections.length === 0) {
        detectionList.innerHTML = '<p style="text-align: center; color: #999;">No detections yet</p>';
        return;
    }
    
    const html = detections.slice(0, 15).map((det, idx) => `
        <div class="detection-item" style="animation: slideIn 0.3s ease ${idx * 0.05}s;">
            <span class="detection-class">${escapeHtml(det.class_name || det['class'])}</span>
            <span class="detection-confidence">${((det.confidence || 0) * 100).toFixed(1)}%</span>
            <span style="font-size: 0.8rem; color: #999;">${new Date(det.timestamp).toLocaleTimeString()}</span>
        </div>
    `).join('');
    
    detectionList.innerHTML = html;
}

/**
 * Update class statistics with visual bars
 */
function updateClassStats(classDistribution) {
    const classStats = document.getElementById('classStats');
    if (!classStats) return;
    
    if (!classDistribution || classDistribution.length === 0) {
        classStats.innerHTML = '<p style="text-align: center; color: #999;">No statistics yet</p>';
        return;
    }
    
    // Find max count for scaling
    const maxCount = Math.max(...classDistribution.map(c => c.count || 0));
    
    const html = classDistribution.slice(0, 8).map((cls, idx) => {
        const percentage = maxCount > 0 ? (cls.count / maxCount * 100) : 0;
        const avg_conf = (cls.avg_confidence || 0) * 100;
        return `
        <div class="detection-item" style="animation: slideIn 0.3s ease ${idx * 0.05}s;">
            <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                <span class="detection-class">${escapeHtml(cls.class_name)}</span>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <div style="width: 60px; height: 6px; background: #eee; border-radius: 3px;">
                        <div style="width: ${percentage}%; height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 3px;"></div>
                    </div>
                    <span class="detection-confidence">${cls.count}</span>
                </div>
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-top: 4px;">Avg Conf: ${avg_conf.toFixed(1)}%</div>
        </div>
    `}).join('');
    
    classStats.innerHTML = html;
}

/**
 * Update alerts
 */
async function updateAlerts() {
    try {
        const response = await fetch('/get_alerts');
        if (!response.ok) throw new Error('Failed to fetch alerts');
        
        const alerts = await response.json();
        const alertsList = document.getElementById('alertsList');
        
        if (!alertsList) return;
        
        if (!alerts || alerts.length === 0) {
            alertsList.innerHTML = '<p style="text-align: center; color: #999;">No alerts</p>';
            return;
        }
        
        const html = alerts.map(alert => `
            <div class="alert-box">
                <strong>${escapeHtml(alert.message)}</strong>
                <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
            </div>
        `).join('');
        
        alertsList.innerHTML = html;
        
    } catch (error) {
        console.error('Error updating alerts:', error);
    }
}

/**
 * Export data to CSV
 */
async function exportData() {
    try {
        window.location.href = '/export_csv';
        showNotification('Data exported successfully!', 'success');
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('Error exporting data: ' + error.message, 'error');
    }
}

/**
 * Handle video file upload
 */
async function handleVideoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        showNotification('Uploading video...', 'info');
        
        const response = await fetch('/upload_video', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Video uploaded successfully!', 'success');
            console.log('Video uploaded:', data.filename);
        } else {
            showNotification('Upload failed: ' + data.message, 'error');
        }
        
        // Reset file input
        event.target.value = '';
        
    } catch (error) {
        console.error('Error uploading video:', error);
        showNotification('Error: ' + error.message, 'error');
    }
}

/**
 * Handle photo file upload and detection
 */
async function handlePhotoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        showNotification('Processing image...', 'info');
        
        const response = await fetch('/detect_photo', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayPhotoResults(data);
            showNotification(`Detection complete! ${data.objects_detected} object(s) found.`, 'success');
            console.log('Photo detected:', data);
        } else {
            showNotification('Detection failed: ' + data.message, 'error');
        }
        
        // Reset file input
        event.target.value = '';
        
    } catch (error) {
        console.error('Error processing photo:', error);
        showNotification('Error: ' + error.message, 'error');
    }
}

/**
 * Display photo detection results in modal with enhanced features
 */
function displayPhotoResults(results) {
    // Store current results for history
    currentPhotoData = {
        ...results,
        detectionTime: new Date().toISOString(),
        processingTime: results.processing_time || 0
    };
    
    // Add to history
    addToDetectionHistory(results);
    
    // Update object count
    const objectCount = document.getElementById('photoObjectCount');
    if (objectCount) {
        objectCount.textContent = results.objects_detected;
    }
    
    // Update processing time
    const processingTime = document.getElementById('photoProcessingTime');
    if (processingTime && results.processing_time) {
        processingTime.textContent = `${(results.processing_time * 1000).toFixed(2)}ms`;
    }
    
    // Calculate and update average confidence
    if (results.detections && results.detections.length > 0) {
        const avgConfidence = results.detections.reduce((sum, det) => sum + det.confidence, 0) / results.detections.length;
        const confidenceEl = document.getElementById('photoAvgConfidence');
        if (confidenceEl) {
            confidenceEl.textContent = `${(avgConfidence * 100).toFixed(1)}%`;
        }
    }
    
    // Update timestamp
    const timestamp = document.getElementById('photoTimestamp');
    if (timestamp) {
        timestamp.textContent = new Date().toLocaleTimeString();
    }
    
    // Display result image
    const imageContainer = document.getElementById('photoResultImage');
    if (imageContainer && results.result_image) {
        imageContainer.innerHTML = `<img src="/get_result_image/${results.result_image}" alt="Detection Result" style="max-width: 100%; border-radius: 10px;">`;
    }
    
    // Display detections list
    const detectionsList = document.getElementById('photoDetectionsList');
    if (detectionsList && results.detections) {
        if (results.detections.length === 0) {
            detectionsList.innerHTML = '<p style="text-align: center; color: #999;">No objects detected</p>';
        } else {
            const html = results.detections.map((det, index) => `
                <div class="photo-detection-item" style="animation: slideIn 0.3s ease ${index * 0.05}s;">
                    <div>
                        <div class="photo-detection-class">${escapeHtml(det.class)}</div>
                        <div style="font-size: 0.85rem; color: #666;">
                            Box: [${det.bbox.join(', ')}]
                            <br/>Confidence Score: ${(det.confidence * 100).toFixed(2)}%
                        </div>
                    </div>
                    <div class="photo-detection-conf">${(det.confidence * 100).toFixed(1)}%</div>
                </div>
            `).join('');
            detectionsList.innerHTML = html;
        }
        
        // Populate confidence chart
        populateConfidenceChart(results.detections);
    }
    
    // Show modal
    openPhotoModal();
}

/**
 * Open photo modal
 */
function openPhotoModal() {
    const modal = document.getElementById('photoModal');
    if (modal) {
        modal.classList.add('show');
    }
}

/**
 * Close photo modal
 */
function closePhotoModal() {
    const modal = document.getElementById('photoModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

/**
 * Switch between modal tabs
 */
function switchPhotoTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Deactivate all buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + 'Tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activate selected button
    event.target.classList.add('active');
}

/**
 * Add detection to history
 */
function addToDetectionHistory(results) {
    const historyItem = {
        id: Date.now(),
        detections: results.detections || [],
        objectCount: results.objects_detected || 0,
        timestamp: new Date().toLocaleString(),
        processingTime: results.processing_time || 0,
        resultImage: results.result_image || null
    };
    
    detectionHistory.unshift(historyItem);
    
    // Limit history size
    if (detectionHistory.length > MAX_HISTORY) {
        detectionHistory.pop();
    }
    
    // Save to local storage
    saveDetectionHistoryToStorage();
    
    // Update history display
    updateDetectionHistoryDisplay();
}

/**
 * Update detection history display
 */
function updateDetectionHistoryDisplay() {
    const historyContainer = document.getElementById('detectionHistory');
    if (!historyContainer) return;
    
    if (detectionHistory.length === 0) {
        historyContainer.innerHTML = '<p style="text-align: center; color: #999;">No detection history</p>';
        return;
    }
    
    const html = detectionHistory.map((item, index) => `
        <div class="history-item">
            <div class="history-header">
                <span class="history-time">${item.timestamp}</span>
                <span class="history-count">${item.objectCount} objects</span>
            </div>
            <div class="history-details">
                <span>Processing: ${(item.processingTime * 1000).toFixed(2)}ms</span>
                <button class="btn-mini" onclick="showHistoryDetail(${item.id})">View Details</button>
            </div>
        </div>
    `).join('');
    
    historyContainer.innerHTML = html;
}

/**
 * Filter detection history
 */
function filterDetectionHistory() {
    const filterValue = document.getElementById('historyFilter').value.toLowerCase();
    const historyContainer = document.getElementById('detectionHistory');
    
    if (!historyContainer) return;
    
    const filtered = detectionHistory.filter(item => {
        return item.detections.some(det => det.class.toLowerCase().includes(filterValue));
    });
    
    if (filtered.length === 0) {
        historyContainer.innerHTML = '<p style="text-align: center; color: #999;">No matches found</p>';
        return;
    }
    
    const html = filtered.map((item, index) => `
        <div class="history-item">
            <div class="history-header">
                <span class="history-time">${item.timestamp}</span>
                <span class="history-count">${item.objectCount} objects</span>
            </div>
            <div class="history-details">
                <span>Processing: ${(item.processingTime * 1000).toFixed(2)}ms</span>
                <span>${item.detections.map(d => d.class).join(', ')}</span>
            </div>
        </div>
    `).join('');
    
    historyContainer.innerHTML = html;
}

/**
 * Clear detection history
 */
function clearDetectionHistory() {
    if (confirm('Are you sure you want to clear all detection history?')) {
        detectionHistory = [];
        saveDetectionHistoryToStorage();
        updateDetectionHistoryDisplay();
        showNotification('Detection history cleared', 'info');
    }
}

/**
 * Save detection history to local storage
 */
function saveDetectionHistoryToStorage() {
    try {
        localStorage.setItem('detectionHistory', JSON.stringify(detectionHistory));
    } catch (e) {
        console.warn('Failed to save history to storage:', e);
    }
}

/**
 * Load detection history from local storage
 */
function loadDetectionHistoryFromStorage() {
    try {
        const stored = localStorage.getItem('detectionHistory');
        if (stored) {
            detectionHistory = JSON.parse(stored);
        }
    } catch (e) {
        console.warn('Failed to load history from storage:', e);
    }
}

/**
 * Populate confidence chart
 */
function populateConfidenceChart(detections) {
    const chartContainer = document.getElementById('confidenceChart');
    if (!chartContainer) return;
    
    if (!detections || detections.length === 0) {
        chartContainer.innerHTML = '<p style="text-align: center; color: #999;">No detections to display</p>';
        return;
    }
    
    const maxConfidence = Math.max(...detections.map(d => d.confidence));
    
    const html = detections.map((det, index) => `
        <div class="confidence-bar-item">
            <div class="bar-label">${escapeHtml(det.class)}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: ${(det.confidence / maxConfidence) * 100}%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);"></div>
            </div>
            <div class="bar-value">${(det.confidence * 100).toFixed(1)}%</div>
        </div>
    `).join('');
    
    chartContainer.innerHTML = html;
    
    // Update confidence statistics
    updateConfidenceStats(detections);
}

/**
 * Update confidence statistics
 */
function updateConfidenceStats(detections) {
    const statsContainer = document.getElementById('confidenceStats');
    if (!statsContainer) return;
    
    const confidences = detections.map(d => d.confidence);
    const avgConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;
    const minConfidence = Math.min(...confidences);
    const maxConfidence = Math.max(...confidences);
    
    const html = `
        <div class="stat-row">
            <span>Average:</span>
            <strong>${(avgConfidence * 100).toFixed(2)}%</strong>
        </div>
        <div class="stat-row">
            <span>Minimum:</span>
            <strong>${(minConfidence * 100).toFixed(2)}%</strong>
        </div>
        <div class="stat-row">
            <span>Maximum:</span>
            <strong>${(maxConfidence * 100).toFixed(2)}%</strong>
        </div>
        <div class="stat-row">
            <span>Total Detections:</span>
            <strong>${detections.length}</strong>
        </div>
    `;
    
    statsContainer.innerHTML = html;
}

/**
 * Update status indicator
 */
function updateStatusIndicator() {
    const indicator = document.getElementById('statusIndicator');
    if (!indicator) return;
    
    if (isRunning) {
        indicator.className = 'status-indicator status-active';
    } else {
        indicator.className = 'status-indicator status-inactive';
    }
}

/**
 * Show notification (simple implementation)
 */
function showNotification(message, type = 'info') {
    // Create a simple alert - in production, use a toast library
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // You can replace this with a proper toast notification library
    // For now, we'll use the browser's alert for critical messages
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Update performance metrics
 */
function updatePerformanceMetrics(stats) {
    const qualityScore = document.getElementById('qualityScore');
    const avgProcTime = document.getElementById('avgProcTime');
    const totalFrames = document.getElementById('totalFrames');
    const avgConfidence = document.getElementById('avgConfidence');
    
    if (qualityScore && stats.quality_score !== undefined) {
        const quality = Math.round(stats.quality_score);
        qualityScore.textContent = quality + '%';
        qualityScore.style.color = quality > 80 ? '#48bb78' : quality > 60 ? '#ffd93d' : '#ff6b6b';
    }
    
    if (avgProcTime && stats.avg_processing_time !== undefined) {
        const procTime = (stats.avg_processing_time * 1000).toFixed(1);
        avgProcTime.textContent = procTime + 'ms';
    }
    
    if (totalFrames && stats.frame_count !== undefined) {
        totalFrames.textContent = stats.frame_count;
    }
    
    if (avgConfidence && stats.avg_confidence !== undefined) {
        const conf = (stats.avg_confidence * 100).toFixed(1);
        avgConfidence.textContent = conf + '%';
    }
}

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (isRunning) {
        stopCamera();
    }
});

// Cleanup on page visibility change
document.addEventListener('visibilitychange', function() {
    if (document.hidden && isRunning) {
        // Optionally stop camera when page is hidden
        console.log('Page hidden');
    } else if (!document.hidden && isRunning) {
        // Resume updates when page becomes visible
        console.log('Page visible');
        if (!updateInterval) {
            updateInterval = setInterval(updateStats, UPDATE_INTERVAL);
        }
    }
});

// ==================== MOBILE API FUNCTIONS ====================

/**
 * Detect objects in base64 encoded image (Mobile API)
 */
async function mobileDetectImage(base64Image) {
    try {
        const response = await fetch('/mobile/detect_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: base64Image
            })
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('Mobile image detection successful:', data);
            return data;
        } else {
            showNotification('Detection failed: ' + data.error, 'error');
            return null;
        }
    } catch (error) {
        console.error('Error in mobile image detection:', error);
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

/**
 * Detect objects from camera (Mobile API)
 */
async function mobileDetectCamera(cameraId = 0) {
    try {
        const response = await fetch('/mobile/detect_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                camera_id: cameraId
            })
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('Mobile camera detection successful:', data);
            return data;
        } else {
            showNotification('Detection failed: ' + data.error, 'error');
            return null;
        }
    } catch (error) {
        console.error('Error in mobile camera detection:', error);
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

/**
 * Get list of available cameras (Mobile API)
 */
async function mobileGetAvailableCameras() {
    try {
        const response = await fetch('/mobile/available_cameras');
        const data = await response.json();
        if (data.success) {
            console.log('Available cameras:', data.cameras);
            return data.cameras;
        } else {
            return [];
        }
    } catch (error) {
        console.error('Error getting available cameras:', error);
        return [];
    }
}

/**
 * Detect objects in video file (Mobile API)
 */
async function mobileDetectVideo(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        showNotification('Processing video... This may take a moment.', 'info');
        
        const response = await fetch('/mobile/detect_video', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('Mobile video detection successful:', data);
            showNotification(`Video processed: ${data.total_detections} objects found`, 'success');
            return data;
        } else {
            showNotification('Detection failed: ' + data.error, 'error');
            return null;
        }
    } catch (error) {
        console.error('Error in mobile video detection:', error);
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

/**
 * Batch process multiple images (Mobile API)
 */
async function mobileBatchDetect(base64Images) {
    try {
        showNotification(`Processing ${base64Images.length} images...`, 'info');
        
        const response = await fetch('/mobile/batch_detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                images: base64Images
            })
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('Mobile batch detection successful:', data);
            showNotification(`Batch processing complete: ${data.total_images} images processed`, 'success');
            return data;
        } else {
            showNotification('Batch processing failed: ' + data.error, 'error');
            return null;
        }
    } catch (error) {
        console.error('Error in mobile batch detection:', error);
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

/**
 * Stream camera video with MJPEG (Mobile API)
 */
function mobileStreamCamera(cameraId = 0) {
    return `/mobile/stream_camera?camera_id=${cameraId}`;
}

/**
 * Get current statistics (Mobile API)
 */
async function mobileGetStats() {
    try {
        const response = await fetch('/mobile/stats');
        const data = await response.json();
        if (data.success) {
            console.log('Mobile stats:', data);
            return data;
        } else {
            return null;
        }
    } catch (error) {
        console.error('Error getting mobile stats:', error);
        return null;
    }
}

/**
 * File to base64 conversion utility
 */
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

/**
 * Canvas to base64 conversion utility
 */
function canvasToBase64(canvas) {
    return canvas.toDataURL('image/jpeg', 0.85);
}

/**
 * Process image using mobile API
 */
async function processImageWithMobileAPI(file) {
    try {
        showNotification('Processing image with mobile API...', 'info');
        const base64 = await fileToBase64(file);
        const result = await mobileDetectImage(base64);
        return result;
    } catch (error) {
        console.error('Error processing image:', error);
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}
