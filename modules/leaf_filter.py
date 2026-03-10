# modules/leaf_filter.py — Rule-based leaf-shape filtering
#
# Applies configurable geometric thresholds to decide which contours
# are "leaf-like".  All limits come from config/settings.py.

from config.settings import (
    LEAF_MIN_AREA, LEAF_MAX_AREA,
    LEAF_ASPECT_RATIO_MIN, LEAF_ASPECT_RATIO_MAX,
    LEAF_SOLIDITY_MIN,
    LEAF_CIRCULARITY_MIN, LEAF_CIRCULARITY_MAX,
)


def is_leaf(features):
    """Check whether a feature dict passes all leaf-shape criteria.

    Args:
        features: dict returned by leaf_features.extract_features().

    Returns:
        True if the contour looks leaf-like, False otherwise.
    """
    a = features["area"]
    ar = features["aspect_ratio"]
    sol = features["solidity"]
    circ = features["circularity"]

    # Area bounds
    if a < LEAF_MIN_AREA or a > LEAF_MAX_AREA:
        return False

    # Aspect ratio — leaves are moderately elongated, not extremely thin
    if ar < LEAF_ASPECT_RATIO_MIN or ar > LEAF_ASPECT_RATIO_MAX:
        return False

    # Solidity — leaves have relatively smooth, convex boundaries
    if sol < LEAF_SOLIDITY_MIN:
        return False

    # Circularity — not a perfect circle, not a jagged line
    if circ < LEAF_CIRCULARITY_MIN or circ > LEAF_CIRCULARITY_MAX:
        return False

    return True


def filter_leaves(contours_with_features):
    """Filter a list of (contour, features) tuples to keep only leaf-like shapes.

    Args:
        contours_with_features: list of (contour, features_dict) from
                                leaf_features.extract_all().

    Returns:
        list of (contour, features_dict) that passed all leaf criteria.
    """
    return [(cnt, feat) for cnt, feat in contours_with_features if is_leaf(feat)]
