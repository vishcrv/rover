# streaming/server.py — Flask MJPEG live video streaming server
#
# Streams annotated leaf-detection frames so the browser shows
# contour outlines, bounding boxes and labels in real time.

import cv2
import time
import logging
import threading
from flask import Flask, Response
from config.settings import STREAM_HOST, STREAM_PORT
from modules import camera, detector

# Suppress werkzeug request logs so they don't drown out application logs
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)

_server_thread = None

# Thread-safe storage for the latest annotated frame
_annotated_lock = threading.Lock()
_latest_annotated = None


# --------------------------------------------------------------------------- #
# Background detection + annotation loop
# --------------------------------------------------------------------------- #

def _detection_render_loop():
    """Continuously grab frames, run leaf detection, and cache the annotated result."""
    global _latest_annotated
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        # Run the leaf detection pipeline and annotate
        leaves = detector.detect_leaves(frame)
        annotated = detector.annotate_frame(frame, leaves)

        with _annotated_lock:
            _latest_annotated = annotated

        time.sleep(0.03)  # ~30 fps cap to avoid saturating the CPU


# --------------------------------------------------------------------------- #
# Frame generators
# --------------------------------------------------------------------------- #

def _generate_annotated_frames():
    """Yield annotated JPEG frames as an MJPEG stream."""
    while True:
        with _annotated_lock:
            frame = _latest_annotated

        if frame is None:
            time.sleep(0.05)
            continue

        ret, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        )
        time.sleep(0.03)


def _generate_raw_frames():
    """Yield raw (un-annotated) JPEG frames as an MJPEG stream."""
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        # Camera gives RGB; imencode expects BGR
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, jpeg = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        )
        time.sleep(0.03)


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #

@app.route("/video")
def video_feed():
    """MJPEG stream with leaf-detection overlays — open in browser."""
    return Response(
        _generate_annotated_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/video_raw")
def video_raw_feed():
    """MJPEG stream of the raw camera feed (no overlays)."""
    return Response(
        _generate_raw_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/")
def index():
    """Simple page that embeds the annotated live stream."""
    return (
        "<html><head><title>Rover — Leaf Detection Stream</title></head>"
        "<body style='margin:0;background:#111;display:flex;"
        "justify-content:center;align-items:center;height:100vh'>"
        "<img src='/video' style='max-width:100%;max-height:100%'>"
        "</body></html>"
    )


# --------------------------------------------------------------------------- #
# Server start
# --------------------------------------------------------------------------- #

def start(blocking=False):
    """Start the streaming server.

    Args:
        blocking: If True, runs in the current thread (blocks).
                  If False, runs in a daemon thread (non-blocking).
    """
    global _server_thread

    # Start the background detection/annotation loop
    render_thread = threading.Thread(target=_detection_render_loop, daemon=True)
    render_thread.start()

    if blocking:
        app.run(host=STREAM_HOST, port=STREAM_PORT, threaded=True)
    else:
        _server_thread = threading.Thread(
            target=lambda: app.run(host=STREAM_HOST, port=STREAM_PORT, threaded=True),
            daemon=True,
        )
        _server_thread.start()
