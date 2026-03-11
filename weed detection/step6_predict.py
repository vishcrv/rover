"""
=============================================================
WEED CLASSIFIER - STEP 6: Predict on New Images
=============================================================
Usage:
    python step6_predict.py --image path/to/plant.jpg
    python step6_predict.py --folder path/to/images/
    python step6_predict.py --image plant.jpg --threshold 0.4
=============================================================
"""

import os
import sys
import argparse
import pickle
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# preprocess_image is in step2, extract_features is in step3
from step2_preprocessing     import preprocess_image
from step3_feature_extraction import extract_features

IMAGE_SIZE = (128, 128)
VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


# ---------------------------------------------
# 1. LOAD MODEL
# ---------------------------------------------

def load_model(model_dir: str = "models"):
    with open(f"{model_dir}/scaler.pkl",     "rb") as f: scaler     = pickle.load(f)
    with open(f"{model_dir}/svm_model.pkl",  "rb") as f: svm        = pickle.load(f)
    with open(f"{model_dir}/thresholds.pkl", "rb") as f: thresholds = pickle.load(f)
    threshold = float(thresholds.get("SVM", 0.5))
    print(f"  Model loaded  |  threshold = {threshold:.2f}")
    return scaler, svm, threshold


# ---------------------------------------------
# 2. PREDICT SINGLE IMAGE
# ---------------------------------------------

def predict_image(img_path: str, scaler, svm, threshold: float):
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        raise ValueError(f"Could not read image: {img_path}")

    img_bgr  = cv2.resize(img_bgr, IMAGE_SIZE)
    img_proc = preprocess_image(img_bgr)          # step2: denoise, CLAHE, colour norm
    features = extract_features(img_proc).reshape(1, -1)   # step3: HOG+LBP+colour+shape
    feat_sc  = scaler.transform(features)
    prob     = svm.predict_proba(feat_sc)[0, 1]   # P(weed)
    label    = "WEED" if prob >= threshold else "NON-WEED"

    return label, float(prob), img_proc


# ---------------------------------------------
# 3. HELPERS
# ---------------------------------------------

def confidence_bar(prob: float, width: int = 30) -> str:
    filled = int(prob * width)
    return f"[{'=' * filled}{' ' * (width - filled)}] {prob*100:.1f}%"


# ---------------------------------------------
# 4. ANNOTATE + SAVE
# ---------------------------------------------

def save_annotated(img_bgr, label: str, prob: float,
                   img_path: str, out_dir: str = "outputs/predictions"):
    os.makedirs(out_dir, exist_ok=True)

    img_rgb  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    is_weed  = label == "WEED"
    color    = "#e74c3c" if is_weed else "#2ecc71"
    bg_color = (0.95, 0.88, 0.88) if is_weed else (0.88, 0.95, 0.88)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4),
                             gridspec_kw={"width_ratios": [1, 1.2]})
    fig.patch.set_facecolor(bg_color)

    # Left: image
    axes[0].imshow(img_rgb)
    axes[0].set_title(Path(img_path).name, fontsize=9, color="gray")
    axes[0].axis("off")

    # Right: result card
    ax = axes[1]
    ax.set_facecolor(bg_color)
    ax.axis("off")

    verdict = "WEED DETECTED" if is_weed else "NOT A WEED"
    ax.text(0.5, 0.75, verdict, ha="center", va="center",
            fontsize=22, fontweight="bold", color=color,
            transform=ax.transAxes)
    ax.text(0.5, 0.52, f"P(weed) = {prob:.3f}",
            ha="center", va="center", fontsize=14,
            color="#333333", transform=ax.transAxes)

    # Confidence gauge
    bar_ax = fig.add_axes([0.57, 0.28, 0.36, 0.07])
    bar_ax.barh([0], [prob],       color=color,     height=0.6)
    bar_ax.barh([0], [1 - prob],   color="#dddddd", height=0.6, left=prob)
    bar_ax.set_xlim(0, 1)
    bar_ax.axvline(0.5, color="gray", linewidth=1, linestyle="--", alpha=0.6)
    bar_ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    bar_ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    bar_ax.set_yticks([])
    bar_ax.set_title("Confidence", fontsize=9, pad=3)

    axes[1].text(0.5, 0.10,
                 "Note: model has high weed recall\nbut may flag some crops as weeds",
                 ha="center", va="center", fontsize=7.5,
                 color="gray", transform=axes[1].transAxes, style="italic")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.suptitle("Weed Classifier -- Prediction", fontsize=11,
                 fontweight="bold", color="#333333")

    stem    = Path(img_path).stem
    outpath = os.path.join(out_dir, f"{stem}_prediction.png")
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()
    return outpath


# ---------------------------------------------
# 5. BATCH FOLDER
# ---------------------------------------------

def predict_folder(folder: str, scaler, svm, threshold: float,
                   out_dir: str = "outputs/predictions"):
    folder    = Path(folder)
    img_paths = sorted([p for p in folder.iterdir()
                        if p.suffix.lower() in VALID_EXTS])

    if not img_paths:
        print(f"  No images found in {folder}")
        return []

    print(f"\n  Found {len(img_paths)} images\n")
    print(f"  {'File':<40} {'Label':<10} {'P(weed)':>8}  Confidence")
    print("  " + "-"*75)

    results = []
    for img_path in img_paths:
        try:
            label, prob, img_proc = predict_image(str(img_path), scaler, svm, threshold)
            bar  = confidence_bar(prob, width=20)
            flag = " <-- WEED" if label == "WEED" else ""
            print(f"  {img_path.name:<40} {label:<10} {prob:>7.3f}  {bar}{flag}")
            results.append({"file": img_path.name, "label": label, "prob": prob})
            save_annotated(img_proc, label, prob, str(img_path), out_dir)
        except Exception as e:
            print(f"  [ERROR] {img_path.name}: {e}")

    n_weed = sum(1 for r in results if r["label"] == "WEED")
    n_crop = len(results) - n_weed
    print("\n" + "="*50)
    print(f"  BATCH SUMMARY  ({len(results)} images)")
    print(f"  WEED     : {n_weed}  ({100*n_weed/max(len(results),1):.0f}%)")
    print(f"  NON-WEED : {n_crop}  ({100*n_crop/max(len(results),1):.0f}%)")
    print("="*50)
    return results


def plot_batch_summary(results: list, save_path: str = None):
    if not results:
        return
    names  = [r["file"] for r in results]
    probs  = [r["prob"] for r in results]
    colors = ["#e74c3c" if r["label"] == "WEED" else "#2ecc71" for r in results]

    fig, ax = plt.subplots(figsize=(max(8, len(results)*0.8), 5))
    bars = ax.bar(range(len(names)), probs, color=colors, edgecolor="white")
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([Path(n).stem for n in names],
                       rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("P(weed)"); ax.set_ylim(0, 1.1)
    ax.set_title("Batch Prediction Results", fontsize=13, fontweight="bold")
    for bar, prob in zip(bars, probs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{prob:.2f}", ha="center", va="bottom", fontsize=8)
    weed_p = mpatches.Patch(color="#e74c3c", label="WEED")
    crop_p = mpatches.Patch(color="#2ecc71", label="NON-WEED")
    ax.legend(handles=[weed_p, crop_p])
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[Saved] {save_path}")
    plt.show()


# ---------------------------------------------
# MAIN
# ---------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weed Classifier -- predict on new images")
    parser.add_argument("--image",     type=str,   help="Path to a single image")
    parser.add_argument("--folder",    type=str,   help="Path to a folder of images")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Override decision threshold (default: use saved value)")
    parser.add_argument("--model_dir", type=str,   default="models")
    parser.add_argument("--out_dir",   type=str,   default="outputs/predictions")
    args = parser.parse_args()

    if not args.image and not args.folder:
        parser.print_help()
        print("\nExamples:")
        print("  python step6_predict.py --image my_plant.jpg")
        print("  python step6_predict.py --folder my_plants/")
        sys.exit(0)

    print("\n[Step 6] Loading model ...")
    scaler, svm, threshold = load_model(args.model_dir)

    if args.threshold is not None:
        threshold = args.threshold
        print(f"  Threshold overridden to {threshold:.2f}")

    os.makedirs(args.out_dir, exist_ok=True)

    if args.image:
        print(f"\n[Step 6] Predicting: {args.image}")
        label, prob, img_proc = predict_image(args.image, scaler, svm, threshold)
        print("\n" + "="*50)
        print(f"  FILE      : {Path(args.image).name}")
        print(f"  RESULT    : {label}")
        print(f"  P(weed)   : {prob:.4f}")
        print(f"  CONFIDENCE: {confidence_bar(prob)}")
        print("="*50)
        out = save_annotated(img_proc, label, prob, args.image, args.out_dir)
        print(f"\n  Saved: {out}")

    if args.folder:
        print(f"\n[Step 6] Batch predicting: {args.folder}")
        results = predict_folder(args.folder, scaler, svm, threshold, args.out_dir)
        if results:
            plot_batch_summary(results,
                save_path=os.path.join(args.out_dir, "batch_summary.png"))

    print("\n[Step 6] Done!")
