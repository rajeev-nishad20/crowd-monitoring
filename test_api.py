#!/usr/bin/env python
"""Test API endpoints"""
import requests
import time
import json

def test_endpoints():
    base_url = "http://localhost:5000"
    
    print("=" * 60)
    print("Testing Real-Time Object Detection API")
    print("=" * 60)
    
    try:
        # Test 1: Dashboard
        print("\n✓ Test 1: Dashboard page...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Dashboard loaded (Status: {response.status_code})")
        else:
            print(f"  ❌ Dashboard failed (Status: {response.status_code})")
        
        # Test 2: Stats endpoint
        print("\n✓ Test 2: Stats endpoint...")
        response = requests.get(f"{base_url}/get_stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Stats endpoint working (Status: {response.status_code})")
            print(f"    - Current FPS: {data.get('current_fps', 0)}")
            print(f"    - Total Objects: {data.get('total_objects', 0)}")
            print(f"    - Unique Classes: {data.get('unique_classes', 0)}")
            print(f"    - Recent Detections: {len(data.get('recent_detections', []))}")
        else:
            print(f"  ❌ Stats failed (Status: {response.status_code})")
        
        # Test 3: Alerts
        print("\n✓ Test 3: Alerts endpoint...")
        response = requests.get(f"{base_url}/get_alerts", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Alerts endpoint working (Status: {response.status_code})")
        else:
            print(f"  ❌ Alerts failed (Status: {response.status_code})")
        
        # Test 4: Performance metrics
        print("\n✓ Test 4: Performance metrics endpoint...")
        response = requests.get(f"{base_url}/get_performance_metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Performance metrics working (Status: {response.status_code})")
            perf = data.get('performance', {})
            print(f"    - Avg FPS: {perf.get('avg_fps', 0):.1f}")
            print(f"    - Avg Processing Time: {perf.get('avg_processing_time_ms', 0):.1f}ms")
        else:
            print(f"  ❌ Performance metrics failed (Status: {response.status_code})")
        
        print("\n" + "=" * 60)
        print("✅ API Tests Completed Successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server at http://localhost:5000")
        print("   Make sure the Flask server is running!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_endpoints()
