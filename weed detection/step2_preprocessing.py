"""
=============================================================
WEED CLASSIFIER — STEP 2: Preprocessing
=============================================================
Input  : data/images.npy  (N, 128, 128, 3)  raw BGR uint8
Output : data/images_preprocessed.npy  (N, 128, 128, 3)  processed BGR uint8
         data/images_preprocessed_norm.npy  (N, 128, 128, 3)  float32 [0,1]
=============================================================

PREPROCESSING PIPELINE (applied to every image):
    1. Gaussian blur       — reduce sensor noise
    2. CLAHE               — fix uneven lighting / contrast
    3. Colour normalisation— make colours consistent across images
    4. Resize guard        — ensure all images are exactly 128x128
    5. Quality check       — flag near-black / near-white images

WHY EACH STEP?
    - Plant seedling photos vary widely in lighting, soil colour, and camera
      distance.  Normalising contrast and colour before feature extraction
      makes HOG, LBP, and colour histograms far more consistent.
=============================================================
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

TARGET_SIZE = (128, 128)   # (width, height)


# ─────────────────────────────────────────────
# INDIVIDUAL PREPROCESSING STEPS
# ─────────────────────────────────────────────

def denoise(img_bgr: np.ndarray) -> np.ndarray:
    """
    Mild Gaussian blur to suppress high-frequency noise.
    Kernel 3x3 is enough for 128x128 images — doesn't blur edges needed for HOG.
    """
    return cv2.GaussianBlur(img_bgr, (3, 3), sigmaX=0)


def enhance_contrast(img_bgr: np.ndarray) -> np.ndarray:
    """
    CLAHE (Contrast Limited Adaptive Histogram Equalization) on the L channel
    of LAB colour space.  Boosts local contrast without washing out colour.
    """
    lab  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq  = clahe.apply(l)

    lab_eq = cv2.merge([l_eq, a, b])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)


def normalise_colour(img_bgr: np.ndarray) -> np.ndarray:
    """
    Per-channel min-max stretch so each channel uses the full 0-255 range.
    Removes systematic colour casts from different cameras / lighting.
    """
    out = np.zeros_like(img_bgr, dtype=np.uint8)
    for c in range(3):
        ch = img_bgr[:, :, c].astype(np.float32)
        lo, hi = ch.min(), ch.max()
        if hi > lo:
            ch = (ch - lo) / (hi - lo) * 255.0
        out[:, :, c] = np.clip(ch, 0, 255).astype(np.uint8)
    return out


def resize_guard(img_bgr: np.ndarray, size: tuple = TARGET_SIZE) -> np.ndarray:
    """Ensure the image is exactly TARGET_SIZE (should already be, but just in case)."""
    if img_bgr.shape[:2] != (size[1], size[0]):
        img_bgr = cv2.resize(img_bgr, size, interpolation=cv2.INTER_AREA)
    return img_bgr


# ─────────────────────────────────────────────
# FULL PIPELINE
# ─────────────────────────────────────────────

def preprocess_image(img_bgr: np.ndarray) -> np.ndarray:
    """
    Apply the full preprocessing pipeline to a single BGR image.
    Returns a uint8 BGR image ready for feature extraction.
    """
    img = resize_guard(img_bgr)
    img = denoise(img)
    img = enhance_contrast(img)
    img = normalise_colour(img)
    return img


def preprocess_dataset(images: np.ndarray, verbose: bool = True) -> np.ndarray:
    """
    Apply preprocess_image() to every image in the array.

    Args:
        images  : (N, H, W, 3) uint8
        verbose : print progress every 500 images

    Returns:
        processed : (N, H, W, 3) uint8
    """
    N = len(images)
    processed = np.zeros_like(images)

    for i, img in enumerate(images):
        processed[i] = preprocess_image(img)
        if verbose and (i + 1) % 500 == 0:
            print(f"  Preprocessed {i + 1}/{N} images ...")

    return processed


# ─────────────────────────────────────────────
# QUALITY CHECK
# ─────────────────────────────────────────────

def quality_check(images: np.ndarray, low_thresh: int = 15, high_thresh: int = 240):
    """
    Flag images that are nearly all black or nearly all white —
    these are likely corrupt/blank and could hurt training.

    Returns list of (index, mean_pixel_value) for flagged images.
    """
    flagged = []
    means   = images.mean(axis=(1, 2, 3))   # mean over H, W, C

    for i, mean in enumerate(means):
        if mean < low_thresh or mean > high_thresh:
            flagged.append((i, round(float(mean), 1)))

    return flagged, means


# ─────────────────────────────────────────────
# VISUALISATIONS
# ─────────────────────────────────────────────

def visualise_pipeline(raw_images: np.ndarray, indices: list = None,
                       save_path: str = None):
    """
    Show before / after for each preprocessing step side-by-side.
    """
    if indices is None:
        np.random.seed(0)
        indices = np.random.choice(len(raw_images), 3, replace=False).tolist()

    steps     = ["Raw", "Denoised", "CLAHE", "Colour Norm"]
    n_samples = len(indices)

    fig, axes = plt.subplots(n_samples, len(steps),
                             figsize=(3.5 * len(steps), 3.2 * n_samples))
    fig.suptitle("Preprocessing Pipeline  |  Each row = one image",
                 fontsize=13, fontweight="bold")

    for row, idx in enumerate(indices):
        raw      = raw_images[idx]
        denoised = denoise(resize_guard(raw))
        clahe    = enhance_contrast(denoised)
        colnorm  = normalise_colour(clahe)

        stage_imgs = [raw, denoised, clahe, colnorm]
        for col, (stage_img, title) in enumerate(zip(stage_imgs, steps)):
            ax = axes[row, col] if n_samples > 1 else axes[col]
            ax.imshow(cv2.cvtColor(stage_img, cv2.COLOR_BGR2RGB))
            if row == 0:
                ax.set_title(title, fontsize=10, fontweight="bold")
            ax.axis("off")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[Saved] {save_path}")
    plt.show()


def visualise_brightness_distribution(raw_means: np.ndarray, proc_means: np.ndarray,
                                      save_path: str = None):
    """Histogram of mean pixel values before and after preprocessing."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    for ax, means, title, color in zip(
        axes,
        [raw_means, proc_means],
        ["Raw images — brightness distribution",
         "Preprocessed — brightness distribution"],
        ["#3498db", "#2ecc71"]
    ):
        ax.hist(means, bins=50, color=color, edgecolor="white", alpha=0.85)
        ax.axvline(means.mean(), color="red", linestyle="--",
                   label=f"Mean = {means.mean():.1f}")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Mean pixel value (0-255)")
        ax.set_ylabel("Number of images")
        ax.legend()

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

    # ── Load Step 1 output ────────────────────
    print("\n[Step 2] Loading raw images from data/ ...")
    images  = np.load("data/images.npy")
    labels  = np.load("data/labels.npy")
    species = np.load("data/species.npy", allow_pickle=True)
    print(f"  Loaded {len(images)} images  shape={images.shape}")

    # ── Quality check BEFORE preprocessing ────
    print("\n[Step 2] Running quality check on raw images ...")
    flagged_raw, raw_means = quality_check(images)
    if flagged_raw:
        print(f"  WARNING: {len(flagged_raw)} potentially corrupt images found:")
        for idx, mean in flagged_raw[:10]:
            print(f"    index={idx}  mean_pixel={mean}  species={species[idx]}")
    else:
        print(f"  All {len(images)} images passed quality check.")

    # ── Visualise pipeline steps ───────────────
    print("\n[Step 2] Visualising preprocessing pipeline ...")
    visualise_pipeline(images, indices=None,
                       save_path="outputs/step2_pipeline_steps.png")

    # ── Apply preprocessing ────────────────────
    print("\n[Step 2] Preprocessing all images ...")
    images_proc = preprocess_dataset(images, verbose=True)
    print(f"  Done. Shape: {images_proc.shape}")

    # ── Quality check AFTER preprocessing ─────
    flagged_proc, proc_means = quality_check(images_proc)
    print(f"\n[Step 2] Post-preprocessing quality check: "
          f"{len(flagged_proc)} flagged images.")

    # ── Brightness distribution plot ──────────
    visualise_brightness_distribution(
        raw_means, proc_means,
        save_path="outputs/step2_brightness_distribution.png"
    )

    # ── Save outputs ───────────────────────────
    # uint8 version (for feature extraction)
    np.save("data/images_preprocessed.npy", images_proc)

    # float32 [0, 1] version (for any CNN steps later)
    images_norm = images_proc.astype(np.float32) / 255.0
    np.save("data/images_preprocessed_norm.npy", images_norm)

    print("\n[Step 2] Done!")
    print("  Saved: data/images_preprocessed.npy      (uint8  — for feature extraction)")
    print("  Saved: data/images_preprocessed_norm.npy (float32 — for CNN if needed)")
    print("  -> Ready for Step 3: Feature Extraction")
