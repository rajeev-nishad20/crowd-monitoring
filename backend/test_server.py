"""Lightweight test server for demonstrating camera_id input handling.

This server mirrors the start_camera / stop_camera validation logic from the main
app but avoids heavy dependencies (OpenCV / detector). It's intended for local
testing in environments where those libraries are unavailable.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# Simulated state
camera_state = {
    'camera': None,
    'camera_id': None,
    'is_running': False
}


@app.route('/', methods=['GET'])
def hello():
    return "Test server: /start_camera and /stop_camera available."


@app.route('/start_camera', methods=['POST'])
def start_camera():
    data = request.get_json() or {}
    camera_id_raw = data.get('camera_id', 0)

    # Try to coerce camera_id to int when possible
    try:
        camera_id = int(camera_id_raw)
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid camera_id; must be an integer'}), 400

    if camera_id < 0:
        return jsonify({'success': False, 'message': 'camera_id must be >= 0'}), 400

    # If already running with same id, short-circuit
    if camera_state['is_running'] and camera_state['camera_id'] == camera_id:
        return jsonify({'success': True, 'message': f'Camera {camera_id} already running'})

    # Simulate camera opening success for typical integer ids
    camera_state['camera'] = True
    camera_state['camera_id'] = camera_id
    camera_state['is_running'] = True

    return jsonify({'success': True, 'message': f'Camera {camera_id} started'})


@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    camera_state['is_running'] = False
    camera_state['camera'] = None
    camera_state['camera_id'] = None

    return jsonify({'success': True, 'message': 'Camera stopped'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
