# modules/camera.py — Camera capture and frame provider (Picamera2)

import os
import threading
from picamera2 import Picamera2
from config.settings import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAPTURE_DIR,
)

_camera = None
_lock = threading.Lock()
_latest_frame = None
_running = False
_thread = None


def setup():
    """Initialize Picamera2 and start continuous capture in a background thread."""
    global _camera, _running, _thread

    _camera = Picamera2()

    # Preview config — low-res for real-time detection and streaming
    preview_config = _camera.create_preview_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
    )
    _camera.configure(preview_config)
    _camera.start()

    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Start background thread to continuously grab frames
    _running = True
    _thread = threading.Thread(target=_capture_loop, daemon=True)
    _thread.start()


def _capture_loop():
    """Continuously grab frames and store the latest one (thread-safe)."""
    global _latest_frame
    while _running:
        frame = _camera.capture_array()
        with _lock:
            _latest_frame = frame


def get_frame():
    """Return the latest camera frame as a numpy array (RGB).

    Returns None if no frame is available yet.
    """
    with _lock:
        if _latest_frame is None:
            return None
        return _latest_frame.copy()


def capture_image(filename):
    """Capture a still image and save to CAPTURE_DIR.

    Returns the full path to the saved image.
    """
    filepath = os.path.join(CAPTURE_DIR, filename)

    # Use the current stream to capture a full-res image
    # request() gives us a high-quality capture without reconfiguring
    _camera.capture_file(filepath)

    return filepath


def cleanup():
    """Stop the capture thread and release the camera."""
    global _running
    _running = False
    if _thread is not None:
        _thread.join(timeout=2)
    if _camera is not None:
        _camera.stop()
        _camera.close()
