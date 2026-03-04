# pc_server.py — Runs on PC, receives detection image from rover
# Usage: python pc_server.py

import os
from datetime import datetime
from flask import Flask, request, jsonify

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
        return jsonify({"error": "no image received"}), 400

    # Name file with timestamp for uniqueness
    safe_ts = timestamp.replace(":", "-").replace(" ", "_") if timestamp else datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detection_{safe_ts}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)
    image.save(filepath)

    # Log to console
    print(f"\n{'='*50}")
    print(f"  DETECTION RECEIVED")
    print(f"  Time:      {timestamp}")
    print(f"  Image:     {filepath}")
    print(f"  Size:      {os.path.getsize(filepath)} bytes")
    print(f"{'='*50}\n")

    return jsonify({"status": "ok", "saved": filename}), 200


@app.route("/", methods=["GET"])
def index():
    """Health check / landing page."""
    return "Rover PC Server is running. POST to /detection to send data."


if __name__ == "__main__":
    print("Starting PC server...")
    print(f"Saving images to: {os.path.abspath(SAVE_DIR)}/")
    print("Listening on 0.0.0.0:5000\n")
    app.run(host="0.0.0.0", port=5000)
