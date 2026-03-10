# modules/detector.py — Green object detection using OpenCV

import cv2
import numpy as np
from config.settings import (
    GREEN_LOWER, GREEN_UPPER,
    MIN_CONTOUR_AREA, DETECTION_CONFIRM_FRAMES,
)

_consecutive_hits = 0


def detect_green(frame):
    """Analyze a single frame for green objects.

    Args:
        frame: numpy array in RGB format (from Picamera2).

    Returns:
        (detected, contour):
            detected — True if a green object large enough was found.
            contour  — the largest valid contour, or None.
    """
    # Convert RGB (from Picamera2) to HSV for color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    # Green is continuous in the HSV hue space (around 35-85)
    mask = cv2.inRange(hsv, np.array(GREEN_LOWER), np.array(GREEN_UPPER))

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


def check_confirmed(frame):
    """Process a frame and track multi-frame confirmation.

    Args:
        frame: numpy array in RGB format.

    Returns:
        True only when green is detected for DETECTION_CONFIRM_FRAMES consecutive frames.
    """
    global _consecutive_hits

    detected, _ = detect_green(frame)

    if detected:
        _consecutive_hits += 1
    else:
        _consecutive_hits = 0

    return _consecutive_hits >= DETECTION_CONFIRM_FRAMES


def reset():
    """Reset the consecutive detection counter."""
    global _consecutive_hits
    _consecutive_hits = 0


def get_consecutive_count():
    """Return the current consecutive detection count (useful for debugging)."""
    return _consecutive_hits
