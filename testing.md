# Leaf Detection — Testing & Tuning Guide

This guide explains how to run each test, what to look for, and how to tune the detection parameters in `config/settings.py` for your specific environment.

---

## Quick-Start

```bash
# On the Raspberry Pi, from the project root:

# 1. Run the detection test (console output)
python -m tests.test_detection        # choose option 3

# 2. Run the streaming test (browser)
python -m tests.test_stream           # choose option 1
# Then open  http://<PI_IP>:8080  — you'll see annotated frames
```

---

## Test Scripts

| Script | Option | What it does |
|--------|--------|--------------|
| `tests/test_detection.py` | 1 | Camera feed sanity check (frame shapes) |
| | 2 | Capture a still image |
| | 3 | **Leaf detection (live)** — prints per-leaf features (area, aspect ratio, solidity, circularity, bbox) |
| | 4 | Multi-frame confirmation — tracks consecutive detections |
| | 5 | Annotated preview — OpenCV window with contour overlays (needs display) |
| `tests/test_stream.py` | 1 | **Streaming only** — open browser to see annotated leaf detection stream |
| | 2 | Capture + send to PC |
| | 3 | Stream + capture + send |

---

## Tuning Parameters

All parameters live in `config/settings.py`. Edit them on the Pi and re-run a test; no rebuild needed.

### Preprocessing

| Parameter | Default | What it controls |
|-----------|---------|------------------|
| `USE_GREEN_MASK` | `True` | `True` = HSV green mask isolates candidates; `False` = adaptive threshold on grayscale |
| `GREEN_LOWER` | `(35, 50, 50)` | Lower HSV bound for the green mask |
| `GREEN_UPPER` | `(85, 255, 255)` | Upper HSV bound for the green mask |
| `BLUR_KERNEL_SIZE` | `5` | Gaussian blur kernel (must be odd). Larger = smoother but slower |

**How to tune:**
1. Run test option 3 and point the camera at a leaf.
2. If nothing is detected, try widening `GREEN_LOWER` / `GREEN_UPPER` (e.g. lower the S/V minimums).
3. If too much noise, narrow the range or increase `BLUR_KERNEL_SIZE` to 7 or 9.
4. If leaves are not green (e.g. autumn leaves), set `USE_GREEN_MASK = False` to use adaptive thresholding instead.

### Edge Detection

| Parameter | Default | What it controls |
|-----------|---------|------------------|
| `CANNY_LOW` | `50` | Lower hysteresis threshold |
| `CANNY_HIGH` | `150` | Upper hysteresis threshold |

**How to tune:**
- Lower both values → more edges detected (more candidates, more noise).
- Raise both values → fewer edges (may miss faint leaf outlines).
- A good ratio is roughly 1:3 (e.g. 50:150 or 30:90).

### Shape Filtering

These are the most important parameters for accuracy.

| Parameter | Default | Typical leaf range | Description |
|-----------|---------|-------------------|-------------|
| `LEAF_MIN_AREA` | `500` | 500–2000 | Minimum contour area (pixels²) |
| `LEAF_MAX_AREA` | `100000` | 50000–150000 | Maximum contour area |
| `LEAF_ASPECT_RATIO_MIN` | `0.3` | 0.2–0.5 | Width/height lower bound |
| `LEAF_ASPECT_RATIO_MAX` | `3.5` | 2.5–4.0 | Width/height upper bound |
| `LEAF_SOLIDITY_MIN` | `0.5` | 0.4–0.7 | Contour area / convex hull area |
| `LEAF_CIRCULARITY_MIN` | `0.15` | 0.1–0.3 | Lower circularity bound |
| `LEAF_CIRCULARITY_MAX` | `0.85` | 0.7–0.9 | Upper circularity bound |

**How to tune:**
1. Run test option 3 — you'll see the feature values printed for every detection.
2. Point at a **real leaf** and note the area, aspect_ratio, solidity, circularity values.
3. Point at **non-leaf objects** (rocks, sticks, ground) and note their values.
4. Adjust the min/max bounds so real leaves fall inside and non-leaves fall outside.
5. Iterate: change a value → re-run → check console output.

### Detection Confirmation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DETECTION_CONFIRM_FRAMES` | `5` | Consecutive frames with a leaf before triggering a confirmed detection |

- Increase for fewer false positives (but slower response).
- Decrease for faster response (but more false positives).

---

## Tuning Workflow (Step by Step)

1. **Start with defaults** — run test option 3 and point at leaves.
2. **Check green mask** — if leaves aren't green, set `USE_GREEN_MASK = False`.
3. **Adjust area** — if small leaves are missed, lower `LEAF_MIN_AREA`. If large background blobs are picked up, lower `LEAF_MAX_AREA`.
4. **Adjust shape thresholds** — use the printed feature values from test option 3 to dial in `LEAF_ASPECT_RATIO_*`, `LEAF_SOLIDITY_MIN`, and `LEAF_CIRCULARITY_*`.
5. **Verify with stream** — run `test_stream` option 1 and open the browser to see live annotated frames. Confirm that only leaves are highlighted.
6. **Test confirmation** — run test option 4 to verify that pointing at a leaf for ~0.5s triggers a confirmed detection.

---

## Debugging Tips

- **Too many false positives?** → Raise `LEAF_SOLIDITY_MIN` (e.g. 0.6–0.7). Leaves have smooth boundaries; irregular shapes don't.
- **Missing real leaves?** → Lower `LEAF_CIRCULARITY_MIN` and widen the aspect ratio range.
- **Noisy edges everywhere?** → Raise `CANNY_LOW` and `CANNY_HIGH` (e.g. 80/200).
- **Want to see the raw mask?** → Use test option 5 (annotated preview) and temporarily add `cv2.imshow("mask", mask)` inside `leaf_preprocessor.preprocess()`.
- **Streaming endpoint** → `/video` shows annotated frames, `/video_raw` shows the raw camera feed for comparison.
