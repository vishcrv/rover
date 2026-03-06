# streaming/server.py — Flask MJPEG live video streaming server

import cv2
import time
import threading
from flask import Flask, Response
from utils.config import STREAM_HOST, STREAM_PORT
from modules import camera

app = Flask(__name__)

_server_thread = None


def _generate_frames():
    """Yield JPEG frames as an MJPEG stream.

    Reads from the shared camera module — same frames used by detection.
    """
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        # Encode frame as JPEG
        ret, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        )


@app.route("/video")
def video_feed():
    """MJPEG stream endpoint — open in browser."""
    return Response(
        _generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/")
def index():
    """Simple page that embeds the live stream."""
    return (
        "<html><head><title>Rover Stream</title></head>"
        "<body style='margin:0;background:#111;display:flex;"
        "justify-content:center;align-items:center;height:100vh'>"
        "<img src='/video' style='max-width:100%;max-height:100%'>"
        "</body></html>"
    )


def start(blocking=False):
    """Start the streaming server.

    Args:
        blocking: If True, runs in the current thread (blocks).
                  If False, runs in a daemon thread (non-blocking).
    """
    global _server_thread

    if blocking:
        app.run(host=STREAM_HOST, port=STREAM_PORT, threaded=True)
    else:
        _server_thread = threading.Thread(
            target=lambda: app.run(host=STREAM_HOST, port=STREAM_PORT, threaded=True),
            daemon=True,
        )
        _server_thread.start()
