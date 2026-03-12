# modules/leaf_features.py — Geometric feature extraction for contours
#
# Computes a rich set of shape descriptors for each candidate contour
# so that the downstream filter can decide whether it looks like a leaf.

import cv2
import numpy as np
from config.settings import CANNY_LOW, CANNY_HIGH


def _internal_edge_density(contour, gray_frame):
    """Measure the density of Canny edges *inside* a contour on the gray frame.

    Real leaves have internal vein/texture structure that produces edges
    inside the blob; flat painted/plastic objects produce almost none.

    Args:
        contour: OpenCV contour.
        gray_frame: Grayscale (blurred) frame — same source as used by detector.

    Returns:
        float — ratio of edge pixels inside the contour to contour area.
        Returns 0.0 if the area is too small or the frame is unavailable.
    """
    x, y, w, h = cv2.boundingRect(contour)

    # Safety: skip degenerate bounding boxes
    if w <= 0 or h <= 0:
        return 0.0

    # Crop the region of interest from the grayscale frame
    roi_gray = gray_frame[y:y + h, x:x + w]
    if roi_gray.size == 0:
        return 0.0

    # Build a mask for just the contour interior within the ROI
    roi_mask = np.zeros((h, w), dtype=np.uint8)
    shifted = contour - np.array([x, y])   # shift contour coords to ROI space
    cv2.drawContours(roi_mask, [shifted], -1, 255, thickness=cv2.FILLED)

    # Run Canny on the ROI
    edges = cv2.Canny(roi_gray, CANNY_LOW, CANNY_HIGH)

    # Count edge pixels that fall inside the contour mask
    edge_pixels_inside = cv2.countNonZero(cv2.bitwise_and(edges, roi_mask))

    contour_area = cv2.contourArea(contour)
    if contour_area <= 0:
        return 0.0

    return edge_pixels_inside / contour_area


def _convexity_defect_count(contour):
    """Count significant convexity defects on a contour.

    Leaf lobes and serrations create defects; smooth/flat objects have few.

    Args:
        contour: OpenCV contour.

    Returns:
        int — number of defects where the depth is > 5% of the equivalent
              circle radius (i.e. not just tiny noise bumps).
    """
    if len(contour) < 5:
        return 0

    hull_indices = cv2.convexHull(contour, returnPoints=False)
    if hull_indices is None or len(hull_indices) < 3:
        return 0

    try:
        defects = cv2.convexityDefects(contour, hull_indices)
    except cv2.error:
        return 0

    if defects is None:
        return 0

    area = cv2.contourArea(contour)
    if area <= 0:
        return 0

    # Depth threshold: 5% of the radius of an equivalent circle
    equiv_radius = np.sqrt(area / np.pi)
    depth_threshold = 0.05 * equiv_radius * 256  # defect depth is in 1/256 px units

    count = 0
    for _, _, _, depth in defects[:, 0]:
        if depth > depth_threshold:
            count += 1

    return count


def extract_features(contour, gray_frame=None):
    """Compute geometric features for a single contour.

    Args:
        contour:    OpenCV contour (numpy array of points).
        gray_frame: Optional grayscale frame used to compute internal edge
                    density.  If None, edge density is set to 0 (no gate).

    Returns:
        dict with keys:
            area, perimeter, bbox (x,y,w,h), aspect_ratio, extent,
            hull, solidity, circularity, hu_moments,
            internal_edge_density, convexity_defects_count.
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

    # Texture: internal edge density (requires gray frame)
    edge_density = (
        _internal_edge_density(contour, gray_frame)
        if gray_frame is not None else 0.0
    )

    # Shape complexity: convexity defects
    defect_count = _convexity_defect_count(contour)

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
        "internal_edge_density": edge_density,
        "convexity_defects_count": defect_count,
    }


def extract_all(contours, gray_frame=None):
    """Extract features for a list of contours.

    Args:
        contours:   list of OpenCV contours.
        gray_frame: Optional grayscale frame forwarded to extract_features.

    Returns:
        list of (contour, features_dict) tuples.
        Degenerate contours are silently skipped.
    """
    results = []
    for cnt in contours:
        feat = extract_features(cnt, gray_frame=gray_frame)
        if feat is not None:
            results.append((cnt, feat))
    return results
