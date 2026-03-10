# modules/leaf_features.py — Geometric feature extraction for contours
#
# Computes a rich set of shape descriptors for each candidate contour
# so that the downstream filter can decide whether it looks like a leaf.

import cv2
import numpy as np


def extract_features(contour):
    """Compute geometric features for a single contour.

    Args:
        contour: OpenCV contour (numpy array of points).

    Returns:
        dict with keys:
            area, perimeter, bbox (x,y,w,h), aspect_ratio, extent,
            hull, solidity, circularity, hu_moments.
        Returns None if the contour is degenerate (zero area/perimeter).
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, closed=True)

    if area <= 0 or perimeter <= 0:
        return None

    # Bounding rectangle
    x, y, w, h = cv2.boundingRect(contour)

    # Aspect ratio — width / height of bounding rect
    aspect_ratio = float(w) / h if h > 0 else 0.0

    # Extent — ratio of contour area to bounding-rect area
    rect_area = w * h
    extent = float(area) / rect_area if rect_area > 0 else 0.0

    # Convex hull and solidity
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = float(area) / hull_area if hull_area > 0 else 0.0

    # Circularity — 1.0 for a perfect circle, lower for elongated shapes
    circularity = (4.0 * np.pi * area) / (perimeter * perimeter)

    # Hu moments (7 values, log-transformed for scale invariance)
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()

    return {
        "area": area,
        "perimeter": perimeter,
        "bbox": (x, y, w, h),
        "aspect_ratio": aspect_ratio,
        "extent": extent,
        "hull": hull,
        "solidity": solidity,
        "circularity": circularity,
        "hu_moments": hu,
    }


def extract_all(contours):
    """Extract features for a list of contours.

    Args:
        contours: list of OpenCV contours.

    Returns:
        list of (contour, features_dict) tuples.
        Degenerate contours are silently skipped.
    """
    results = []
    for cnt in contours:
        feat = extract_features(cnt)
        if feat is not None:
            results.append((cnt, feat))
    return results
