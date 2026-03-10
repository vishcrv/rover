# modules/leaf_preprocessor.py — Image preprocessing for leaf detection
#
# Handles colour-space conversions, blurring, optional green masking,
# and morphological clean-up.  All tuneable parameters come from
# config/settings.py so they can be adjusted without touching code.

import cv2
import numpy as np
from config.settings import (
    GREEN_LOWER, GREEN_UPPER,
    BLUR_KERNEL_SIZE, USE_GREEN_MASK,
)


def preprocess(frame):
    """Run the full preprocessing pipeline on a single camera frame.

    Args:
        frame: numpy array in RGB format (from Picamera2).

    Returns:
        (mask, gray):
            mask  — binary mask highlighting candidate leaf regions.
            gray  — grayscale version of the frame (for edge detection).
    """
    # 1. Colour-space conversions
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # 2. Gaussian blur to reduce noise
    k = BLUR_KERNEL_SIZE
    gray = cv2.GaussianBlur(gray, (k, k), 0)
    hsv = cv2.GaussianBlur(hsv, (k, k), 0)

    # 3. Build a binary mask
    if USE_GREEN_MASK:
        # Use green colour range to isolate candidate regions
        mask = cv2.inRange(hsv, np.array(GREEN_LOWER), np.array(GREEN_UPPER))
    else:
        # Fall back to adaptive thresholding on the grayscale image
        mask = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11, C=2,
        )

    # 4. Morphological operations to clean up noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # remove small blobs
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # fill small holes

    return mask, gray
