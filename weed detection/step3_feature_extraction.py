"""
=============================================================
WEED CLASSIFIER — STEP 3: Feature Extraction
=============================================================
Input  : data/images_preprocessed.npy   (N, 128, 128, 3) uint8
Output : data/features.npy              (N, D)            float32
         data/feature_names.npy         (D,)              str
=============================================================

FEATURES EXTRACTED PER IMAGE:
    1. HOG  (Histogram of Oriented Gradients)  — shape / edge structure
    2. LBP  (Local Binary Pattern)             — fine texture
    3. Colour Histograms  (H, S, V channels)  — colour signature
    4. Shape features     (contour-based)     — plant outline geometry
    5. Size features      (area, aspect ratio) — plant dimensions

TOTAL FEATURE VECTOR:  ~700-800 floats per image  (all concatenated)
=============================================================
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skimage.feature import hog, local_binary_pattern
from pathlib import Path


# ─────────────────────────────────────────────
# FEATURE 1 — HOG
# ─────────────────────────────────────────────

def extract_hog(img_bgr: np.ndarray) -> np.ndarray:
    """
    Histogram of Oriented Gradients — captures edges and local shape.

    Settings tuned for 128x128 plant images:
        pixels_per_cell = (16,16)  — each cell covers a ~leaf-vein-sized region
        cells_per_block = (2,2)    — 2x2 block normalisation for lighting invariance
        orientations    = 9        — 9 gradient bins (standard)

    Output size: 9 * (2*2) * ((128/16 - 1) * (128/16 - 1)) = 9*4*49 = 1764 ... 
    but skimage collapses this; actual size printed at runtime.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    feat = hog(
        gray,
        orientations=9,
        pixels_per_cell=(16, 16),
        cells_per_block=(2, 2),
        block_norm="L2-Hys",
        feature_vector=True,
    )
    return feat.astype(np.float32)


# ─────────────────────────────────────────────
# FEATURE 2 — LBP
# ─────────────────────────────────────────────

def extract_lbp(img_bgr: np.ndarray,
                n_points: int = 24,
                radius: int   = 3,
                n_bins: int   = 26) -> np.ndarray:
    """
    Local Binary Pattern histogram — captures fine texture (leaf surface detail).

    radius=3, n_points=24 → looks at a ~6px neighbourhood.
    We use 'uniform' LBP which gives (n_points+2) = 26 distinct patterns,
    discarding noisy non-uniform patterns.

    Output: 26-bin normalised histogram  (float32)
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    lbp  = local_binary_pattern(gray, n_points, radius, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins,
                           range=(0, n_bins), density=True)
    return hist.astype(np.float32)


# ─────────────────────────────────────────────
# FEATURE 3 — COLOUR HISTOGRAMS
# ─────────────────────────────────────────────

def extract_colour_histograms(img_bgr: np.ndarray,
                               n_bins: int = 32) -> np.ndarray:
    """
    Colour histograms in HSV space (32 bins per channel).

    HSV is preferred over BGR for colour histograms because:
      - H (hue) separates green plants from brown soil cleanly
      - S (saturation) captures how vivid the green is
      - V (value/brightness) captures lighting intensity

    Output: 3 x 32 = 96-element normalised histogram  (float32)
    """
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    hists = []
    ranges = [(0, 180), (0, 256), (0, 256)]   # H, S, V OpenCV ranges

    for ch, (lo, hi) in enumerate(ranges):
        h = cv2.calcHist([hsv], [ch], None, [n_bins], [lo, hi])
        h = cv2.normalize(h, h).flatten()
        hists.append(h)

    return np.concatenate(hists).astype(np.float32)


# ─────────────────────────────────────────────
# FEATURE 4+5 — SHAPE & SIZE
# ─────────────────────────────────────────────

def extract_shape_size(img_bgr: np.ndarray) -> np.ndarray:
    """
    Geometry features derived from the plant's segmented contour.

    Steps:
        1. Convert to HSV, threshold the green channel (Hue 25-85°)
        2. Morphological cleanup (remove noise)
        3. Find the largest contour (the plant)
        4. Compute shape descriptors

    Features (12 total):
        area_ratio       — plant pixels / total pixels
        aspect_ratio     — bounding box width / height
        extent           — contour area / bounding box area
        solidity         — contour area / convex hull area
        equiv_diameter   — diameter of circle with same area (normalised)
        circularity      — 4*pi*area / perimeter^2  (1 = perfect circle)
        hu_moments[0-6]  — 7 Hu invariant moments (scale/rotation invariant shape)
    """
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    H, W = img_bgr.shape[:2]
    total_px = H * W

    # Green mask: hue 25-85 covers yellow-green to blue-green
    mask = cv2.inRange(hsv, (25, 30, 30), (85, 255, 255))

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        # No green detected — return zeros
        return np.zeros(12, dtype=np.float32)

    # Largest contour = the plant
    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)

    if area < 10:
        return np.zeros(12, dtype=np.float32)

    # Bounding box
    x, y, w, h      = cv2.boundingRect(cnt)
    aspect_ratio     = float(w) / (h + 1e-6)
    extent           = area / (w * h + 1e-6)

    # Convex hull
    hull             = cv2.convexHull(cnt)
    hull_area        = cv2.contourArea(hull)
    solidity         = area / (hull_area + 1e-6)

    # Perimeter / circularity
    perimeter        = cv2.arcLength(cnt, True)
    circularity      = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)

    # Equivalent diameter (normalised by image diagonal)
    diag             = np.sqrt(H ** 2 + W ** 2)
    equiv_diameter   = np.sqrt(4 * area / np.pi) / diag

    # Area ratio
    area_ratio       = area / total_px

    # Hu moments (log-scaled for better numeric range)
    moments          = cv2.moments(cnt)
    hu               = cv2.HuMoments(moments).flatten()
    hu_log           = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)

    feats = np.array([
        area_ratio,
        aspect_ratio,
        extent,
        solidity,
        equiv_diameter,
        circularity,
    ], dtype=np.float32)

    return np.concatenate([feats, hu_log[:6]]).astype(np.float32)   # 6 + 6 = 12


# ─────────────────────────────────────────────
# COMBINED FEATURE VECTOR
# ─────────────────────────────────────────────

def extract_features(img_bgr: np.ndarray) -> np.ndarray:
    """
    Extract and concatenate all features for one image.

    Feature vector layout:
        [ HOG | LBP | ColourHist | Shape+Size ]
    """
    hog_feat    = extract_hog(img_bgr)
    lbp_feat    = extract_lbp(img_bgr)
    colour_feat = extract_colour_histograms(img_bgr)
    shape_feat  = extract_shape_size(img_bgr)

    return np.concatenate([hog_feat, lbp_feat, colour_feat, shape_feat])


def get_feature_group_sizes(img_bgr: np.ndarray) -> dict:
    """Return the size of each feature group (useful for diagnostics)."""
    return {
        "HOG":          len(extract_hog(img_bgr)),
        "LBP":          len(extract_lbp(img_bgr)),
        "ColourHist":   len(extract_colour_histograms(img_bgr)),
        "Shape+Size":   len(extract_shape_size(img_bgr)),
    }


def extract_all(images: np.ndarray, verbose: bool = True) -> np.ndarray:
    """
    Extract feature vectors for every image in the array.

    Returns:
        features : (N, D) float32  where D = total feature length
    """
    N = len(images)
    # Pre-compute size using first image
    sample = extract_features(images[0])
    D      = len(sample)

    features = np.zeros((N, D), dtype=np.float32)
    features[0] = sample

    for i in range(1, N):
        features[i] = extract_features(images[i])
        if verbose and (i + 1) % 500 == 0:
            print(f"  Extracted features: {i + 1}/{N} images ...")

    return features


# ─────────────────────────────────────────────
# VISUALISATIONS
# ─────────────────────────────────────────────

def visualise_feature_groups(img_bgr: np.ndarray, save_path: str = None):
    """
    For a single image, show the HOG visualisation, LBP map,
    HSV colour histogram, and green mask side by side.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # HOG visualisation
    _, hog_img = hog(gray, orientations=9, pixels_per_cell=(16, 16),
                     cells_per_block=(2, 2), block_norm="L2-Hys",
                     visualize=True, feature_vector=True)

    # LBP map
    lbp_map = local_binary_pattern(gray, 24, 3, method="uniform")

    # Green mask
    mask = cv2.inRange(hsv, (25, 30, 30), (85, 255, 255))

    # Colour histograms
    hue_hist  = cv2.calcHist([hsv], [0], None, [32], [0, 180]).flatten()
    sat_hist  = cv2.calcHist([hsv], [1], None, [32], [0, 256]).flatten()
    val_hist  = cv2.calcHist([hsv], [2], None, [32], [0, 256]).flatten()

    fig = plt.figure(figsize=(16, 8))
    fig.suptitle("Feature Extraction Visualisation", fontsize=13, fontweight="bold")

    # Row 1: image → HOG → LBP → mask
    ax1 = fig.add_subplot(2, 4, 1)
    ax1.imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    ax1.set_title("Input Image"); ax1.axis("off")

    ax2 = fig.add_subplot(2, 4, 2)
    ax2.imshow(hog_img, cmap="inferno")
    ax2.set_title("HOG"); ax2.axis("off")

    ax3 = fig.add_subplot(2, 4, 3)
    ax3.imshow(lbp_map, cmap="viridis")
    ax3.set_title("LBP texture map"); ax3.axis("off")

    ax4 = fig.add_subplot(2, 4, 4)
    ax4.imshow(mask, cmap="Greens")
    ax4.set_title("Green mask (shape)"); ax4.axis("off")

    # Row 2: HSV histograms
    ax5 = fig.add_subplot(2, 4, 5)
    ax5.bar(range(32), hue_hist, color="#e74c3c")
    ax5.set_title("Hue histogram"); ax5.set_xlabel("Bin"); ax5.set_ylabel("Count")

    ax6 = fig.add_subplot(2, 4, 6)
    ax6.bar(range(32), sat_hist, color="#3498db")
    ax6.set_title("Saturation histogram"); ax6.set_xlabel("Bin")

    ax7 = fig.add_subplot(2, 4, 7)
    ax7.bar(range(32), val_hist, color="#f39c12")
    ax7.set_title("Value histogram"); ax7.set_xlabel("Bin")

    ax8 = fig.add_subplot(2, 4, 8)
    shape_feats = extract_shape_size(img_bgr)
    labels_sh   = ["area", "aspect", "extent", "solidity", "eq_diam", "circular",
                   "hu0", "hu1", "hu2", "hu3", "hu4", "hu5"]
    ax8.barh(labels_sh, shape_feats, color="#9b59b6")
    ax8.set_title("Shape + Size features")
    ax8.tick_params(axis="y", labelsize=7)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[Saved] {save_path}")
    plt.show()


def visualise_feature_comparison(images: np.ndarray, labels: np.ndarray,
                                  n_samples: int = 5, save_path: str = None):
    """
    Show colour histograms and LBP histograms averaged over weed vs. crop.
    Useful for sanity-checking that the features actually differ between classes.
    """
    weed_idx = np.where(labels == 1)[0]
    crop_idx = np.where(labels == 0)[0]

    np.random.seed(42)
    weed_sample = np.random.choice(weed_idx, min(n_samples, len(weed_idx)), replace=False)
    crop_sample = np.random.choice(crop_idx, min(n_samples, len(crop_idx)), replace=False)

    def avg_hist(idxs, fn):
        return np.mean([fn(images[i]) for i in idxs], axis=0)

    weed_colour = avg_hist(weed_sample, extract_colour_histograms)
    crop_colour = avg_hist(crop_sample, extract_colour_histograms)
    weed_lbp    = avg_hist(weed_sample, extract_lbp)
    crop_lbp    = avg_hist(crop_sample, extract_lbp)

    fig, axes = plt.subplots(1, 2, figsize=(14, 4))
    fig.suptitle("Feature Comparison: Weed vs. Crop (averaged)", fontsize=12, fontweight="bold")

    x = np.arange(len(weed_colour))
    axes[0].plot(x, weed_colour, color="#e74c3c", label="Weed",     linewidth=1.5)
    axes[0].plot(x, crop_colour, color="#2ecc71", label="Non-Weed", linewidth=1.5)
    axes[0].set_title("Colour Histogram (H+S+V concatenated)")
    axes[0].set_xlabel("Bin"); axes[0].set_ylabel("Normalised count")
    axes[0].legend()

    x2 = np.arange(len(weed_lbp))
    axes[1].plot(x2, weed_lbp, color="#e74c3c", label="Weed",     linewidth=1.5)
    axes[1].plot(x2, crop_lbp, color="#2ecc71", label="Non-Weed", linewidth=1.5)
    axes[1].set_title("LBP Histogram (texture)")
    axes[1].set_xlabel("Pattern bin"); axes[1].set_ylabel("Density")
    axes[1].legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[Saved] {save_path}")
    plt.show()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("data",    exist_ok=True)

    # ── Load preprocessed images ──────────────
    print("\n[Step 3] Loading preprocessed images ...")
    images  = np.load("data/images_preprocessed.npy")
    labels  = np.load("data/labels.npy")
    species = np.load("data/species.npy", allow_pickle=True)
    print(f"  Loaded {len(images)} images  shape={images.shape}")

    # ── Show feature groups on one example ────
    print("\n[Step 3] Visualising feature extraction on a sample image ...")
    sample_idx = np.where(labels == 1)[0][0]   # first weed image
    visualise_feature_groups(images[sample_idx],
                             save_path="outputs/step3_feature_visualisation.png")

    # ── Print feature group sizes ─────────────
    sizes = get_feature_group_sizes(images[0])
    total = sum(sizes.values())
    print("\n  Feature group sizes:")
    for name, size in sizes.items():
        print(f"    {name:<15} {size:>5} features")
    print(f"    {'TOTAL':<15} {total:>5} features per image")

    # ── Compare weed vs. crop features ────────
    print("\n[Step 3] Comparing feature distributions: weed vs. crop ...")
    visualise_feature_comparison(images, labels, n_samples=50,
                                 save_path="outputs/step3_feature_comparison.png")

    # ── Extract features for ALL images ───────
    print(f"\n[Step 3] Extracting features for all {len(images)} images ...")
    features = extract_all(images, verbose=True)
    print(f"\n  Feature matrix shape: {features.shape}")

    # ── Sanity check: no NaN / Inf ─────────────
    n_nan = np.isnan(features).sum()
    n_inf = np.isinf(features).sum()
    print(f"  NaN values : {n_nan}")
    print(f"  Inf values : {n_inf}")
    if n_nan > 0 or n_inf > 0:
        print("  [WARNING] Replacing NaN/Inf with 0")
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    # ── Save ───────────────────────────────────
    np.save("data/features.npy", features)
    np.save("data/labels.npy",   labels)    # re-save just to be sure

    # Save feature group name array for reference
    group_labels = (
        ["HOG"]         * sizes["HOG"] +
        ["LBP"]         * sizes["LBP"] +
        ["ColourHist"]  * sizes["ColourHist"] +
        ["Shape+Size"]  * sizes["Shape+Size"]
    )
    np.save("data/feature_groups.npy", np.array(group_labels))

    print(f"\n[Step 3] Done!")
    print(f"  Saved: data/features.npy        shape={features.shape}")
    print(f"  -> Ready for Step 4: Train Classifier")
