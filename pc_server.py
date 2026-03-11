# pc_server.py — Runs on PC, receives detection image from rover
# Usage: python pc_server.py

import os
import logging
import json
import weed_classifier
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

    # Hardcoded coordinates (4 corners of a square room)
    ROOM_CORNERS = [
        {"lat": 12.843829, "lon": 80.154387},
        {"lat": 12.843830, "lon": 80.154322},
        {"lat": 12.843741, "lon": 80.154350},
        {"lat": 12.843748, "lon": 80.154368}
    ]

    # Classify image using the trained weed detection model
    try:
        result = weed_classifier.classify(filepath)
        weed_probability = result["probability"]
        weed_label = result["label"]
    except Exception as e:
        log.error("Weed classification failed: %s", e)
        weed_probability = 0.0
        weed_label = "ERROR"

    # Load existing log entries (needed for coordinate cycling)
    log_file = os.path.join(SAVE_DIR, "detection_logs.json")
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except Exception as e:
            log.error("Failed to read existing log file: %s", e)

    coord = ROOM_CORNERS[len(logs) % len(ROOM_CORNERS)]

    log_entry = {
        "timestamp": timestamp if timestamp else safe_ts,
        "image_path": filepath,
        "coordinates": coord,
        "weed_probability": weed_probability,
        "weed_label": weed_label,
    }
    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)

    log.info("=" * 50)
    log.info("  DETECTION RECEIVED")
    log.info("  Time:      %s", timestamp)
    log.info("  Image:     %s", filepath)
    log.info("  Size:      %d bytes", size)
    log.info("  Coord:     %.6f, %.6f", coord["lat"], coord["lon"])
    log.info("  Weed:      %s  (P=%.4f)", weed_label, weed_probability)
    log.info("=" * 50)

    return jsonify({"status": "ok", "saved": filename, "log_entry": log_entry}), 200


@app.route("/", methods=["GET"])
def index():
    """Health check / landing page."""
    return "Rover PC Server is running. POST to /detection to send data."


if __name__ == "__main__":
    log.info("Starting PC server...")
    weed_classifier.init()
    log.info("Saving images to: %s/", os.path.abspath(SAVE_DIR))
    log.info("Listening on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
