# modules/detector.py — Leaf detection pipeline
#
# Full pipeline: preprocess → Canny edges → contour extraction →
# feature extraction → leaf-shape filtering → annotation.
# Replaces the old green-only detection.

import cv2
import numpy as np
from config.settings import (
    CANNY_LOW, CANNY_HIGH,
    LEAF_MIN_AREA, DETECTION_CONFIRM_FRAMES,
)
from modules.leaf_preprocessor import preprocess
from modules.leaf_features import extract_all
from modules.leaf_filter import filter_leaves

_consecutive_hits = 0


# --------------------------------------------------------------------------- #
# Core detection
# --------------------------------------------------------------------------- #

def detect_leaves(frame):
    """Run the full leaf-detection pipeline on a single RGB frame.

    Args:
        frame: numpy array in RGB format (from Picamera2).

    Returns:
        list of (contour, features_dict) for every contour that
        passed the leaf-shape filter.  Empty list if nothing found.
    """
    # 1. Preprocess (colour mask / adaptive threshold + morphology)
    mask, gray = preprocess(frame)

    # 2. Canny edge detection on the preprocessed mask
    edges = cv2.Canny(mask, CANNY_LOW, CANNY_HIGH)

    # 3. Combine mask and edges for robust contour extraction
    combined = cv2.bitwise_or(mask, edges)

    # 4. Find contours
    contours, _ = cv2.findContours(
        combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    )

    # 5. Quick area pre-filter to drop obvious noise
    contours = [c for c in contours if cv2.contourArea(c) >= LEAF_MIN_AREA]

    if not contours:
        return []

    # 6. Extract geometric features
    contours_feats = extract_all(contours)

    # 7. Apply leaf-shape rules
    leaves = filter_leaves(contours_feats)

    return leaves


# --------------------------------------------------------------------------- #
# Annotation (draws onto a copy of the frame)
# --------------------------------------------------------------------------- #

def annotate_frame(frame, leaves):
    """Draw leaf detection overlays on a frame.

    Args:
        frame:  numpy array in RGB format.
        leaves: list of (contour, features_dict) from detect_leaves().

    Returns:
        annotated: a BGR copy of the frame with contours, bounding boxes,
                   and labels drawn.  BGR because OpenCV imencode expects it.
    """
    # Work on a BGR copy so colours render correctly in JPEG output
    annotated = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    for cnt, feat in leaves:
        # Green contour outline
        cv2.drawContours(annotated, [cnt], -1, (0, 255, 0), 2)

        # Cyan bounding box
        x, y, w, h = feat["bbox"]
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 255, 0), 2)

        # Label with area info
        label = f"LEAF {feat['area']:.0f}px"
        cv2.putText(
            annotated, label,
            (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
        )

    # Show count in top-left corner
    count_text = f"Leaves: {len(leaves)}"
    cv2.putText(
        annotated, count_text,
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
    )

    return annotated


# --------------------------------------------------------------------------- #
# Multi-frame confirmation (used by the main state machine)
# --------------------------------------------------------------------------- #

def check_confirmed(frame):
    """Process a frame and track multi-frame confirmation.

    Args:
        frame: numpy array in RGB format.

    Returns:
        (confirmed, annotated_frame):
            confirmed      — True when leaves detected for
                             DETECTION_CONFIRM_FRAMES consecutive frames.
            annotated_frame — BGR frame with detection overlays.
    """
    global _consecutive_hits

    leaves = detect_leaves(frame)
    annotated = annotate_frame(frame, leaves)

    if leaves:
        _consecutive_hits += 1
    else:
        _consecutive_hits = 0

    confirmed = _consecutive_hits >= DETECTION_CONFIRM_FRAMES
    return confirmed, annotated


def reset():
    """Reset the consecutive detection counter."""
    global _consecutive_hits
    _consecutive_hits = 0


def get_consecutive_count():
    """Return the current consecutive detection count (useful for debugging)."""
    return _consecutive_hits
