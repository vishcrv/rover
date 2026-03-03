# tests/test_transmit.py — Validation for data transmission
# Run on Raspberry Pi:  python -m tests.test_transmit
# Run on PC first:      python pc_server.py

import os
import sys
from datetime import datetime
from modules import transmitter


def test_send():
    """Send a test image with dummy GPS data to the PC server."""
    print("=== Transmission Test ===\n")

    # Use a test image — create a small one if none exists
    test_image = "/tmp/test_transmit.jpg"
    if not os.path.exists(test_image):
        try:
            import cv2
            import numpy as np
            # Create a small red test image
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            img[:, :, 2] = 255  # red channel
            cv2.imwrite(test_image, img)
            print(f"  Created test image: {test_image}")
        except ImportError:
            print("  ERROR: No test image and OpenCV not available to create one.")
            print(f"  Place a .jpg file at {test_image} and retry.")
            return

    lat = 12.971599
    lon = 77.594566
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"  Image:     {test_image}")
    print(f"  GPS:       {lat}, {lon}")
    print(f"  Timestamp: {ts}")
    print()

    success = transmitter.send_detection(test_image, lat, lon, ts)

    if success:
        print("  SUCCESS — PC server received the data.")
    else:
        print("  FAILED — check that pc_server.py is running on the PC")
        print(f"           and PC_SERVER_IP in config/settings.py is correct.")


def test_send_no_gps():
    """Send with no GPS fix (None values) — should still succeed."""
    print("=== Transmission Test (No GPS) ===\n")

    test_image = "/tmp/test_transmit.jpg"
    if not os.path.exists(test_image):
        print(f"  Run test 1 first to create {test_image}")
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"  GPS:       None, None")
    print(f"  Timestamp: {ts}")
    print()

    success = transmitter.send_detection(test_image, None, None, ts)

    if success:
        print("  SUCCESS — server handled null GPS gracefully.")
    else:
        print("  FAILED — check server connection.")


def run():
    print("Select test:")
    print("  1 — Send test detection (with GPS)")
    print("  2 — Send test detection (no GPS fix)")

    choice = input("\nEnter choice (1-2): ").strip()

    if choice == "1":
        test_send()
    elif choice == "2":
        test_send_no_gps()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    run()
