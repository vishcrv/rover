# sensors/camera_detection.py — Camera capture and red object detection

import os
import threading
import cv2
import numpy as np
from picamera2 import Picamera2
from utils.config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAPTURE_DIR,
    RED_LOWER_1, RED_UPPER_1,
    RED_LOWER_2, RED_UPPER_2,
    MIN_CONTOUR_AREA, DETECTION_CONFIRM_FRAMES,
)

_camera = None
_lock = threading.Lock()
_latest_frame = None
_running = False
_thread = None
_consecutive_hits = 0


def setup():
    """Initialize Picamera2 and start continuous capture and detection in a thread."""
    global _camera, _running, _thread

    _camera = Picamera2()

    # Preview config — low-res for real-time detection and streaming
    preview_config = _camera.create_preview_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
    )
    _camera.configure(preview_config)
    _camera.start()

    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Start background thread to continuously grab frames and analyze
    _running = True
    _thread = threading.Thread(target=_capture_loop, daemon=True)
    _thread.start()


def _detect_red(frame):
    """Analyze a single frame for red objects."""
    # Convert to HSV for color detection (note picamera gives RGB initially so convert to BGR then HSV)
    # Actually wait, picamera RGB means we convert RGB -> HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    # Red wraps around hue 0/180 — combine two masks
    mask1 = cv2.inRange(hsv, np.array(RED_LOWER_1), np.array(RED_UPPER_1))
    mask2 = cv2.inRange(hsv, np.array(RED_LOWER_2), np.array(RED_UPPER_2))
    mask = mask1 | mask2

    # Clean up noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return False, None

    # Find the largest contour
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    if area >= MIN_CONTOUR_AREA:
        return True, largest

    return False, None


def _capture_loop():
    """Continuously grab frames, store the latest, and process detection (thread-safe)."""
    global _latest_frame, _consecutive_hits
    while _running:
        frame = _camera.capture_array()
        
        # Process detection directly inline so it's always up to date
        detected, _ = _detect_red(frame)
        
        with _lock:
            _latest_frame = frame
            if detected:
                _consecutive_hits += 1
            else:
                _consecutive_hits = 0


def is_red_detected():
    """Quickly check if red object is currently confirmed."""
    with _lock:
        return _consecutive_hits >= DETECTION_CONFIRM_FRAMES


def reset_detection():
    """Reset the consecutive detection counter."""
    global _consecutive_hits
    with _lock:
        _consecutive_hits = 0


def get_frame():
    """Return the latest camera frame as a numpy array (RGB)."""
    with _lock:
        if _latest_frame is None:
            return None
        return _latest_frame.copy()


def capture_image(filename):
    """Capture a high-res still image and save to CAPTURE_DIR. Returns filepath."""
    filepath = os.path.join(CAPTURE_DIR, filename)

    # Use the current stream to capture a full-res image
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
