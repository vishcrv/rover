# weed_classifier.py — Server-side weed classification using trained SVM model
#
# Wraps the weed detection pipeline (step2 preprocessing + step3 feature
# extraction + SVM model) into a simple classify() API for use by pc_server.py.

import os
import sys
import logging

log = logging.getLogger("weed_classifier")

# ---------------------------------------------------------------------------
# Add the 'weed detection' directory to sys.path so we can import its modules
# ---------------------------------------------------------------------------
_WEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weed detection")
_MODEL_DIR = os.path.join(_WEED_DIR, "models")

sys.path.insert(0, _WEED_DIR)

from step6_predict import load_model, predict_image  # noqa: E402

# ---------------------------------------------------------------------------
# Load model once at import time — avoids reloading on every request
# ---------------------------------------------------------------------------
_scaler = None
_svm = None
_threshold = None


def init():
    """Load the SVM model, scaler, and threshold from disk.

    Called once at server startup.  Safe to call multiple times (idempotent).
    """
    global _scaler, _svm, _threshold

    if _scaler is not None:
        return  # already loaded

    log.info("Loading weed detection model from %s ...", _MODEL_DIR)
    _scaler, _svm, _threshold = load_model(_MODEL_DIR)
    log.info("Weed model ready  (threshold=%.2f)", _threshold)


def classify(image_path):
    """Classify a single image as weed or non-weed.

    Args:
        image_path: Path to a saved JPEG/PNG image file.

    Returns:
        dict with keys:
            is_weed       (bool)  — True if the model classifies as weed
            probability   (float) — P(weed) from the SVM, range [0, 1]
            label         (str)   — "WEED" or "NON-WEED"
    """
    if _scaler is None:
        init()

    label, prob, _ = predict_image(image_path, _scaler, _svm, _threshold)

    return {
        "is_weed": label == "WEED",
        "probability": round(prob, 4),
        "label": label,
    }
