# pc_server.py — Runs on PC, receives detection image from rover
# Usage: python pc_server.py

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# ---------------------------------------------------------------------------
# Logging — use proper logging instead of bare print()
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pc_server")

app = Flask(__name__)

SAVE_DIR = "received_detections"
os.makedirs(SAVE_DIR, exist_ok=True)


@app.route("/detection", methods=["POST"])
def receive_detection():
    """Receive detection data from the rover."""
    # Extract timestamp
    timestamp = request.form.get("timestamp", "")

    # Save image
    image = request.files.get("image")
    if image is None:
        log.warning("Received detection with no image")
        return jsonify({"error": "no image received"}), 400

    # Name file with timestamp for uniqueness
    safe_ts = timestamp.replace(":", "-").replace(" ", "_") if timestamp else datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detection_{safe_ts}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)
    image.save(filepath)

    size = os.path.getsize(filepath)

    log.info("=" * 50)
    log.info("  DETECTION RECEIVED")
    log.info("  Time:      %s", timestamp)
    log.info("  Image:     %s", filepath)
    log.info("  Size:      %d bytes", size)
    log.info("=" * 50)

    return jsonify({"status": "ok", "saved": filename}), 200


@app.route("/", methods=["GET"])
def index():
    """Health check / landing page."""
    return "Rover PC Server is running. POST to /detection to send data."


if __name__ == "__main__":
    log.info("Starting PC server...")
    log.info("Saving images to: %s/", os.path.abspath(SAVE_DIR))
    log.info("Listening on 0.0.0.0:5001")
    app.run(host="0.0.0.0", port=5001)
