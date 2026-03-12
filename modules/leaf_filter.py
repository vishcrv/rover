# modules/leaf_filter.py — Rule-based leaf-shape filtering
#
# Applies configurable geometric thresholds to decide which contours
# are "leaf-like".  All limits come from config/settings.py.

from config.settings import (
    LEAF_MIN_AREA, LEAF_MAX_AREA,
    LEAF_ASPECT_RATIO_MIN, LEAF_ASPECT_RATIO_MAX,
    LEAF_SOLIDITY_MIN,
    LEAF_CIRCULARITY_MIN, LEAF_CIRCULARITY_MAX,
    LEAF_EXTENT_MIN,
    LEAF_EDGE_DENSITY_MIN,
)


def is_leaf(features):
    """Check whether a feature dict passes all leaf-shape criteria.

    Checks (in order of computational cheapness / exclusion power):
      1. Area bounds
      2. Aspect ratio
      3. Extent (rejects thin grass blades)
      4. Solidity (smooth contour boundary)
      5. Circularity (not a circle, not a jagged line)
      6. Convexity defects (natural lobes/serrations; 1–12 expected)
      7. Internal edge density (rejects flat/uniform surfaces like plastic)

    Args:
        features: dict returned by leaf_features.extract_features().

    Returns:
        True if the contour looks leaf-like, False otherwise.
    """
    a    = features["area"]
    ar   = features["aspect_ratio"]
    ext  = features["extent"]
    sol  = features["solidity"]
    circ = features["circularity"]
    defs = features["convexity_defects_count"]
    dens = features["internal_edge_density"]

    # 1. Area bounds
    if a < LEAF_MIN_AREA or a > LEAF_MAX_AREA:
        return False

    # 2. Aspect ratio — leaves are moderately elongated, not extremely thin
    if ar < LEAF_ASPECT_RATIO_MIN or ar > LEAF_ASPECT_RATIO_MAX:
        return False

    # 3. Extent — thin grass blades fill very little of their bounding box
    if ext < LEAF_EXTENT_MIN:
        return False

    # 4. Solidity — leaves have relatively smooth, convex boundaries
    if sol < LEAF_SOLIDITY_MIN:
        return False

    # 5. Circularity — not a perfect circle, not a jagged line
    if circ < LEAF_CIRCULARITY_MIN or circ > LEAF_CIRCULARITY_MAX:
        return False

    # 6. Convexity defects — natural leaf lobes/serrations produce 1–12
    #    significant defects.  Smooth shapes (rectangles, circles, grass)
    #    produce 0.  Heavily fragmented noise produces >12.
    if defs < 1 or defs > 12:
        return False

    # 7. Internal edge density — flat painted/plastic objects have near-zero
    #    internal structure; real leaves have veins and texture.
    if dens < LEAF_EDGE_DENSITY_MIN:
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
