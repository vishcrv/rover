# modules/detector.py — Red object detection using OpenCV

import cv2
import numpy as np
from config.settings import (
    RED_LOWER_1, RED_UPPER_1,
    RED_LOWER_2, RED_UPPER_2,
    MIN_CONTOUR_AREA, DETECTION_CONFIRM_FRAMES,
)

_consecutive_hits = 0


def detect_red(frame):
    """Analyze a single frame for red objects.

    Args:
        frame: numpy array in RGB format (from Picamera2).

    Returns:
        (detected, contour):
            detected — True if a red object large enough was found.
            contour  — the largest valid contour, or None.
    """
    # Convert RGB (from Picamera2) to HSV for color detection
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


def check_confirmed(frame):
    """Process a frame and track multi-frame confirmation.

    Args:
        frame: numpy array in RGB format.

    Returns:
        True only when red is detected for DETECTION_CONFIRM_FRAMES consecutive frames.
    """
    global _consecutive_hits

    detected, _ = detect_red(frame)

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
