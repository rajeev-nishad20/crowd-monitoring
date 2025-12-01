"""Test script for Mobile API endpoints"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_available_cameras():
    """Test: Get available cameras"""
    print("\n" + "="*60)
    print("TEST 1: Get Available Cameras")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/mobile/available_cameras")
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_mobile_stats():
    """Test: Get mobile statistics"""
    print("\n" + "="*60)
    print("TEST 2: Get Mobile Stats")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/mobile/stats")
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success')}")
        print(f"Current FPS: {data.get('current_fps')}")
        print(f"Current Objects: {data.get('current_objects')}")
        print(f"Unique Classes: {data.get('unique_classes')}")
        if data.get('detector_stats'):
            stats = data['detector_stats']
            print(f"Total Detections: {stats.get('total_detections')}")
            print(f"Quality Score: {stats.get('quality_score')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_detect_camera():
    """Test: Detect objects from camera"""
    print("\n" + "="*60)
    print("TEST 3: Detect Objects from Camera")
    print("="*60)
    try:
        payload = {"camera_id": 0}
        response = requests.post(
            f"{BASE_URL}/mobile/detect_camera",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success')}")
        print(f"Objects Detected: {data.get('objects_detected')}")
        print(f"Processing Time: {data.get('metrics', {}).get('processing_time_ms'):.2f}ms")
        print(f"FPS: {data.get('metrics', {}).get('fps')}")
        
        if data.get('detections'):
            print(f"First Detection: {data['detections'][0]}")
        
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_detect_image_with_file():
    """Test: Detect objects from image file"""
    print("\n" + "="*60)
    print("TEST 4: Detect Objects from Image File")
    print("="*60)
    try:
        import base64
        import cv2
        
        # Create a simple test image
        img = cv2.imread("../uploads/test.jpg") if Path("../uploads/test.jpg").exists() else None
        
        if img is None:
            print("No test image found, creating dummy image for testing...")
            # Create a dummy image
            import numpy as np
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img[:] = (100, 150, 200)
            ret, buffer = cv2.imencode('.jpg', img)
        else:
            ret, buffer = cv2.imencode('.jpg', img)
        
        base64_image = base64.b64encode(buffer.tobytes()).decode('utf-8')
        base64_image = f"data:image/jpeg;base64,{base64_image}"
        
        payload = {"image": base64_image}
        response = requests.post(
            f"{BASE_URL}/mobile/detect_image",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success')}")
        print(f"Objects Detected: {data.get('objects_detected')}")
        print(f"Processing Time: {data.get('metrics', {}).get('processing_time_ms'):.2f}ms")
        
        if data.get('detections'):
            print(f"Detections: {len(data['detections'])} objects found")
            for det in data['detections'][:3]:  # Show first 3
                print(f"  - {det['class']}: {det['confidence']:.2%}")
        
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_batch_detect():
    """Test: Batch detect multiple images"""
    print("\n" + "="*60)
    print("TEST 5: Batch Detect Multiple Images")
    print("="*60)
    try:
        import base64
        import cv2
        import numpy as np
        
        # Create test images
        base64_images = []
        for i in range(3):
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img[:] = (100 + i*30, 150, 200)
            ret, buffer = cv2.imencode('.jpg', img)
            base64_img = base64.b64encode(buffer.tobytes()).decode('utf-8')
            base64_images.append(f"data:image/jpeg;base64,{base64_img}")
        
        payload = {"images": base64_images}
        response = requests.post(
            f"{BASE_URL}/mobile/batch_detect",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {data.get('success')}")
        print(f"Total Images: {data.get('total_images')}")
        print(f"Total Detections: {data.get('total_detections')}")
        print(f"Avg Processing Time: {data.get('metrics', {}).get('avg_processing_time_ms'):.2f}ms")
        
        if data.get('results'):
            for result in data['results']:
                print(f"  Image {result['image_index']}: {result.get('objects_detected', 0)} objects")
        
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_stream_camera():
    """Test: Stream camera endpoint"""
    print("\n" + "="*60)
    print("TEST 6: Stream Camera Endpoint")
    print("="*60)
    try:
        url = f"{BASE_URL}/mobile/stream_camera?camera_id=0"
        response = requests.head(url)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Stream URL: {url}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n\n")
    print("#"*60)
    print("# MOBILE API TEST SUITE")
    print("#"*60)
    
    results = {
        "Available Cameras": test_available_cameras(),
        "Mobile Stats": test_mobile_stats(),
        "Detect Camera": test_detect_camera(),
        "Detect Image": test_detect_image_with_file(),
        "Batch Detect": test_batch_detect(),
        "Stream Camera": test_stream_camera(),
    }
    
    print("\n\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*60)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
